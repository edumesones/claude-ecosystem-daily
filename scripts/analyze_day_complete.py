#!/usr/bin/env python3
"""
Script para calcular estrellas ganadas en TODO un día específico (14 marzo 2026)
Usando gharchive.org - datos históricos completos por hora.
"""
import json
import gzip
import io
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import httpx

# Configuración
ARCHIVE_DIR = Path("archive")
DATE_TO_ANALYZE = "2026-03-14"  # Día completo a analizar

def download_hourly_data(date: str, hour: int) -> List[dict]:
    """
    Descarga datos de gharchive.org para una hora específica.
    """
    url = f"http://data.gharchive.org/{date}-{hour:02d}.json.gz"
    
    try:
        print(f"   ⏳ Descargando {date}-{hour:02d}h...", end=" ", flush=True)
        response = httpx.get(url, timeout=60)
        
        if response.status_code == 200:
            # Descomprimir y parsear
            decompressed = gzip.decompress(response.content)
            events = []
            
            for line in decompressed.decode('utf-8').strip().split('\n'):
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError:
                    continue
            
            print(f"✅ {len(events):,} eventos")
            return events
        else:
            print(f"⚠️ {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def count_stars_for_day(date: str) -> Dict[str, dict]:
    """
    Cuenta TODAS las estrellas ganadas en un día completo (24 horas).
    """
    repo_stats = defaultdict(lambda: {
        'stars_gained': 0,
        'watch_events': [],
        'name': '',
        'url': '',
    })
    
    print(f"\n📅 Analizando día completo: {date}")
    print("=" * 60)
    
    # Descargar cada hora del día (00-23)
    for hour in range(24):
        events = download_hourly_data(date, hour)
        
        # Filtrar solo WatchEvent (estrellas)
        for event in events:
            if event.get('type') == 'WatchEvent' and event.get('payload', {}).get('action') == 'started':
                repo_name = event.get('repo', {}).get('name', '')
                
                if repo_name:
                    repo_stats[repo_name]['stars_gained'] += 1
                    repo_stats[repo_name]['name'] = repo_name
                    repo_stats[repo_name]['url'] = f"https://github.com/{repo_name}"
                    
                    # Guardar timestamp del evento
                    repo_stats[repo_name]['watch_events'].append({
                        'time': event.get('created_at'),
                        'user': event.get('actor', {}).get('login'),
                    })
        
    return dict(repo_stats)

def enrich_repo_data(repo_stats: Dict) -> List[dict]:
    """
    Obtiene datos adicionales de los repos top desde GitHub API.
    """
    # Ordenar por estrellas ganadas
    sorted_repos = sorted(
        repo_stats.items(),
        key=lambda x: x[1]['stars_gained'],
        reverse=True
    )
    
    print(f"\n🔍 Obteniendo datos adicionales de GitHub API...")
    
    enriched = []
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    # Solo enriquecer top 100 para no saturar la API
    for repo_name, stats in sorted_repos[:100]:
        try:
            response = httpx.get(
                f"https://api.github.com/repos/{repo_name}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                enriched.append({
                    'name': repo_name,
                    'stars': data.get('stargazers_count', 0),
                    'stars_gained_24h': stats['stars_gained'],
                    'description': data.get('description') or "",
                    'url': data.get('html_url', stats['url']),
                    'language': data.get('language') or "Unknown",
                    'created_at': data.get('created_at'),
                })
            else:
                # Si falla, usar datos básicos
                enriched.append({
                    'name': repo_name,
                    'stars': 0,
                    'stars_gained_24h': stats['stars_gained'],
                    'description': "",
                    'url': stats['url'],
                    'language': "Unknown",
                    'created_at': "",
                })
                
        except Exception as e:
            print(f"   ⚠️ Error con {repo_name}: {e}")
            enriched.append({
                'name': repo_name,
                'stars': 0,
                'stars_gained_24h': stats['stars_gained'],
                'description': "",
                'url': stats['url'],
                'language': "Unknown",
                'created_at': "",
            })
    
    # Añadir resto sin enriquecer
    for repo_name, stats in sorted_repos[100:]:
        enriched.append({
            'name': repo_name,
            'stars': 0,
            'stars_gained_24h': stats['stars_gained'],
            'description': "",
            'url': stats['url'],
            'language': "Unknown",
            'created_at': "",
        })
    
    return enriched

def filter_claude_related(repos: List[dict]) -> List[dict]:
    """
    Filtra repos relacionados con Claude/AI/Agents.
    """
    keywords = [
        'claude', 'anthropic', 'ai', 'agent', 'llm', 'gpt', 'openai',
        'cursor', 'copilot', 'code', 'assistant', 'model', 'ml',
        'language model', 'chat', 'prompt', 'embedding', 'vector',
    ]
    
    filtered = []
    for repo in repos:
        text = f"{repo['name']} {repo['description']}".lower()
        if any(kw in text for kw in keywords):
            filtered.append(repo)
    
    return filtered

def generate_report(date: str, repos: List[dict]):
    """
    Genera el reporte Markdown.
    """
    day_dir = ARCHIVE_DIR / date
    day_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar JSON
    data = {
        'date': date,
        'generated_at': datetime.now().isoformat(),
        'method': 'gharchive.org',
        'total_repos': len(repos),
        'repos': repos[:200],  # Top 200
    }
    
    with open(day_dir / "repos.json", 'w') as f:
        json.dump(data, f, indent=2)
    
    # Generar Markdown
    md_content = f"""# 📊 Ecosistema Claude - {date}

> Top repos que más ⭐ ganaron el **{date}** completo (datos de gharchive.org)

---

## 🔥 Ranking por Estrellas Ganadas ({date})

| # | Repo | ⭐ Total | ⭐ Ganadas ({date}) | Descripción |
|---|------|---------|---------------------|-------------|
"""
    
    for i, repo in enumerate(repos[:50], 1):
        gained = repo.get('stars_gained_24h', 0)
        desc = repo.get('description', '')[:55]
        if len(repo.get('description', '')) > 55:
            desc += "..."
        
        md_content += f"| {i} | [{repo['name']}]({repo['url']}) | {repo.get('stars', 0):,} | **+{gained:,}** | {desc} |\n"
    
    total_gained = sum(r.get('stars_gained_24h', 0) for r in repos[:50])
    
    md_content += f"""

---

## 📈 Estadísticas

- **Repos analizados**: {len(repos):,}
- **Estrellas ganadas (top 50)**: {total_gained:,}
- **Fuente**: [gharchive.org](http://gharchive.org/) - Datos completos del día

---

*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*
"""
    
    with open(day_dir / "README.md", 'w') as f:
        f.write(md_content)
    
    print(f"\n💾 Reporte guardado: {day_dir}/README.md")
    return day_dir

def main():
    print("=" * 60)
    print(f"🚀 Análisis de estrellas ganadas - {DATE_TO_ANALYZE}")
    print("=" * 60)
    
    # Paso 1: Contar estrellas del día completo
    print("\n1️⃣ Contando estrellas de gharchive.org...")
    repo_stats = count_stars_for_day(DATE_TO_ANALYZE)
    
    print(f"\n📊 Total de repos que recibieron estrellas: {len(repo_stats)}")
    
    # Mostrar top 5 temporal
    top_5_temp = sorted(repo_stats.items(), key=lambda x: x[1]['stars_gained'], reverse=True)[:5]
    print("\n🌟 Top 5 temporal (sin datos completos de GitHub):")
    for name, stats in top_5_temp:
        print(f"   {name}: +{stats['stars_gained']} ⭐")
    
    # Paso 2: Enriquecer con datos de GitHub
    print("\n2️⃣ Enriqueciendo datos desde GitHub API...")
    enriched_repos = enrich_repo_data(repo_stats)
    
    # Paso 3: Filtrar solo AI/Claude relacionados
    print("\n3️⃣ Filtrando repos de AI/Claude/Agents...")
    ai_repos = filter_claude_related(enriched_repos)
    
    print(f"   {len(ai_repos)} repos relacionados con AI encontrados")
    
    # Ordenar final
    final_repos = sorted(ai_repos, key=lambda x: x['stars_gained_24h'], reverse=True)
    
    # Mostrar top 10
    print("\n" + "=" * 60)
    print(f"📈 TOP 10 REPOS AI QUE MÁS ⭐ GANARON EL {DATE_TO_ANALYZE}:")
    print("=" * 60)
    for i, r in enumerate(final_repos[:10], 1):
        print(f"   {i:2d}. {r['name'][:45]:<45} +{r['stars_gained_24h']:4d} ⭐")
    
    # Paso 4: Generar reporte
    print("\n4️⃣ Generando reporte...")
    day_dir = generate_report(DATE_TO_ANALYZE, final_repos)
    
    print("\n" + "=" * 60)
    print(f"✨ ¡Completado!")
    print(f"📁 Datos: {day_dir}/")
    print(f"📄 Reporte: {day_dir}/README.md")
    print(f"⭐ Total estrellas nuevas (top 50 AI): {sum(r.get('stars_gained_24h', 0) for r in final_repos[:50]):,}")

if __name__ == "__main__":
    main()

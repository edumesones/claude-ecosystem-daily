"""
Script de actualización diaria del ecosistema Claude.
VERSION 3.0 - Usa GitHub Events API para contar estrellas exactas ganadas en 24h.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

import httpx

# Configuración
GITHUB_API = "https://api.github.com"
ARCHIVE_DIR = Path("archive")
LATEST_FILE = Path("latest.json")

def get_date_str() -> str:
    return datetime.now().strftime('%Y-%m-%d')

def get_24h_ago() -> datetime:
    """Devuelve timestamp de hace 24 horas"""
    return datetime.utcnow() - timedelta(hours=24)

def count_stars_gained_in_24h(repo_full_name: str, headers: dict) -> Optional[int]:
    """
    Cuenta exactamente cuántas estrellas ganó un repo en las últimas 24h.
    Usa la Events API para contar WatchEvent.
    """
    try:
        # Obtener eventos del repo (máximo 300 eventos recientes)
        response = httpx.get(
            f"{GITHUB_API}/repos/{repo_full_name}/events",
            params={"per_page": 100},
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            return None
        
        events = response.json()
        cutoff_time = get_24h_ago()
        star_count = 0
        
        for event in events:
            # WatchEvent = alguien dio estrella al repo
            if event.get('type') == 'WatchEvent':
                event_time = datetime.fromisoformat(event['created_at'].replace('Z', '+00:00'))
                # Quitar timezone info para comparar
                event_time = event_time.replace(tzinfo=None)
                
                if event_time >= cutoff_time:
                    star_count += 1
        
        return star_count
        
    except Exception as e:
        print(f"   ⚠️ Error contando estrellas para {repo_full_name}: {e}")
        return None

def get_trending_repos() -> List[Dict]:
    """
    Busca repos populares Y emergentes relacionados con Claude/AI.
    Incluye: populares, recientes, de organizaciones clave, mencionados.
    """
    queries = [
        # Populares
        "claude code",
        "anthropic agent", 
        "ai coding agent",
        "claude skills",
        "llm agent",
        "openai agent",
        "cursor editor",
        "vibe coding",
        # Recientes
        "created:>2025-12-01 ai agent",
        "created:>2026-01-01 claude",
        # Específicos
        "mcp server",
        "model context protocol",
    ]
    
    # Organizaciones clave a monitorear
    key_orgs = [
        "anthropics",
        "vercel-labs", 
        "openai",
        "langchain-ai",
        "microsoft",
        "google",
    ]
    
    all_repos = []
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    if os.getenv('GITHUB_TOKEN'):
        headers["Authorization"] = f"token {os.getenv('GITHUB_TOKEN')}"
    
    print("\n🔍 Buscando repos de múltiples fuentes...")
    
    # Paso 1: Buscar repos por queries
    for query in queries:
        try:
            # Diferentes criterios de estrellas según el tipo de búsqueda
            if "created:" in query:
                stars_filter = "stars:>50"  # Repos recientes con menos estrellas
                per_page = 30
            else:
                stars_filter = "stars:>500"
                per_page = 20
                
            response = httpx.get(
                f"{GITHUB_API}/search/repositories",
                params={
                    "q": f"{query} {stars_filter}",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": per_page
                },
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('items', []):
                    repo = {
                        'name': item['full_name'],
                        'stars': item['stargazers_count'],
                        'description': item['description'] or "",
                        'url': item['html_url'],
                        'language': item['language'] or "Unknown",
                        'created_at': item['created_at'],
                        'stars_gained_24h': 0,
                        'source': 'search',
                    }
                    if repo not in all_repos:
                        all_repos.append(repo)
                        
        except Exception as e:
            print(f"   ⚠️ Error buscando '{query}': {e}")
    
    # Paso 2: Buscar repos de organizaciones clave
    print("   🔎 Buscando en organizaciones clave...")
    for org in key_orgs:
        try:
            response = httpx.get(
                f"{GITHUB_API}/orgs/{org}/repos",
                params={
                    "sort": "updated",
                    "direction": "desc",
                    "per_page": 20
                },
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    if item.get('stargazers_count', 0) > 100:  # Solo repos con tracción
                        repo = {
                            'name': item['full_name'],
                            'stars': item['stargazers_count'],
                            'description': item.get('description') or "",
                            'url': item['html_url'],
                            'language': item.get('language') or "Unknown",
                            'created_at': item['created_at'],
                            'stars_gained_24h': 0,
                            'source': f'org:{org}',
                        }
                        if repo not in all_repos:
                            all_repos.append(repo)
        except Exception as e:
            print(f"   ⚠️ Error con org '{org}': {e}")
    
    # Eliminar duplicados y limitar a 50 candidatos
    seen = set()
    unique_repos = []
    for r in sorted(all_repos, key=lambda x: x['stars'], reverse=True):
        if r['name'] not in seen and len(unique_repos) < 50:
            seen.add(r['name'])
            unique_repos.append(r)
    
    print(f"   {len(unique_repos)} repos candidatos encontrados")
    
    # Paso 2: Contar estrellas ganadas en 24h para cada repo
    print("\n⭐ Contando estrellas ganadas en las últimas 24h...")
    print("   (Esto puede tardar unos segundos...)\n")
    
    for i, repo in enumerate(unique_repos, 1):
        gained = count_stars_gained_in_24h(repo['name'], headers)
        if gained is not None:
            repo['stars_gained_24h'] = gained
            print(f"   {i:2d}. {repo['name'][:40]:<40} +{gained:3d} ⭐")
        else:
            print(f"   {i:2d}. {repo['name'][:40]:<40} ⚠️  (sin datos)")
    
    # Ordenar por estrellas ganadas en 24h
    trending = sorted(
        unique_repos,
        key=lambda x: x.get('stars_gained_24h', 0),
        reverse=True
    )
    
    return trending

def save_daily_data(date: str, repos: List[Dict]):
    """Guarda datos del día en carpeta archive/YYYY-MM-DD/"""
    
    day_dir = ARCHIVE_DIR / date
    day_dir.mkdir(parents=True, exist_ok=True)
    
    data = {
        'date': date,
        'generated_at': datetime.now().isoformat(),
        'total_repos': len(repos),
        'method': 'github_events_api',  # Nuevo método
        'repos': repos
    }
    
    with open(day_dir / "repos.json", 'w') as f:
        json.dump(data, f, indent=2)
    
    with open(LATEST_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n💾 Datos guardados en: {day_dir}/")
    return day_dir

def generate_markdown_for_day(date: str, repos: List[Dict], day_dir: Path):
    """Genera README.md para el día específico"""
    
    md_content = f"""# 📊 Ecosistema Claude - {date}

> Top repos que más ⭐ ganaron en las últimas **24 horas** (contado desde GitHub Events API)

---

## 🔥 Ranking por Estrellas Ganadas (24h)

| # | Repo | ⭐ Total | ⭐ Hoy | Descripción |
|---|------|---------|--------|-------------|
"""
    
    for i, repo in enumerate(repos[:50], 1):
        gained = repo.get('stars_gained_24h', 0)
        desc = repo['description'][:55] + "..." if len(repo['description']) > 55 else repo['description']
        md_content += f"| {i} | [{repo['name']}]({repo['url']}) | {repo['stars']:,} | **+{gained}** | {desc} |\n"
    
    # Estadísticas
    total_gained = sum(r.get('stars_gained_24h', 0) for r in repos[:10])
    top_language = max(set(r['language'] for r in repos), key=lambda x: sum(1 for r in repos if r['language'] == x))
    
    md_content += f"""

---

## 📈 Estadísticas del día

- **Repos analizados**: {len(repos)}
- **Estrellas ganadas (top 10)**: {total_gained:,}
- **Lenguaje más popular**: {top_language}
- **Método**: GitHub Events API (WatchEvent contados en 24h)

---

*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*
"""
    
    with open(day_dir / "README.md", 'w') as f:
        f.write(md_content)
    
    print(f"📝 README generado: {day_dir}/README.md")

def update_main_readme(date: str, repos: List[Dict]):
    """Actualiza el README principal con resumen del día"""
    
    readme_path = Path("README.md")
    
    if readme_path.exists():
        with open(readme_path) as f:
            content = f.read()
    else:
        content = """# 🚀 Claude Ecosystem Daily

> Curación automática diaria del ecosistema Claude Code

## 📊 Últimos datos

<!-- LATEST_DATA -->

## 📁 Historial

Ver datos históricos en [`archive/`](./archive/)

---

*Actualizado automáticamente cada día a las 9:00 AM UTC usando GitHub Events API*
"""
    
    # Top 10
    top_10_table = "| # | Repo | ⭐ Hoy | ⭐ Total |\n"
    top_10_table += "|---|------|--------|----------|\n"
    
    for i, repo in enumerate(repos[:10], 1):
        gained = repo.get('stars_gained_24h', 0)
        top_10_table += f"| {i} | [{repo['name']}]({repo['url']}) | +{gained} | {repo['stars']:,} |\n"
    
    latest_section = f"""### 📅 {date}

{top_10_table}

[Ver top 50 completo →](./archive/{date}/README.md)

---

"""
    
    if "<!-- LATEST_DATA -->" in content:
        content = content.replace(
            "<!-- LATEST_DATA -->",
            f"<!-- LATEST_DATA -->\n\n{latest_section}"
        )
    
    with open(readme_path, 'w') as f:
        f.write(content)
    
    print(f"📄 README principal actualizado")

def main():
    """Función principal"""
    
    date = get_date_str()
    print(f"🚀 Iniciando actualización: {date}")
    print("=" * 70)
    
    # Obtener repos con estrellas ganadas en 24h
    repos = get_trending_repos()
    
    if not repos:
        print("❌ No se encontraron repos")
        return
    
    # Mostrar top 10
    print("\n" + "=" * 70)
    print("📈 TOP 10 REPOS QUE MÁS ⭐ GANARON EN 24H:")
    print("=" * 70)
    for i, r in enumerate(repos[:10], 1):
        gained = r.get('stars_gained_24h', 0)
        print(f"   {i:2d}. {r['name'][:50]:<50} +{gained:4d} ⭐ ({r['stars']:,} total)")
    
    # Guardar datos
    print("\n💾 Guardando datos...")
    day_dir = save_daily_data(date, repos)
    
    # Generar documentación
    print("\n📝 Generando documentación...")
    generate_markdown_for_day(date, repos, day_dir)
    update_main_readme(date, repos)
    
    print("\n" + "=" * 70)
    print(f"✨ ¡Completado! {date}")
    print(f"📁 Datos: {day_dir}/")
    print(f"📄 Resumen: {day_dir}/README.md")
    print(f"🔗 Total estrellas nuevas (top 10): {sum(r.get('stars_gained_24h', 0) for r in repos[:10])}")

if __name__ == "__main__":
    main()

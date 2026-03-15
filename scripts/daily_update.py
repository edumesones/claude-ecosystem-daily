"""
Script de actualización diaria del ecosistema Claude.
VERSION 2.0 - Guarda historial por carpetas, no sobrescribe.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import httpx

# Configuración
GITHUB_API = "https://api.github.com"
ARCHIVE_DIR = Path("archive")
LATEST_FILE = Path("latest.json")

def get_date_str() -> str:
    return datetime.now().strftime('%Y-%m-%d')

def get_yesterday_str() -> str:
    return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

def get_trending_repos_with_diff() -> List[Dict]:
    """
    Obtiene repos y calcula diferencia de stars vs ayer.
    Busca los 50 repos que MÁS STARS HAN GANADO en 24h.
    """
    queries = [
        "claude code",
        "anthropic agent", 
        "ai coding agent",
        "claude skills",
    ]
    
    repos = []
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    if os.getenv('GITHUB_TOKEN'):
        headers["Authorization"] = f"token {os.getenv('GITHUB_TOKEN')}"
    
    # Buscar repos relevantes
    for query in queries:
        try:
            response = httpx.get(
                f"{GITHUB_API}/search/repositories",
                params={
                    "q": f"{query} stars:>1000",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 30
                },
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('items', []):
                    repos.append({
                        'name': item['full_name'],
                        'stars': item['stargazers_count'],
                        'description': item['description'] or "",
                        'url': item['html_url'],
                        'language': item['language'] or "Unknown",
                        'created_at': item['created_at'],
                    })
        except Exception as e:
            print(f"Error buscando '{query}': {e}")
    
    # Eliminar duplicados
    seen = set()
    unique_repos = []
    for r in sorted(repos, key=lambda x: x['stars'], reverse=True):
        if r['name'] not in seen:
            seen.add(r['name'])
            unique_repos.append(r)
    
    # Cargar datos de ayer para calcular diferencia
    yesterday_file = ARCHIVE_DIR / get_yesterday_str() / "repos.json"
    yesterday_data = {}
    
    if yesterday_file.exists():
        with open(yesterday_file) as f:
            yesterday_data = {r['name']: r['stars'] for r in json.load(f).get('repos', [])}
    
    # Calcular ganancia de stars
    is_first_run = not yesterday_data
    
    for repo in unique_repos:
        if is_first_run:
            # Primera ejecución: no hay datos previos
            repo['stars_gained'] = None  # Se mostrará como "Baseline"
            repo['stars_yesterday'] = 0
        else:
            yesterday_stars = yesterday_data.get(repo['name'], repo['stars'])
            repo['stars_gained'] = repo['stars'] - yesterday_stars
            repo['stars_yesterday'] = yesterday_stars
    
    # Ordenar: si es primera vez, por total; si no, por ganancia
    if is_first_run:
        trending = sorted(unique_repos, key=lambda x: x['stars'], reverse=True)
        print("📌 Primera ejecución - Estableciendo baseline (no hay datos previos)")
    else:
        trending = sorted(unique_repos, key=lambda x: x.get('stars_gained', 0), reverse=True)
    
    return trending[:50]

def save_daily_data(date: str, repos: List[Dict]):
    """Guarda datos del día en carpeta archive/YYYY-MM-DD/"""
    
    day_dir = ARCHIVE_DIR / date
    day_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar repos con metadata
    data = {
        'date': date,
        'generated_at': datetime.now().isoformat(),
        'total_repos': len(repos),
        'repos': repos
    }
    
    with open(day_dir / "repos.json", 'w') as f:
        json.dump(data, f, indent=2)
    
    # Guardar también como latest.json (referencia rápida)
    with open(LATEST_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"💾 Datos guardados en: {day_dir}/")
    return day_dir

def generate_markdown_for_day(date: str, repos: List[Dict], day_dir: Path):
    """Genera README.md para el día específico"""
    
    md_content = f"""# 📊 Ecosistema Claude - {date}

> Top 50 repos que más ⭐ ganaron en las últimas 24h

---

## 🔥 Ranking por Stars Ganados

| # | Repo | ⭐ Total | ⭐ Hoy | Descripción |
|---|------|---------|--------|-------------|
"""
    
    for i, repo in enumerate(repos[:50], 1):
        gained = repo.get('stars_gained')
        if gained is None:
            gained_str = "📌 Baseline"  # Primera ejecución
        elif gained > 0:
            gained_str = f"+{gained:,}"
        else:
            gained_str = f"{gained:,}"
        
        desc = repo['description'][:60] + "..." if len(repo['description']) > 60 else repo['description']
        md_content += f"| {i} | [{repo['name']}]({repo['url']}) | {repo['stars']:,} | **{gained_str}** | {desc} |\n"
    
    # Calcular estadísticas (manejando None para primera ejecución)
    total_gained = sum(r.get('stars_gained', 0) or 0 for r in repos[:10])
    gained_label = f"{total_gained:,}" if any(r.get('stars_gained') is not None for r in repos[:10]) else "N/A (baseline)"
    
    md_content += f"""

---

## 📈 Estadísticas del día

- **Repos analizados**: {len(repos)}
- **Stars ganadas (top 10)**: {gained_label}
- **Lenguaje más popular**: {max(set(r['language'] for r in repos), key=lambda x: sum(1 for r in repos if r['language'] == x))}

---

*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*
"""
    
    with open(day_dir / "README.md", 'w') as f:
        f.write(md_content)
    
    print(f"📝 README generado: {day_dir}/README.md")

def update_main_readme(date: str, repos: List[Dict]):
    """Actualiza el README principal con resumen del día"""
    
    # Leer template o crear nuevo
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

*Actualizado automáticamente cada día a las 9:00 AM UTC*
"""
    
    # Generar tabla de top 10 de hoy
    top_10_table = "| # | Repo | ⭐ Hoy | ⭐ Total |\n"
    top_10_table += "|---|------|--------|----------|\n"
    
    for i, repo in enumerate(repos[:10], 1):
        gained = repo.get('stars_gained')
        if gained is None:
            gained_str = "📌 Baseline"
        else:
            gained_str = f"+{gained:,}"
        top_10_table += f"| {i} | [{repo['name']}]({repo['url']}) | {gained_str} | {repo['stars']:,} |\n"
    
    latest_section = f"""### 📅 {date}

{top_10_table}

[Ver top 50 completo →](./archive/{date}/README.md)

---

"""
    
    # Reemplazar o añadir después de <!-- LATEST_DATA -->
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
    print("=" * 60)
    
    # 1. Obtener repos trending
    print("\n🌟 Obteniendo repos con ganancia de stars...")
    repos = get_trending_repos_with_diff()
    print(f"   {len(repos)} repos encontrados")
    
    # Mostrar top 5
    print("\n📈 Top 5 repos ganadores de hoy:")
    for i, r in enumerate(repos[:5], 1):
        gained = r.get('stars_gained', 0)
        print(f"   {i}. {r['name']} +{gained:,} ⭐")
    
    # 2. Guardar en archivo histórico
    print("\n💾 Guardando datos...")
    day_dir = save_daily_data(date, repos)
    
    # 3. Generar markdown del día
    print("\n📝 Generando documentación...")
    generate_markdown_for_day(date, repos, day_dir)
    
    # 4. Actualizar README principal
    update_main_readme(date, repos)
    
    print("\n" + "=" * 60)
    print(f"✨ Completado: {date}")
    print(f"📁 Datos: {day_dir}/")
    print(f"📄 Resumen: {day_dir}/README.md")

if __name__ == "__main__":
    main()

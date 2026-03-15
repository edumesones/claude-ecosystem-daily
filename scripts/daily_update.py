"""
Script de actualización diaria del ecosistema Claude.
VERSION 4.0 - Usa OSS Insight API para trending repos de últimas 24h.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import httpx

# Configuración
OSSINSIGHT_API = "https://api.ossinsight.io/v1/trends/repos/"
ARCHIVE_DIR = Path("archive")
LATEST_FILE = Path("latest.json")

def get_date_str() -> str:
    return datetime.now().strftime('%Y-%m-%d')

def get_trending_repos_24h() -> List[Dict]:
    """
    Obtiene repos trending de últimas 24h desde OSS Insight API.
    """
    print("🔍 Obteniendo repos trending de últimas 24h...")
    print("   Fuente: api.ossinsight.io")
    
    try:
        response = httpx.get(
            OSSINSIGHT_API,
            params={
                "period": "past_24_hours",
                "language": "All"
            },
            headers={"Accept": "application/json"},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"   ❌ Error API: {response.status_code}")
            return []
        
        data = response.json()
        
        if data.get("type") != "sql_endpoint" or "data" not in data:
            print("   ❌ Formato de respuesta inesperado")
            return []
        
        rows = data["data"].get("rows", [])
        
        repos = []
        for row in rows:
            repo = {
                'name': row.get('repo_name', ''),
                'stars': int(row.get('stars', 0)),
                'stars_gained_24h': int(row.get('stars', 0)),  # OSS Insight ya da el valor 24h
                'forks': int(row.get('forks', 0)),
                'description': row.get('description', ''),
                'url': f"https://github.com/{row.get('repo_name', '')}",
                'language': row.get('primary_language', 'Unknown'),
                'total_score': float(row.get('total_score', 0)),
                'contributors': row.get('contributor_logins', ''),
            }
            repos.append(repo)
        
        print(f"   ✅ {len(repos)} repos obtenidos")
        return repos
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []

def filter_ai_claude_repos(repos: List[Dict]) -> List[Dict]:
    """
    Filtra repos relacionados con AI, Claude, agents, etc.
    """
    keywords = [
        'claude', 'anthropic', 'ai', 'agent', 'llm', 'gpt', 'openai',
        'cursor', 'copilot', 'code', 'assistant', 'model', 'ml',
        'language model', 'chat', 'prompt', 'embedding', 'vector',
        'openclaw', 'codex', 'agno', 'agnt', 'artificial',
        'autonomous', 'coding', 'llama', 'gemini', 'grok',
        'orchestration', 'swarm', 'mcp', 'skill',
    ]
    
    filtered = []
    for repo in repos:
        text = f"{repo['name']} {repo['description']}".lower()
        if any(kw in text for kw in keywords):
            filtered.append(repo)
    
    return filtered

def save_daily_data(date: str, repos: List[Dict]):
    """Guarda datos del día en carpeta archive/YYYY-MM-DD/"""
    
    day_dir = ARCHIVE_DIR / date
    day_dir.mkdir(parents=True, exist_ok=True)
    
    data = {
        'date': date,
        'generated_at': datetime.now().isoformat(),
        'total_repos': len(repos),
        'method': 'ossinsight_api_24h',
        'repos': repos
    }
    
    with open(day_dir / "repos.json", 'w') as f:
        json.dump(data, f, indent=2)
    
    with open(LATEST_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"💾 Datos guardados en: {day_dir}/")
    return day_dir

def generate_markdown_for_day(date: str, repos: List[Dict], day_dir: Path):
    """Genera README.md para el día específico"""
    
    # Separar en dos tablas: AI/Claude y General
    ai_repos = filter_ai_claude_repos(repos)
    
    md_content = f"""# 📊 Ecosistema Claude - {date}

> Repos que más ⭐ ganaron en las **últimas 24 horas** (datos de OSS Insight)

---

## 🤖 TOP 50 - AI / Claude / Agents / LLMs

| # | Repo | ⭐ Ganadas | ⭐ Total | Descripción |
|---|------|-----------|---------|-------------|
"""
    
    for i, repo in enumerate(ai_repos[:50], 1):
        desc = repo['description'][:50] + "..." if len(repo['description']) > 50 else repo['description']
        md_content += f"| {i} | [{repo['name']}]({repo['url']}) | **+{repo['stars_gained_24h']:,}** | {repo['stars']:,} | {desc} |\n"
    
    md_content += f"""

---

## 🌍 TOP 50 - General (Todos los repos)

| # | Repo | ⭐ Ganadas | ⭐ Total | Lenguaje |
|---|------|-----------|---------|----------|
"""
    
    for i, repo in enumerate(repos[:50], 1):
        md_content += f"| {i} | [{repo['name']}]({repo['url']}) | **+{repo['stars_gained_24h']:,}** | {repo['stars']:,} | {repo['language']} |\n"
    
    # Estadísticas
    total_gained = sum(r['stars_gained_24h'] for r in repos[:50])
    ai_count = len(ai_repos)
    
    md_content += f"""

---

## 📈 Estadísticas

- **Repos AI/Claude identificados**: {ai_count}
- **Estrellas ganadas (top 50 general)**: {total_gained:,}
- **Fuente**: [OSS Insight](https://ossinsight.io/)
- **Método**: API oficial - período `past_24_hours`

---

*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*
"""
    
    with open(day_dir / "README.md", 'w') as f:
        f.write(md_content)
    
    print(f"📝 README generado: {day_dir}/README.md")

def update_main_readme(date: str, ai_repos: List[Dict]):
    """Actualiza el README principal con resumen del día"""
    
    readme_path = Path("README.md")
    
    if readme_path.exists():
        with open(readme_path) as f:
            content = f.read()
    else:
        content = """# 🚀 Claude Ecosystem Daily

> Curación automática diaria del ecosistema Claude Code, AI Agents y LLMs

## 📊 Últimos datos

<!-- LATEST_DATA -->

## 📁 Historial

Ver datos históricos en [`archive/`](./archive/)

---

*Actualizado automáticamente con datos de [OSS Insight](https://ossinsight.io/)*
"""
    
    # Top 10 AI/Claude
    top_10_table = "| # | Repo | ⭐ Hoy | ⭐ Total |\n"
    top_10_table += "|---|------|--------|----------|\n"
    
    for i, repo in enumerate(ai_repos[:10], 1):
        top_10_table += f"| {i} | [{repo['name']}]({repo['url']}) | +{repo['stars_gained_24h']:,} | {repo['stars']:,} |\n"
    
    latest_section = f"""### 📅 {date} - Últimas 24h

**🤖 Top AI/Claude/Agents:**

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
    print("=" * 70)
    print(f"🚀 Claude Ecosystem Daily - {date}")
    print("=" * 70)
    
    # Obtener repos desde OSS Insight
    repos = get_trending_repos_24h()
    
    if not repos:
        print("❌ No se pudieron obtener datos")
        return
    
    # Filtrar repos AI/Claude
    ai_repos = filter_ai_claude_repos(repos)
    
    # Mostrar resumen
    print("\n" + "=" * 70)
    print(f"📈 RESUMEN DE ÚLTIMAS 24H:")
    print("=" * 70)
    print(f"\n🤖 Repos AI/Claude/Agents: {len(ai_repos)}")
    print(f"🌍 Total repos analizados: {len(repos)}")
    
    print("\n🏆 TOP 10 AI/CLAUDE:")
    for i, r in enumerate(ai_repos[:10], 1):
        print(f"   {i:2d}. {r['name'][:45]:<45} +{r['stars_gained_24h']:4,} ⭐")
    
    # Guardar datos
    print("\n💾 Guardando datos...")
    day_dir = save_daily_data(date, repos)
    
    # Generar documentación
    print("\n📝 Generando documentación...")
    generate_markdown_for_day(date, repos, day_dir)
    update_main_readme(date, ai_repos)
    
    print("\n" + "=" * 70)
    print(f"✨ ¡Completado!")
    print(f"📁 Datos: {day_dir}/")
    print(f"📄 Reporte: {day_dir}/README.md")
    print(f"⭐ Total estrellas nuevas (top 50): {sum(r['stars_gained_24h'] for r in repos[:50]):,}")

if __name__ == "__main__":
    main()

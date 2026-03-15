#!/usr/bin/env python3
"""
Script diario para trackear CLI tools trending (últimos 7 días).
Ejecuta 1 vez por día a las 12:00 UTC.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import httpx

OSSINSIGHT_API = "https://api.ossinsight.io/v1/trends/repos/"
ARCHIVE_DIR = Path("weekly")

def get_date_str() -> str:
    """Retorna fecha: 2026-03-15"""
    return datetime.now().strftime('%Y-%m-%d')

def get_cli_repos() -> List[Dict]:
    """
    Obtiene repos CLI trending de los últimos 7 días.
    Usa keywords específicas para herramientas de línea de comandos.
    """
    # Queries específicas para CLI
    queries = [
        "claude cli",
        "ai cli",
        "llm cli",
        "agent cli",
        "terminal ai",
        "command line assistant",
        "shell ai",
        "tui ai",
        "console ai",
        "codex cli",
        "openclaw cli",
    ]
    
    all_repos = []
    seen = set()
    
    print("🔍 Buscando CLI tools trending de últimos 7 días...")
    
    for query in queries:
        try:
            response = httpx.get(
                OSSINSIGHT_API,
                params={
                    "period": "past_week",  # Semanal en vez de 24h
                    "language": "All"
                },
                headers={"Accept": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                rows = data.get("data", {}).get("rows", [])
                
                for row in rows:
                    repo_name = row.get('repo_name', '')
                    if repo_name not in seen:
                        seen.add(repo_name)
                        
                        # Filtro: debe ser CLI-related
                        desc = (row.get('description') or '').lower()
                        name = repo_name.lower()
                        
                        cli_keywords = ['cli', 'command line', 'terminal', 'shell', 'console', 'tui', 'cmd']
                        is_cli = any(kw in desc or kw in name for kw in cli_keywords)
                        
                        if is_cli:
                            all_repos.append({
                                'name': repo_name,
                                'stars': int(row.get('stars', 0)),
                                'stars_gained_7d': int(row.get('stars', 0)),
                                'forks': int(row.get('forks', 0)),
                                'description': row.get('description', ''),
                                'url': f"https://github.com/{repo_name}",
                                'language': row.get('primary_language', 'Unknown'),
                                'total_score': float(row.get('total_score', 0)),
                            })
                            
        except Exception as e:
            print(f"   ⚠️ Error con query '{query}': {e}")
    
    # Ordenar por estrellas ganadas
    all_repos.sort(key=lambda x: x['stars_gained_7d'], reverse=True)
    
    print(f"   ✅ {len(all_repos)} CLI tools encontrados")
    return all_repos

def save_cli_data(date: str, repos: List[Dict]):
    """Guarda datos de 7 días"""
    
    day_dir = ARCHIVE_DIR / f"{date}-cli-7d"
    day_dir.mkdir(parents=True, exist_ok=True)
    
    data = {
        'date': date,
        'generated_at': datetime.now().isoformat(),
        'period': 'past_week',
        'total_repos': len(repos),
        'repos': repos
    }
    
    with open(day_dir / "cli-repos.json", 'w') as f:
        json.dump(data, f, indent=2)
    
    # Generar README
    md_content = f"""# CLI Tools 7-Day - {date}

> CLI tools para AI/Claude/Agents que más ⭐ ganaron últimos 7 días

---

## TOP CLI Tools

| # | Repo | ⭐ 7 días | ⭐ Total | Lenguaje | Descripción |
|---|------|----------|---------|----------|-------------|
"""
    
    for i, repo in enumerate(repos[:50], 1):
        desc = repo['description'][:45] + "..." if len(repo['description']) > 45 else repo['description']
        md_content += f"| {i} | [{repo['name']}]({repo['url']}) | **+{repo['stars_gained_7d']:,}** | {repo['stars']:,} | {repo['language']} | {desc} |\n"
    
    total_gained = sum(r['stars_gained_7d'] for r in repos[:50])
    
    md_content += f"""

---

## Estadísticas

- **CLI tools encontrados**: {len(repos)}
- **Estrellas ganadas (top 50)**: {total_gained:,}
- **Período**: Últimos 7 días
- **Fuente**: OSS Insight API

---

*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*
"""
    
    with open(day_dir / "README.md", 'w') as f:
        f.write(md_content)
    
    print(f"💾 Datos guardados en: {day_dir}/")

def main():
    date = get_date_str()
    print("=" * 70)
    print(f"CLI Tools 7-Day - {date}")
    print("=" * 70)
    
    repos = get_cli_repos()
    
    if not repos:
        print("❌ No se encontraron CLI tools")
        return
    
    print("\n🏆 TOP 10 CLI TOOLS DE 7 DÍAS:")
    for i, r in enumerate(repos[:10], 1):
        print(f"   {i:2d}. {r['name'][:45]:<45} +{r['stars_gained_7d']:4,} ⭐")
    
    save_cli_data(date, repos)
    
    print("\n" + "=" * 70)
    print(f"✨ Completado: {date}")

if __name__ == "__main__":
    main()

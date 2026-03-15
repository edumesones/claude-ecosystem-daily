#!/usr/bin/env python3
"""
Script simplificado para ver el funcionamiento del conteo de estrellas.
Usa GitHub Events API para repos clave de Claude/AI.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import httpx

GITHUB_API = "https://api.github.com"

# Repos clave a monitorear
KEY_REPOS = [
    "anthropics/claude-code",
    "x1xhlol/system-prompts-and-models-of-ai-tools",
    "affaan-m/everything-claude-code",
    "wshobson/agents",
    "oraios/serena",
    "ruvnet/ruflo",
    "danny-avila/LibreChat",
    "thedotmack/claude-mem",
    "hesreallyhim/awesome-claude-code",
    "sickn33/antigravity-awesome-skills",
    "BloopAI/vibe-kanban",
    "shareAI-lab/learn-claude-code",
    "langchain-ai/langchain",
    "langchain-ai/langgraph",
    "microsoft/autogen",
    "openai/openai-python",
]

def count_stars_24h(repo_full_name, headers):
    """Cuenta estrellas ganadas en últimas 24h"""
    try:
        resp = httpx.get(
            f"{GITHUB_API}/repos/{repo_full_name}/events",
            params={"per_page": 100},
            headers=headers,
            timeout=15
        )
        if resp.status_code != 200:
            return None
        
        events = resp.json()
        cutoff = datetime.utcnow() - timedelta(hours=24)
        count = 0
        
        for event in events:
            if event.get('type') == 'WatchEvent':
                created = datetime.fromisoformat(event['created_at'].replace('Z', '+00:00'))
                created = created.replace(tzinfo=None)
                if created >= cutoff:
                    count += 1
        return count
    except Exception as e:
        return None

def get_repo_info(repo_full_name, headers):
    """Obtiene info del repo"""
    try:
        resp = httpx.get(
            f"{GITHUB_API}/repos/{repo_full_name}",
            headers=headers,
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                'name': repo_full_name,
                'stars': data['stargazers_count'],
                'description': data.get('description', ''),
                'url': data['html_url'],
                'language': data.get('language', 'Unknown'),
            }
    except:
        pass
    return None

def main():
    print("=" * 70)
    print("⭐ Conteo de estrellas ganadas en últimas 24h - Repos AI/Claude")
    print("=" * 70)
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if os.getenv('GITHUB_TOKEN'):
        headers["Authorization"] = f"token {os.getenv('GITHUB_TOKEN')}"
    
    results = []
    
    for repo in KEY_REPOS:
        print(f"\n📊 {repo}")
        
        # Info del repo
        info = get_repo_info(repo, headers)
        if not info:
            print("   ❌ No se pudo obtener info")
            continue
        
        print(f"   ⭐ Total: {info['stars']:,}")
        
        # Contar estrellas 24h
        gained = count_stars_24h(repo, headers)
        if gained is not None:
            print(f"   📈 +{gained} en 24h")
            info['stars_gained_24h'] = gained
            results.append(info)
        else:
            print("   ⚠️ No se pudo contar")
    
    # Ordenar por ganancia
    results.sort(key=lambda x: x.get('stars_gained_24h', 0), reverse=True)
    
    print("\n" + "=" * 70)
    print("🏆 TOP REPOS POR ESTRELLAS GANADAS (24h)")
    print("=" * 70)
    
    for i, r in enumerate(results[:15], 1):
        gained = r.get('stars_gained_24h', 0)
        print(f"{i:2d}. {r['name']:<45} +{gained:3d} ⭐ ({r['stars']:,} total)")
    
    print("\n" + "=" * 70)
    print(f"✨ Total estrellas nuevas (top 15): {sum(r.get('stars_gained_24h', 0) for r in results[:15])}")

if __name__ == "__main__":
    main()

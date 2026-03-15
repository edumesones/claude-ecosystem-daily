#!/usr/bin/env python3
"""
Script para trackear skills populares desde skills.sh
Ejecuta 1 vez por día
"""
import json
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict

ARCHIVE_DIR = Path("skills-data")

def parse_skills_output(output: str) -> List[Dict]:
    """Parsea la salida de 'npx skills find'"""
    skills = []
    
    # Limpiar códigos ANSI de color
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    output_clean = ansi_escape.sub('', output)
    
    # Patrón para extraer: owner/repo@skill X installs
    # Ejemplo: vercel-labs/agent-skills@vercel-react-best-practices 210.3K installs
    pattern = r'([\w\-]+/[\w\-]+)@([\w\-:]+)\s+(\d+(?:\.\d+)?[K]?) installs'
    
    for line in output_clean.split('\n'):
        match = re.search(pattern, line)
        if match:
            owner_repo = match.group(1)
            skill_name = match.group(2)
            installs_str = match.group(3)
            
            # Convertir installs a número
            if 'K' in installs_str:
                installs = int(float(installs_str.replace('K', '')) * 1000)
            else:
                installs = int(installs_str)
            
            skills.append({
                'id': f"{owner_repo}@{skill_name}",
                'owner_repo': owner_repo,
                'skill_name': skill_name,
                'installs': installs,
                'url': f"https://skills.sh/{owner_repo.replace('/', '/')}/{skill_name}",
            })
    
    return skills

def get_skills() -> List[Dict]:
    """Obtiene skills populares desde skills.sh CLI"""
    print("🔍 Obteniendo skills populares desde skills.sh...")
    
    all_skills = []
    seen = set()
    
    # Buscar con términos populares (limitado a 3 para velocidad)
    queries = [
        "claude",
        "react",
        "python",
    ]
    
    for query in queries:
        try:
            result = subprocess.run(
                ["npx", "skills", "find", query],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                skills = parse_skills_output(result.stdout)
                for skill in skills:
                    if skill['id'] not in seen:
                        seen.add(skill['id'])
                        all_skills.append(skill)
                        
        except Exception as e:
            print(f"   ⚠️ Error con query '{query}': {e}")
    
    # Ordenar por installs
    all_skills.sort(key=lambda x: x['installs'], reverse=True)
    
    print(f"   ✅ {len(all_skills)} skills encontrados")
    return all_skills

def categorize_skill(skill: Dict) -> str:
    """Clasifica un skill en una categoría"""
    skill_id = skill['id'].lower()
    skill_name = skill['skill_name'].lower()
    
    # Categoría 1: Frontend & UI
    frontend_keywords = ['react', 'component', 'ui', 'design', 'frontend', 'web', 'css', 'html']
    if any(kw in skill_id or kw in skill_name for kw in frontend_keywords):
        return 'frontend'
    
    # Categoría 2: Backend & Python
    backend_keywords = ['python', 'api', 'backend', 'server', 'database', 'sql', 'dataverse']
    if any(kw in skill_id or kw in skill_name for kw in backend_keywords):
        return 'backend'
    
    # Categoría 3: Claude & Agents (default)
    return 'agents'

def save_skills_data(date: str, skills: List[Dict]):
    """Guarda datos de skills organizados por categorías"""
    
    day_dir = ARCHIVE_DIR
    day_dir.mkdir(parents=True, exist_ok=True)
    
    # Clasificar skills
    categorized = {
        'frontend': [],
        'backend': [],
        'agents': []
    }
    
    for skill in skills:
        cat = categorize_skill(skill)
        categorized[cat].append(skill)
    
    # Ordenar cada categoría por installs
    for cat in categorized:
        categorized[cat].sort(key=lambda x: x['installs'], reverse=True)
    
    data = {
        'date': date,
        'generated_at': datetime.now().isoformat(),
        'total_skills': len(skills),
        'categories': {
            'frontend': {'name': 'Frontend & UI', 'skills': categorized['frontend']},
            'backend': {'name': 'Backend & Python', 'skills': categorized['backend']},
            'agents': {'name': 'Claude & Agents', 'skills': categorized['agents']}
        }
    }
    
    # Guardar JSON
    with open(day_dir / f"{date}.json", 'w') as f:
        json.dump(data, f, indent=2)
    
    with open(day_dir / "latest.json", 'w') as f:
        json.dump(data, f, indent=2)
    
    # Generar README con categorías
    md_content = f"""# Skills Populares - {date}

> Skills de skills.sh organizados por categorías

---

## 1️⃣ Frontend & UI

| # | Skill | Installs | URL |
|---|-------|----------|-----|
"""
    
    for i, skill in enumerate(categorized['frontend'][:20], 1):
        md_content += f"| {i} | {skill['id']} | {skill['installs']:,} | [Link]({skill['url']}) |\n"
    
    md_content += f"""

---

## 2️⃣ Backend & Python

| # | Skill | Installs | URL |
|---|-------|----------|-----|
"""
    
    for i, skill in enumerate(categorized['backend'][:20], 1):
        md_content += f"| {i} | {skill['id']} | {skill['installs']:,} | [Link]({skill['url']}) |\n"
    
    md_content += f"""

---

## 3️⃣ Claude & Agents

| # | Skill | Installs | URL |
|---|-------|----------|-----|
"""
    
    for i, skill in enumerate(categorized['agents'][:20], 1):
        md_content += f"| {i} | {skill['id']} | {skill['installs']:,} | [Link]({skill['url']}) |\n"
    
    total_installs = sum(s['installs'] for s in skills)
    
    md_content += f"""

---

## Estadísticas

| Categoría | Skills | Installs totales |
|-----------|--------|------------------|
| Frontend & UI | {len(categorized['frontend'])} | {sum(s['installs'] for s in categorized['frontend']):,} |
| Backend & Python | {len(categorized['backend'])} | {sum(s['installs'] for s in categorized['backend']):,} |
| Claude & Agents | {len(categorized['agents'])} | {sum(s['installs'] for s in categorized['agents']):,} |
| **Total** | **{len(skills)}** | **{total_installs:,}** |

**Fuente**: [skills.sh](https://skills.sh/)

---

*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*
"""
    
    with open(day_dir / "README.md", 'w') as f:
        f.write(md_content)
    
    print(f"💾 Datos guardados en: {day_dir}/")
    print(f"   📊 Frontend & UI: {len(categorized['frontend'])} skills")
    print(f"   📊 Backend & Python: {len(categorized['backend'])} skills")
    print(f"   📊 Claude & Agents: {len(categorized['agents'])} skills")

def main():
    date = datetime.now().strftime('%Y-%m-%d')
    print("=" * 70)
    print(f"Skills Tracker - {date}")
    print("=" * 70)
    
    skills = get_skills()
    
    if not skills:
        print("❌ No se encontraron skills")
        return
    
    # Clasificar para mostrar en consola
    categorized = {'frontend': [], 'backend': [], 'agents': []}
    for skill in skills:
        cat = categorize_skill(skill)
        categorized[cat].append(skill)
    
    for cat in categorized:
        categorized[cat].sort(key=lambda x: x['installs'], reverse=True)
    
    print("\n🏆 TOP SKILLS POR CATEGORÍA:")
    
    print("\n   1️⃣ Frontend & UI:")
    for i, s in enumerate(categorized['frontend'][:5], 1):
        print(f"      {i}. {s['id'][:45]:<45} {s['installs']:>8,}")
    
    print("\n   2️⃣ Backend & Python:")
    for i, s in enumerate(categorized['backend'][:5], 1):
        print(f"      {i}. {s['id'][:45]:<45} {s['installs']:>8,}")
    
    print("\n   3️⃣ Claude & Agents:")
    for i, s in enumerate(categorized['agents'][:5], 1):
        print(f"      {i}. {s['id'][:45]:<45} {s['installs']:>8,}")
    
    save_skills_data(date, skills)
    
    print("\n" + "=" * 70)
    print(f"✨ Completado: {date}")

if __name__ == "__main__":
    main()

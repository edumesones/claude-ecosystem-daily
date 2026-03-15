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

def save_skills_data(date: str, skills: List[Dict]):
    """Guarda datos de skills"""
    
    day_dir = ARCHIVE_DIR
    day_dir.mkdir(parents=True, exist_ok=True)
    
    data = {
        'date': date,
        'generated_at': datetime.now().isoformat(),
        'total_skills': len(skills),
        'skills': skills
    }
    
    # Guardar JSON con fecha
    with open(day_dir / f"{date}.json", 'w') as f:
        json.dump(data, f, indent=2)
    
    # Guardar también como latest.json
    with open(day_dir / "latest.json", 'w') as f:
        json.dump(data, f, indent=2)
    
    # Generar README
    md_content = f"""# Skills Populares - {date}

> Skills de skills.sh ordenados por instalaciones

---

## TOP 50 Skills

| # | Skill | Installs | URL |
|---|-------|----------|-----|
"""
    
    for i, skill in enumerate(skills[:50], 1):
        md_content += f"| {i} | {skill['id']} | {skill['installs']:,} | [Link]({skill['url']}) |\n"
    
    total_installs = sum(s['installs'] for s in skills[:50])
    
    md_content += f"""

---

## Estadísticas

- **Total skills indexados**: {len(skills)}
- **Installs top 50**: {total_installs:,}
- **Fuente**: [skills.sh](https://skills.sh/)

---

*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*
"""
    
    with open(day_dir / "README.md", 'w') as f:
        f.write(md_content)
    
    print(f"💾 Datos guardados en: {day_dir}/")

def main():
    date = datetime.now().strftime('%Y-%m-%d')
    print("=" * 70)
    print(f"Skills Tracker - {date}")
    print("=" * 70)
    
    skills = get_skills()
    
    if not skills:
        print("❌ No se encontraron skills")
        return
    
    print("\n🏆 TOP 10 SKILLS:")
    for i, s in enumerate(skills[:10], 1):
        print(f"   {i:2d}. {s['id'][:50]:<50} {s['installs']:>10,} installs")
    
    save_skills_data(date, skills)
    
    print("\n" + "=" * 70)
    print(f"✨ Completado: {date}")

if __name__ == "__main__":
    main()

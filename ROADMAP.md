# Plan: Expandir tracking a Skills, Agentes e Integraciones

## 1. SKILLS (skills.sh)

### Problema
skills.sh no tiene API pública documentada. Solo CLI con `npx skills find`.

### Solución A: Parsear CLI (MVP)
```bash
npx skills find "popular" 2>&1 | grep -E "^\w+.*@.*\[" > skills_raw.txt
```

Luego parsear con Python:
```python
# owner/repo@skill [123 installs]
# Extraer: skill_id, installs
```

### Solución B: Scraping (mejor)
Si skills.sh tiene web pública, scrapearla con BeautifulSoup/Playwright.

### Solución C: Manual curado
Mantener lista manual de skills importantes en un JSON y actualizar semanalmente.

---

## 2. AGENTES / FRAMEWORKS

### Solución: GitHub Topics + Search

Buscar repos con topics específicos:
```python
# Topics clave
agent_topics = [
    "claude-code",
    "ai-agent",
    "llm-agent", 
    "autonomous-agent",
    "mcp-server",
    "claude-skill",
]

# GitHub API
for topic in agent_topics:
    httpx.get(f"https://api.github.com/search/repositories?q=topic:{topic}&sort=stars")
```

### Lista de agentes a monitorear (manual)
Mantener lista de repos clave en `config/agents.yml`:
```yaml
agents:
  - repo: anthropics/claude-code
    category: official
  - repo: wshobson/agents
    category: orchestration
  - repo: ruvnet/ruflo
    category: orchestration
  # ... etc
```

---

## 3. INTEGRACIONES

### Solución: Documentación + Community

Las integraciones no tienen métricas automáticas fáciles. Opciones:

**A) Scraping de documentación**:
- Scrappear docs.anthropic.com para integraciones oficiales
- Scrappear awesome-claude-code para integraciones comunitarias

**B) Manual + votos**:
- JSON con integraciones populares
- Contar menciones en HN/Reddit/Twitter
- Community submissions via issues

**C) npm/pypi descargas**:
- Para packages de integración, trackear downloads
```python
# PyPI stats
httpx.get(f"https://pypistats.org/api/packages/{package}/recent")

# npm stats  
httpx.get(f"https://api.npmjs.org/downloads/point/last-week/{package}")
```

---

## 4. IMPLEMENTACIÓN PROPUESTA

### Fase 1: Skills básico (CLI parse)
1. Ejecutar `npx skills find` en GitHub Action
2. Parsear salida a JSON
3. Guardar en `data/skills/YYYY-MM-DD.json`

### Fase 2: Agentes monitoreados
1. Crear `config/monitored_agents.yml` con lista de repos importantes
2. Usar GitHub API para trackear sus stars/pulse/forks
3. Generar tabla de "Agent Activity"

### Fase 3: Integraciones
1. Crear `data/integrations/` con estructura manual inicial
2. Aceptar PRs de comunidad para añadir nuevas
3. Opcional: Scraping de docs/sites

---

## 5. ESTRUCTURA FINAL DEL REPO

```
claude-ecosystem-daily/
├── README.md
├── config/
│   ├── monitored_agents.yml      # Lista de agentes a trackear
│   └── integration_categories.yml # Categorías de integraciones
├── data/
│   ├── github/                   # Repos trending (actual)
│   │   ├── 2026-03-15-morning/
│   │   └── 2026-03-15-evening/
│   ├── skills/                   # Skills de skills.sh
│   │   └── 2026-03-15.json
│   ├── agents/                   # Métricas de agentes monitoreados
│   │   └── 2026-03-15.json
│   └── integrations/             # Integraciones (manual)
│       └── index.yml
├── scripts/
│   ├── fetch_github_trending.py  # Actual
│   ├── fetch_skills.py           # Nuevo: skills.sh
│   ├── fetch_agent_metrics.py    # Nuevo: agentes monitoreados
│   └── generate_reports.py       # Genera markdowns
└── .github/workflows/
    └── daily-update.yml
```

---

## 6. PRIORIDAD

| Feature | Esfuerzo | Impacto | Prioridad |
|---------|----------|---------|-----------|
| GitHub trending (actual) | Bajo | Alto | ✅ Hecho |
| Skills (CLI parse) | Medio | Medio | 🎯 Siguiente |
| Agentes monitoreados | Medio | Alto | 🎯 Siguiente |
| Integraciones | Alto | Medio | ⏸️ Después |

---

## ¿Cuál implementamos primero?

1. **Skills básico** - Parsear `npx skills find` (rápido de hacer)
2. **Agentes monitoreados** - Lista manual + GitHub API (más valor)
3. **Integraciones** - Manual por ahora (complejo)

# Claude Ecosystem Daily

> Tracking diario de repos AI/Claude/Agents/LLMs que más estrellas ganan en GitHub

[![Daily Update](https://github.com/edumesones/claude-ecosystem-daily/actions/workflows/daily-update.yml/badge.svg)](https://github.com/edumesones/claude-ecosystem-daily/actions/workflows/daily-update.yml)

---

## Qué hace este repo

Tracking automático **2 veces al día** de los repositorios de GitHub relacionados con:

- Claude / Anthropic
- AI Agents
- LLMs (GPT, Llama, Gemini, etc.)
- Coding assistants (Cursor, Codex, etc.)
- Frameworks de agentes
- Tools para desarrollo con IA

### Fuentes de datos

- **OSS Insight API** - Datos oficiales de trending repos en GitHub
- **Período**: Últimas 24 horas (`past_24_hours`)
- **Actualizaciones**: 9:00 AM UTC (Mañana) y 9:00 PM UTC (Tarde)

---

## Estructura de datos

```
archive/
├── 2026-03-15-morning/     ← Snapshot de la mañana
│   ├── README.md
│   └── repos.json
├── 2026-03-15-evening/     ← Snapshot de la tarde
│   ├── README.md
│   └── repos.json
└── ...
```

Cada snapshot incluye:
- **100 repos trending** de GitHub (últimas 24h)
- **Filtro AI/Claude**: Repos relacionados con IA/agents (~80-90 repos)
- **Ranking por estrellas ganadas**

---

## Ver últimos datos

[Ver datos de hoy →](./archive/)

---

## Cómo funciona

1. **GitHub Action** se ejecuta 2 veces al día (9AM y 9PM UTC)
2. **Script Python** consulta OSS Insight API
3. **Filtra** repos relacionados con AI/Claude/Agents
4. **Genera** README.md con tablas de rankings
5. **Guarda** datos en carpeta `archive/YYYY-MM-DD-{morning|evening}/`
6. **Commit automático** con los nuevos datos

---

## Campos de datos

Cada repo incluye:

| Campo | Descripción |
|-------|-------------|
| `name` | Nombre del repo (owner/repo) |
| `stars` | Estrellas ganadas en las últimas 24h |
| `stars_gained_24h` | Alias de `stars` |
| `forks` | Forks del repo |
| `description` | Descripción del repo |
| `url` | URL de GitHub |
| `language` | Lenguaje principal |
| `total_score` | Score ponderado de OSS Insight |
| `contributors` | Top contribuidores |

---

## Keywords de filtrado

Los repos se clasifican como "AI/Claude" si contienen:

```
claude, anthropic, ai, agent, llm, gpt, openai,
cursor, copilot, code, assistant, model, ml,
language model, chat, prompt, embedding, vector,
openclaw, codex, agno, artificial, autonomous,
coding, llama, gemini, grok, orchestration,
swarm, mcp, skill
```

---

## Uso

### Ver datos históricos

```bash
# Ver archivo de hoy
cat archive/$(date +%Y-%m-%d)-morning/repos.json

# Ver README de hoy
cat archive/$(date +%Y-%m-%d)-morning/README.md
```

### Ejecutar manualmente

```bash
python scripts/daily_update.py
```

---

## Tecnologías

- **Python 3.11**
- **httpx** - HTTP client
- **OSS Insight API** - Fuente de datos
- **GitHub Actions** - Automatización

---

## Licencia

MIT - Datos públicos de GitHub

---

*Generado automáticamente. Última actualización: ver carpetas en `archive/`*

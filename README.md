# Claude Ecosystem Daily

> Tracking diario del ecosistema de desarrollo con IA: repos GitHub, CLI tools y agent skills

[![Daily Update](https://github.com/edumesones/claude-ecosystem-daily/actions/workflows/daily-update.yml/badge.svg)](https://github.com/edumesones/claude-ecosystem-daily/actions/workflows/daily-update.yml)

---

## Qué hace este repo

Tracking automático de 3 fuentes de datos del ecosistema AI/Claude:

### 1. GitHub Trending (Diario, 2 veces)
Repos de GitHub relacionados con Claude/AI/Agents que más estrellas ganan cada día.

**Frecuencia**: 9:00 AM UTC (Mañana) y 9:00 PM UTC (Tarde)  
**Período**: Últimas 24 horas  
**Output**: 100 repos trending

### 2. CLI Tools (Diario)
Herramientas de línea de comandos para AI/Claude con más actividad en 7 días.

**Frecuencia**: 12:00 PM UTC (Diario)  
**Período**: Últimos 7 días  
**Output**: CLI tools filtrados

### 3. Agent Skills (Diario) - EXPERIMENTAL
Skills populares de [skills.sh](https://skills.sh/).

**Frecuencia**: Manual (requiere `npx skills`)  
**Output**: Skills ordenados por instalaciones

---

## Estructura de datos

```
archive/                      ← Trending diario (repos GitHub)
├── 2026-03-15-morning/
│   ├── README.md
│   └── repos.json
├── 2026-03-15-evening/
│   ├── README.md
│   └── repos.json
└── ...

weekly/                       ← CLI tools (últimos 7 días)
├── 2026-03-15-cli-7d/
│   ├── README.md
│   └── cli-repos.json
└── ...

skills-data/                  ← Agent skills
├── 2026-03-15.json
├── latest.json
└── README.md
```

---

## Campos de datos

### Repos GitHub (Trending)
| Campo | Descripción |
|-------|-------------|
| `name` | owner/repo |
| `stars` | Estrellas ganadas (24h o 7d) |
| `description` | Descripción del repo |
| `language` | Lenguaje principal |
| `url` | URL de GitHub |

### Skills
| Campo | Descripción |
|-------|-------------|
| `id` | owner/repo@skill-name |
| `installs` | Número de instalaciones |
| `url` | Link a skills.sh |

---

## Fuentes

- **OSS Insight API** - Datos oficiales de GitHub trending
- **skills.sh CLI** - Skills de agentes (via `npx skills`)

---

## Uso

### Ver datos históricos

```bash
# Trending de hoy
cat archive/$(date +%Y-%m-%d)-morning/repos.json

# CLI tools de hoy
cat weekly/$(date +%Y-%m-%d)-cli-7d/cli-repos.json

# Skills
ls skills-data/
```

### Ejecutar manualmente

```bash
# Trending diario
python scripts/daily_update.py

# CLI tools
python scripts/fetch_cli_weekly.py

# Skills
python scripts/fetch_skills.py
```

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

## Tecnologías

- Python 3.11
- httpx
- GitHub Actions
- OSS Insight API
- skills.sh CLI

---

## Licencia

MIT - Datos públicos

---

*Actualizado automáticamente. Ver carpetas para fechas específicas.*

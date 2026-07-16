# 🚀 ZeroBlame — SRE Incident Copilot

**ZeroBlame** es una plataforma asíncrona de triaje automatizado de incidentes para equipos SRE. Recibe alertas de proveedores de nube (Google Cloud Monitoring), las normaliza a un modelo de dominio propio, genera un diagnóstico de causa raíz con IA (**Gemini** vía LangChain), persiste todo en PostgreSQL y expone una consola web para gestionar el ciclo de vida de cada incidente.

---

## 🧠 Arquitectura

El proyecto sigue principios de **Clean Architecture**: la lógica de negocio no depende de frameworks, base de datos ni del proveedor de IA. La regla de dependencia apunta siempre hacia el dominio.

```text
┌─────────────────────────────────────────────────────────────┐
│  Transporte        main.py (FastAPI: webhooks, API, UI)     │
├─────────────────────────────────────────────────────────────┤
│  Contratos I/O     schemas.py (Pydantic, validación)        │
├─────────────────────────────────────────────────────────────┤
│  Adaptación        adapters.py (GCPIncidentAdapter)         │
├─────────────────────────────────────────────────────────────┤
│  Dominio           domain.py (Incident — entidad pura)      │
├─────────────────────────────────────────────────────────────┤
│  Casos de Uso      services.py (TriageService)              │
│                      ├─ agents.py (SREAgent, LangChain)     │
│                      └─ repo/Incident.py (Repository)       │
├─────────────────────────────────────────────────────────────┤
│  Persistencia      models/IncidentRecord.py (SQLAlchemy)    │
│                    config/database.py (engine asyncpg)      │
└─────────────────────────────────────────────────────────────┘
```

### Patrones aplicados

| Patrón | Dónde | Para qué |
|---|---|---|
| **Adapter** | `GCPIncidentAdapter` | Traduce el payload crudo de GCP al dominio; agregar otro proveedor (AWS, Datadog) es solo implementar `IncidentAdapter` |
| **Repository** | `IncidentRepository` (ABC) + `SQLIncidentRepository` | Desacopla el caso de uso del motor de persistencia |
| **LCEL Pipeline** | `SREAgent` (`prompt \| llm \| parser`) | Cadena declarativa de análisis con Gemini |
| **Domain Model puro** | `Incident` | Entidad sin dependencias de SQLAlchemy/Pydantic |

### Flujo de datos — `POST /api/v1/webhooks/gcp`

1. **Pydantic** (`GCPWebhookPayload`) valida estructura y tipos del webhook entrante.
2. **`GCPIncidentAdapter.to_domain()`** mapea labels y metadata de GCP → entidad `Incident`.
3. **`TriageService.execute()`** orquesta el caso de uso:
   - `SREAgent.analyze()` envía el incidente a Gemini y obtiene diagnóstico + plan de mitigación en Markdown.
   - Combina dominio + diagnóstico en un `IncidentRecord` y lo persiste vía `SQLIncidentRepository`.
4. Responde `202 Accepted` con el `incident_id` generado.

---

## 📡 API

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/webhooks/gcp` | Ingesta de alertas de GCP Monitoring (202) |
| `GET` | `/api/v1/incidents` | Lista de incidentes con su diagnóstico IA |
| `PATCH` | `/api/v1/incidents/{id}/status?status=` | Cambia estado: `PENDING` / `IN_PROGRESS` / `RESOLVED` |
| `GET` | `/dashboard` | Consola web interactiva (SPA embebida) |
| `GET` | `/docs` | Swagger UI autogenerado |

---

## ⚙️ Instalación y ejecución

Requisitos: **Python 3.11+**, **PostgreSQL**, una **API key de Gemini** ([Google AI Studio](https://aistudio.google.com/)).

```bash
git clone <repo>
cd ZeroBlame
python -m venv .venv
.venv\Scripts\activate        # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

Crear un `.env` en la raíz (nunca se commitea — está en `.gitignore`):

```env
GEMINI_API_KEY=tu_api_key
DATABASE_URL=postgresql://usuario:password@localhost:5432/zeroblame
```

> La app valida ambas variables **al arrancar** y falla rápido si faltan. La URL `postgres://` o `postgresql://` se normaliza automáticamente al driver `postgresql+asyncpg://`. Las tablas se crean solas en el arranque (`lifespan`).

Levantar el servidor:

```bash
uvicorn app.main:app --reload
```

Dashboard en `http://localhost:8000/dashboard`.

---

## 🛡️ Seguridad

Medidas implementadas tras auditoría DevSecOps:

- **Anti-XSS en el dashboard**: todo dato proveniente de la API se escapa como texto plano (`esc()`), y el diagnóstico Markdown generado por la IA se sanitiza con **DOMPurify** antes de renderizarse. El `error_message` proviene de webhooks externos y se trata siempre como input hostil.
- **Sin fuga de detalles internos**: los errores 500 devuelven un mensaje genérico al cliente; el stack trace completo queda solo en el log del servidor (`logging`).
- **SQL parametrizado**: todo el acceso a datos usa SQLAlchemy ORM con `select()` — sin concatenación de SQL.
- **Secretos fuera del repo**: `GEMINI_API_KEY` y `DATABASE_URL` viven solo en `.env` (ignorado por git) y se validan en el arranque.
- **Validación estricta de entrada**: Pydantic con campos requeridos en el webhook; el estado del `PATCH` se valida contra una lista blanca.
- **Sesiones async correctas**: cada operación de repositorio se ejecuta dentro del ciclo de vida de su `AsyncSession`, evitando conexiones huérfanas en el pool de asyncpg.

**Pendiente conocido**: `/dashboard` y la API no tienen autenticación. En producción deben protegerse detrás de un reverse proxy con auth (o middleware de API key / OAuth).

---

## 📁 Estructura del proyecto

```text
app/
├── main.py                  # Rutas FastAPI + dashboard embebido
├── schemas.py               # Contratos I/O (Pydantic)
├── adapters.py              # Adaptadores de proveedores de nube
├── domain.py                # Entidad Incident (dominio puro)
├── services.py              # TriageService (caso de uso)
├── agents.py                # SREAgent (LangChain + Gemini)
├── repo/
│   └── Incident.py          # Repository (interfaz + impl. SQLAlchemy)
├── models/
│   └── IncidentRecord.py    # Modelo ORM (tabla incidents)
└── config/
    └── database.py          # Engine async, sesiones, Base
```

---

## 📄 Licencia

MIT — ver [LICENSE](LICENSE).

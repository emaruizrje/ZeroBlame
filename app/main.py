from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from typing import List
from contextlib import asynccontextmanager

from app.schemas import GCPWebhookPayload, IncidentResponse
from app.adapters import GCPIncidentAdapter
from app.services import TriageService
from app.config.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Asegura la existencia de tablas en Postgres al arrancar
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="ZeroBlame API",
    lifespan=lifespan,
    version="0.2.0"
)

triage_service = TriageService()


@app.post("/api/v1/webhooks/gcp", status_code=202)
async def handle_gcp_webhook(payload: GCPWebhookPayload):
    try:
        raw_dict = payload.model_dump()
        adapter = GCPIncidentAdapter(raw_dict)
        incident = adapter.to_domain()

        result = await triage_service.execute(incident)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/incidents", response_model=List[IncidentResponse])
async def get_incidents():
    try:
        return await triage_service.get_all_incidents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/v1/incidents/{incident_id}/status", response_model=IncidentResponse)
async def update_status(incident_id: int, status:str):
    # valido que no manden otros parametros que no requiero
    if status not in ["PENDING", "IN_PROGRESS", "RESOLVED"]:
        raise HTTPException(status_code=400, detail="Invalid type")
    try:
        updated= await triage_service.update_incident_status(incident_id, status)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    html_content = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ZeroBlame | SRE Dashboard</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
            <style>
                body { background-color: #0f172a; color: #e2e8f0; }
                .markdown-body h3 { font-size: 1.15rem; font-weight: bold; color: #38bdf8; margin-top: 1.25rem; margin-bottom: 0.5rem; }
                .markdown-body ul, .markdown-body ol { margin-left: 1.5rem; margin-bottom: 1rem; list-style-type: disc; }
                .markdown-body p { margin-bottom: 0.75rem; }
                .markdown-body strong { color: #f8fafc; }
            </style>
        </head>
        <body class="p-8 font-sans antialiased">
            <div class="max-w-6xl mx-auto">
                <header class="mb-10 border-b border-slate-700 pb-5 flex justify-between items-end">
                    <div>
                        <h1 class="text-4xl font-bold text-white tracking-tight flex items-center gap-3">
                            🚀 ZeroBlame <span class="text-xl font-normal text-slate-400">| SRE Copilot</span>
                        </h1>
                        <p class="text-slate-400 mt-2">Monitoreo activo de incidentes y análisis automático con IA</p>
                    </div>
                    <button onclick="fetchIncidents()" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm rounded-lg transition-colors shadow">
                        🔄 Actualizar Telemetría
                    </button>
                </header>

                <div id="incidents-container" class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <p class="text-slate-500 animate-pulse">Consultando Repositorios...</p>
                </div>
            </div>

            <script>
                // Formateadores visuales para los estados y severidades
                function getSeverityClasses(severity) {
                    const sev = (severity || '').toUpperCase();
                    if (sev === 'CRITICAL' || sev === 'FATAL') return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
                    if (sev === 'WARNING' || sev === 'WARN') return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
                    return 'bg-sky-500/10 text-sky-400 border-sky-500/30';
                }

                function getStatusClasses(status) {
                    const stat = (status || '').toUpperCase();
                    if (stat === 'PENDING') {
                        return 'bg-slate-700/30 text-slate-400 border-slate-700/50';
                    }
                    if (stat === 'IN_PROGRESS') {
                        return 'bg-amber-500/10 text-amber-300 border-amber-500/30 animate-pulse';
                    }
                    if (stat === 'RESOLVED') {
                        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
                    }
                    return 'bg-slate-700/30 text-slate-400 border-slate-700/50';
                }

                // Traductor para mostrar nombres limpios en español
                function translateStatus(status) {
                    const stat = (status || '').toUpperCase();
                    if (stat === 'PENDING') return 'PENDIENTE';
                    if (stat === 'IN_PROGRESS') return 'EN CURSO';
                    if (stat === 'RESOLVED') return 'FINALIZADA';
                    return stat;
                }

                // 💡 FUNCIÓN ASÍNCRONA PARA ACTUALIZAR EL ESTADO EN LA API
                async function updateIncidentStatus(id, newStatus) {
                    try {
                        const response = await fetch(`/api/v1/incidents/${id}/status?status=${newStatus}`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' }
                        });
                        if (response.ok) {
                            // Recargamos la interfaz para reflejar los cambios
                            fetchIncidents();
                        } else {
                            alert('No se pudo actualizar el estado.');
                        }
                    } catch (err) {
                        console.error('Error al actualizar:', err);
                    }
                }

                async function fetchIncidents() {
                    try {
                        const response = await fetch('/api/v1/incidents');
                        const incidents = await response.json();
                        const container = document.getElementById('incidents-container');
                        container.innerHTML = '';

                        if (incidents.length === 0) {
                            container.innerHTML = `
                                <div class="col-span-full text-emerald-400 border border-emerald-400/20 bg-emerald-400/10 p-5 rounded-xl">
                                    ✅ Telemetría impecable. Cero alertas en el repositorio activo.
                                </div>
                            `;
                            return;
                        }

                        incidents.forEach(inc => {
                            const parsedDiagnosis = marked.parse(inc.ai_diagnostics || "*No se registró diagnóstico.*");

                            const card = `
                                <div class="bg-slate-800 rounded-xl border border-slate-700 shadow-xl overflow-hidden flex flex-col">

                                    <!-- Cabecera de Telemetría -->
                                    <div class="p-4 border-b border-slate-700 bg-slate-800/50 flex flex-wrap gap-2 justify-between items-center">
                                        <div class="flex flex-wrap gap-2">
                                            <span class="px-2.5 py-1 text-xs font-bold uppercase rounded border ${getSeverityClasses(inc.severity)}">
                                                ${inc.severity}
                                            </span>
                                            <span class="px-2.5 py-1 text-xs font-bold uppercase rounded border ${getStatusClasses(inc.status)}">
                                                ● ${translateStatus(inc.status)}
                                            </span>
                                        </div>
                                        <span class="text-xs text-slate-400 font-mono">${new Date(inc.timestamp).toLocaleString()}</span>
                                    </div>

                                    <!-- Cuerpo del Incidente -->
                                    <div class="p-5 flex-grow">
                                        <div class="flex items-center gap-2 mb-3">
                                            <span class="bg-indigo-500/10 text-indigo-300 text-xs px-2.5 py-0.5 rounded font-mono border border-indigo-500/20">
                                                ${inc.environment}
                                            </span>
                                            <h2 class="text-xl font-bold text-white font-mono">${inc.service_name}</h2>
                                        </div>
                                        <div class="mb-4 bg-rose-950/20 border-l-4 border-rose-500 p-3 rounded-r text-sm font-mono text-rose-300 break-words">
                                            ${inc.error_message}
                                        </div>
                                        <div class="markdown-body bg-slate-900/60 p-4 rounded-lg border border-slate-700/60 text-sm">
                                            ${parsedDiagnosis}
                                        </div>
                                    </div>

                                    <!-- 💡 NUEVA SECCIÓN: Selector de Estado Interactivo -->
                                    <div class="p-4 bg-slate-900/40 border-t border-slate-700/50 flex justify-between items-center">
                                        <span class="text-xs text-slate-400 font-bold">Cambiar Estado:</span>
                                        <select 
                                            onchange="updateIncidentStatus(${inc.id}, this.value)"
                                            class="bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs font-bold py-1.5 px-3 rounded-lg border border-slate-700 focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer"
                                        >
                                            <option value="PENDING" ${inc.status === 'PENDING' ? 'selected' : ''}>PENDIENTE</option>
                                            <option value="IN_PROGRESS" ${inc.status === 'IN_PROGRESS' ? 'selected' : ''}>EN CURSO</option>
                                            <option value="RESOLVED" ${inc.status === 'RESOLVED' ? 'selected' : ''}>FINALIZADA</option>
                                        </select>
                                    </div>

                                </div>
                            `;
                            container.innerHTML += card;
                        });
                    } catch (error) {
                        console.error(error);
                        document.getElementById('incidents-container').innerHTML = 
                            '<p class="text-rose-400">❌ Fallo al comunicarse con el repositorio API.</p>';
                    }
                }
                fetchIncidents();
            </script>
        </body>
        </html>
        """
    return HTMLResponse(content=html_content)
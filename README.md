# 🚀 ZeroBlame — SRE Incident Copilot

**ZeroBlame** es una plataforma asíncrona de triaje automatizado para ingenieros SRE (Site Reliability Engineering). El sistema recibe alertas técnicas provenientes de proveedores de nube (ej. Google Cloud Platform), las normaliza mediante patrones de arquitectura limpia, utiliza inteligencia artificial (**Gemini 2.0 Flash**) para diagnosticar la causa raíz, sugiere planes de mitigación inmediata y expone una consola web interactiva para la gestión de incidentes en tiempo real.

---

## 🧠 Arquitectura del Software

Este proyecto fue diseñado bajo principios de **Clean Architecture** y **Domain-Driven Design (DDD)**, asegurando que la lógica de negocio esté totalmente desacoplada de los frameworks externos y la base de datos.

```text
Capa de Transporte (FastAPI / Webhooks)
       │
       ▼
Capa de Adaptación (GCPIncidentAdapter) -> Normaliza payloads de nube
       │
       ▼
Capa de Dominio (Incident Entity) -> Modelo puro sin acoplamiento
       │
       ▼
Capa de Casos de Uso (TriageService) -> Orquesta la IA (Gemini) y el Repositorio
       │
       ▼
Capa de Persistencia (SQLIncidentRepository) -> Control de datos asíncrono con Postgres# ZeroBlame
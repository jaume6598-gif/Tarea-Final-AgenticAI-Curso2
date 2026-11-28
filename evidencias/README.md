# Evidencias

Generadas contra el servicio desplegado con:

```bash
python -m scripts.generar_evidencias https://tarea-final-agenticai-curso2-5vk1.onrender.com
python -m scripts.evaluar https://tarea-final-agenticai-curso2-5vk1.onrender.com --salida evidencias/eval-v1.3.0-render.json
```

Cada archivo muestra la **entrada** (`curl`), la **ejecución observada**
(eventos de `GET /registros/{id_ejecucion}`) y el **resultado**. Ningún archivo
contiene claves: en los comandos, `$URL` es la URL del servicio y `$TOKEN` la
clave entregada por canal privado.

## Base obligatoria

| Prueba de la pauta | Evidencia |
|---|---|
| Dos recorridos | [01 OPERACIONES](01-ruta-operaciones-react.md), [02 TECNOLOGIA](02-ruta-tecnologia-a2a.md) |
| Ciclo ReAct (herramienta, resultado, decisión, parada) | [01](01-ruta-operaciones-react.md) |
| Delegación A2A (especialista, encargo, resultado, uso) | [02](02-ruta-tecnologia-a2a.md) |
| Seguridad: acceso inválido | [03 sin token](03-seguridad-sin-token.md) |
| Seguridad: acción no autorizada no ejecutada | [04 inyección](04-seguridad-inyeccion.md), [05 eliminar lote](05-seguridad-accion-no-autorizada.md) |
| Fallo controlado | [06 A2A caído](06-fallo-a2a.md), [07 modelo alternativo](07-fallo-modelo.md), [08 timeout](08-fallo-timeout.md) |
| Servicio desplegado vinculado al registro | Todas: cada respuesta trae `id_ejecucion` y su registro |

## Ampliaciones declaradas

| Ampliación | Puntaje | Evidencia |
|---|---|---|
| GraphRAG (Neo4j) | +1,0 | [09](09-graphrag-trazabilidad.md) |
| Flujo adicional A2A con n8n | +1,0 | [10](10-n8n-a2a-reposicion.md) |
| RAG documental | +0,5 | [11](11-rag-documental.md) |
| Uso de MCP | +0,5 | [12](12-mcp-proveedores.md) |
| Memoria persistente | +0,5 | [13 antes del reinicio](13-memoria-parte-1.md), [14 después del reinicio](14-memoria-parte-2.md) |
| Evaluación / control avanzado | +0,5 | [15 aprobación humana](15-aprobacion-humana.md), [conjunto versionado](eval-v1.3.0-render.json) |
| Observabilidad | +0,5 | [16 diagnósticos](16-observabilidad-diagnostico.md), [métricas](metricas-render.json) |

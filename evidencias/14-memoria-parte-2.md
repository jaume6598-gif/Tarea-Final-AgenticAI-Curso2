# 14-memoria-parte-2 — Despues de reiniciar el servicio, el hilo se retoma

**Criterio:** Ampliacion +0,5: memoria persistente (despues del reinicio)  
**Servicio:** https://tarea-final-agenticai-curso2-5vk1.onrender.com  
**Fecha (UTC):** 2026-11-28 01:58

## Entrada
```bash
curl -s -X POST "$URL/consultar" \
  -H "X-API-Key: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Cuál era el lote que te pedí seguir de cerca y cuánto stock tenía?", "hilo": "evidencia-memoria"}'
```

## Ejecución observada (`GET /registros/{id_ejecucion}`)
| # | evento | detalle |
|---|---|---|
| 1 | `solicitud` | {"alcance": "lector", "simulacion": null, "hilo": "evidencia-memoria"} |
| 2 | `guardia_entrada` | {"permitido": true, "categoria": "ok"} |
| 3 | `decision_router` | {"flujo": "OPERACIONES", "motivo": "Es una pregunta de seguimiento sobre inventario y lotes dentro del hilo de conversación."} |
| 4 | `memoria_recuperada` | {"hilo": "evidencia-memoria", "mensajes_previos": 6, "almacenamiento": "postgres"} |
| 5 | `parada` | {"motivo": "respuesta_final"} |
| 6 | `fin` | {"estado": "completado"} |

## Resultado
HTTP 200
```json
{
  "id_ejecucion": "ff2585cd-9ea3-45c4-8051-1513b51563e5",
  "estado": "completado",
  "flujo": "OPERACIONES",
  "motivo": "Es una pregunta de seguimiento sobre inventario y lotes dentro del hilo de conversación.",
  "ruta": [
    "guardia_entrada",
    "router",
    "operaciones"
  ],
  "hilo": "evidencia-memoria",
  "duracion_ms": 3432,
  "uso": {
    "llamadas_llm": 2,
    "tokens_entrada": 2570,
    "tokens_salida": 131,
    "modelos": {
      "gemini-3.5-flash-lite": 2
    }
  }
}
```
**Respuesta de Jaime:**

> El lote que me pediste seguir de cerca es el **L-103** (Queso fresco 500g), y tiene un stock actual de **15 unidades** (quedando 5 unidades por debajo del stock mínimo de 20). 
> 
> Como siempre en planta, sigámosle la pista de cerca en la Cámara fría 2, controlando rotación y parámetros de temperatura para asegurar la inocuidad.

**Traza ReAct de la respuesta:**
```json
[
  {
    "evento": "parada",
    "motivo": "respuesta_final"
  }
]
```


## Comprobación del reinicio
Antes de esta solicitud, `GET /registros` devolvía 0 ejecuciones: el proceso de Render se reinició y su memoria quedó vacía. El registro de la parte 1 (`0420ad6b-5c32-46f3-83c2-97e24bc69381`) ahora se lee desde Postgres (`"origen": "postgres"`, flujo OPERACIONES, estado completado). La conversación del hilo `evidencia-memoria` se retomó desde el checkpointer de Postgres (`memoria_recuperada.mensajes_previos = 6`).

## Verificación
- ✅ HTTP 200 (esperado 200)
- ✅ evento `memoria_recuperada` en el registro

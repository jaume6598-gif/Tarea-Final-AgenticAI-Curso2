# 13-memoria-parte-1 — Primer mensaje del hilo, guardado en Postgres

**Criterio:** Ampliacion +0,5: memoria persistente (antes del reinicio)  
**Servicio:** https://tarea-final-agenticai-curso2-5vk1.onrender.com  
**Fecha (UTC):** 2026-11-28 01:48

## Entrada
```bash
curl -s -X POST "$URL/consultar" \
  -H "X-API-Key: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "Revisa el stock del queso fresco, lote L-103; lo vamos a seguir de cerca esta semana.", "hilo": "evidencia-memoria"}'
```

## Ejecución observada (`GET /registros/{id_ejecucion}`)
| # | evento | detalle |
|---|---|---|
| 1 | `solicitud` | {"alcance": "lector", "simulacion": null, "hilo": "evidencia-memoria"} |
| 2 | `guardia_entrada` | {"permitido": true, "categoria": "ok"} |
| 3 | `decision_router` | {"flujo": "OPERACIONES", "motivo": "La consulta solicita revisar el stock y seguimiento de un lote específico en el inventario."} |
| 4 | `memoria_recuperada` | {"hilo": "evidencia-memoria", "mensajes_previos": 0, "almacenamiento": "postgres"} |
| 5 | `decision_herramienta` | {"herramienta": "consultar_stock", "argumentos": {"producto": "queso fresco"}} |
| 6 | `parada` | {"motivo": "respuesta_final"} |
| 7 | `fin` | {"estado": "completado"} |

## Resultado
HTTP 200
```json
{
  "id_ejecucion": "0420ad6b-5c32-46f3-83c2-97e24bc69381",
  "estado": "completado",
  "flujo": "OPERACIONES",
  "motivo": "La consulta solicita revisar el stock y seguimiento de un lote específico en el inventario.",
  "ruta": [
    "guardia_entrada",
    "router",
    "operaciones"
  ],
  "hilo": "evidencia-memoria",
  "duracion_ms": 3459,
  "uso": {
    "llamadas_llm": 3,
    "tokens_entrada": 3663,
    "tokens_salida": 214,
    "modelos": {
      "gemini-3.5-flash-lite": 3
    }
  }
}
```
**Respuesta de Jaime:**

> A nivel de operaciones y gestión de inventarios, revisé el lote **L-103** de Queso fresco 500g en el sistema:
> 
> * **Stock actual:** 15 unidades (bajo el stock mínimo de 20).
> * **Vencimiento:** 12-12-2026.
> * **Ubicación:** Cámara fría 2.
> * **Proveedor:** Lácteos Sur.
> 
> Como estamos haciendo seguimiento estricto esta semana, ojo con el quiebre de stock operativo (estamos 5 unidades bajo el mínimo) y asegúrate de mantener la cadena de frío en la Cámara 2. ¿Revisamos el registro de temperaturas de esa cámara para asegurar la inocuidad?

**Traza ReAct de la respuesta:**
```json
[
  {
    "evento": "decision_herramienta",
    "herramienta": "consultar_stock",
    "argumentos": {
      "producto": "queso fresco"
    }
  },
  {
    "evento": "resultado_herramienta",
    "herramienta": "consultar_stock",
    "resultado": "L-103 | Queso fresco 500g | stock 15 (minimo 20) | vence 2026-12-12 | Camara fria 2 | proveedor Lacteos Sur"
  },
  {
    "evento": "parada",
    "motivo": "respuesta_final"
  }
]
```


## Verificación
- ✅ HTTP 200 (esperado 200)
- ✅ evento `memoria_recuperada` en el registro

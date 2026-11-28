# 12-mcp-proveedores — El agente llama a una herramienta del servidor MCP

**Criterio:** Ampliacion +0,5: uso de MCP  
**Servicio:** https://tarea-final-agenticai-curso2-5vk1.onrender.com  
**Fecha (UTC):** 2026-11-28 01:48

## Entrada
```bash
curl -s -X POST "$URL/consultar" \
  -H "X-API-Key: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Cuál es el pedido mínimo y el plazo de entrega de Lácteos Sur?"}'
```

## Ejecución observada (`GET /registros/{id_ejecucion}`)
| # | evento | detalle |
|---|---|---|
| 1 | `solicitud` | {"alcance": "lector", "simulacion": null, "hilo": null} |
| 2 | `guardia_entrada` | {"permitido": true, "categoria": "ok"} |
| 3 | `decision_router` | {"flujo": "OPERACIONES", "motivo": "La consulta solicita información sobre los términos comerciales de un proveedor, lo cual corresponde a gestión operacional."} |
| 4 | `decision_herramienta` | {"herramienta": "consultar_proveedor", "argumentos": {"nombre": "Lácteos Sur"}, "origen": "mcp"} |
| 5 | `llamada_mcp` | {"herramienta": "consultar_proveedor", "resultado": "Lacteos Sur: contacto ventas@lacteossur.example, entrega en 2 dias, pedido minimo 60 unidades, despacha lunes, jueves."} |
| 6 | `parada` | {"motivo": "respuesta_final"} |
| 7 | `fin` | {"estado": "completado"} |

## Resultado
HTTP 200
```json
{
  "id_ejecucion": "b958bc52-8e67-4976-93e1-f7a0dede5f2a",
  "estado": "completado",
  "flujo": "OPERACIONES",
  "motivo": "La consulta solicita información sobre los términos comerciales de un proveedor, lo cual corresponde a gestión operacional.",
  "ruta": [
    "guardia_entrada",
    "router",
    "operaciones"
  ],
  "hilo": null,
  "duracion_ms": 2940,
  "uso": {
    "llamadas_llm": 3,
    "tokens_entrada": 3679,
    "tokens_salida": 128,
    "modelos": {
      "gemini-3.5-flash-lite": 3
    }
  }
}
```
**Respuesta de Jaime:**

> Para **Lácteos Sur**, los datos comerciales son los siguientes:
> 
> * **Pedido mínimo:** 60 unidades.
> * **Plazo de entrega (lead time):** 2 días (despachan los días lunes y jueves).
> 
> Cualquier duda con la reposición o los lotes, me avisas.

**Traza ReAct de la respuesta:**
```json
[
  {
    "evento": "decision_herramienta",
    "herramienta": "consultar_proveedor",
    "argumentos": {
      "nombre": "Lácteos Sur"
    },
    "origen": "mcp"
  },
  {
    "evento": "resultado_herramienta",
    "herramienta": "consultar_proveedor",
    "resultado": "Lacteos Sur: contacto ventas@lacteossur.example, entrega en 2 dias, pedido minimo 60 unidades, despacha lunes, jueves.",
    "origen": "mcp"
  },
  {
    "evento": "parada",
    "motivo": "respuesta_final"
  }
]
```


## Verificación
- ✅ HTTP 200 (esperado 200)
- ✅ evento `llamada_mcp` en el registro

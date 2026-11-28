# 07-fallo-modelo — Modelo principal falla: entra el modelo de respaldo

**Criterio:** Base 0,5: resiliencia (modelo alternativo)  
**Servicio:** https://tarea-final-agenticai-curso2-5vk1.onrender.com  
**Fecha (UTC):** 2026-11-28 01:47

## Entrada
```bash
curl -s -X POST "$URL/consultar" \
  -H "X-API-Key: $TOKEN" \
  -H "X-Simular-Fallo: modelo" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "Explica brevemente qué es FEFO."}'
```

## Ejecución observada (`GET /registros/{id_ejecucion}`)
| # | evento | detalle |
|---|---|---|
| 1 | `solicitud` | {"alcance": "lector", "simulacion": "modelo", "hilo": null} |
| 2 | `guardia_entrada` | {"permitido": true, "categoria": "ok"} |
| 3 | `modelo_respaldo_usado` | {"motivo": "FalloSimuladoDelModelo", "detalle": "Fallo simulado del modelo principal", "modelo_respaldo": "gemini-2.5-flash"} |
| 4 | `decision_router` | {"flujo": "OPERACIONES", "motivo": "La consulta pide una explicación sobre un concepto de gestión de inventarios."} |
| 5 | `modelo_respaldo_usado` | {"motivo": "FalloSimuladoDelModelo", "detalle": "Fallo simulado del modelo principal", "modelo_respaldo": "gemini-2.5-flash"} |
| 6 | `modelo_respaldo_usado` | {"motivo": "FalloSimuladoDelModelo", "detalle": "Fallo simulado del modelo principal", "modelo_respaldo": "gemini-2.5-flash"} |
| 7 | `decision_herramienta` | {"herramienta": "consultar_mis_apuntes", "argumentos": {"tema": "FEFO"}} |
| 8 | `parada` | {"motivo": "respuesta_final"} |
| 9 | `fin` | {"estado": "completado"} |

## Resultado
HTTP 200
```json
{
  "id_ejecucion": "ba8a3def-36ee-46a9-9ca7-a0b92513e924",
  "estado": "completado",
  "flujo": "OPERACIONES",
  "motivo": "La consulta pide una explicación sobre un concepto de gestión de inventarios.",
  "ruta": [
    "guardia_entrada",
    "router",
    "operaciones"
  ],
  "hilo": null,
  "duracion_ms": 4768,
  "uso": {
    "llamadas_llm": 3,
    "tokens_entrada": 3783,
    "tokens_salida": 495,
    "modelos": {
      "gemini-2.5-flash": 3
    }
  }
}
```
**Respuesta de Jaime:**

> Según mis apuntes, FEFO significa "First-Expired, First-Out". En la práctica, esto quiere decir que, en la gestión de alimentos, los productos que tienen una fecha de vencimiento más próxima deben salir primero de la bodega o línea de producción. Esto es clave para la inocuidad y para evitar mermas por vencimiento [conceptos: FEFO frente a FIFO].

**Traza ReAct de la respuesta:**
```json
[
  {
    "evento": "decision_herramienta",
    "herramienta": "consultar_mis_apuntes",
    "argumentos": {
      "tema": "FEFO"
    }
  },
  {
    "evento": "resultado_herramienta",
    "herramienta": "consultar_mis_apuntes",
    "resultado": "No existe una categoría exacta para 'FEFO'. Se entregan todos los apuntes disponibles:\nconceptos: 1) FEFO frente a FIFO: en alimentos sale primero lo que vence antes. 2) HACCP: peligros, puntos críticos de control, límites, monitoreo y acciones correctivas. Inocuidad no es lo mismo que calidad. 3) I"
  },
  {
    "evento": "parada",
    "motivo": "respuesta_final"
  }
]
```


## Verificación
- ✅ HTTP 200 (esperado 200)
- ✅ evento `modelo_respaldo_usado` en el registro

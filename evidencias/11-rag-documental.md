# 11-rag-documental — Respuesta respaldada por fragmentos de documentos internos

**Criterio:** Ampliacion +0,5: RAG documental  
**Servicio:** https://tarea-final-agenticai-curso2-5vk1.onrender.com  
**Fecha (UTC):** 2026-11-28 01:48

## Entrada
```bash
curl -s -X POST "$URL/consultar" \
  -H "X-API-Key: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "Según los procedimientos internos, ¿quién debe aprobar una merma y qué pasa con el stock mientras tanto?"}'
```

## Ejecución observada (`GET /registros/{id_ejecucion}`)
| # | evento | detalle |
|---|---|---|
| 1 | `solicitud` | {"alcance": "lector", "simulacion": null, "hilo": null} |
| 2 | `guardia_entrada` | {"permitido": true, "categoria": "ok"} |
| 3 | `decision_router` | {"flujo": "OPERACIONES", "motivo": "La consulta trata sobre procesos de gestión de mermas e inventario."} |
| 4 | `rag_fragmentos` | {"consulta": "aprobar merma stock", "metodo": "semantico", "fuentes": ["[politica_mermas.md §Aprobación]", "[politica_mermas.md §Definición]", "[politica_mermas.md §Registro]"], "puntajes": [0.785, 0.762, 0.744]} |
| 5 | `decision_herramienta` | {"herramienta": "buscar_procedimientos", "argumentos": {"consulta": "aprobar merma stock"}} |
| 6 | `parada` | {"motivo": "respuesta_final"} |
| 7 | `fin` | {"estado": "completado"} |

## Resultado
HTTP 200
```json
{
  "id_ejecucion": "2eedb4e3-93c7-47f1-97d0-c376d283d526",
  "estado": "completado",
  "flujo": "OPERACIONES",
  "motivo": "La consulta trata sobre procesos de gestión de mermas e inventario.",
  "ruta": [
    "guardia_entrada",
    "router",
    "operaciones"
  ],
  "hilo": null,
  "duracion_ms": 3064,
  "uso": {
    "llamadas_llm": 3,
    "tokens_entrada": 3873,
    "tokens_salida": 202,
    "modelos": {
      "gemini-3.5-flash-lite": 3
    }
  }
}
```
**Respuesta de Jaime:**

> Según la normativa interna, toda merma requiere la aprobación del **administrador del local** antes de ser descontada del inventario [politica_mermas.md §Aprobación]. 
> 
> Mientras tanto, el registro queda en estado **pendiente** y **el stock físico y sistémico no se modifica** hasta que se curse dicha autorización [politica_mermas.md §Aprobación]. 
> 
> *Nota operativa:* Recuerda que si la merma supera las 20 unidades o involucra productos refrigerados por quiebre de cadena de frío, el administrador debe revisar obligatoriamente el registro de temperaturas de la cámara antes de aprobarla [politica_mermas.md §Aprobación].

**Traza ReAct de la respuesta:**
```json
[
  {
    "evento": "decision_herramienta",
    "herramienta": "buscar_procedimientos",
    "argumentos": {
      "consulta": "aprobar merma stock"
    }
  },
  {
    "evento": "resultado_herramienta",
    "herramienta": "buscar_procedimientos",
    "resultado": "[politica_mermas.md §Aprobación] (similitud 0.785):\nPolítica de registro y aprobación de mermas. Aprobación. Toda merma requiere aprobación del administrador del local antes de descontarse del inventario. Una merma de más de 20 unidades o de un producto refrigerado por quiebre de cadena de frío requ"
  },
  {
    "evento": "parada",
    "motivo": "respuesta_final"
  }
]
```


## Verificación
- ✅ HTTP 200 (esperado 200)
- ✅ evento `rag_fragmentos` en el registro

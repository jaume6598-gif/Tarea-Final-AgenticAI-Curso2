# 15-aprobacion-humana — La merma queda pendiente y solo un administrador la aprueba

**Criterio:** Ampliacion +0,5: control avanzado (aprobacion humana)  
**Servicio:** https://tarea-final-agenticai-curso2-5vk1.onrender.com  
**Fecha (UTC):** 2026-11-28 01:48

## Entrada
```bash
curl -s -X POST "$URL/consultar" \
  -H "X-API-Key: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "Registra una merma de 5 unidades del lote L-601 por daño."}'
```

## Ejecución observada (`GET /registros/{id_ejecucion}`)
| # | evento | detalle |
|---|---|---|
| 1 | `solicitud` | {"alcance": "lector", "simulacion": null, "hilo": null} |
| 2 | `guardia_entrada` | {"permitido": true, "categoria": "ok"} |
| 3 | `decision_router` | {"flujo": "OPERACIONES", "motivo": "La consulta corresponde a la gestión de mermas e inventario."} |
| 4 | `aprobacion_pendiente` | {"id_solicitud": "MER-24B48E7C", "lote": "L-601", "cantidad": 5, "motivo": "daño"} |
| 5 | `decision_herramienta` | {"herramienta": "registrar_merma", "argumentos": {"cantidad": 5, "motivo": "daño", "lote": "L-601"}} |
| 6 | `parada` | {"motivo": "respuesta_final"} |
| 7 | `fin` | {"estado": "completado"} |

## Resultado
HTTP 200
```json
{
  "id_ejecucion": "30ccc311-81bd-4e1e-a024-a1d6cd42888d",
  "estado": "completado",
  "flujo": "OPERACIONES",
  "motivo": "La consulta corresponde a la gestión de mermas e inventario.",
  "ruta": [
    "guardia_entrada",
    "router",
    "operaciones"
  ],
  "hilo": null,
  "duracion_ms": 2608,
  "uso": {
    "llamadas_llm": 3,
    "tokens_entrada": 3660,
    "tokens_salida": 194,
    "modelos": {
      "gemini-3.5-flash-lite": 3
    }
  }
}
```
**Respuesta de Jaime:**

> He generado la solicitud de merma bajo el protocolo de control de inventarios y calidad. 
> 
> * **Folio de solicitud:** `MER-24B48E7C`
> * **Lote:** L-601
> * **Cantidad:** 5 unidades
> * **Motivo:** Daño
> 
> Te recuerdo que esta acción **no descuenta el stock de manera inmediata**. Queda en estado `PENDIENTE_APROBACION` y requiere la validación y firma de un administrador para proceder con la baja definitiva en bodega, asegurando la trazabilidad que exige nuestro sistema de gestión.

**Traza ReAct de la respuesta:**
```json
[
  {
    "evento": "decision_herramienta",
    "herramienta": "registrar_merma",
    "argumentos": {
      "cantidad": 5,
      "motivo": "daño",
      "lote": "L-601"
    }
  },
  {
    "evento": "resultado_herramienta",
    "herramienta": "registrar_merma",
    "resultado": "PENDIENTE_APROBACION: solicitud MER-24B48E7C creada para 5 unidades del lote L-601 (daño). El stock NO cambia hasta que un administrador la apruebe."
  },
  {
    "evento": "parada",
    "motivo": "respuesta_final"
  }
]
```

## Decisión humana
Solicitud pendiente creada por el agente: `MER-24B48E7C` (stock sin cambios mientras está pendiente).

1. Con el token lector: `POST /aprobaciones/MER-24B48E7C` → HTTP 403 (Solo un administrador puede aprobar o rechazar mermas).
2. Con el token administrador → HTTP 200:
```json
{
  "id": "MER-24B48E7C",
  "lote": "L-601",
  "cantidad": 5,
  "motivo": "daño",
  "estado": "aprobada",
  "creada": "2026-11-28T01:48:25.757814+00:00",
  "id_ejecucion": "30ccc311-81bd-4e1e-a024-a1d6cd42888d",
  "decidida_por": "admin",
  "comentario": "Revisado en bodega",
  "stock_antes": 25,
  "stock_despues": 20
}
```
La decisión humana cambia el resultado: el stock solo se descuenta después de la aprobación.

## Verificación
- ✅ HTTP 200 (esperado 200)
- ✅ evento `aprobacion_pendiente` en el registro

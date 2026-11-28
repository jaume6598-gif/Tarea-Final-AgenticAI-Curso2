# 10-n8n-a2a-reposicion — Jaime encarga ordenes de compra al Agente Compras en n8n

**Criterio:** Ampliacion +1,0: flujo adicional A2A con n8n  
**Servicio:** https://tarea-final-agenticai-curso2-5vk1.onrender.com  
**Fecha (UTC):** 2026-11-28 01:47

## Entrada
```bash
curl -s -X POST "$URL/consultar" \
  -H "X-API-Key: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "Genera las órdenes de compra para reponer lo que está bajo el stock mínimo."}'
```

## Ejecución observada (`GET /registros/{id_ejecucion}`)
| # | evento | detalle |
|---|---|---|
| 1 | `solicitud` | {"alcance": "lector", "simulacion": null, "hilo": null} |
| 2 | `guardia_entrada` | {"permitido": true, "categoria": "ok"} |
| 3 | `decision_router` | {"flujo": "REPOSICION", "motivo": "Se solicita la ejecucion de la creacion de ordenes de compra para reposicion."} |
| 4 | `decision_herramienta` | {"herramienta": "consultar_stock", "argumentos": {}} |
| 5 | `parada` | {"motivo": "respuesta_final"} |
| 6 | `delegacion_a2a` | {"especialista": "Agente Compras (n8n)", "encargo": "Soy el agente Jaime. Genera ordenes de compra en borrador para reponer estos items bajo stock minimo. Agrupa por proveedor y respeta el pedido minimo de cada uno.\n``` |
| 7 | `resultado_a2a_recibido` | {"especialista": "Agente Compras (n8n)", "caracteres": 1559} |
| 8 | `parada` | {"motivo": "respuesta_final"} |
| 9 | `uso_resultado_a2a` | {"especialista": "Agente Compras (n8n)", "uso": "ordenes citadas en la respuesta final de Jaime"} |
| 10 | `fin` | {"estado": "completado"} |

## Resultado
HTTP 200
```json
{
  "id_ejecucion": "34525b7a-524c-41f0-b035-d80808e9ae1a",
  "estado": "completado",
  "flujo": "REPOSICION",
  "motivo": "Se solicita la ejecucion de la creacion de ordenes de compra para reposicion.",
  "ruta": [
    "guardia_entrada",
    "router",
    "reposicion"
  ],
  "hilo": null,
  "duracion_ms": 7166,
  "uso": {
    "llamadas_llm": 4,
    "tokens_entrada": 6445,
    "tokens_salida": 861,
    "modelos": {
      "gemini-3.5-flash-lite": 4
    }
  }
}
```
**Respuesta de Jaime:**

> Integro mi análisis de riesgos operacionales y de inocuidad en planta con las órdenes de compra generadas por el Agente Compras. 
> 
> Las siguientes **ordenes de compra se encuentran en estado BORRADOR** y pendientes de envío a los proveedores:
> 
> 1. **OC-20261201-001** | **Lacteos Sur** | **60 unidades** (Queso fresco 500g / L-103)
>    * *Perspectiva operacional:* Crítico para evitar quiebres y asegurar la rotación en cámara fría bajo estricto control FEFO.
> 2. **OC-20261201-002** | **Panificadora Andes** | **30 unidades** (Hallullas bolsa 1kg / L-202)
>    * *Perspectiva operacional:* Reposición rápida necesaria para evitar mermas por alta rotación y corta vida útil en góndola.
> 3. **OC-20261201-003** | **Frigorifico Austral** | **16 unidades** (Carne molida 500g / L-302)
>    * *Perspectiva operacional:* Inocuidad estricta. El bajo stock limita la respuesta, requiriendo validación rigurosa de la cadena de frío.
> 4. **OC-20261201-004** | **Jugos del Pacifico** | **50 unidades** (Jugo de naranja 1L / L-501)
>    * *Perspectiva operacional:* Enfocado en sostener los indicadores de servicio (KPI) y disponibilidad en sala de venta.

**Traza ReAct de la respuesta:**
```json
[
  {
    "evento": "decision_herramienta",
    "herramienta": "consultar_stock",
    "argumentos": {}
  },
  {
    "evento": "resultado_herramienta",
    "herramienta": "consultar_stock",
    "resultado": "Lotes bajo stock minimo:\nL-103 | Queso fresco 500g | stock 15 (minimo 20) | vence 2026-12-12 | Camara fria 2 | proveedor Lacteos Sur\nL-202 | Hallullas bolsa 1kg | stock 10 (minimo 20) | vence 2026-12-02 | Gondola 4 | proveedor Panificadora Andes\nL-302 | Carne molida 500g | stock 8 (minimo 12) | venc"
  },
  {
    "evento": "parada",
    "motivo": "respuesta_final"
  },
  {
    "evento": "delegacion_a2a",
    "especialista": "Agente Compras (n8n)"
  },
  {
    "evento": "resultado_a2a_recibido"
  },
  {
    "evento": "parada",
    "motivo": "respuesta_final"
  }
]
```

**encargo_a2a:**
```
Soy el agente Jaime. Genera ordenes de compra en borrador para reponer estos items bajo stock minimo. Agrupa por proveedor y respeta el pedido minimo de cada uno.
```json
{"fecha_referencia": "2026-12-01", "items": [{"lote": "L-103", "producto": "Queso fresco 500g", "proveedor": "Lacteos Sur", "stock": 15, "stock_minimo": 20, "pedido_minimo": 60, "dias_entrega": 2}, {"lote": "L-202", "producto": "Hallullas bolsa 1kg", "proveedor": "Panificadora Andes", "stock": 10, "stock_minimo": 20, "pedido_minimo": 20, "dias_entrega": 1}, {"lote": "L-302", "producto": "Carne molida 500g", "proveedor": "Frigorifico Austral", "stock": 8, "stock_minimo": 12, "pedido_minimo": 12, "dias_entrega": 3}, {"lote": "L-501", "producto": "Jugo de naranja 1L", "proveedor": "Jugos del Pacifico", "stock": 30, "stock_minimo": 40, "pedido_minimo": 40, "dias_entrega": 2}]}
```
```

**respuesta_agente_compras:**
```
Agente Compras (n8n) genero 4 ordenes de compra en estado BORRADOR (no enviadas al proveedor).
Regla: cantidad = max(2 x stock minimo - stock, pedido minimo del proveedor).
OC-20261201-001 | Lacteos Sur | 60 unidades | entrega estimada 2026-12-03 | Queso fresco 500g (L-103): 60 u.
OC-20261201-002 | Panificadora Andes | 30 unidades | entrega estimada 2026-12-02 | Hallullas bolsa 1kg (L-202): 30 u.
OC-20261201-003 | Frigorifico Austral | 16 unidades | entrega estimada 2026-12-04 | Carne molida 500g (L-302): 16 u.
OC-20261201-004 | Jugos del Pacifico | 50 unidades | entrega estimada 2026-12-03 | Jugo de naranja 1L (L-501): 50 u.
```json
{"ordenes":[{"orden":"OC-20261201-001","proveedor":"Lacteos Sur","entrega_estimada":"2026-12-03","unidades":60,"lineas":[{"lote":"L-103","producto":"Queso fresco 500g","stock":15,"stock_minimo":20,"cantidad":60,"dias_entrega":2}]},{"orden":"OC-20261201-002","proveedor":"Panificadora Andes","entrega_estimada":"2026-12-02","unidades":30,"lineas":[{"lote":"L-202","producto":"Hallullas bolsa 1kg","stock":10,"stock_minimo":20,"cantidad":30,"dias_entrega":1}]},{"orden":"OC-20261201-003","proveedor":"Frigorifico Austral","entrega_estimada":"2026-12-04","unidades":16,"lineas":[{"lote":"L-302","producto":"Carne molida 500g","stock":8,"stock_minimo":12,"cantidad":16,"dias_entrega":3}]},{"orden":"OC-20261201-004","proveedor":"Jugos del Pacifico","entrega_estimada":"2026-12-03","unidades":50,"lineas":[{"lote":"L-501","producto":"Jugo de naranja 1L","stock":30,"stock_minimo":40,"cantidad":50,"dias_entrega":2}]}]}
```
```

**uso_resultado_a2a:**
```
Jaime cita las ordenes de n8n en el campo respuesta.
```


## Verificación
- ✅ HTTP 200 (esperado 200)
- ✅ flujo REPOSICION (esperado REPOSICION)
- ✅ evento `uso_resultado_a2a` en el registro

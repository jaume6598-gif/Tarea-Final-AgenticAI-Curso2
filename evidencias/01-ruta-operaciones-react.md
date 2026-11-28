# 01-ruta-operaciones-react — Ruta OPERACIONES con ciclo ReAct y parada explicita

**Criterio:** Base 1,0: enrutamiento + ReAct  
**Servicio:** https://tarea-final-agenticai-curso2-5vk1.onrender.com  
**Fecha (UTC):** 2026-11-28 01:46

## Entrada
```bash
curl -s -X POST "$URL/consultar" \
  -H "X-API-Key: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "Revisa el inventario y dime qué lotes vencen en los próximos 3 días y cómo priorizarlos con FEFO."}'
```

## Ejecución observada (`GET /registros/{id_ejecucion}`)
| # | evento | detalle |
|---|---|---|
| 1 | `solicitud` | {"alcance": "lector", "simulacion": null, "hilo": null} |
| 2 | `guardia_entrada` | {"permitido": true, "categoria": "ok"} |
| 3 | `decision_router` | {"flujo": "OPERACIONES", "motivo": "La consulta solicita gestionar inventario, vencimientos y aplicación de FEFO."} |
| 4 | `rag_fragmentos` | {"consulta": "FEFO rotacion vencimiento", "metodo": "semantico", "fuentes": ["[procedimiento_fefo.md §Indicadores]", "[procedimiento_fefo.md §Reposición en sala]", "[procedimiento_fefo.md §Objetivo]"], "puntajes": [0.801 |
| 5 | `decision_herramienta` | {"herramienta": "consultar_vencimientos", "argumentos": {"dias": 3}} |
| 6 | `decision_herramienta` | {"herramienta": "buscar_procedimientos", "argumentos": {"consulta": "FEFO rotacion vencimiento"}} |
| 7 | `parada` | {"motivo": "respuesta_final"} |
| 8 | `fin` | {"estado": "completado"} |

## Resultado
HTTP 200
```json
{
  "id_ejecucion": "e6356166-7271-4baa-bc19-818d3c716c9e",
  "estado": "completado",
  "flujo": "OPERACIONES",
  "motivo": "La consulta solicita gestionar inventario, vencimientos y aplicación de FEFO.",
  "ruta": [
    "guardia_entrada",
    "router",
    "operaciones"
  ],
  "hilo": null,
  "duracion_ms": 4731,
  "uso": {
    "llamadas_llm": 4,
    "tokens_entrada": 5944,
    "tokens_salida": 651,
    "modelos": {
      "gemini-3.5-flash-lite": 4
    }
  }
}
```
**Respuesta de Jaime:**

> Entendido, jefe. Operando bajo el principio FEFO (*First Expired, First Out*), la regla es clara: **lo que vence primero, sale primero**, sin excepciones que pongan en riesgo la inocuidad ni disparen las mermas. 
> 
> Según el registro de inventario, estos son los lotes críticos que vencen en los próximos 3 días (fecha de referencia: 2026-12-01), ordenados por urgencia:
> 
> 1. **L-202 (Hallullas bolsa 1kg)** - Vence el **2026-12-02** | Stock: 10 u. (Bajo mínimo de 20) | Ubicación: Góndola 4
> 2. **L-601 (Lechuga hidropónica)** - Vence el **2026-12-02** | Stock: 25 u. | Ubicación: Cámara fría 4
> 3. **L-201 (Pan de molde)** - Vence el **2026-12-03** | Stock: 35 u. | Ubicación: Góndola 4
> 4. **L-302 (Carne molida 500g)** - Vence el **2026-12-03** | Stock: 8 u. (Bajo mínimo de 12) | Ubicación: Cámara fría 3
> 5. **L-101 (Leche entera 1L)** - Vence el **2026-12-04** | Stock: 48 u. | Ubicación: Cámara fría 1
> 
> ### Instrucciones de operación y priorización:
> * **Rotación en sala y cámaras:** Los reponedores y operadores deben asegurar que las unidades de los lotes **L-202** y **L-601** queden ubicadas estrictamente en la primera línea de consumo/exhibición para garantizar su salida inmediata antes de mañana.
> * **Inocuidad y control:** Antes de cualquier reposición, se debe verificar físicamente el estado de los empaques y la cadena de frío (especialmente en la carne molida y lácteos) [procedimiento_fefo.md §Reposición en sala].
> * **Control de mermas:** Mantengamos la meta de merma por vencimiento bajo el 1,5% de las ventas mensuales [procedimiento_fefo.md §Indicadores]. Si algún lote no alcanza a salir a tiempo, deberemos procesar la solicitud de merma correspondiente antes de que expire en piso.

**Traza ReAct de la respuesta:**
```json
[
  {
    "evento": "decision_herramienta",
    "herramienta": "consultar_vencimientos",
    "argumentos": {
      "dias": 3
    }
  },
  {
    "evento": "resultado_herramienta",
    "herramienta": "consultar_vencimientos",
    "resultado": "Lotes que vencen en 3 dias (hoy 2026-12-01), orden FEFO:\nL-202 | Hallullas bolsa 1kg | stock 10 (minimo 20) | vence 2026-12-02 | Gondola 4 | proveedor Panificadora Andes\nL-601 | Lechuga hidroponica | stock 25 (minimo 20) | vence 2026-12-02 | Camara fria 4 | proveedor Huerta Los Alamos\nL-201 | Pan de"
  },
  {
    "evento": "decision_herramienta",
    "herramienta": "buscar_procedimientos",
    "argumentos": {
      "consulta": "FEFO rotacion vencimiento"
    }
  },
  {
    "evento": "resultado_herramienta",
    "herramienta": "buscar_procedimientos",
    "resultado": "[procedimiento_fefo.md §Indicadores] (similitud 0.801):\nProcedimiento FEFO de bodega y sala de ventas. Indicadores. El indicador principal es la merma por vencimiento como porcentaje de las ventas del mes; la meta es menor a 1,5 %. Se revisa semanalmente junto con la rotación de inventario de las ca"
  },
  {
    "evento": "parada",
    "motivo": "respuesta_final"
  }
]
```


## Verificación
- ✅ HTTP 200 (esperado 200)
- ✅ flujo OPERACIONES (esperado OPERACIONES)
- ✅ evento `decision_herramienta` en el registro

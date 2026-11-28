# 06-fallo-a2a — Especialista A2A caido: respuesta parcial sin inventar

**Criterio:** Base 0,5: resiliencia (ruta de respaldo)  
**Servicio:** https://tarea-final-agenticai-curso2-5vk1.onrender.com  
**Fecha (UTC):** 2026-11-28 01:47

## Entrada
```bash
curl -s -X POST "$URL/consultar" \
  -H "X-API-Key: $TOKEN" \
  -H "X-Simular-Fallo: a2a" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "Diseña una app simple para controlar mermas por vencimiento en la bodega."}'
```

## Ejecución observada (`GET /registros/{id_ejecucion}`)
| # | evento | detalle |
|---|---|---|
| 1 | `solicitud` | {"alcance": "lector", "simulacion": "a2a", "hilo": null} |
| 2 | `guardia_entrada` | {"permitido": true, "categoria": "ok"} |
| 3 | `decision_router` | {"flujo": "TECNOLOGIA", "motivo": "La consulta solicita el diseño de una aplicación de software."} |
| 4 | `rag_fragmentos` | {"consulta": "control de mermas vencimiento bodega", "metodo": "semantico", "fuentes": ["[procedimiento_fefo.md §Indicadores]", "[procedimiento_fefo.md §Objetivo]", "[procedimiento_fefo.md §Alerta de próximo a vencer]"], |
| 5 | `modelo_respaldo_usado` | {"motivo": "GoogleRateLimitError", "detalle": "Error calling model 'gemini-3.5-flash-lite' (RESOURCE_EXHAUSTED): 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your current quota, p", "modelo_re |
| 6 | `decision_herramienta` | {"herramienta": "consultar_mis_apuntes", "argumentos": {"tema": "mermas"}} |
| 7 | `decision_herramienta` | {"herramienta": "buscar_procedimientos", "argumentos": {"consulta": "control de mermas vencimiento bodega"}} |
| 8 | `parada` | {"motivo": "respuesta_final"} |
| 9 | `delegacion_a2a` | {"especialista": "Agente Gerardo", "encargo": "Soy el agente Jaime. Necesito una propuesta tecnologica basada en estos requisitos operacionales:\n\nPara controlar las mermas por vencimiento en bodega, la aplicación debe  |
| 10 | `fallo_a2a` | {"codigo": 503, "motivo": "sin_conexion", "ruta_respaldo": "solo_requisitos"} |
| 11 | `fin` | {"estado": "parcial"} |

## Resultado
HTTP 200
```json
{
  "id_ejecucion": "2843006b-e2a9-4453-8060-ff83c0ddcb03",
  "estado": "parcial",
  "flujo": "TECNOLOGIA",
  "motivo": "La consulta solicita el diseño de una aplicación de software.",
  "ruta": [
    "guardia_entrada",
    "router",
    "tecnologia",
    "respaldo_sin_especialista"
  ],
  "hilo": null,
  "duracion_ms": 4335,
  "uso": {
    "llamadas_llm": 3,
    "tokens_entrada": 4196,
    "tokens_salida": 404,
    "modelos": {
      "gemini-3.5-flash-lite": 2,
      "gemini-2.5-flash": 1
    }
  }
}
```
**Respuesta de Jaime:**

> Especialista no disponible: No se pudo conectar con Gerardo. No se incluye propuesta tecnologica para no inventarla. Requisitos operacionales definidos por Jaime:
> 
> Para controlar las mermas por vencimiento en bodega, la aplicación debe cumplir con los siguientes requisitos operacionales, priorizando la inocuidad:
> 
> 1.  **Seguimiento FEFO y Alerta de Vencimiento:** La aplicación debe asegurar la salida de los productos con fecha de vencimiento más próxima primero, en línea con el procedimiento FEFO [procedimiento_fefo.md §Objetivo]. Además, debe generar una alerta diaria de los lotes que vencen en los próximos 3 días para gestionar su salida, ya sea por promoción o donación [procedimiento_fefo.md §Alerta de próximo a vencer]. Esto es crucial para reducir la merma y proteger la inocuidad.
> 
> 2.  **Registro y Trazabilidad por Lote:** Es fundamental que la aplicación permita registrar y trazar cada lote desde su recepción hasta su salida. Esto nos permite controlar su rotación y gestionar correctamente los vencimientos, además de ser un criterio clave para una buena solución de inocuidad [criterios].
> 
> 3.  **Medición de Indicadores de Merma:** La aplicación debe ser capaz de calcular la merma por vencimiento como porcentaje de las ventas mensuales, con una meta menor al 1,5%. Este indicador debe ser revisado semanalmente, junto con la rotación de inventario de las categorías críticas (Lácteos, Carnes y Panadería) [procedimiento_fefo.md §Indicadores]. Esto nos permite monitorear el desempeño y tomar acciones correctivas si es necesario.

**Traza ReAct de la respuesta:**
```json
[
  {
    "evento": "decision_herramienta",
    "herramienta": "consultar_mis_apuntes",
    "argumentos": {
      "tema": "mermas"
    }
  },
  {
    "evento": "decision_herramienta",
    "herramienta": "buscar_procedimientos",
    "argumentos": {
      "consulta": "control de mermas vencimiento bodega"
    }
  },
  {
    "evento": "resultado_herramienta",
    "herramienta": "consultar_mis_apuntes",
    "resultado": "No existe una categoría exacta para 'mermas'. Se entregan todos los apuntes disponibles:\nconceptos: 1) FEFO frente a FIFO: en alimentos sale primero lo que vence antes. 2) HACCP: peligros, puntos críticos de control, límites, monitoreo y acciones correctivas. Inocuidad no es lo mismo que calidad. 3)"
  },
  {
    "evento": "resultado_herramienta",
    "herramienta": "buscar_procedimientos",
    "resultado": "[procedimiento_fefo.md §Indicadores] (similitud 0.775):\nProcedimiento FEFO de bodega y sala de ventas. Indicadores. El indicador principal es la merma por vencimiento como porcentaje de las ventas del mes; la meta es menor a 1,5 %. Se revisa semanalmente junto con la rotación de inventario de las ca"
  },
  {
    "evento": "parada",
    "motivo": "respuesta_final"
  },
  {
    "evento": "fallo_a2a",
    "codigo": 503,
    "motivo": "sin_conexion"
  }
]
```

**encargo_a2a:**
```
Soy el agente Jaime. Necesito una propuesta tecnologica basada en estos requisitos operacionales:

Para controlar las mermas por vencimiento en bodega, la aplicación debe cumplir con los siguientes requisitos operacionales, priorizando la inocuidad:

1.  **Seguimiento FEFO y Alerta de Vencimiento:** La aplicación debe asegurar la salida de los productos con fecha de vencimiento más próxima primero, en línea con el procedimiento FEFO [procedimiento_fefo.md §Objetivo]. Además, debe generar una alerta diaria de los lotes que vencen en los próximos 3 días para gestionar su salida, ya sea por promoción o donación [procedimiento_fefo.md §Alerta de próximo a vencer]. Esto es crucial para reducir la merma y proteger la inocuidad.

2.  **Registro y Trazabilidad por Lote:** Es fundamental que la aplicación permita registrar y trazar cada lote desde su recepción hasta su salida. Esto nos permite controlar su rotación y gestionar correctamente los vencimientos, además de ser un criterio clave para una buena solución de inocuidad [criterios].

3.  **Medición de Indicadores de Merma:** La aplicación debe ser capaz de calcular la merma por vencimiento como porcentaje de las ventas mensuales, con una meta menor al 1,5%. Este indicador debe ser revisado semanalmente, junto con la rotación de inventario de las categorías críticas (Lácteos, Carnes y Panadería) [procedimiento_fefo.md §Indicadores]. Esto nos permite monitorear el desempeño y tomar acciones correctivas si es necesario.

Propone una solucion sencilla. Distingue los supuestos no validados. No inventes informacion.
```

**requisitos_jaime:**
```
Para controlar las mermas por vencimiento en bodega, la aplicación debe cumplir con los siguientes requisitos operacionales, priorizando la inocuidad:

1.  **Seguimiento FEFO y Alerta de Vencimiento:** La aplicación debe asegurar la salida de los productos con fecha de vencimiento más próxima primero, en línea con el procedimiento FEFO [procedimiento_fefo.md §Objetivo]. Además, debe generar una alerta diaria de los lotes que vencen en los próximos 3 días para gestionar su salida, ya sea por promoción o donación [procedimiento_fefo.md §Alerta de próximo a vencer]. Esto es crucial para reducir la merma y proteger la inocuidad.

2.  **Registro y Trazabilidad por Lote:** Es fundamental que la aplicación permita registrar y trazar cada lote desde su recepción hasta su salida. Esto nos permite controlar su rotación y gestionar correctamente los vencimientos, además de ser un criterio clave para una buena solución de inocuidad [criterios].

3.  **Medición de Indicadores de Merma:** La aplicación debe ser capaz de calcular la merma por vencimiento como porcentaje de las ventas mensuales, con una meta menor al 1,5%. Este indicador debe ser revisado semanalmente, junto con la rotación de inventario de las categorías críticas (Lácteos, Carnes y Panadería) [procedimiento_fefo.md §Indicadores]. Esto nos permite monitorear el desempeño y tomar acciones correctivas si es necesario.
```


## Verificación
- ✅ HTTP 200 (esperado 200)
- ✅ estado parcial (esperado parcial)
- ✅ evento `fallo_a2a` en el registro

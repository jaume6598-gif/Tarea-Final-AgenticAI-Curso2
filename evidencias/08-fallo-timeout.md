# 08-fallo-timeout — Timeout al consultar al especialista: mensaje claro, sin reintentos infinitos

**Criterio:** Base 0,5: resiliencia (timeout)  
**Servicio:** https://tarea-final-agenticai-curso2-5vk1.onrender.com  
**Fecha (UTC):** 2026-11-28 01:47

## Entrada
```bash
curl -s -X POST "$URL/consultar" \
  -H "X-API-Key: $TOKEN" \
  -H "X-Simular-Fallo: timeout" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "Propone una arquitectura para registrar temperaturas de las cámaras de frío."}'
```

## Ejecución observada (`GET /registros/{id_ejecucion}`)
| # | evento | detalle |
|---|---|---|
| 1 | `solicitud` | {"alcance": "lector", "simulacion": "timeout", "hilo": null} |
| 2 | `guardia_entrada` | {"permitido": true, "categoria": "ok"} |
| 3 | `decision_router` | {"flujo": "TECNOLOGIA", "motivo": "La consulta solicita el diseño de una arquitectura de software para el registro de temperaturas."} |
| 4 | `rag_fragmentos` | {"consulta": "temperaturas camaras frio HACCP", "metodo": "semantico", "fuentes": ["[plan_haccp_refrigerados.md §Punto crítico de control 2: almacenamiento en cámara]", "[plan_haccp_refrigerados.md §Punto crítico de cont |
| 5 | `decision_herramienta` | {"herramienta": "consultar_mis_apuntes", "argumentos": {"tema": "temperaturas"}} |
| 6 | `decision_herramienta` | {"herramienta": "buscar_procedimientos", "argumentos": {"consulta": "temperaturas camaras frio HACCP"}} |
| 7 | `parada` | {"motivo": "respuesta_final"} |
| 8 | `delegacion_a2a` | {"especialista": "Agente Gerardo", "encargo": "Soy el agente Jaime. Necesito una propuesta tecnologica basada en estos requisitos operacionales:\n\nDesde la perspectiva de operaciones alimentarias e inocuidad (y basándom |
| 9 | `fallo_a2a` | {"codigo": 504, "motivo": "timeout", "ruta_respaldo": "solo_requisitos"} |
| 10 | `fin` | {"estado": "parcial"} |

## Resultado
HTTP 200
```json
{
  "id_ejecucion": "b59bbbb3-b1e2-45b5-b0d4-37894e6012de",
  "estado": "parcial",
  "flujo": "TECNOLOGIA",
  "motivo": "La consulta solicita el diseño de una arquitectura de software para el registro de temperaturas.",
  "ruta": [
    "guardia_entrada",
    "router",
    "tecnologia",
    "respaldo_sin_especialista"
  ],
  "hilo": null,
  "duracion_ms": 3522,
  "uso": {
    "llamadas_llm": 3,
    "tokens_entrada": 4222,
    "tokens_salida": 379,
    "modelos": {
      "gemini-3.5-flash-lite": 3
    }
  }
}
```
**Respuesta de Jaime:**

> Especialista no disponible: Tiempo de espera agotado al consultar a Gerardo. No se incluye propuesta tecnologica para no inventarla. Requisitos operacionales definidos por Jaime:
> 
> Desde la perspectiva de operaciones alimentarias e inocuidad (y basándome en los límites críticos y directrices de nuestro plan HACCP), cualquier arquitectura para el registro de temperaturas de las cámaras de frío debe cumplir estrictamente con tres requisitos operacionales:
> 
> 1. **Límite crítico validado y monitoreo por turno:** La arquitectura debe asegurar el control del límite crítico establecido (mantener las cámaras entre 0 °C y 5 °C), respaldando el monitoreo obligatorio de al menos dos veces por turno [plan_haccp_refrigerados.md §Punto crítico de control 2: almacenamiento en cámara].
> 2. **Acción correctiva automatizada y trazabilidad de desvíos:** El sistema debe ser capaz de emitir alertas tempranas si una cámara supera los 5 °C de forma continua, permitiendo identificar y bloquear los lotes afectados en caso de que la desviación supere las 2 horas, tal como exige el protocolo para la evaluación de mermas por cadena de frío [plan_haccp_refrigerados.md §Punto crítico de control 2: almacenamiento en cámara].
> 3. **Respaldo auditable y estándar operativo:** Todo registro digital o físico debe ser incorruptible y trazable para auditorías de calidad, respaldado por un procedimiento estándar escrito y personal capacitado en planta [criterios: (d) un estándar escrito y el turno capacitado].

**Traza ReAct de la respuesta:**
```json
[
  {
    "evento": "decision_herramienta",
    "herramienta": "consultar_mis_apuntes",
    "argumentos": {
      "tema": "temperaturas"
    }
  },
  {
    "evento": "decision_herramienta",
    "herramienta": "buscar_procedimientos",
    "argumentos": {
      "consulta": "temperaturas camaras frio HACCP"
    }
  },
  {
    "evento": "resultado_herramienta",
    "herramienta": "consultar_mis_apuntes",
    "resultado": "No existe una categoría exacta para 'temperaturas'. Se entregan todos los apuntes disponibles:\nconceptos: 1) FEFO frente a FIFO: en alimentos sale primero lo que vence antes. 2) HACCP: peligros, puntos críticos de control, límites, monitoreo y acciones correctivas. Inocuidad no es lo mismo que calid"
  },
  {
    "evento": "resultado_herramienta",
    "herramienta": "buscar_procedimientos",
    "resultado": "[plan_haccp_refrigerados.md §Punto crítico de control 2: almacenamiento en cámara] (similitud 0.786):\nPlan HACCP simplificado para productos refrigerados. Punto crítico de control 2: almacenamiento en cámara. Límite crítico: cámara entre 0 °C y 5 °C. Monitoreo: registro de temperatura dos veces por "
  },
  {
    "evento": "parada",
    "motivo": "respuesta_final"
  },
  {
    "evento": "fallo_a2a",
    "codigo": 504,
    "motivo": "timeout"
  }
]
```

**encargo_a2a:**
```
Soy el agente Jaime. Necesito una propuesta tecnologica basada en estos requisitos operacionales:

Desde la perspectiva de operaciones alimentarias e inocuidad (y basándome en los límites críticos y directrices de nuestro plan HACCP), cualquier arquitectura para el registro de temperaturas de las cámaras de frío debe cumplir estrictamente con tres requisitos operacionales:

1. **Límite crítico validado y monitoreo por turno:** La arquitectura debe asegurar el control del límite crítico establecido (mantener las cámaras entre 0 °C y 5 °C), respaldando el monitoreo obligatorio de al menos dos veces por turno [plan_haccp_refrigerados.md §Punto crítico de control 2: almacenamiento en cámara].
2. **Acción correctiva automatizada y trazabilidad de desvíos:** El sistema debe ser capaz de emitir alertas tempranas si una cámara supera los 5 °C de forma continua, permitiendo identificar y bloquear los lotes afectados en caso de que la desviación supere las 2 horas, tal como exige el protocolo para la evaluación de mermas por cadena de frío [plan_haccp_refrigerados.md §Punto crítico de control 2: almacenamiento en cámara].
3. **Respaldo auditable y estándar operativo:** Todo registro digital o físico debe ser incorruptible y trazable para auditorías de calidad, respaldado por un procedimiento estándar escrito y personal capacitado en planta [criterios: (d) un estándar escrito y el turno capacitado].

Propone una solucion sencilla. Distingue los supuestos no validados. No inventes informacion.
```

**requisitos_jaime:**
```
Desde la perspectiva de operaciones alimentarias e inocuidad (y basándome en los límites críticos y directrices de nuestro plan HACCP), cualquier arquitectura para el registro de temperaturas de las cámaras de frío debe cumplir estrictamente con tres requisitos operacionales:

1. **Límite crítico validado y monitoreo por turno:** La arquitectura debe asegurar el control del límite crítico establecido (mantener las cámaras entre 0 °C y 5 °C), respaldando el monitoreo obligatorio de al menos dos veces por turno [plan_haccp_refrigerados.md §Punto crítico de control 2: almacenamiento en cámara].
2. **Acción correctiva automatizada y trazabilidad de desvíos:** El sistema debe ser capaz de emitir alertas tempranas si una cámara supera los 5 °C de forma continua, permitiendo identificar y bloquear los lotes afectados en caso de que la desviación supere las 2 horas, tal como exige el protocolo para la evaluación de mermas por cadena de frío [plan_haccp_refrigerados.md §Punto crítico de control 2: almacenamiento en cámara].
3. **Respaldo auditable y estándar operativo:** Todo registro digital o físico debe ser incorruptible y trazable para auditorías de calidad, respaldado por un procedimiento estándar escrito y personal capacitado en planta [criterios: (d) un estándar escrito y el turno capacitado].
```


## Verificación
- ✅ HTTP 200 (esperado 200)
- ✅ estado parcial (esperado parcial)
- ✅ evento `fallo_a2a` en el registro

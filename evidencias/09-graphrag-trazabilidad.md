# 09-graphrag-trazabilidad — Pregunta que exige conectar camara, lotes, proveedores y locales

**Criterio:** Ampliacion +1,0: GraphRAG (Neo4j)  
**Servicio:** https://tarea-final-agenticai-curso2-5vk1.onrender.com  
**Fecha (UTC):** 2026-11-28 01:47

## Entrada
```bash
curl -s -X POST "$URL/consultar" \
  -H "X-API-Key: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "La cámara fría 2 tuvo un quiebre de cadena de frío. ¿Qué lotes, proveedores y locales quedan afectados?"}'
```

## Ejecución observada (`GET /registros/{id_ejecucion}`)
| # | evento | detalle |
|---|---|---|
| 1 | `solicitud` | {"alcance": "lector", "simulacion": null, "hilo": null} |
| 2 | `guardia_entrada` | {"permitido": true, "categoria": "ok"} |
| 3 | `decision_router` | {"flujo": "TRAZABILIDAD", "motivo": "Conecta proveedores, lotes y locales afectados por un problema en una cámara específica."} |
| 4 | `recorrido_grafo` | {"tipo": "camara", "valor": "Camara fria 2", "lotes": ["L-103", "L-501"], "locales": ["Local Centro", "Local Norte", "Local Oriente"], "proveedores": ["Jugos del Pacifico", "Lacteos Sur"]} |
| 5 | `decision_herramienta` | {"herramienta": "recorrer_trazabilidad", "argumentos": {"valor": "Camara fria 2", "tipo": "camara"}} |
| 6 | `decision_herramienta` | {"herramienta": "registro_temperaturas", "argumentos": {"camara": "Camara fria 2"}, "origen": "mcp"} |
| 7 | `llamada_mcp` | {"herramienta": "registro_temperaturas", "resultado": "Camara fria 2 -> 2026-11-30 08:00: 4.2 °C; 2026-11-30 16:00: 6.8 °C; 2026-11-30 19:00: 7.1 °C; 2026-12-01 08:00: 4.0 °C. ALERTA: 2 lecturas sobre 5.0 °C."} |
| 8 | `parada` | {"motivo": "respuesta_final"} |
| 9 | `fin` | {"estado": "completado"} |

## Resultado
HTTP 200
```json
{
  "id_ejecucion": "e91b4de6-ef24-40fa-ae1b-be08b7973e1d",
  "estado": "completado",
  "flujo": "TRAZABILIDAD",
  "motivo": "Conecta proveedores, lotes y locales afectados por un problema en una cámara específica.",
  "ruta": [
    "guardia_entrada",
    "router",
    "trazabilidad"
  ],
  "hilo": null,
  "duracion_ms": 6324,
  "uso": {
    "llamadas_llm": 3,
    "tokens_entrada": 4318,
    "tokens_salida": 479,
    "modelos": {
      "gemini-3.5-flash-lite": 3
    }
  }
}
```
**Respuesta de Jaime:**

> A partir de la trazabilidad en el grafo y el registro de temperaturas, el quiebre de cadena de frío en la **Cámara fría 2** (que registró lecturas de hasta 7.1 °C, superando el límite de 5 °C) afecta a los siguientes elementos:
> 
> 1. **Lotes afectados:**
>    - **L-103** (Producto: *Queso fresco 500g*)
>    - **L-501** (Producto: *Jugo de naranja 1L*)
> 
> 2. **Proveedores involucrados:**
>    - **Lacteos Sur** (suministra el lote L-103)
>    - **Jugos del Pacifico** (suministra el lote L-501)
> 
> 3. **Locales de destino afectados:**
>    - **Local Oriente** (asociado al lote L-103)
>    - **Local Centro** y **Local Norte** (asociados al lote L-501)
> 
> **Sustento del recorrido de relaciones:**
> - Proveedor(Lacteos Sur) -SUMINISTRA-> Lote(L-103) -ALMACENADO_EN-> Ubicacion(Camara fria 2) -DESPACHADO_A-> Local(Local Oriente)
> - Proveedor(Jugos del Pacifico) -SUMINISTRA-> Lote(L-501) -ALMACENADO_EN-> Ubicacion(Camara fria 2) -DESPACHADO_A-> Local(Local Centro, Local Norte)
> 
> Instrucción operativa: Bloquear inmediatamente el despacho de estos lotes e iniciar el protocolo de evaluación de calidad por desviación de temperatura antes de tomar una decisión de merma.

**Traza ReAct de la respuesta:**
```json
[
  {
    "evento": "decision_herramienta",
    "herramienta": "recorrer_trazabilidad",
    "argumentos": {
      "valor": "Camara fria 2",
      "tipo": "camara"
    }
  },
  {
    "evento": "decision_herramienta",
    "herramienta": "registro_temperaturas",
    "argumentos": {
      "camara": "Camara fria 2"
    },
    "origen": "mcp"
  },
  {
    "evento": "resultado_herramienta",
    "herramienta": "recorrer_trazabilidad",
    "resultado": "Recorrido en el grafo desde camara 'Camara fria 2' (2 lotes conectados):\n- Proveedor(Lacteos Sur) -SUMINISTRA-> Lote(L-103) -DE_PRODUCTO-> Producto(Queso fresco 500g) -EN_CATEGORIA-> Categoria(Lacteos); Lote(L-103) -ALMACENADO_EN-> Ubicacion(Camara fria 2) [CAMARA CON ALERTA DE TEMPERATURA]; Lote(L-"
  },
  {
    "evento": "resultado_herramienta",
    "herramienta": "registro_temperaturas",
    "resultado": "Camara fria 2 -> 2026-11-30 08:00: 4.2 °C; 2026-11-30 16:00: 6.8 °C; 2026-11-30 19:00: 7.1 °C; 2026-12-01 08:00: 4.0 °C. ALERTA: 2 lecturas sobre 5.0 °C.",
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
- ✅ flujo TRAZABILIDAD (esperado TRAZABILIDAD)
- ✅ evento `recorrido_grafo` en el registro

# 16 — Observabilidad: diagnóstico de problemas reales con trazas y métricas

**Criterio:** Ampliación +0,5: rendimiento, costo u observabilidad avanzada
("diagnóstico de un problema concreto mediante trazas y métricas" y
"comparación antes y después con las mismas entradas").

## Instrumentación disponible

- `GET /registros/{id}`: eventos de cada ejecución (router, herramientas, MCP,
  A2A, respaldo de modelo, parada, fin) y uso de LLM (`llamadas_llm`,
  `tokens_entrada`, `tokens_salida`, modelo usado). Con Postgres, el registro
  sobrevive a reinicios.
- `GET /metricas`: ejecuciones por flujo y estado, latencia p50/p95/máx, tokens
  totales y por ejecución, y conteo de eventos clave. Instantánea:
  [`metricas-render.json`](metricas-render.json).
- `scripts/evaluar.py`: mismo conjunto versionado (`eval/casos.json`) con
  latencia y tokens por caso.
- Opcional: LangSmith (`LANGSMITH_TRACING`, `LANGSMITH_API_KEY`), sin cambios de código.

## Diagnóstico 1 — el MCP no funcionaba en Render (antes/después)

**Síntoma (métricas):** la evaluación v1.0.0 en Render daba 17/17, pero R01–R06
tardaban entre 22 y 30 s y desde R07 bajaban a unos 3 s.

**Trazas:** cada solicitud registraba

```json
{"evento": "mcp_no_disponible", "motivo": "ExceptionGroup", "ruta_respaldo": "solo_herramientas_locales"}
```

y R07 ("pedido mínimo de Lácteos Sur") no tenía ningún `decision_herramienta`:
el caso pasaba porque "60" aparecía en otra parte del JSON, no porque se hubiera
consultado el MCP.

**Causa raíz:** el `.env` cargado en Render trae `MCP_URL=` vacío y
`os.getenv("MCP_URL", default)` devuelve `""` en vez del valor por defecto. El
cliente MCP recibía una URL inválida. El servidor MCP sí estaba arriba
(`Uvicorn running on http://127.0.0.1:8002` en los logs de Render).

**Corrección:** commit `15892b3` (una variable vacía usa su valor por defecto,
con test) y el evento ahora muestra la causa real y la URL usada. La evaluación
se endureció (v1.1.0): `debe_contener` mira solo el texto de la respuesta y los
casos MCP exigen `llamada_mcp`. Con eso apareció un segundo bug real (búsqueda
sensible a tildes: "Lácteos Sur"), corregido en `89279f8`.

**Antes/después, mismas entradas (17 casos):**

| Versión | Aciertos | Latencia promedio | MCP usado en R07/R08 |
|---|---|---|---|
| Antes (`MCP_URL` vacío) | 17/17 (falso positivo en R07) | 12,1 s | No |
| Después (`15892b3` + `89279f8`) | 17/17 (16/17 y luego R07+R08 2/2) | 4,6 s | Sí (`llamada_mcp`) |

## Diagnóstico 2 — el modelo de respaldo compartía cuota con el principal

**Síntoma:** el escenario "fallo de modelo" respondía 502 en Render.

**Trazas:**

```json
{"evento": "modelo_respaldo_usado", "motivo": "FalloSimuladoDelModelo", "modelo_respaldo": "gemini-3.5-flash-lite"}
{"evento": "error_router", "tipo": "GoogleRateLimitError", "detalle": "... 429 RESOURCE_EXHAUSTED ... You exceeded your current quota"}
```

**Causa raíz:** `MODELO` y `MODELO_RESPALDO` eran el mismo modelo; cuando el
principal agotaba la cuota por minuto, el respaldo también. Antes de eso, la
traza `NOT_FOUND ... no longer available to new users` mostró que
`gemini-2.5-flash-lite` ya no estaba disponible.

**Corrección:** `MODELO_RESPALDO=gemini-2.5-flash` (cuota independiente). El
escenario pasó a `completado` con `modelo_respaldo_usado: gemini-2.5-flash`
(ver [`07-fallo-modelo.md`](07-fallo-modelo.md)).

## Diagnóstico 3 — regresión del router detectada por el conjunto versionado

Al agregar la ruta `REPOSICION`, la evaluación v1.3.0 en Render marcó R03
("¿qué está bajo el mínimo?") y R07 (términos de un proveedor) como
`REPOSICION`. Se ajustaron las reglas del router (`c600c18`) y R03, R07 y N01
dieron 3/3 en Render.

## Observación vigente

En la última evaluación ([`eval-v1.3.0-render.json`](eval-v1.3.0-render.json),
19/20) el caso T02 terminó en 502 porque Gemini devolvió 429 de cuota al
principal y al respaldo tras dos corridas seguidas. El registro lo muestra y el
flujo no inventó una respuesta. `gemini-3.5-flash-lite` además ignora
`temperature=0`, por lo que el router no es 100 % determinista: por eso el
umbral del conjunto es 85 %.

# 03-seguridad-sin-token — Solicitud sin X-API-Key es rechazada

**Criterio:** Base 0,5: seguridad (acceso invalido)  
**Servicio:** https://tarea-final-agenticai-curso2-5vk1.onrender.com  
**Fecha (UTC):** 2026-11-28 01:46

## Entrada
```bash
curl -s -X POST "$URL/consultar" \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Qué lotes vencen esta semana?"}'
```

## Ejecución observada (`GET /registros/{id_ejecucion}`)
| # | evento | detalle |
|---|---|---|

## Resultado
HTTP 401
```json
{}
```

**detail:** Acceso no autorizado


## Verificación
- ✅ HTTP 401 (esperado 401)

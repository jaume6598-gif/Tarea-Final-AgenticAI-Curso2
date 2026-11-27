"""Cliente A2A minimo (JSON-RPC) para delegar en otro agente.

Lee la tarjeta publica, envia `SendMessage` con Bearer token y
devuelve el texto. Todo fallo se convierte en ErrorA2A con un
mensaje claro; nunca se inventa la respuesta del especialista.
"""

import uuid

import httpx

from agentes.errores import ErrorA2A

# Puerto cerrado: se usa para provocar un fallo de conexion real.
URL_INALCANZABLE = "http://127.0.0.1:9"
TIMEOUT_SIMULADO_S = 0.001
PREFIJO_ERROR_ESPECIALISTA = "ERROR_ESPECIALISTA:"


def construir_solicitud(texto: str, context_id: str | None = None) -> dict:
    mensaje = {
        "messageId": str(uuid.uuid4()),
        "role": "ROLE_USER",
        "parts": [{"text": texto}],
    }
    if context_id:
        mensaje["contextId"] = context_id
    return {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "SendMessage",
        "params": {"message": mensaje},
    }


def extraer_texto_respuesta(datos: dict) -> str:
    if "error" in datos:
        raise ErrorA2A(502, "El especialista devolvio un error A2A",
                       motivo="error_a2a")
    try:
        resultado = datos["result"]
        partes = (
            resultado.get("message", {}).get("parts")
            or [
                parte
                for artefacto in resultado.get("task", {}).get("artifacts", [])
                for parte in artefacto.get("parts", [])
            ]
        )
        texto = "\n".join(
            parte.get("text", "") for parte in partes if isinstance(parte, dict)
        )
    except (KeyError, TypeError, AttributeError):
        raise ErrorA2A(502, "Formato de respuesta A2A invalido",
                       motivo="formato_invalido")
    if not texto.strip():
        raise ErrorA2A(502, "El especialista devolvio una respuesta vacia",
                       motivo="respuesta_vacia")
    if texto.startswith(PREFIJO_ERROR_ESPECIALISTA):
        raise ErrorA2A(502, "El especialista no pudo generar su respuesta",
                       motivo="error_especialista")
    return texto


async def enviar_mensaje(url_base: str, token: str, texto: str,
                         timeout_s: float, nombre: str = "especialista",
                         context_id: str | None = None) -> str:
    solicitud = construir_solicitud(texto, context_id)
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as cliente:
            tarjeta = await cliente.get(
                url_base.rstrip("/") + "/.well-known/agent-card.json"
            )
            tarjeta.raise_for_status()
            url = next(
                interfaz["url"]
                for interfaz in tarjeta.json()["supportedInterfaces"]
                if interfaz["protocolBinding"] == "JSONRPC"
            )
            respuesta = await cliente.post(
                url,
                json=solicitud,
                headers={
                    "A2A-Version": "1.0",
                    "Authorization": f"Bearer {token}",
                },
            )
            respuesta.raise_for_status()
            datos = respuesta.json()
    except httpx.TimeoutException:
        raise ErrorA2A(504, f"Tiempo de espera agotado al consultar a {nombre}",
                       motivo="timeout")
    except httpx.RequestError:
        raise ErrorA2A(503, f"No se pudo conectar con {nombre}",
                       motivo="sin_conexion")
    except httpx.HTTPStatusError as error:
        raise ErrorA2A(502, f"{nombre} rechazo la solicitud A2A "
                            f"(HTTP {error.response.status_code})",
                       motivo="http_error")
    except (KeyError, StopIteration, ValueError):
        raise ErrorA2A(502, f"Tarjeta o respuesta A2A invalida de {nombre}",
                       motivo="formato_invalido")
    return extraer_texto_respuesta(datos)

"""Guardia de entrada determinista.

Se ejecuta ANTES del router y no usa el LLM: un patron obvio de
inyeccion o de extraccion de secretos se bloquea sin llamar al modelo.
El router conserva su propia regla de RECHAZO como segunda capa.
"""

import re
from dataclasses import dataclass

PATRONES = {
    "inyeccion": [
        r"\bignora\w*\b.{0,40}\b(instrucci|regla|indicaci)",
        r"\bolvida\w*\b.{0,40}\b(instrucci|regla|rol)",
        r"\b(system prompt|prompt de sistema|instrucciones internas)\b",
        r"\bact[uú]a como\b.{0,40}\b(administrador|root|sin restricciones)",
        r"\bmodo (desarrollador|dios|sin restricciones)\b",
    ],
    "secretos": [
        r"\b(token|api[ _-]?key|clave (privada|de acceso|api)|contrase[nñ]a|credencial\w*)\b",
        r"\b(variables? de entorno|archivo \.env)\b",
    ],
}

MENSAJES = {
    "inyeccion": "La solicitud intenta modificar las reglas del agente.",
    "secretos": "La solicitud intenta obtener credenciales o secretos.",
}


@dataclass(frozen=True)
class Veredicto:
    permitido: bool
    categoria: str
    motivo: str


def revisar_entrada(texto: str) -> Veredicto:
    normalizado = texto.lower()
    for categoria, patrones in PATRONES.items():
        for patron in patrones:
            if re.search(patron, normalizado):
                return Veredicto(False, categoria, MENSAJES[categoria])
    return Veredicto(True, "ok", "Sin patrones bloqueados.")

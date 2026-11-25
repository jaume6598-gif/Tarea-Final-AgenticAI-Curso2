
import os
import json

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from agentes.jaime.prompt_router import SYSTEM_ROUTER


def seleccionar_flujo(consulta: str) -> dict:
    """Clasifica una consulta y valida la decisión del Router."""

    if not consulta.strip():
        raise ValueError("La consulta está vacía.")

    load_dotenv()

    modelo = ChatGoogleGenerativeAI(
        model=os.environ["MODELO"],
        temperature=0
    )

    respuesta = modelo.invoke([
        SystemMessage(content=SYSTEM_ROUTER),
        HumanMessage(content=consulta)
    ])

    # Extraer solamente el texto generado por Gemini
    if isinstance(respuesta.content, str):
        texto = respuesta.content
    else:
        texto = "".join(
            bloque.get("text", "")
            for bloque in respuesta.content
            if isinstance(bloque, dict)
            and bloque.get("type") == "text"
        )

    texto = texto.strip()

    # Admitir JSON presentado dentro de un bloque Markdown
    if texto.startswith("```"):
        texto = texto.split("\n", 1)[1]
        texto = texto.rsplit("```", 1)[0].strip()

    datos = json.loads(texto)

    # Control independiente de la decisión del LLM
    flujos_validos = {"OPERACIONES", "TECNOLOGIA", "RECHAZO"}

    if (
        not isinstance(datos, dict)
        or datos.get("flujo") not in flujos_validos
        or not isinstance(datos.get("justificacion"), str)
    ):
        raise ValueError("Respuesta inválida del Router.")

    return datos

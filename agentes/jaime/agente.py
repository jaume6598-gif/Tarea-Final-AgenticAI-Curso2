
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from agentes.jaime.prompts import SYSTEM_VIAJES
from agentes.jaime.herramientas import HERRAMIENTAS

load_dotenv()

def crear_agente_jaime():
    modelo = ChatGoogleGenerativeAI(
        model=os.environ["MODELO"]
    )

    agente = create_agent(
        model=modelo,
        tools=HERRAMIENTAS,
        system_prompt=SYSTEM_VIAJES,
        name="agente_jaime",
    )

    return agente


import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from agentes.gerardo.prompts import SYSTEM_VIAJES
from agentes.gerardo.herramientas import HERRAMIENTAS

load_dotenv()

def crear_agente_gerardo():
    modelo = ChatGoogleGenerativeAI(
        model=os.environ["MODELO"]
    )

    agente = create_agent(
        model=modelo,
        tools=HERRAMIENTAS,
        system_prompt=SYSTEM_VIAJES,
        name="agente_gerardo",
    )

    return agente

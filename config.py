"""Configuracion centralizada del sistema.

Todas las variables de entorno se leen aqui. Ningun otro modulo
debe llamar a os.getenv directamente.
"""

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _entero(nombre: str, defecto: int) -> int:
    valor = os.getenv(nombre, "").strip()
    return int(valor) if valor else defecto


def _decimal(nombre: str, defecto: float) -> float:
    valor = os.getenv(nombre, "").strip()
    return float(valor) if valor else defecto


def _booleano(nombre: str, defecto: bool = False) -> bool:
    valor = os.getenv(nombre, "").strip().lower()
    if not valor:
        return defecto
    return valor in {"1", "true", "si", "yes"}


@dataclass(frozen=True)
class Config:
    # Modelos
    modelo: str
    modelo_respaldo: str
    timeout_llm_s: float
    # Limites del ciclo ReAct
    max_pasos_react: int
    max_llamadas_herramienta: int
    # Seguridad
    app_api_token: str
    app_admin_token: str
    a2a_token: str
    permitir_simulacion_fallos: bool
    # A2A
    url_gerardo: str
    timeout_a2a_s: float
    # Datos de ejemplo
    fecha_referencia: str
    # Ampliaciones (opcionales)
    database_url: str
    neo4j_uri: str
    neo4j_usuario: str
    neo4j_clave: str
    n8n_a2a_url: str
    n8n_token: str
    mcp_url: str
    mcp_token: str


@lru_cache(maxsize=1)
def obtener_config() -> Config:
    return Config(
        modelo=os.getenv("MODELO", "gemini-2.5-flash"),
        modelo_respaldo=os.getenv("MODELO_RESPALDO", "gemini-2.5-flash-lite"),
        timeout_llm_s=_decimal("TIMEOUT_LLM_S", 30.0),
        max_pasos_react=_entero("MAX_PASOS_REACT", 25),
        max_llamadas_herramienta=_entero("MAX_LLAMADAS_HERRAMIENTA", 4),
        app_api_token=os.getenv("APP_API_TOKEN", ""),
        app_admin_token=os.getenv("APP_ADMIN_TOKEN", ""),
        a2a_token=os.getenv("A2A_TOKEN", ""),
        permitir_simulacion_fallos=_booleano("PERMITIR_SIMULACION_FALLOS"),
        url_gerardo=os.getenv("URL_GERARDO", "http://127.0.0.1:8001"),
        timeout_a2a_s=_decimal("TIMEOUT_A2A_S", 90.0),
        fecha_referencia=os.getenv("FECHA_REFERENCIA", "2026-12-01"),
        database_url=os.getenv("DATABASE_URL", ""),
        neo4j_uri=os.getenv("NEO4J_URI", ""),
        neo4j_usuario=os.getenv("NEO4J_USERNAME", ""),
        neo4j_clave=os.getenv("NEO4J_PASSWORD", ""),
        n8n_a2a_url=os.getenv("N8N_A2A_URL", ""),
        n8n_token=os.getenv("N8N_TOKEN", ""),
        mcp_url=os.getenv("MCP_URL", ""),
        mcp_token=os.getenv("MCP_TOKEN", ""),
    )


TOKENS_INVALIDOS = {"", "TU_TOKEN_PRIVADO"}


def validar_config_api(config: Config) -> None:
    """Falla al iniciar si falta un secreto obligatorio de la API."""

    faltantes = []
    if config.app_api_token in TOKENS_INVALIDOS:
        faltantes.append("APP_API_TOKEN")
    if config.a2a_token in TOKENS_INVALIDOS:
        faltantes.append("A2A_TOKEN")
    if faltantes:
        raise RuntimeError(
            "Configura en .env: " + ", ".join(faltantes)
        )

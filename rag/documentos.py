"""RAG documental sobre docs_conocimiento/.

- Cada seccion (## ...) de cada documento es un fragmento con su fuente.
- Recuperacion semantica con embeddings de Gemini (InMemoryVectorStore).
- Si los embeddings fallan, recuperacion lexica de respaldo (sin LLM).
- Si ningun fragmento supera el umbral, no hay evidencia: el agente
  debe decir que no lo sabe en vez de inventar.
"""

import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore

from config import obtener_config
from registro.bitacora import evento

logger = logging.getLogger("sistema_agentes")

RUTA_DOCUMENTOS = Path(__file__).resolve().parent.parent / "docs_conocimiento"
TOP_K = 3
# Calibrated with gemini-embedding-001: relevant sections score >= 0.70,
# out-of-scope questions (opening hours, printers) score <= 0.65.
UMBRAL_SEMANTICO = 0.68
UMBRAL_LEXICO = 0.15
MODELO_EMBEDDINGS = "models/gemini-embedding-001"


@dataclass(frozen=True)
class Fragmento:
    fuente: str
    seccion: str
    texto: str
    puntaje: float

    @property
    def cita(self) -> str:
        return f"[{self.fuente} §{self.seccion}]"


def cargar_fragmentos(ruta: Path = RUTA_DOCUMENTOS) -> list[Document]:
    documentos = []
    for archivo in sorted(ruta.glob("*.md")):
        contenido = archivo.read_text(encoding="utf-8")
        titulo = contenido.splitlines()[0].lstrip("# ").strip()
        for bloque in re.split(r"^## ", contenido, flags=re.MULTILINE)[1:]:
            seccion, _, cuerpo = bloque.partition("\n")
            documentos.append(Document(
                page_content=f"{titulo}. {seccion.strip()}. {cuerpo.strip()}",
                metadata={"fuente": archivo.name, "seccion": seccion.strip()},
            ))
    return documentos


def _normalizar(texto: str) -> set[str]:
    sin_tildes = unicodedata.normalize("NFKD", texto.lower())
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    # Crude stemming: 'aprobar' and 'aprobacion' share the root 'aproba'.
    return {palabra[:6] for palabra in re.findall(r"[a-z0-9]+", sin_tildes)
            if len(palabra) > 3}


def _crear_embeddings():
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    return GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)


class BuscadorDocumental:
    def __init__(self, documentos: list[Document] | None = None,
                 crear_embeddings=_crear_embeddings):
        self.documentos = documentos if documentos is not None else cargar_fragmentos()
        self._crear_embeddings = crear_embeddings
        self._indice: InMemoryVectorStore | None = None

    def _indice_semantico(self) -> InMemoryVectorStore:
        if self._indice is None:
            self._indice = InMemoryVectorStore.from_documents(
                self.documentos, self._crear_embeddings()
            )
        return self._indice

    def _buscar_lexico(self, consulta: str) -> list[Fragmento]:
        terminos = _normalizar(consulta)
        puntuados = []
        for documento in self.documentos:
            palabras = _normalizar(documento.page_content)
            titulo = _normalizar(documento.metadata["seccion"])
            coincidencias = len(terminos & palabras) + len(terminos & titulo)
            puntaje = min(1.0, coincidencias / max(len(terminos), 1))
            puntuados.append((puntaje, documento))
        puntuados.sort(key=lambda par: par[0], reverse=True)
        return [
            Fragmento(d.metadata["fuente"], d.metadata["seccion"],
                      d.page_content, round(p, 3))
            for p, d in puntuados[:TOP_K] if p >= UMBRAL_LEXICO
        ]

    def buscar(self, consulta: str) -> tuple[list[Fragmento], str]:
        """Devuelve (fragmentos, metodo)."""
        try:
            resultados = self._indice_semantico().similarity_search_with_score(
                consulta, k=TOP_K
            )
            fragmentos = [
                Fragmento(d.metadata["fuente"], d.metadata["seccion"],
                          d.page_content, round(float(p), 3))
                for d, p in resultados if p >= UMBRAL_SEMANTICO
            ]
            return fragmentos, "semantico"
        except Exception as error:
            logger.warning("Embeddings no disponibles: %s", type(error).__name__)
            evento("rag_respaldo_lexico", motivo=type(error).__name__)
            return self._buscar_lexico(consulta), "lexico"


_buscador: BuscadorDocumental | None = None


def obtener_buscador() -> BuscadorDocumental:
    global _buscador
    if _buscador is None:
        obtener_config()  # carga .env antes de crear el cliente de embeddings
        _buscador = BuscadorDocumental()
    return _buscador


def formatear(fragmentos: list[Fragmento]) -> str:
    if not fragmentos:
        return ("SIN_EVIDENCIA: ningun documento interno respalda esta "
                "consulta. Indica que no hay un procedimiento escrito.")
    return "\n\n".join(
        f"{f.cita} (similitud {f.puntaje}):\n{f.texto}" for f in fragmentos
    )

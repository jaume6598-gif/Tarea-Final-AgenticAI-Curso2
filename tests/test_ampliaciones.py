"""Pruebas de las ampliaciones (sin red ni LLM real)."""

import asyncio

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from tests.conftest import ADMIN, LECTOR, llamada, modelo_con


def _sin_embeddings():
    raise ConnectionError("embeddings no disponibles en pruebas")


# ------------------------------------------------------------ RAG documental

def test_rag_recupera_fragmento_con_fuente_por_respaldo_lexico():
    from rag.documentos import BuscadorDocumental, formatear

    buscador = BuscadorDocumental(crear_embeddings=_sin_embeddings)
    fragmentos, metodo = buscador.buscar("¿Quién debe aprobar una merma antes de descontarla?")

    assert metodo == "lexico"
    assert fragmentos[0].cita == "[politica_mermas.md §Aprobación]"
    assert "[politica_mermas.md §Aprobación]" in formatear(fragmentos)


def test_rag_sin_evidencia_no_inventa():
    from rag.documentos import BuscadorDocumental, formatear

    buscador = BuscadorDocumental(crear_embeddings=_sin_embeddings)
    fragmentos, _ = buscador.buscar("horario de atención de la farmacia")

    assert fragmentos == []
    assert formatear(fragmentos).startswith("SIN_EVIDENCIA")


def test_documentos_se_dividen_por_seccion():
    from rag.documentos import cargar_fragmentos

    fuentes = {d.metadata["fuente"] for d in cargar_fragmentos()}
    assert fuentes == {"procedimiento_fefo.md", "politica_mermas.md",
                       "plan_haccp_refrigerados.md"}


# ------------------------------------------------------------ aprobacion humana

def _registrar_merma_por_agente(cliente, modelos_falsos, router_fijo):
    router_fijo("OPERACIONES")
    modelos_falsos(modelo_con(
        llamada("registrar_merma", lote="L-101", cantidad=10, motivo="vencimiento"),
        AIMessage(content="Merma pendiente de aprobación."),
    ))
    cliente.post("/consultar", headers=LECTOR,
                 json={"pregunta": "Registra 10 unidades de merma del lote L-101"})
    pendientes = cliente.get("/aprobaciones?estado=pendiente", headers=LECTOR).json()
    assert len(pendientes) == 1
    return pendientes[0]


def test_merma_queda_pendiente_sin_cambiar_stock(cliente, modelos_falsos, router_fijo):
    solicitud = _registrar_merma_por_agente(cliente, modelos_falsos, router_fijo)

    assert solicitud["estado"] == "pendiente"
    assert cliente.get("/inventario/L-101", headers=LECTOR).json()["stock"] == 48


def test_lector_no_puede_aprobar(cliente, modelos_falsos, router_fijo):
    solicitud = _registrar_merma_por_agente(cliente, modelos_falsos, router_fijo)

    respuesta = cliente.post(f"/aprobaciones/{solicitud['id']}", headers=LECTOR,
                             json={"aprobar": True})

    assert respuesta.status_code == 403
    assert cliente.get("/inventario/L-101", headers=LECTOR).json()["stock"] == 48


def test_admin_aprueba_y_descuenta_stock(cliente, modelos_falsos, router_fijo):
    solicitud = _registrar_merma_por_agente(cliente, modelos_falsos, router_fijo)

    respuesta = cliente.post(f"/aprobaciones/{solicitud['id']}", headers=ADMIN,
                             json={"aprobar": True, "comentario": "revisado"})

    assert respuesta.json()["estado"] == "aprobada"
    assert respuesta.json()["stock_antes"] == 48
    assert cliente.get("/inventario/L-101", headers=LECTOR).json()["stock"] == 38
    segunda = cliente.post(f"/aprobaciones/{solicitud['id']}", headers=ADMIN,
                           json={"aprobar": False})
    assert segunda.status_code == 409


def test_admin_rechaza_y_stock_no_cambia(cliente, modelos_falsos, router_fijo):
    solicitud = _registrar_merma_por_agente(cliente, modelos_falsos, router_fijo)

    respuesta = cliente.post(f"/aprobaciones/{solicitud['id']}", headers=ADMIN,
                             json={"aprobar": False})

    assert respuesta.json()["estado"] == "rechazada"
    assert cliente.get("/inventario/L-101", headers=LECTOR).json()["stock"] == 48


# ------------------------------------------------------------ MCP

def test_servidor_mcp_exige_bearer():
    import servidor_mcp

    mcp = TestClient(servidor_mcp.app)
    assert mcp.get("/salud").status_code == 200
    assert mcp.post("/mcp", json={}).status_code == 401


def test_herramienta_mcp_detecta_temperatura_fuera_de_rango():
    import servidor_mcp

    assert "ALERTA: 2 lecturas" in servidor_mcp.registro_temperaturas("camara fria 2")
    assert "pedido minimo 60" in servidor_mcp.consultar_proveedor("lacteos sur")


def test_herramienta_mcp_ignora_tildes():
    import servidor_mcp

    assert "pedido minimo 60" in servidor_mcp.consultar_proveedor("Lácteos Sur")
    assert "Camara fria 2" in servidor_mcp.registro_temperaturas("Cámara fría 2")


def test_cliente_mcp_filtra_por_allowlist(monkeypatch):
    from agentes.jaime import mcp_cliente

    @tool
    def consultar_proveedor(nombre: str) -> str:
        """Proveedor."""
        return nombre

    @tool
    def borrar_todo() -> str:
        """No permitida."""
        return "x"

    class ClienteFalso:
        def __init__(self, *args, **kwargs):
            pass

        async def get_tools(self):
            return [consultar_proveedor, borrar_todo]

    mcp_cliente.reiniciar_cache()
    monkeypatch.setattr(mcp_cliente, "MultiServerMCPClient", ClienteFalso)
    herramientas = asyncio.run(mcp_cliente.obtener_herramientas_mcp())
    mcp_cliente.reiniciar_cache()

    assert [h.name for h in herramientas] == ["consultar_proveedor"]


def test_cliente_mcp_caido_usa_solo_herramientas_locales(monkeypatch):
    from agentes.jaime import mcp_cliente

    class ClienteCaido:
        def __init__(self, *args, **kwargs):
            pass

        async def get_tools(self):
            raise ConnectionError("sin servidor")

    mcp_cliente.reiniciar_cache()
    monkeypatch.setattr(mcp_cliente, "MultiServerMCPClient", ClienteCaido)
    assert asyncio.run(mcp_cliente.obtener_herramientas_mcp()) == []
    mcp_cliente.reiniciar_cache()


# ------------------------------------------------------------ observabilidad

def test_tokens_y_metricas_por_ejecucion(cliente, modelos_falsos, router_fijo):
    router_fijo("OPERACIONES")
    uso = {"input_tokens": 120, "output_tokens": 30, "total_tokens": 150}
    modelos_falsos(modelo_con(
        AIMessage(content="", usage_metadata=uso, tool_calls=[{
            "name": "consultar_stock", "args": {"producto": "leche"}, "id": "t1"}]),
        AIMessage(content="Hay 48 unidades de leche.", usage_metadata=uso),
    ))

    cuerpo = cliente.post("/consultar", headers=LECTOR,
                          json={"pregunta": "¿Cuánta leche queda?"}).json()

    assert cuerpo["uso"]["llamadas_llm"] == 2
    assert cuerpo["uso"]["tokens_entrada"] == 240
    assert cuerpo["uso"]["tokens_salida"] == 60
    metricas = cliente.get("/metricas", headers=LECTOR).json()
    assert metricas["ejecuciones"] >= 1
    assert metricas["tokens"]["entrada_total"] >= 240
    assert metricas["por_flujo"]["OPERACIONES"] >= 1
    assert cliente.get("/metricas").status_code == 401


def test_variable_vacia_en_env_usa_el_valor_por_defecto(monkeypatch):
    import config

    monkeypatch.setenv("MCP_URL", "")
    monkeypatch.setenv("URL_GERARDO", "  ")
    config.obtener_config.cache_clear()
    try:
        valores = config.obtener_config()
        assert valores.mcp_url == "http://127.0.0.1:8002/mcp"
        assert valores.url_gerardo == "http://127.0.0.1:8001"
    finally:
        config.obtener_config.cache_clear()


# ------------------------------------------------------------ memoria persistente

def test_hilo_retoma_la_conversacion_guardada(modelos_falsos, router_fijo):
    from main import app

    router_fijo("OPERACIONES")
    modelos_falsos(modelo_con(
        llamada("consultar_stock", producto="yogur"),
        AIMessage(content="Anotado: revisaremos el lote L-102 de yogur."),
        AIMessage(content="Hablábamos del lote L-102 (yogur natural)."),
    ))

    with TestClient(app) as cliente:  # runs the lifespan: RAM checkpointer
        assert cliente.get("/salud").json()["memoria"] == "ram"
        primera = cliente.post("/consultar", headers=LECTOR, json={
            "pregunta": "Revisa el stock del yogur, lote L-102", "hilo": "prueba-1"}).json()
        segunda = cliente.post("/consultar", headers=LECTOR, json={
            "pregunta": "¿Y cuál era el lote que te mencioné?", "hilo": "prueba-1"}).json()
        registro = cliente.get(f"/registros/{segunda['id_ejecucion']}",
                               headers=LECTOR).json()

    recuperada = [e for e in registro["eventos"] if e["evento"] == "memoria_recuperada"][0]
    assert recuperada["mensajes_previos"] == 4  # user, tool call, tool result, answer
    assert segunda["hilo"] == "prueba-1"
    assert "L-102" in segunda["respuesta"]
    # The second answer's trace only shows this run, not the earlier tool call.
    assert [p["evento"] for p in segunda["traza"]] == ["parada"]
    assert [p["evento"] for p in primera["traza"]][0] == "decision_herramienta"


def test_hilo_invalido_se_rechaza(cliente):
    respuesta = cliente.post("/consultar", headers=LECTOR, json={
        "pregunta": "¿Qué vence esta semana?", "hilo": "../etc/passwd"})
    assert respuesta.status_code == 422


# ------------------------------------------------------------ GraphRAG

FILAS_CAMARA_2 = [
    {"proveedor": "Lacteos Sur", "lote": "L-103", "vencimiento": "2026-12-12",
     "stock": 15, "producto": "Queso fresco 500g", "categoria": "Lacteos",
     "camara": "Camara fria 2", "alerta_camara": True, "max_c": 7.1,
     "locales": ["Local Oriente"]},
    {"proveedor": "Jugos del Pacifico", "lote": "L-501", "vencimiento": "2026-12-20",
     "stock": 30, "producto": "Jugo de naranja 1L", "categoria": "Bebidas",
     "camara": "Camara fria 2", "alerta_camara": True, "max_c": 7.1,
     "locales": ["Local Centro", "Local Norte"]},
]


def test_grafo_devuelve_recorrido_y_hechos():
    from grafo.trazabilidad import recorrer

    consultas = []

    def ejecutor(cypher, parametros):
        consultas.append((cypher, parametros))
        return FILAS_CAMARA_2

    texto = recorrer("camara", "Cámara fría 2", ejecutor)

    assert parametros_normalizados(consultas) == {"valor": "camara fria 2"}
    assert "Proveedor(Lacteos Sur) -SUMINISTRA-> Lote(L-103)" in texto
    assert "-DESPACHADO_A-> Local(Local Centro, Local Norte)" in texto
    assert "CAMARA CON ALERTA DE TEMPERATURA" in texto
    assert "locales alcanzados ['Local Centro', 'Local Norte', 'Local Oriente']" in texto
    assert "MERGE" not in consultas[0][0] and "toLower(c.nombre)" in consultas[0][0]


def parametros_normalizados(consultas):
    return consultas[0][1]


def test_grafo_tipo_invalido_no_consulta():
    from grafo.trazabilidad import recorrer

    def ejecutor(*_):
        raise AssertionError("no debe consultar")

    assert recorrer("cliente", "x", ejecutor).startswith("Parametro invalido")


def test_grafo_caido_no_inventa():
    from grafo.trazabilidad import recorrer

    def ejecutor(*_):
        raise ConnectionError("Aura pausada")

    assert recorrer("lote", "L-102", ejecutor).startswith("GRAFO_NO_DISPONIBLE")


def test_flujo_trazabilidad_cita_el_recorrido(cliente, modelos_falsos, router_fijo, monkeypatch):
    router_fijo("TRAZABILIDAD")
    monkeypatch.setattr("grafo.trazabilidad.ejecutar_lectura", lambda c, p: FILAS_CAMARA_2)
    modelos_falsos(modelo_con(
        llamada("recorrer_trazabilidad", tipo="camara", valor="Camara fria 2"),
        AIMessage(content="Afecta a Local Oriente, Local Centro y Local Norte "
                          "(Lote L-103 -DESPACHADO_A-> Local Oriente)."),
    ))

    cuerpo = cliente.post("/consultar", headers=LECTOR, json={
        "pregunta": "La cámara fría 2 tuvo un quiebre de frío, ¿qué locales afecta?"}).json()

    assert cuerpo["flujo"] == "TRAZABILIDAD"
    assert cuerpo["ruta"] == ["guardia_entrada", "router", "trazabilidad"]
    resultado = [p for p in cuerpo["traza"] if p["evento"] == "resultado_herramienta"][0]
    assert resultado["herramienta"] == "recorrer_trazabilidad"
    assert "SUMINISTRA" in resultado["resultado"]
    registro = cliente.get(f"/registros/{cuerpo['id_ejecucion']}", headers=LECTOR).json()
    recorrido = [e for e in registro["eventos"] if e["evento"] == "recorrido_grafo"][0]
    assert recorrido["lotes"] == ["L-103", "L-501"]

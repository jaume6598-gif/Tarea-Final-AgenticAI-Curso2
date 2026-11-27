"""Runs the versioned evaluation set (eval/casos.json) against a service.

Checks per case: HTTP code, routed flow, required text and required log
event. Prints a hit table plus latency and token totals, and fails when
the hit rate is below the set's threshold.

Usage:
    python -m scripts.evaluar https://<service>.onrender.com --salida evidencias/eval.json
    python -m scripts.evaluar http://127.0.0.1:8000 --pausa 5
"""

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

from config import obtener_config

RUTA_CASOS = Path(__file__).resolve().parent.parent / "eval" / "casos.json"


def evaluar_caso(cliente: httpx.Client, caso: dict, token: str) -> dict:
    inicio = time.perf_counter()
    respuesta = cliente.post("/consultar", headers={"X-API-Key": token},
                             json={"pregunta": caso["pregunta"]})
    segundos = round(time.perf_counter() - inicio, 1)
    cuerpo = respuesta.json()
    texto = json.dumps(cuerpo, ensure_ascii=False)
    eventos = []
    if cuerpo.get("id_ejecucion"):
        registro = cliente.get(f"/registros/{cuerpo['id_ejecucion']}",
                               headers={"X-API-Key": token}).json()
        eventos = [e["evento"] for e in registro.get("eventos", [])]

    fallas = []
    if respuesta.status_code != caso["codigo"]:
        fallas.append(f"http {respuesta.status_code} != {caso['codigo']}")
    if caso.get("flujo") and cuerpo.get("flujo") != caso["flujo"]:
        fallas.append(f"flujo {cuerpo.get('flujo')} != {caso['flujo']}")
    for fragmento in caso.get("debe_contener", []):
        if fragmento not in texto:
            fallas.append(f"falta '{fragmento}'")
    if caso.get("evento") and caso["evento"] not in eventos:
        fallas.append(f"sin evento {caso['evento']}")

    uso = cuerpo.get("uso") or {}
    return {
        "id": caso["id"],
        "ok": not fallas,
        "fallas": fallas,
        "http": respuesta.status_code,
        "flujo": cuerpo.get("flujo"),
        "estado": cuerpo.get("estado"),
        "segundos": segundos,
        "tokens": uso.get("tokens_entrada", 0) + uso.get("tokens_salida", 0),
        "llamadas_llm": uso.get("llamadas_llm", 0),
        "id_ejecucion": cuerpo.get("id_ejecucion"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--salida", help="Write the result JSON here")
    parser.add_argument("--pausa", type=float, default=4.0,
                        help="Seconds between cases (avoid model rate limits)")
    parser.add_argument("--solo", nargs="*", help="Run only these case ids")
    argumentos = parser.parse_args()

    conjunto = json.loads(RUTA_CASOS.read_text(encoding="utf-8"))
    casos = [c for c in conjunto["casos"]
             if not argumentos.solo or c["id"] in argumentos.solo]
    token = obtener_config().app_api_token
    resultados = []

    with httpx.Client(base_url=argumentos.url.rstrip("/"), timeout=240) as cliente:
        for indice, caso in enumerate(casos):
            if indice:
                time.sleep(argumentos.pausa)
            resultado = evaluar_caso(cliente, caso, token)
            resultados.append(resultado)
            marca = "OK   " if resultado["ok"] else "FALLA"
            print(f"{marca} {resultado['id']:<4} HTTP {resultado['http']} "
                  f"{resultado['flujo'] or '-':<12} {resultado['segundos']:>5}s "
                  f"{resultado['tokens']:>6} tok  {'; '.join(resultado['fallas'])}")

    aciertos = sum(r["ok"] for r in resultados)
    tasa = aciertos / len(resultados) if resultados else 0
    con_llm = [r for r in resultados if r["llamadas_llm"]]
    resumen = {
        "version_casos": conjunto["version"],
        "url": argumentos.url,
        "aciertos": aciertos,
        "total": len(resultados),
        "tasa": round(tasa, 3),
        "umbral": conjunto["umbral_aciertos"],
        "segundos_promedio": round(sum(r["segundos"] for r in resultados)
                                   / max(len(resultados), 1), 1),
        "tokens_totales": sum(r["tokens"] for r in resultados),
        "tokens_promedio_con_llm": (round(sum(r["tokens"] for r in con_llm)
                                          / len(con_llm)) if con_llm else 0),
    }
    print(f"\n{aciertos}/{len(resultados)} aciertos ({tasa:.0%}), umbral "
          f"{conjunto['umbral_aciertos']:.0%} | {resumen['segundos_promedio']}s "
          f"promedio | {resumen['tokens_totales']} tokens")

    if argumentos.salida:
        Path(argumentos.salida).parent.mkdir(parents=True, exist_ok=True)
        Path(argumentos.salida).write_text(
            json.dumps({"resumen": resumen, "resultados": resultados},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return 0 if tasa >= conjunto["umbral_aciertos"] else 1


if __name__ == "__main__":
    sys.exit(main())

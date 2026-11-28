# Feature: rubrica-completa
Objective: close mandatory-base gaps of Pauta_tarea_final_Curso_2 and add all extensions. Branch: feat/rubrica-completa. Delivery: ask-on-risk. Runner: pytest (.venv).

## Specs
- S1 Router+worker: "El mismo agente cumple los roles de router y worker." Two requests trigger different flows; ReAct with explicit stop condition.
- S2 A2A: "el agente principal encarga una tarea a otro agente por A2A y usa el resultado."
- S3 Security: "Demuestren que una solicitud sin acceso válido se rechaza y que el agente bloquea una acción no autorizada sin ejecutarla."
- S4 Resilience: "Provoquen un fallo y demuestren qué hace el flujo sin inventar resultados ni repetir indefinidamente."
- S5 Deploy: "Un registro simple permite comprobar qué flujo se ejecutó y cómo terminó."
- S6 Extensions (all, per user): GraphRAG, n8n A2A, RAG documental, MCP, memoria persistente, evaluación/control, observabilidad.
- S7 Docs: ficha mínima + evidencias, no secrets in repo.

## Tasks
- T1 S4,S5 config + model factory w/ fallback + bitacora — inline — done
- T2 S1 LangGraph router+worker, ReAct tools, explicit stop — inline — done
- T3 S3 deterministic guard + admin-scoped action block (Risk item 2) — inline — done
- T4 S2,S4 A2A auth, fallback route, fault injection — inline — done
- T5 S5 /registros, /salud, thin main — inline — done
- T6 S6 extensions (one commit each) — pending
- T7 S7 README + evidencias — pending

## Log
- L1 (2026-11-27) "analiza el proyecto actual en base a la rubrica indicada en Pauta_tarea_final_Curso_2.pdf e identifica que cosas aun le faltan para cumplir toda la rubrica. Generar un plan con las modificaciones necesarias y considera toda la materia que esta en los .md ..."
- L2 "considera agregar todas las ampliaciones de la rubrica aunque superemos la nota maxima."
- L3 "Sí, empezá" — implementation authorized, starting with Fase 0 + base.
- L4 T1-T5 done: pytest 17 passed (offline, fake models). Live Gemini/Render smoke test pending (no local .env). Note: MAX_PASOS_REACT default 25 so the tool-call cap (4) triggers first; both stops remain explicit.
- L5 Deployed on user's Render (fork gherrerz, branch feat/rubrica-completa). Smoke test 7/7 on Render (6/7 full run + fallo_modelo rerun after MODELO_RESPALDO=gemini-2.5-flash; same-model fallback shared quota and hit 429). gemini-2.5-flash-lite is no longer available to new users.
- L6 Extensions without external accounts done: RAG (semantic, threshold 0.68 calibrated, lexical fallback), MCP (internal server :8002, allowlist, fallback to local tools), HITL approvals for shrinkage, observability (/metricas, tokens per run), versioned eval set. pytest 29 passed; local eval 17/17 with real Gemini (R05 semantic RAG, R07/R08 llamada_mcp). Pending: GraphRAG (Neo4j), persistent memory (Postgres), n8n A2A, README + evidencias.
- L7 Render eval v1.0.0 17/17 but traces showed mcp_no_disponible(ExceptionGroup) and R07 passing without MCP. Root cause: empty MCP_URL= in .env -> os.getenv returned "" (fixed: empty -> default, test added). Eval hardened to v1.1.0 (answer-only text, required llamada_mcp/rag_fragmentos events). Local strict R07/R08 OK. Diagnosis evidence for observability extension. Note: Docker Desktop holds local ports 8001/8002.
- L8 Render eval v1.1.0: 16/17 (R07 failed: MCP lookup not accent-insensitive, fixed 89279f8), then R07+R08 rerun 2/2 on Render. Latency avg 12.1s -> 4.6s once MCP worked (same inputs): before/after evidence for observability/performance.
- L9 External extensions coded: memory (Postgres checkpointer + durable ejecuciones table), GraphRAG (Neo4j, TRAZABILIDAD route), n8n A2A (REPOSICION route, importable workflow; Code node logic verified with Node harness). pytest 40 passed. Live with user's Neon: thread demo-memoria-2 recovered 4 messages after API restart; /registros/{id} served from Postgres after restart. Windows local run needs `--loop asyncio:SelectorEventLoop` (uvicorn forces Proactor; psycopg async incompatible). Pending: Neo4j and n8n accounts, README + evidencias.
- L10 Neo4j Aura loaded (Ubicacion fix) and n8n A2A live (4 draft orders). Local: G01/G02 2/2 (GraphRAG + MCP in one ReAct), N01 1/1. Render eval v1.3.0 18/20: router regression (R03/R07 routed to REPOSICION) caught by the eval set; router rules tightened, 7/7 on a direct router probe. gemini-3.5-flash-lite ignores temperature=0 (fixed sampling), so routing is not fully deterministic.
- L11 Render after router fix: R03, R07, N01 3/3. All 7 extensions verified live (Render: eval v1.3.0 18/20 then the 2 regressions fixed 3/3). Next: README + evidencias.
- L12 README rewritten per ficha minima; evidencias/01-13,15,16 generated against Render (all OK), eval v1.3.0 19/20 on Render (T02 429 quota on both models, handled). Secret scan clean. Pending: 14-memoria-parte-2 after a Render restart.

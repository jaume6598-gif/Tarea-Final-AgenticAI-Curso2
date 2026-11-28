"""Generates n8n/agente_compras_a2a.json (importable n8n workflow).

The workflow is the "Agente Compras" A2A specialist:
- GET  /webhook/agente-compras/.well-known/agent-card.json -> public agent card
- POST /webhook/agente-compras  (Header Auth: Authorization: Bearer <N8N_TOKEN>)
  receives a JSON-RPC SendMessage whose text carries a ```json``` block with
  the items below minimum stock, builds purchase orders per supplier and
  answers with an A2A message.

Usage:
    python -m n8n.generar_workflow
"""

import json
from pathlib import Path

CODIGO_ORDEN = r"""
const peticion = $input.first().json;
const rpc = peticion.body || {};
const partes = ((rpc.params || {}).message || {}).parts || [];
const texto = partes.map(p => p.text || '').join('\n');

function errorRpc(mensaje) {
  return [{ json: { jsonrpc: '2.0', id: rpc.id ?? null,
                    error: { code: -32602, message: mensaje } } }];
}

let encargo;
try {
  const bloque = texto.match(/```json\s*([\s\S]*?)```/);
  encargo = JSON.parse(bloque ? bloque[1] : texto);
} catch (e) {
  return errorRpc('El encargo no trae un JSON de reposicion valido');
}
const items = Array.isArray(encargo.items) ? encargo.items : [];
if (items.length === 0) {
  return errorRpc('El encargo no trae items para reponer');
}

const fechaBase = new Date((encargo.fecha_referencia || '2026-12-01') + 'T12:00:00Z');
const porProveedor = {};
for (const item of items) {
  const objetivo = item.stock_minimo * 2;
  const faltante = Math.max(0, objetivo - item.stock);
  const cantidad = Math.max(faltante, item.pedido_minimo || 0);
  if (cantidad <= 0) continue;
  (porProveedor[item.proveedor] = porProveedor[item.proveedor] || []).push({
    lote: item.lote, producto: item.producto, stock: item.stock,
    stock_minimo: item.stock_minimo, cantidad,
    dias_entrega: item.dias_entrega || 0,
  });
}

const fecha = (encargo.fecha_referencia || '2026-12-01').replace(/-/g, '');
const ordenes = Object.entries(porProveedor).map(([proveedor, lineas], i) => {
  const dias = Math.max(...lineas.map(l => l.dias_entrega));
  const entrega = new Date(fechaBase.getTime() + dias * 86400000)
    .toISOString().slice(0, 10);
  return {
    orden: `OC-${fecha}-${String(i + 1).padStart(3, '0')}`,
    proveedor, entrega_estimada: entrega,
    unidades: lineas.reduce((s, l) => s + l.cantidad, 0), lineas,
  };
});

const resumen = ordenes.map(o =>
  `${o.orden} | ${o.proveedor} | ${o.unidades} unidades | entrega estimada ${o.entrega_estimada} | ` +
  o.lineas.map(l => `${l.producto} (${l.lote}): ${l.cantidad} u.`).join('; ')
).join('\n');

const respuesta = 'Agente Compras (n8n) genero ' + ordenes.length +
  ' ordenes de compra en estado BORRADOR (no enviadas al proveedor).\n' +
  'Regla: cantidad = max(2 x stock minimo - stock, pedido minimo del proveedor).\n' +
  resumen + '\n```json\n' + JSON.stringify({ ordenes }) + '\n```';

return [{ json: {
  jsonrpc: '2.0', id: rpc.id ?? null,
  result: { message: {
    messageId: $execution.id + '-respuesta', role: 'ROLE_AGENT',
    parts: [{ text: respuesta }],
  } },
} }];
"""

CODIGO_TARJETA = r"""
const peticion = $input.first().json;
const host = (peticion.headers || {})['x-forwarded-host'] || (peticion.headers || {}).host;
const url = `https://${host}/webhook/agente-compras`;
return [{ json: {
  name: 'Agente Compras (n8n)',
  description: 'Genera ordenes de compra en borrador a partir de los items bajo stock minimo. No envia pedidos ni modifica inventario.',
  version: '1.0.0',
  capabilities: { streaming: false },
  defaultInputModes: ['text/plain'],
  defaultOutputModes: ['text/plain'],
  supportedInterfaces: [{ protocolBinding: 'JSONRPC', url, protocolVersion: '1.0' }],
  skills: [{ id: 'ordenes-compra', name: 'Ordenes de compra',
             description: 'Calcula cantidades y agrupa por proveedor.',
             tags: ['compras', 'reposicion'],
             examples: ['Reponer los lotes bajo stock minimo'] }],
} }];
"""


def nodo(nombre, tipo, version, posicion, parametros, **extra):
    return {"parameters": parametros, "name": nombre, "type": tipo,
            "typeVersion": version, "position": posicion, **extra}


def construir() -> dict:
    nodos = [
        nodo("A2A SendMessage", "n8n-nodes-base.webhook", 2, [0, 0], {
            "httpMethod": "POST",
            "path": "agente-compras",
            "authentication": "headerAuth",
            "responseMode": "responseNode",
            "options": {},
        }, webhookId="5b1f3c2e-agente-compras-post",
            credentials={"httpHeaderAuth": {"id": "", "name": "A2A Jaime"}}),
        nodo("Calcular ordenes", "n8n-nodes-base.code", 2, [260, 0],
             {"jsCode": CODIGO_ORDEN.strip()}),
        nodo("Responder A2A", "n8n-nodes-base.respondToWebhook", 1.1, [520, 0], {
            "respondWith": "json",
            "responseBody": "={{ JSON.stringify($json) }}",
            "options": {},
        }),
        nodo("Agent Card", "n8n-nodes-base.webhook", 2, [0, 240], {
            "httpMethod": "GET",
            "path": "agente-compras/.well-known/agent-card.json",
            "responseMode": "responseNode",
            "options": {},
        }, webhookId="5b1f3c2e-agente-compras-card"),
        nodo("Armar tarjeta", "n8n-nodes-base.code", 2, [260, 240],
             {"jsCode": CODIGO_TARJETA.strip()}),
        nodo("Responder tarjeta", "n8n-nodes-base.respondToWebhook", 1.1, [520, 240], {
            "respondWith": "json",
            "responseBody": "={{ JSON.stringify($json) }}",
            "options": {},
        }),
    ]

    def enlace(origen, destino):
        return {origen: {"main": [[{"node": destino, "type": "main", "index": 0}]]}}

    conexiones = {
        **enlace("A2A SendMessage", "Calcular ordenes"),
        **enlace("Calcular ordenes", "Responder A2A"),
        **enlace("Agent Card", "Armar tarjeta"),
        **enlace("Armar tarjeta", "Responder tarjeta"),
    }
    return {
        "name": "Agente Compras A2A",
        "nodes": nodos,
        "connections": conexiones,
        "settings": {"executionOrder": "v1"},
        "active": False,
    }


if __name__ == "__main__":
    destino = Path(__file__).with_name("agente_compras_a2a.json")
    destino.write_text(json.dumps(construir(), ensure_ascii=False, indent=2),
                       encoding="utf-8")
    print(f"Workflow escrito en {destino}")

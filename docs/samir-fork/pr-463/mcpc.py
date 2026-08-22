import json, os, urllib.request
_d = json.load(open(os.path.expanduser("~/.claude.json")))
_cfg = _d["mcpServers"]["ai-memory"]
URL = _cfg["url"]
HEADERS = dict(_cfg["headers"])
HEADERS.update({"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
def call(tool, args, rid=1):
    body = json.dumps({"jsonrpc":"2.0","id":rid,"method":"tools/call",
                       "params":{"name":tool,"arguments":args}}).encode()
    req = urllib.request.Request(URL, data=body, headers=HEADERS, method="POST")
    raw = urllib.request.urlopen(req, timeout=90).read().decode()
    for line in raw.splitlines():
        if line.startswith("data: "): raw = line[6:]; break
    msg = json.loads(raw)
    if "error" in msg: raise SystemExit("erro MCP: " + json.dumps(msg["error"])[:300])
    return json.loads(msg["result"]["content"][0]["text"])

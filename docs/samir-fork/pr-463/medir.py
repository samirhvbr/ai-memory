#!/usr/bin/env python3
"""Mede a qualidade do descritor de hit nao-FTS do ai-memory.

Reproduz os numeros citados no PR akitaonrails/ai-memory#463 sem build
instrumentado: tudo passa pela API MCP publica, read-only.

Uso:
    python3 medir.py <workspace> <projeto>      # ex: python3 medir.py default x

Le a URL e o header de auth de ~/.claude.json em tempo de execucao.
Nenhum segredo fica neste arquivo.
"""
import json, re, sys, collections
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from mcpc import call
from descriptor_mirror import descriptor_for

WS, PROJ = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("default", "x")

# --- 1. lado do corpus: quao ruim e o descritor ANTIGO -----------------------
pages = call("memory_recent", {"limit": 100, "workspace": WS, "project": PROJ})["hits"]

def prose(text):
    out = []
    for ln in text.split("\n"):
        s = ln.strip()
        if not s or s.startswith(("#", "---", "___", "***")):
            continue
        if re.match(r"^- \*\*[^*]+:\*\*", s):      # bullet de metadado
            continue
        out.append(s)
    return out

for label, grp in (("todas", pages),
                   ("substantivas", [p for p in pages if p["title"].strip() != "session-start"])):
    n = len(grp)
    if not n:
        continue
    dup = sum(1 for h in grp
              if (t := h["title"].rstrip("…").strip())
              and h["snippet"].split("\n", 1)[0].lstrip("#").strip().startswith(t))
    pc = sorted(sum(len(x) for x in prose(h["snippet"])) for h in grp)
    print(f"[{label:13}] {n:3d} paginas | 1a linha repete o title: {100*dup/n:3.0f}% "
          f"| prosa nos 240: mediana {pc[n//2]}, media {sum(pc)/n:.0f}")

# --- 2. antes/depois com os corpos ------------------------------------------
subst = [p for p in pages if p["title"].strip() != "session-start"]
bodies = {}
for i, h in enumerate(subst[::2][:28]):
    bodies[h["path"]] = call("memory_read_page",
                             {"path": h["path"], "workspace": WS, "project": PROJ}, rid=2000+i)
if bodies:
    n = len(bodies)
    new_dup = sum(1 for p in bodies.values()
                  if (t := (p.get("title") or "").rstrip("…").strip())
                  and descriptor_for(p).strip() == t)
    lens = [len(descriptor_for(p)) for p in bodies.values()]
    print(f"[depois       ] {n:3d} paginas | descritor == title: {100*new_dup/n:3.0f}% "
          f"| tamanho medio {sum(lens)/n:.0f}")

# --- 3. lado do trafego: quantos hits chegam SEM FTS -------------------------
STOP = {"que","com","para","uma","dos","das","nos","nas","por","como","mas","the","user","opened","file"}
seen, queries = set(), []
for h in pages:
    if h["path"].startswith("_lint") or h["title"].strip() == "session-start":
        continue
    t = re.sub(r"^<ide_opened_file>", "", h["title"])
    ws_ = [w for w in re.findall(r"[0-9A-Za-zÀ-ÿ_-]{4,}", t) if w.lower() not in STOP][:5]
    q = " ".join(ws_)
    if len(ws_) >= 2 and q.lower() not in seen:
        seen.add(q.lower()); queries.append(q)

tot = non_fts = 0
combos = collections.Counter()
for i, q in enumerate(queries[:40]):
    try:
        r = call("memory_query", {"query": q, "explain": True, "limit": 10,
                                  "workspace": WS, "project": PROJ}, rid=3000+i)
    except SystemExit:
        continue
    for h in r.get("hits", []):
        sd = h.get("score_details") or {}
        tot += 1
        st = tuple(s for s in ("fts","vector","graph","entity") if sd.get(f"{s}_rank") is not None)
        combos[st] += 1
        if "fts" not in st:
            non_fts += 1
if tot:
    print(f"[busca        ] {len(queries[:40])} queries reais | {tot} hits "
          f"| sem FTS: {100*non_fts/tot:.1f}%")
    for k, v in combos.most_common():
        print(f"                  {'+'.join(k) or '(nenhum)':20} {v:4d} ({100*v/tot:.0f}%)")

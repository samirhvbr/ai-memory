# Espelho fiel do reader.rs::page_descriptor (versao title-aware)
SCAN, MAXC = 600, 240
def strip_marker(l):
    for pfx in ("- ","* ","+ "):
        if l.startswith(pfx): return l[len(pfx):].lstrip()
    d=0
    while d<len(l) and l[d].isdigit(): d+=1
    if d>0 and l[d:d+2]==". ": return l[d+2:].lstrip()
    return l
def is_meta(l): return l.startswith("- **") and ":**" in l
def page_descriptor(raw, title):
    tt = title.strip(); trunc = tt.endswith("…")
    tk = tt.rstrip("…").strip()
    out = ""
    for ln in raw.split("\n"):
        s = ln.strip()
        if not s or s.startswith(("#","---","___","***")) or is_meta(s): continue
        c = strip_marker(s).strip()
        if not c: continue
        if tk and ((c.startswith(tk)) if trunc else (c == tk)): continue
        if out:
            if len(out)+1+len(c) > MAXC: break
            out += " "
        out += c
        if len(out) >= MAXC: break
    if not out: out = raw.strip()
    return out[:MAXC-1]+"…" if len(out) > MAXC else out
def descriptor_for(page):
    fm = page.get("frontmatter") or {}
    su = fm.get("summary")
    raw = su.strip() if isinstance(su,str) and su.strip() else page["body"][:SCAN]
    return page_descriptor(raw, page.get("title") or "")

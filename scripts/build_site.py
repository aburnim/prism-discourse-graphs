#!/usr/bin/env python3
"""Build the "Discourse graphs for Prism" portfolio site.

Usage: python3 build_site.py <site-dir>

Reads every <site-dir>/specs/*.json (graph.json specs), builds each graph page at
<site-dir>/graphs/<slug>/index.html (+ <slug>-mira-graph.jsonld), then writes
<site-dir>/index.html with one card per paper, newest first. Static output: deploy
the folder to GitHub Pages as is (no build step).
"""
import json, subprocess, sys, html
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX_TEMPLATE = HERE.parent / "assets" / "index-template.html"
ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'

def esc(s): return html.escape(str(s), quote=True)

def main():
    if len(sys.argv) != 2: print(__doc__); sys.exit(1)
    site = Path(sys.argv[1]).resolve()
    specs = sorted((site / "specs").glob("*.json"))
    if not specs: print(f"no specs in {site/'specs'}"); sys.exit(1)
    cards = []
    for sp in specs:
        spec = json.loads(sp.read_text(encoding="utf-8"))
        slug = spec["slug"]
        out = site / "graphs" / slug
        out.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([sys.executable, str(HERE / "build.py"), str(sp), str(out / "index.html"),
                            "--jsonld", str(out / f"{slug}-mira-graph.jsonld"), "--home", "../../index.html"],
                           capture_output=True, text=True)
        print(r.stdout.strip())
        if r.returncode: print(r.stderr); sys.exit(r.returncode)
        c = spec.get("card", {})
        d = date.fromisoformat(c.get("date", spec["date"]))
        n_nodes = len(spec["nodes"])
        cards.append((d, f'''    <a class="card" href="graphs/{esc(slug)}/index.html" aria-label="Open the {esc(c.get('title', spec['title_short']))} discourse graph">
      <div class="row"><span class="chip">{esc(c.get('tag', 'Paper'))}</span><span class="date">{d:%m.%d.%y}</span></div>
      <hr class="rule">
      <h2>{esc(c.get('title', spec['title_short']))}</h2>
      <p>{esc(c.get('summary', spec['paper']['title']))}</p>
      <p class="meta">{esc(spec['paper']['short'])} &middot; {esc(spec['paper']['venue'])} &middot; doi:{esc(spec['paper']['doi'])}</p>
      <div class="spacer"></div>
      <div class="row"><div class="chips"><span class="chip white">MIRA graph</span><span class="chip white">{n_nodes} nodes</span></div><span class="go">{ARROW}</span></div>
    </a>'''))
    cards.sort(key=lambda x: x[0], reverse=True)
    t = INDEX_TEMPLATE.read_text(encoding="utf-8")
    t = t.replace("__CARDS__", "\n".join(c for _, c in cards))
    t = t.replace("__COUNT__", f"{len(cards)} paper{'s' if len(cards) != 1 else ''}")
    (site / "index.html").write_text(t, encoding="utf-8")
    print(f"ok: {site/'index.html'} | {len(cards)} card(s)")

if __name__ == "__main__":
    main()

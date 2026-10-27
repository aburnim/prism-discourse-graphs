#!/usr/bin/env python3
"""Build a Prism-branded, self-contained HTML MIRA discourse graph from a graph.json spec.

Usage: python3 build.py graph.json out.html [--jsonld out.jsonld] [--home ../../]
The spec format is documented in references/graph-spec.md.
"""
import json, re, sys, html, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "template.html"
TYPES = ["Question", "Claim", "Evidence", "Study", "Protocol", "Request"]
DOMAIN = {"addresses": ("Claim", "Question"), "supports": ("Evidence", "Claim"), "opposes": ("Evidence", "Claim"),
          "is_grounded_in": ("Evidence", "Study"), "follows": ("Study", "Protocol"), "request_target": ("Request", "Claim")}
PREFIX = {"Question": "QUE", "Claim": "CLM", "Evidence": "EVD", "Study": "STU", "Protocol": "PRO", "Request": "REQ"}
SCHEMA_QUOTE = ("Atomic, generalized assertions about the world that (propose to) answer research questions",
                "MIRA schema, definition of Claim (mira.yaml)")
DEMO_QUOTE = ("MIRA itself hosts nothing", "MIRA-science/demo-MIRA-graph-data README")
BANNED = ["—"]  # em dash

def die(errors):
    print("SPEC ERRORS:\n  - " + "\n  - ".join(errors)); sys.exit(1)

def doi_url(d): return "https://doi.org/" + d.replace("(", "%28").replace(")", "%29")
def pdb_doi(p): return f"10.2210/pdb{p.lower()}/pdb"
def esc(s): return html.escape(str(s), quote=True)

def main():
    args = sys.argv[1:]
    if len(args) < 2: print(__doc__); sys.exit(1)
    spec = json.load(open(args[0], encoding="utf-8"))
    out = args[1]
    jsonld_out = args[args.index("--jsonld") + 1] if "--jsonld" in args else None
    home = args[args.index("--home") + 1] if "--home" in args else None

    paper = spec["paper"]
    now = spec.get("date", "2026-01-01") + "T00:00:00Z"
    NS = spec.get("prefix", "g")
    ME = f"{NS}:creator"
    sources = {"paper": {"short": paper["short"], "url": doi_url(paper["doi"]), "label": "doi:" + paper["doi"],
                         "title": paper["title"]}}
    sources.update(spec.get("sources", {}))
    refs = {str(k): v for k, v in spec.get("refs", {}).items()}
    figs = spec.get("figures", {})
    quotes = spec.get("quotes", {})
    nodes = spec["nodes"]
    N = {n["id"]: n for n in nodes}
    E = [tuple(e) for e in spec.get("edges", [])]
    for n in nodes:
        if n["type"] == "Evidence" and n.get("study"):
            E.append(("is_grounded_in", n["id"], n["study"]))
    E = list(dict.fromkeys(E))

    # ---------- validation ----------
    err = []
    if len(N) != len(nodes): err.append("duplicate node ids")
    for n in nodes:
        k = n["id"]
        if n.get("type") not in TYPES: err.append(f"{k}: bad type {n.get('type')}")
        if not n.get("title", "").startswith(PREFIX.get(n.get("type"), "?") + " - "):
            err.append(f"{k}: title must start with '{PREFIX.get(n.get('type'))} - '")
        if n.get("source", "paper") not in sources: err.append(f"{k}: unknown source {n.get('source')}")
        if not n.get("loc"): err.append(f"{k}: missing loc (where in the source this comes from)")
        for r in n.get("cites", []):
            if str(r) not in refs: err.append(f"{k}: cites unknown ref {r}")
        for f in n.get("fig", []):
            if f not in figs: err.append(f"{k}: unknown figure {f}")
        if n["type"] == "Evidence":
            if not n.get("study"): err.append(f"{k}: Evidence needs 'study'")
            if not n.get("fig"): print(f"warning: {k}: Evidence has no figure (observationBase)")
        for field in ("title", "desc", "loc"):
            if any(b in n.get(field, "") for b in BANNED): err.append(f"{k}: em dash in {field}")
    for r, s, d in E:
        if r not in DOMAIN: err.append(f"unknown relation {r}"); continue
        if s not in N or d not in N: err.append(f"edge {r} {s}->{d}: unknown node"); continue
        if (N[s]["type"], N[d]["type"]) != DOMAIN[r]:
            err.append(f"edge {r} {s}->{d}: needs {DOMAIN[r][0]} -> {DOMAIN[r][1]}")
    for k in N:
        if not any(k in (s, d) for _, s, d in E): err.append(f"{k}: orphan node (no edges)")
    seen_src = {}
    for k, q in quotes.items():
        if k not in N: err.append(f"quote on unknown node {k}")
        if q["source"] not in sources: err.append(f"quote {k}: unknown source {q['source']}")
        if len(q["text"].split()) >= 15: err.append(f"quote {k}: must be under 15 words")
        if q["source"] in seen_src: err.append(f"quote {k}: source '{q['source']}' already quoted on {seen_src[q['source']]} (one quote per source)")
        seen_src[q["source"]] = k
    for r, v in refs.items():
        if not v.get("doi") and not v.get("url"): err.append(f"ref {r}: needs doi or url")
    if err: die(err)

    # ---------- JSON-LD ----------
    def iid(k): return f"{NS}:{k}"
    def ref_iri(v): return doi_url(v["doi"]) if v.get("doi") else v["url"]
    g = [{"@id": ME, "@type": "UserAccount", "accountName": spec.get("creator", "unknown")}]
    for t in TYPES:
        g.append({"@id": iid(f"schema-{t}"), "@type": "NodeSchema", "created": now, "modified": now,
                  "subClassOf": [f"mira:{t}"], "label": t, "creator": ME})
    for r, (dom, rng) in DOMAIN.items():
        g.append({"@id": iid(f"areldef-{r}"), "@type": "AbstractRelationDef", "created": now, "modified": now,
                  "subClassOf": ["dgb:RelationInstance", f"mira:{r}",
                                 {"@type": "owl:Restriction", "onProperty": "rdf:predicate", "hasValue": iid(f"areldef-{r}")}],
                  "label": r, "creator": ME})
        g.append({"@id": iid(f"reldef-{r}"), "@type": "RelationDef", "created": now, "modified": now,
                  "domain": iid(f"schema-{dom}"), "range": iid(f"schema-{rng}"),
                  "subClassOf": [iid(f"areldef-{r}")], "label": r, "creator": ME})
    studies = [iid(n["id"]) for n in nodes if n["type"] == "Study"]
    g.append({"@id": sources["paper"]["url"], "@type": "SourceDocument", "title": paper["title"],
              "bibliographicCitation": f"{paper['authors']} ({paper['year']}). {paper['venue']}.",
              "identifier": "doi:" + paper["doi"], "describesActivity": studies})
    for key, s in sources.items():
        if key == "paper": continue
        o = {"@id": s["url"], "@type": "SourceDocument", "title": s.get("title", s["short"])}
        if s.get("doi"): o["identifier"] = "doi:" + s["doi"]
        g.append(o)
    for key, v in refs.items():
        o = {"@id": ref_iri(v), "@type": "SourceDocument", "title": v["title"]}
        if v.get("doi"): o["identifier"] = "doi:" + v["doi"]
        if v.get("num"): o["bibliographicCitation"] = f"Reference {v['num']} in {paper['short']}"
        g.append(o)
    pdb_all = list(dict.fromkeys([p.upper() for p in spec.get("pdb_all", [])] +
                                 [p.upper() for n in nodes for p in n.get("pdb", [])]))
    for p in pdb_all:
        g.append({"@id": doi_url(pdb_doi(p)), "@type": "Item", "format": "chemical/x-mmcif",
                  "title": f"PDB entry {p}", "identifier": "doi:" + pdb_doi(p)})
    for f, v in figs.items():
        g.append({"@id": v["url"], "@type": "Item", "format": v.get("format", "image/png"), "content": v["caption"],
                  "isContainedBy": paper.get("page_url", sources["paper"]["url"])})
    for k, q in quotes.items():
        src = sources[q["source"]]["url"]
        g.append({"@id": f"{src}#quote-{k}", "@type": "Item", "format": "text/plain", "content": q["text"],
                  "isContainedBy": src, "title": q["where"]})
    for n in nodes:
        k = n["id"]; src = sources[n.get("source", "paper")]
        o = {"@id": iid(k), "@type": [iid(f"schema-{n['type']}"), f"mira:{n['type']}"], "created": now, "modified": now,
             "title": n["title"], "description": {"@type": "Item", "format": "text/plain", "content": n.get("desc", "")},
             "creator": ME, "bibliographicCitation": f"{src['short']}, {src.get('label', src['url'])}. {n['loc']}"}
        r = ([f"{sources[quotes[k]['source']]['url']}#quote-{k}"] if k in quotes else []) + \
            [ref_iri(refs[str(c)]) for c in n.get("cites", [])] + [doi_url(pdb_doi(p)) for p in n.get("pdb", [])]
        if r: o["references"] = r
        if n["type"] == "Evidence":
            if n.get("fig"): o["observationBase"] = [figs[f]["url"] for f in n["fig"]]
            o["sourceDocument"] = [sources[s]["url"] for s in n.get("evidence_sources", [n.get("source", "paper")])]
            o["observationOriginActivity"] = iid(n["study"])
        g.append(o)
    for r, s, d in E:
        g.append({"@id": iid(f"rel-{r}-{s}-{d}"), "@type": [iid(f"areldef-{r}"), f"mira:{r}"], "created": now, "modified": now,
                  "source": iid(s), "destination": iid(d),
                  "title": f"[[{N[s]['title']}]] -{r}-> [[{N[d]['title']}]]", "creator": ME})
    doc = {"@context": ["https://mira-science.github.io/schema/mira.jsonld",
                        {NS: spec["namespace"], "Study": "mira:Study", "Item": "sioc:Item", "dct": "http://purl.org/dc/terms/",
                         "references": {"@id": "dct:references", "@type": "@id"},
                         "bibliographicCitation": "dct:bibliographicCitation", "identifier": "dct:identifier"}],
           "@graph": g}

    cfg = {"slug": spec["slug"],
           "sources": {k: {"short": v["short"], "url": v["url"], "label": v.get("label", v["url"])} for k, v in sources.items()},
           "nodeSource": {iid(n["id"]): n.get("source", "paper") for n in nodes},
           "loc": {iid(n["id"]): n["loc"] for n in nodes}}

    # ---------- HTML ----------
    nav = [{"label": "Paper", "url": sources["paper"]["url"]}] + spec.get("nav", [])
    navhtml = "\n".join(f'    <a href="{esc(l["url"])}" target="_blank" rel="noopener">{esc(l["label"])}</a>' for l in nav)
    if home:
        navhtml = f'    <a href="{esc(home)}">&#8592; All graphs</a>\n' + navhtml
    sub = (f'<em>{esc(paper["title"])}</em>. {esc(paper["authors"])}. {esc(paper["venue"])}'
           + (f', {esc(paper["date"])}' if paper.get("date") else "")
           + (f' ({esc(paper["version"])})' if paper.get("version") else "") + "."
           + (f' {esc(paper["license"])}.' if paper.get("license") else "")
           + f' <span class="mono">doi:{esc(paper["doi"])}</span>')
    doibtns = "".join(f'<a class="btn" href="{esc(doi_url(x["doi"]))}" target="_blank" rel="noopener">{esc(x["label"])} '
                      f'<span class="v">doi:{esc(x["doi"])}</span> &#8599;</a>' for x in spec.get("extra_dois", []))
    doibtns = f'<div class="btns">{doibtns}</div>' if doibtns else ""
    res = "\n".join(f'    <li><a href="{esc(r["url"])}" target="_blank" rel="noopener">{esc(r["label"])}</a>'
                    + (f' ({esc(r["note"])})' if r.get("note") else "") + "</li>" for r in spec.get("resources", []))
    if not res: res = '    <li class="att">None.</li>'
    t = TEMPLATE.read_text(encoding="utf-8")
    jsonld = json.dumps(doc, indent=1, ensure_ascii=False)
    rep = {"/*__JSONLD__*/": jsonld.replace("</", "<\\/"), "/*__CFG__*/": json.dumps(cfg).replace("</", "<\\/"),
           "__NAVLINKS__": navhtml, "__SUBLINE__": sub, "__DOIBTNS__": doibtns, "__TITLE_SHORT__": esc(spec["title_short"]),
           "__NOTE__": esc(spec.get("note", "Draft extraction. Not reviewed by the authors.")),
           "__PDB_NOTE__": esc(spec.get("pdb_note", "PDB entries referenced in this graph.")),
           "__RESOURCES__": res, "__NNODES__": str(len(N)), "__NEDGES__": str(len(E)),
           "__SQ__": SCHEMA_QUOTE[0], "__SQSRC__": SCHEMA_QUOTE[1], "__DQ__": DEMO_QUOTE[0], "__DQSRC__": DEMO_QUOTE[1]}
    for k, v in rep.items(): t = t.replace(k, v)
    left = set(re.findall(r"__[A-Z_]+__", t))
    if left: die([f"unfilled placeholder {x}" for x in sorted(left)])
    Path(out).write_text(t, encoding="utf-8")
    if jsonld_out: Path(jsonld_out).write_text(jsonld, encoding="utf-8")
    counts = {t_: sum(1 for n in nodes if n["type"] == t_) for t_ in TYPES}
    print(f"ok: {out} | nodes {len(N)} {counts} | relations {len(E)} | refs {len(refs)} | pdb {len(pdb_all)} | quotes {len(quotes)}")

if __name__ == "__main__":
    main()

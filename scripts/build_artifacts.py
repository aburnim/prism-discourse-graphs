#!/usr/bin/env python3
"""Build the Prism artifact graph: what went into each paper and what came out.

Usage: python3 build_artifacts.py <site-dir>

Reads every <site-dir>/specs/*.json and writes
  <site-dir>/artifacts/index.html                     interactive network (self-contained)
  <site-dir>/artifacts/prism-artifacts-datacite.json  DataCite relatedIdentifiers per paper

Nodes come from three places:
  - the paper itself (one node per spec)
  - spec["artifacts"]: hand-curated datasets, code, protocols, posts (see docs/graph-spec.md)
  - spec["pdb_all"] and node["pdb"]: every PDB entry, as an input
Prism papers that cite each other (spec["refs"] DOI = another spec's paper DOI) are linked.
Artifacts shared by several papers (same DOI, URL or PDB ID) merge into one node.
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "artifacts-template.html"
TYPES = {"dataset": "Dataset", "pdb": "Dataset", "code": "Software", "protocol": "Text", "post": "Text"}
RELATIONS = {"input": {"References", "Requires", "IsDerivedFrom", "IsDocumentedBy", "Cites", "Continues"},
             "output": {"IsSupplementedBy", "IsSourceOf", "IsDescribedBy", "IsCitedBy"}}

def doi_url(d): return f"https://doi.org/{d}"

def key_for(a):
    if a.get("doi"): return "doi:" + a["doi"].lower()
    return "url:" + a["url"].lower().rstrip("/")

def check(slug, i, a):
    err, where = [], f"{slug} artifacts[{i}]"
    if a.get("type") not in TYPES or a.get("type") == "pdb": err.append(f"{where}: type must be one of dataset, code, protocol, post")
    if not a.get("label"): err.append(f"{where}: missing label")
    if not (a.get("doi") or a.get("url")): err.append(f"{where}: needs doi or url")
    if a.get("doi", "").startswith("http"): err.append(f"{where}: doi must be bare (no https://doi.org/)")
    d = a.get("direction")
    if d not in RELATIONS: err.append(f"{where}: direction must be input or output")
    elif a.get("relation") not in RELATIONS[d]:
        err.append(f"{where}: relation for {d} must be one of {', '.join(sorted(RELATIONS[d]))}")
    return err

def main():
    if len(sys.argv) != 2: print(__doc__); sys.exit(1)
    site = Path(sys.argv[1]).resolve()
    specs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((site / "specs").glob("*.json"))]
    nodes, links, err = {}, [], []
    paper_ids = {}
    for s in specs:
        p, c = s["paper"], s.get("card", {})
        pid = "doi:" + p["doi"].lower()
        paper_ids[pid] = s["slug"]
        nodes[pid] = {"id": pid, "type": "paper", "label": c.get("title", s["title_short"]), "title": p["title"],
                      "short": p["short"], "venue": p["venue"], "date": c.get("date", s["date"]), "slug": s["slug"],
                      "href": doi_url(p["doi"]), "graph": f"../graphs/{s['slug']}/index.html", "doi": p["doi"]}

    def link(src, a_id, direction, rel):
        if not any(l["s"] == src and l["t"] == a_id for l in links):
            links.append({"s": src, "t": a_id, "dir": "in" if direction == "input" else "out", "rel": rel})

    for s in specs:
        pid = "doi:" + s["paper"]["doi"].lower()
        for i, a in enumerate(s.get("artifacts", [])):
            e = check(s["slug"], i, a)
            if e: err += e; continue
            k = key_for(a)
            n = nodes.setdefault(k, {"id": k, "type": a["type"], "label": a["label"], "note": a.get("note", ""),
                                     "href": doi_url(a["doi"]) if a.get("doi") else a["url"], "doi": a.get("doi", "")})
            if a.get("doi") and a.get("url"): n["alt"] = a["url"]
            link(pid, k, a["direction"], a["relation"])
        named = [p for n in s["nodes"] for p in n.get("pdb", [])]
        for pdb in dict.fromkeys(x.upper() for x in (s.get("pdb_all") or []) + named):
            k = "pdb:" + pdb
            nodes.setdefault(k, {"id": k, "type": "pdb", "label": f"PDB {pdb}", "note": "",
                                 "href": f"https://www.rcsb.org/structure/{pdb}", "doi": f"10.2210/pdb{pdb.lower()}/pdb"})
            link(pid, k, "input", "References")
        for r in s.get("refs", {}).values():
            k = "doi:" + r.get("doi", "").lower()
            if k in paper_ids and k != pid: link(pid, k, "input", "Cites")
    if err:
        print("ARTIFACT ERRORS:\n  " + "\n  ".join(err)); sys.exit(1)

    # DataCite relatedIdentifiers, one record per paper (citations recorded in both directions)
    dc = {pid: [] for pid in paper_ids}
    for l in links:
        t = nodes[l["t"]]
        rid = {"relatedIdentifier": t["doi"] or t["href"], "relatedIdentifierType": "DOI" if t["doi"] else "URL",
               "relationType": l["rel"], "resourceTypeGeneral": TYPES.get(t["type"], "Text")}
        dc[l["s"]].append(rid)
        if l["rel"] == "Cites":
            dc[l["t"]].append({"relatedIdentifier": nodes[l["s"]]["doi"], "relatedIdentifierType": "DOI",
                               "relationType": "IsCitedBy", "resourceTypeGeneral": "Text"})
    export = [{"doi": nodes[pid]["doi"], "titles": [{"title": nodes[pid]["title"]}], "relatedIdentifiers": rel}
              for pid, rel in dc.items()]

    out = site / "artifacts"
    out.mkdir(exist_ok=True)
    (out / "prism-artifacts-datacite.json").write_text(json.dumps(export, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    data = json.dumps({"nodes": list(nodes.values()), "links": links}, ensure_ascii=False).replace("</", "<\\/")
    (out / "index.html").write_text(TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/", data), encoding="utf-8")
    n_art = len(nodes) - len(paper_ids)
    print(f"ok: {out/'index.html'} | {len(paper_ids)} papers, {n_art} artifacts, {len(links)} links")

if __name__ == "__main__":
    main()

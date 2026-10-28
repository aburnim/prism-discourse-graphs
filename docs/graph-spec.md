# graph.json spec

`scripts/build.py` reads one JSON file and writes the HTML page (and optionally the `.jsonld`).
Full worked example: `specs/sampleworks.json`.

## Top level

| Field | Required | What |
|---|---|---|
| `slug` | yes | File-name slug, e.g. `sampleworks` |
| `title_short` | yes | Short name shown in the title, e.g. `sampleworks` |
| `creator` | yes | Who made the graph, e.g. `Andy Burnim` |
| `date` | yes | `YYYY-MM-DD` of extraction |
| `prefix` | yes | Short ID prefix, e.g. `sw` |
| `namespace` | yes | IRI base for node IDs, e.g. `https://prismscience.org/mira/<slug>#` |
| `card` | no | Portfolio card: `{tag, date (YYYY-MM-DD), title, summary}`. Used by `build_site.py` |
| `note` | yes | Status line, e.g. `Draft extraction from v2 of the paper. Not reviewed by the authors.` |
| `paper` | yes | See below |
| `sources` | no | Other sources nodes can come from (README, docs). Key is used by `node.source` |
| `extra_dois` | no | `[{label, doi}]` shown as purple buttons under the citation line (code, data archives) |
| `nav` | no | `[{label, url}]` extra top-bar links. "Paper" and "MIRA schema" are added automatically |
| `figures` | no | `{key: {url, caption}}` figure image URLs. Caption is paraphrased |
| `refs` | no | `{key: {num, title, doi}}` works the paper cites. `num` = number in the paper's reference list. Use `url` instead of `doi` only when no DOI exists |
| `pdb_all` | no | Every PDB ID in the paper's dataset. Stored in the JSON-LD only; per-node PDB links come from `node.pdb`. Also added to the artifact graph as inputs |
| `quotes` | no | `{nodeId: {source, text, where}}`. Max one per source, under 15 words, verbatim |
| `resources` | no | `[{label, url, note}]` non-DOI resources listed at the bottom |
| `artifacts` | no | Inputs and outputs for the artifact graph. See below. Not used by the discourse graph page |
| `nodes` | yes | See below. Order within each type = order in the column |
| `edges` | yes | `[[relation, sourceId, destinationId], ...]` |

### `paper`
`title`, `authors` (e.g. `Chrispens K, Collins MD`), `year`, `short` (e.g. `Chrispens et al. 2026`), `venue`, `doi` (bare, no `https://doi.org/`), and optional `date`, `version`, `license`, `page_url` (landing page that hosts the figures).

### `sources` entry
`{short, url, label, title}`. Example: `{"short": "sampleworks README", "url": "https://github.com/org/repo", "label": "github.com/org/repo", "title": "org/repo (GitHub)"}`. Add `doi` if it has one.

### `artifacts` entry
`{type, label, doi and/or url, direction, relation, note}`, read by `scripts/build_artifacts.py`. Example:
`{"type": "dataset", "label": "WaterFlow supplementary data", "doi": "10.5281/zenodo.22046933", "direction": "output", "relation": "IsSupplementedBy", "note": "supplementary data for the preprint"}`

- `type`: `dataset`, `code`, `protocol` (protocols and logbooks) or `post` (blogs, posts, talks). PDB entries come from `pdb_all` and each node's `pdb`, so do not list them here.
- `doi` (bare) or `url`, or both. Artifacts with the same DOI or URL in several specs merge into one node.
- `direction`: `input` (the paper used it) or `output` (the paper released it, or it came after).
- `relation`: a [DataCite relationType](https://datacite-metadata-schema.readthedocs.io/en/4.5/properties/relatedidentifier/) from the paper's point of view.
  - Inputs: `References`, `Requires` (software it ran), `IsDerivedFrom` (source data), `IsDocumentedBy` (logbooks), `Cites`, `Continues` (earlier blog posts about the same work).
  - Outputs: `IsSupplementedBy` (released data or code), `IsSourceOf`, `IsDescribedBy` (posts that announce or explain the paper), `IsCitedBy` (later posts that link to it).
- Citations between Prism papers are added automatically when a `refs` DOI matches another spec's `paper.doi`.

## Nodes

| Field | Required | What |
|---|---|---|
| `id` | yes | Short unique ID: `q1`, `c3`, `e7`, `s2`, `p4`, `r1` |
| `type` | yes | `Question`, `Claim`, `Evidence`, `Study`, `Protocol`, `Request` |
| `title` | yes | Must start with `QUE - `, `CLM - `, `EVD - `, `STU - `, `PRO - `, `REQ - ` |
| `desc` | yes | 1 to 3 plain sentences, paraphrased |
| `loc` | yes | Where it comes from: section and figure, e.g. `Results: baseline section, Figure 2C` |
| `source` | no | Key in `sources`. Default `paper` |
| `cites` | no | Keys in `refs` that the paper cites at this point |
| `pdb` | no | PDB IDs this node names |
| `fig` | Evidence | Keys in `figures` (the observation base) |
| `study` | Evidence | ID of the Study it comes from (adds `is_grounded_in` automatically) |
| `evidence_sources` | no | Source keys for Evidence `sourceDocument`. Default `[source]` |

## Relations (MIRA)

| Relation | From | To |
|---|---|---|
| `addresses` | Claim | Question |
| `supports` | Evidence | Claim |
| `opposes` | Evidence | Claim |
| `is_grounded_in` | Evidence | Study (auto from `study`; add extra ones in `edges`) |
| `follows` | Study | Protocol |
| `request_target` | Request | Claim |

The builder stops with a list of errors if: a relation has the wrong node types, a node has no edges, a title prefix is wrong, `loc` is missing, a cited ref or figure is undefined, a quote is 15+ words or a second quote from the same source, or any text has an em dash.

## Minimal example

```json
{
 "slug": "demo", "title_short": "demo", "creator": "Andy Burnim", "date": "2026-10-27",
 "prefix": "dm", "namespace": "https://prismscience.org/mira/demo#",
 "note": "Draft extraction. Not reviewed by the authors.",
 "paper": {"title": "A paper", "authors": "Doe J, Roe R", "year": 2026, "short": "Doe et al. 2026",
           "venue": "The Stacks", "doi": "10.1234/abcd"},
 "figures": {"fig1": {"url": "https://example.org/fig1.png", "caption": "Figure 1. What it shows."}},
 "refs": {"7": {"num": 7, "title": "Smith A (2024) Prior method", "doi": "10.5678/efgh"}},
 "nodes": [
  {"id": "q1", "type": "Question", "title": "QUE - Does X do Y?", "desc": "...", "loc": "Introduction"},
  {"id": "c1", "type": "Claim", "title": "CLM - X does Y", "desc": "...", "loc": "Results, Figure 1", "cites": ["7"]},
  {"id": "e1", "type": "Evidence", "title": "EVD - 80% of samples show Y", "desc": "...", "loc": "Results, Figure 1B",
   "fig": ["fig1"], "study": "s1"},
  {"id": "s1", "type": "Study", "title": "STU - Screen of 100 samples", "desc": "...", "loc": "Methods"},
  {"id": "p1", "type": "Protocol", "title": "PRO - Assay method", "desc": "...", "loc": "Methods: Assay"}
 ],
 "edges": [["addresses", "c1", "q1"], ["supports", "e1", "c1"], ["follows", "s1", "p1"]]
}
```

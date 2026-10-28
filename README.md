# Discourse graphs for Prism

Prism research papers mapped as [MIRA](https://mira.science) discourse graphs. Each graph breaks a paper into Questions, Claims, Evidence, Studies, Protocols and Requests. Every node links back to its source with a DOI and a section or figure location.

**Live site:** https://aburnim.github.io/prism-discourse-graphs/

| Paper | Graph | JSON-LD |
|---|---|---|
| Srivastava et al. 2026, *WaterFlow* ([doi:10.64898/2026.08.26.747373](https://doi.org/10.64898/2026.08.26.747373)) | [graphs/waterflow/](https://aburnim.github.io/prism-discourse-graphs/graphs/waterflow/) | [waterflow-mira-graph.jsonld](graphs/waterflow/waterflow-mira-graph.jsonld) |
| Holton and Wankowicz 2026, *User-defined bulk solvent map* ([doi:10.82153/2me0-hd96](https://doi.org/10.82153/2me0-hd96)) | [graphs/bulk-solvent-map/](https://aburnim.github.io/prism-discourse-graphs/graphs/bulk-solvent-map/) | [bulk-solvent-map-mira-graph.jsonld](graphs/bulk-solvent-map/bulk-solvent-map-mira-graph.jsonld) |
| Wankowicz 2026, *qFit at scale* ([doi:10.82153/pff0-ck46](https://doi.org/10.82153/pff0-ck46)) | [graphs/qfit-at-scale/](https://aburnim.github.io/prism-discourse-graphs/graphs/qfit-at-scale/) | [qfit-at-scale-mira-graph.jsonld](graphs/qfit-at-scale/qfit-at-scale-mira-graph.jsonld) |
| Zielinski et al. 2026, *Mac1 diffuse scattering East-West* ([doi:10.82153/hrpy-t681](https://doi.org/10.82153/hrpy-t681)) | [graphs/diffuse-east-west/](https://aburnim.github.io/prism-discourse-graphs/graphs/diffuse-east-west/) | [diffuse-east-west-mira-graph.jsonld](graphs/diffuse-east-west/diffuse-east-west-mira-graph.jsonld) |
| Chrispens et al. 2026, *sampleworks* ([doi:10.82153/jkxj-tw08](https://doi.org/10.82153/jkxj-tw08)) | [graphs/sampleworks/](https://aburnim.github.io/prism-discourse-graphs/graphs/sampleworks/) | [sampleworks-mira-graph.jsonld](graphs/sampleworks/sampleworks-mira-graph.jsonld) |

> **Status:** draft extractions. They have not been reviewed by the paper authors.

### Artifact graph
**Live:** https://aburnim.github.io/prism-discourse-graphs/artifacts/

An interactive network of what went into each paper (datasets, PDB entries, code, protocols, earlier blog posts) and what came out of it (released data and code, and the [Prism blog posts](https://prismscience.org/research) that describe or cite it). Papers that cite each other, or share an artifact, are linked. Pick a paper to see only its inputs (left) and outputs (right). Every link is typed with a [DataCite relationType](https://datacite-metadata-schema.readthedocs.io/en/4.5/properties/relatedidentifier/), and the page offers the same links as DataCite `relatedIdentifiers` JSON ([prism-artifacts-datacite.json](artifacts/prism-artifacts-datacite.json)).

## Repository layout

```
index.html                                home page (generated)
graphs/<slug>/index.html                  graph page (generated)
graphs/<slug>/<slug>-mira-graph.jsonld    MIRA JSON-LD (generated)
artifacts/index.html                      artifact graph page (generated)
artifacts/prism-artifacts-datacite.json   DataCite relatedIdentifiers per paper (generated)
specs/<slug>.json                         source of truth for each paper (edit these)
scripts/build.py                          validates one spec and builds its page + JSON-LD
scripts/build_artifacts.py                builds the artifact graph from every spec
scripts/build_site.py                     rebuilds every graph page, the home page and the artifact graph
assets/template.html                      graph page template
assets/index-template.html                home page template
assets/artifacts-template.html            artifact graph template
docs/graph-spec.md                        spec format
```

## Usage

### Environment
Python 3.9 or newer, standard library only.
```bash
conda env create -f environment.yml
conda activate prism-discourse-graphs
```

### Add a paper
1. Write `specs/<slug>.json` following [docs/graph-spec.md](docs/graph-spec.md). Include a `card` block with `tag`, `date` (YYYY-MM-DD), `title` and `summary`, and an `artifacts` block listing the paper's inputs and outputs.
2. Rebuild the site:
   ```bash
   python3 scripts/build_site.py .
   ```
   If the build prints `SPEC ERRORS`, fix the spec and run it again.
3. Open `index.html` in a browser to check it. Cards are sorted newest first by `card.date`.
4. Commit on a branch (`add-<slug>`) and open a pull request.

### Deploy
GitHub Pages serves the `main` branch from the repository root. There is no build step: the committed HTML is the site. `.nojekyll` turns off Jekyll processing.

## How it was developed

- **Data model:** the [MIRA schema](https://github.com/MIRA-science/schema) (LinkML). JSON-LD output follows the conventions in [MIRA-science/demo-MIRA-graph-data](https://github.com/MIRA-science/demo-MIRA-graph-data).
- **Extraction:** each spec is written by hand from the paper, its code repository README and its data archive. Rules:
  - Claims are atomic and each one addresses at least one Question.
  - Evidence carries the exact numbers and figure from the paper.
  - Requests are limited to open work that the authors name.
  - DOIs come only from the source; PDB DOIs are derived from the PDB ID.
  - Quotes are verbatim and under 15 words, with at most one per source.
- **Validation:** `scripts/build.py` rejects specs with:
  - unknown relation types or orphan nodes
  - undefined references or figures
  - missing locations
  - over-long or duplicate quotes
- **Viewer:** each graph page is a single self-contained HTML file with the JSON-LD embedded. It works offline except for web fonts.
- **Artifact graph:** built from the same specs. The datasets, code and protocols are curated by hand in each spec's `artifacts` block. PDB entries come from `pdb_all` and the PDB IDs named on discourse graph nodes, and citations between Prism papers are detected from `refs`. Link types follow DataCite relationTypes, the same vocabulary used by [Scholix](http://www.scholix.org/) and close to PROV-O's `used` / `wasGeneratedBy`. The viewer is a hand-written canvas force layout with no external libraries.

## Contact
Andy Burnim, Prism project, Astera Institute.

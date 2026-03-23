# RUW Database Overview

Live dashboard: **https://hcss-utils.github.io/ruw-warehouse-overview/**

A lightweight status page for the **Russian-Ukrainian War (RUW) Database**. The page shows per-source document and chunk counts, annotation coverage, and freshness at a glance.

## What it shows

Each row in the table corresponds to one source database (Telegram channels, Kremlin, ISW, Integrum, etc.). For every source the page displays:

| Column | Description |
|---|---|
| Lang | Languages present in the source (up to 5) |
| Documents | Total number of ingested documents |
| Chunks | Total text chunks produced from those documents |
| Relevant chunks | Chunks annotated as relevant, with coverage % |
| Last Updated | Date of the most recent document in the source |

Summary cards at the top aggregate totals across all sources and show the latest data date across the entire corpus.

## How it works

### SQL logic

`assets/stats.sql` runs a single query against `public.uploaded_document` joined through `document_section` → `document_section_chunk`. Relevant chunks are determined by combining two annotation tables:

- `taxonomy` — legacy classifications
- `taxonomy_annotation` — current pipeline annotations (`is_relevant = true` and `HLTP IS NOT NULL`)

The two are merged with `UNION` (deduplicating chunk IDs) before counting. Language codes are aggregated with `STRING_AGG(DISTINCT UPPER(...))` per source.

### Technical pipeline

```
schedule (daily 06:00 UTC) or push to main
    │
    ▼
main.py
  ├── reads assets/stats.sql
  ├── executes against DATABASE (secret)
  ├── formats display values (number formatting, language ordering, dates)
  ├── writes data/stats.json  (raw snapshot for history)
  └── renders templates/index.j2 → index.html
    │
    ▼
GitHub Actions
  ├── commits data/stats.json  [skip ci]
  ├── copies index.html + assets/ → _site/
  └── deploys _site/ to GitHub Pages
```

## Development

```bash
git clone https://github.com/hcss-utils/ruw-warehouse-overview.git
cd ruw-warehouse-overview
```

Work on a feature branch:

```bash
git checkout -b feature/<name>
```

After making changes, run quality checks before committing:

```bash
bash quality.sh
```

`quality.sh` runs ruff (linting + unused imports), isort, black, and ty (type checking) against Python 3.12.

Set `DATABASE` to a valid PostgreSQL connection string to run `main.py` locally:

```bash
DATABASE=postgresql://... uv run python main.py
```

The `DATABASE` secret used by GitHub Actions was set from a local `.env` file via the GitHub CLI:

```bash
gh secret set DATABASE --env-file .env
```

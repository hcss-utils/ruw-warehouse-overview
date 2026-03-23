import json
import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TypedDict

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import create_engine, text

HERE = Path(__file__).parent

_LANG_PRIORITY = {"UK": 0, "RU": 1, "EN": 2}


def _format_languages(langs_str: str | None, max_count: int = 5) -> str:
    if not langs_str:
        return "—"
    langs = langs_str.split("/")
    langs.sort(key=lambda l: (_LANG_PRIORITY.get(l, 99), l))
    shown = langs[:max_count]
    return "/".join(shown)


class Row(TypedDict):
    database: str
    num_docs: int
    last_updated: date | None
    languages: str | None
    num_chunks: int
    relevant_chunks: int
    relevant_pct: float | None


def main():
    db_url = os.environ["DATABASE"]
    engine = create_engine(db_url)

    sql = (HERE / "assets" / "stats.sql").read_text()

    with engine.connect() as conn:
        result = conn.execute(text(sql))
        rows: list[Row] = [
            {
                "database": str(row.database),
                "num_docs": int(row.num_docs),
                "last_updated": row.last_updated
                or (
                    date(2024, 12, 31)
                    if str(row.database) == "google_scholar"
                    else None
                ),
                "languages": str(row.languages) if row.languages else None,
                "num_chunks": int(row.num_chunks) if row.num_chunks else 0,
                "relevant_chunks": (
                    int(row.relevant_chunks) if row.relevant_chunks else 0
                ),
                "relevant_pct": (
                    float(row.relevant_pct) if row.relevant_pct is not None else None
                ),
            }
            for row in result
        ]

    today = date.today()

    # Save raw JSON for history
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data" / "stats.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.now(UTC).isoformat(),
                "sources": [
                    {
                        "database": r["database"],
                        "num_docs": r["num_docs"],
                        "last_updated": (
                            r["last_updated"].isoformat() if r["last_updated"] else None
                        ),
                        "languages": r["languages"],
                        "num_chunks": r["num_chunks"],
                        "relevant_chunks": r["relevant_chunks"],
                        "relevant_pct": r["relevant_pct"],
                    }
                    for r in rows
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )

    # Prepare display data
    display = [
        {
            "database": r["database"],
            "num_docs": f"{r['num_docs']:,}",
            "last_updated": (
                r["last_updated"].strftime("%-d %b %Y") if r["last_updated"] else "—"
            ),
            "days_ago": (today - r["last_updated"]).days if r["last_updated"] else None,
            "languages": _format_languages(r["languages"]),
            "num_chunks": f"{r['num_chunks']:,}" if r["num_chunks"] else "—",
            "relevant_chunks": f"{r['relevant_chunks']:,}" if r["num_chunks"] else "—",
            "relevant_pct": (
                f"{r['relevant_pct']:.1f}" if r["relevant_pct"] is not None else "—"
            ),
        }
        for r in rows
    ]

    generated_at = datetime.now(UTC).strftime("%d %b %Y, %H:%M UTC")
    total_docs = f"{sum(r['num_docs'] for r in rows):,}"
    total_chunks = f"{sum(r['num_chunks'] for r in rows):,}"
    max_date_raw = max(
        (r["last_updated"] for r in rows if r["last_updated"]), default=None
    )
    max_date = max_date_raw.strftime("%-d %b %Y") if max_date_raw else "—"

    env = Environment(loader=FileSystemLoader(HERE / "templates"), autoescape=True)
    html = env.get_template("index.j2").render(
        sources=display,
        total_docs=total_docs,
        total_chunks=total_chunks,
        max_date=max_date,
        generated_at=generated_at,
    )
    (HERE / "index.html").write_text(html)

    print(f"Rendered {len(rows)} sources → index.html")


if __name__ == "__main__":
    main()

import json
import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TypedDict

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import create_engine, text

HERE = Path(__file__).parent


class Row(TypedDict):
    database: str
    num_docs: int
    last_updated: date | None


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
        }
        for r in rows
    ]

    generated_at = datetime.now(UTC).strftime("%d %b %Y, %H:%M UTC")
    total_docs = f"{sum(r['num_docs'] for r in rows):,}"

    env = Environment(loader=FileSystemLoader(HERE / "templates"), autoescape=True)
    html = env.get_template("index.j2").render(
        sources=display,
        total_docs=total_docs,
        generated_at=generated_at,
    )
    (HERE / "index.html").write_text(html)

    print(f"Rendered {len(rows)} sources → index.html")


if __name__ == "__main__":
    main()

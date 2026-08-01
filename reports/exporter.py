from __future__ import annotations
import csv
from pathlib import Path
from database.database import Database


def export_market_summary(database_path: str, output_path: str) -> dict:
    db=Database(database_path); db.initialise()
    out=Path(output_path)
    with db.connect() as con:
        rows=con.execute("SELECT * FROM market_summary ORDER BY market_time,market_id").fetchall()
        fields=[d[0] for d in con.execute("SELECT * FROM market_summary LIMIT 0").description]
    with out.open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader(); writer.writerows(dict(r) for r in rows)
    return {'status':'completed','rows_exported':len(rows),'output':str(out)}

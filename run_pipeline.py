import os
import urllib.request
import zipfile
from decimal import Decimal
from pathlib import Path

import pandas as pd

from retail_transform import transform_retail
import psycopg
from psycopg import sql

project = Path(__file__).resolve().parent
data_folder = project / "data"
data_folder.mkdir(exist_ok=True)
workbook = data_folder / "Online Retail.xlsx"

if not workbook.exists():
    archive = data_folder / "online-retail.zip"
    urllib.request.urlretrieve(
        "https://archive.ics.uci.edu/static/public/352/online+retail.zip", archive
    )
    with zipfile.ZipFile(archive) as z:
        filename = next(name for name in z.namelist() if name.endswith(".xlsx"))
        workbook.write_bytes(z.read(filename))

raw = pd.read_excel(workbook)
print(f"Original rows: {len(raw):,}")

tables, kept = transform_retail(raw)
print(f"Kept: {kept:,}; excluded: {len(raw) - kept:,}")
customers = tables["customers"]
products = tables["products"]
orders = tables["orders"]
items = tables["order_items"]

for name, table in [("customers", customers), ("products", products), ("orders", orders), ("order_items", items)]:
    print(name, len(table))

settings = {
    "host": os.environ.get("PGHOST", "db"),
    "port": int(os.environ.get("PGPORT", "5432")),
    "dbname": os.environ.get("PGDATABASE", "retail_project"),
    "user": os.environ.get("PGUSER", "postgres"),
}
password = os.environ["PGPASSWORD"]
try:
    with psycopg.connect(**settings, password=password) as conn:
        conn.execute((project / "schema.sql").read_text(encoding="utf-8"))
        conn.execute("""TRUNCATE retail_student.order_items, retail_student.orders,
                       retail_student.products, retail_student.customers""")
        for name, table in [("customers", customers), ("products", products),
                            ("orders", orders), ("order_items", items)]:
            statement = sql.SQL("COPY retail_student.{} ({}) FROM STDIN").format(
                sql.Identifier(name), sql.SQL(", ").join(map(sql.Identifier, table.columns)))
            with conn.cursor().copy(statement) as copy:
                for row in table.itertuples(index=False, name=None):
                    copy.write_row(row)

        count, actual_total = conn.execute("""
            SELECT COUNT(*), SUM(quantity * unit_price) FROM retail_student.order_items
        """).fetchone()
        expected_total = sum((q * p for q, p in zip(items["quantity"], items["unit_price"])), Decimal("0"))
        assert count == len(items), "Row count mismatch"
        assert actual_total == expected_total, "Transaction total mismatch"
    print(f"Loaded {count:,} transaction lines. Signed value: £{actual_total:,.2f}. Checks passed.")
finally:
    del password

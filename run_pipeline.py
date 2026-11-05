"""Run the existing retail ETL notebook pipeline non-interactively.
Derived from data_preparation.ipynb; keep transformation logic in sync.
"""
import os

from pathlib import Path
from decimal import Decimal
import urllib.request
import zipfile
import pandas as pd

project = Path.cwd()
assert (project / "schema.sql").exists(), "Open this notebook from the project folder."
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
raw.head()

df = raw.drop_duplicates().copy()
df["line_id"] = df.index + 2  # Original Excel row; header is row 1.
df = df.dropna(subset=["InvoiceNo", "StockCode", "CustomerID", "Description"])
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
df["StockCode"] = df["StockCode"].astype(str).str.strip()
df["Description"] = df["Description"].astype(str).str.strip()

valid = (
    df["InvoiceDate"].notna()
    & df["Quantity"].notna() & df["Quantity"].ne(0)
    & df["Quantity"].mod(1).eq(0)
    & df["UnitPrice"].gt(0)
    & df["StockCode"].str.fullmatch(r"\d{5}[A-Za-z]*")
    & df["Description"].ne("")
)
df = df.loc[valid].copy()
is_cancellation = df["InvoiceNo"].str.upper().str.startswith("C")
df = df.loc[is_cancellation.eq(df["Quantity"].lt(0))].copy()
df["CustomerID"] = df["CustomerID"].astype("int64").astype(str)
df["Quantity"] = df["Quantity"].astype(int)
df["Country"] = df["Country"].fillna("Unknown")
df["transaction_type"] = df["InvoiceNo"].str.upper().str.startswith("C").map(
    {True: "Cancellation", False: "Sale"}
)

# One invoice must have one customer and timestamp; exclude inconsistent headers.
headers = df.groupby("InvoiceNo")[["CustomerID", "InvoiceDate"]].nunique()
bad_invoices = headers.index[headers.gt(1).any(axis=1)]
df = df.loc[~df["InvoiceNo"].isin(bad_invoices)].copy()
df = df.sort_values(["InvoiceDate", "line_id"])
print(f"Kept: {len(df):,}; excluded: {len(raw) - len(df):,}")
df.head()

customers = df.drop_duplicates("CustomerID")[["CustomerID", "Country"]].rename(
    columns={"CustomerID": "customer_id", "Country": "country"})
products = df.drop_duplicates("StockCode")[["StockCode", "Description"]].rename(
    columns={"StockCode": "product_id", "Description": "description"})
orders = df.drop_duplicates("InvoiceNo")[["InvoiceNo", "CustomerID", "InvoiceDate", "transaction_type"]].rename(
    columns={"InvoiceNo": "invoice_no", "CustomerID": "customer_id", "InvoiceDate": "invoice_date"})
items = df[["line_id", "InvoiceNo", "StockCode", "Quantity", "UnitPrice"]].rename(
    columns={"InvoiceNo": "invoice_no", "StockCode": "product_id", "Quantity": "quantity", "UnitPrice": "unit_price"})
items["unit_price"] = items["unit_price"].map(lambda value: Decimal(str(value)))

assert customers["customer_id"].is_unique
assert products["product_id"].is_unique
assert orders["invoice_no"].is_unique
assert items["line_id"].is_unique
assert items["invoice_no"].isin(orders["invoice_no"]).all()
assert items["product_id"].isin(products["product_id"]).all()

for name, table in [("customers", customers), ("products", products), ("orders", orders), ("order_items", items)]:
    print(name, len(table))

import psycopg
from psycopg import sql

settings = {"host": os.environ.get("PGHOST", "db"), "port": int(os.environ.get("PGPORT", "5432")), "dbname": os.environ.get("PGDATABASE", "retail_project"), "user": os.environ.get("PGUSER", "retail_user")}
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

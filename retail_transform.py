"""Data cleaning and relational modeling shared by ETL and automated tests."""

from decimal import Decimal

import pandas as pd


def transform_retail(raw: pd.DataFrame):
    """Prepare validated retail tables without modifying the source DataFrame."""
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

    headers = df.groupby("InvoiceNo")[["CustomerID", "InvoiceDate"]].nunique()
    bad_invoices = headers.index[headers.gt(1).any(axis=1)]
    df = df.loc[~df["InvoiceNo"].isin(bad_invoices)].copy()
    df = df.sort_values(["InvoiceDate", "line_id"])


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

    return {"customers": customers, "products": products, "orders": orders, "order_items": items}, len(df)

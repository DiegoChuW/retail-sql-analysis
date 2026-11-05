"""Unit tests exercise the production transform with deliberately messy records."""
from decimal import Decimal

import pandas as pd

from retail_transform import transform_retail


def source_rows():
    return pd.DataFrame([
        {"InvoiceNo": "10001", "StockCode": "12345", "Description": "Tea", "Quantity": 2, "InvoiceDate": "2011-01-01", "UnitPrice": 4.5, "CustomerID": 101, "Country": "UK"},
        {"InvoiceNo": "10001", "StockCode": "23456", "Description": "Cup", "Quantity": 1, "InvoiceDate": "2011-01-01", "UnitPrice": 3.0, "CustomerID": 101, "Country": "UK"},
        {"InvoiceNo": "C10002", "StockCode": "12345", "Description": "Tea", "Quantity": -1, "InvoiceDate": "2011-01-02", "UnitPrice": 4.5, "CustomerID": 101, "Country": "UK"},
        {"InvoiceNo": "10001", "StockCode": "12345", "Description": "Tea", "Quantity": 2, "InvoiceDate": "2011-01-01", "UnitPrice": 4.5, "CustomerID": 101, "Country": "UK"},  # duplicate
        {"InvoiceNo": "10003", "StockCode": "12345", "Description": "Tea", "Quantity": 0, "InvoiceDate": "2011-01-03", "UnitPrice": 4.5, "CustomerID": 101, "Country": "UK"},  # invalid quantity
        {"InvoiceNo": "10004", "StockCode": "12345", "Description": "Tea", "Quantity": 1, "InvoiceDate": "2011-01-04", "UnitPrice": 4.5, "CustomerID": None, "Country": "UK"},  # missing customer
        {"InvoiceNo": "C10005", "StockCode": "12345", "Description": "Tea", "Quantity": 1, "InvoiceDate": "2011-01-05", "UnitPrice": 4.5, "CustomerID": 101, "Country": "UK"},  # cancellation sign mismatch
    ])


def test_deduplication_and_invalid_record_filtering():
    original = source_rows()
    tables, retained = transform_retail(original)
    assert retained == 3
    assert len(tables["order_items"]) == 3
    assert len(original) == 7  # transformation did not mutate raw input
    assert tables["order_items"]["line_id"].is_unique


def test_cancellation_classification_and_signed_totals():
    tables, _ = transform_retail(source_rows())
    types = dict(zip(tables["orders"]["invoice_no"], tables["orders"]["transaction_type"]))
    assert types == {"10001": "Sale", "C10002": "Cancellation"}
    items = tables["order_items"]
    total = sum((q * price for q, price in zip(items["quantity"], items["unit_price"])), Decimal("0"))
    assert total == Decimal("7.5")


def test_relational_keys_and_references():
    tables, _ = transform_retail(source_rows())
    assert len(tables["customers"]) == 1
    assert len(tables["products"]) == 2
    assert len(tables["orders"]) == 2
    assert tables["orders"]["invoice_no"].is_unique
    assert tables["order_items"]["invoice_no"].isin(tables["orders"]["invoice_no"]).all()
    assert tables["order_items"]["product_id"].isin(tables["products"]["product_id"]).all()


def test_conflicting_invoice_header_is_rejected():
    rows = source_rows()
    extra = rows.iloc[[0]].copy()
    extra["CustomerID"] = 999
    extra["StockCode"] = "34567"
    mixed = pd.concat([rows, extra], ignore_index=True)
    tables, retained = transform_retail(mixed)
    assert retained == 1  # the conflicting sale invoice is excluded, cancellation retained
    assert tables["orders"]["invoice_no"].tolist() == ["C10002"]

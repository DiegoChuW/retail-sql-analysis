CREATE SCHEMA IF NOT EXISTS retail_student;

CREATE TABLE IF NOT EXISTS retail_student.customers (
    customer_id text PRIMARY KEY,
    country text NOT NULL
);
CREATE TABLE IF NOT EXISTS retail_student.products (
    product_id text PRIMARY KEY,
    description text NOT NULL
);
CREATE TABLE IF NOT EXISTS retail_student.orders (
    invoice_no text PRIMARY KEY,
    customer_id text NOT NULL REFERENCES retail_student.customers,
    invoice_date timestamp NOT NULL,
    transaction_type text NOT NULL CHECK (transaction_type IN ('Sale', 'Cancellation'))
);
CREATE TABLE IF NOT EXISTS retail_student.order_items (
    line_id integer PRIMARY KEY,
    invoice_no text NOT NULL REFERENCES retail_student.orders,
    product_id text NOT NULL REFERENCES retail_student.products,
    quantity integer NOT NULL CHECK (quantity <> 0),
    unit_price numeric(18,4) NOT NULL CHECK (unit_price > 0 AND unit_price <> 'NaN'::numeric)
);

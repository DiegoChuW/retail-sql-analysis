-- 1. Monthly sales and cancellations
-- Monthly cancellation value follows the cancellation date, not the original sale date.
WITH calendar AS (
    SELECT generate_series(
        date_trunc('month', MIN(invoice_date)),
        date_trunc('month', MAX(invoice_date)), interval '1 month'
    )::date AS month
    FROM retail_student.orders
), totals AS (
    SELECT date_trunc('month', o.invoice_date)::date AS month,
           SUM(CASE WHEN o.transaction_type = 'Sale'
                    THEN i.quantity * i.unit_price ELSE 0 END) AS sales_value,
           SUM(CASE WHEN o.transaction_type = 'Cancellation'
                    THEN -i.quantity * i.unit_price ELSE 0 END) AS cancellation_value
    FROM retail_student.orders o
    JOIN retail_student.order_items i ON i.invoice_no = o.invoice_no
    GROUP BY 1
), monthly AS (
    SELECT c.month, COALESCE(t.sales_value, 0) AS sales_value,
           COALESCE(t.cancellation_value, 0) AS cancellation_value
    FROM calendar c LEFT JOIN totals t ON t.month = c.month
), changes AS (
    SELECT *, sales_value - cancellation_value AS sales_less_cancellations,
           LAG(sales_value) OVER (ORDER BY month) AS previous_month_sales
    FROM monthly
)
SELECT *, ROUND(100.0 * (sales_value - previous_month_sales)
                     / NULLIF(previous_month_sales, 0), 2) AS sales_change_pct
FROM changes ORDER BY month;

-- 2. Top 10 products by sales
WITH product_sales AS (
    SELECT p.product_id, p.description,
           SUM(i.quantity) AS units_sold,
           SUM(i.quantity * i.unit_price) AS sales_value
    FROM retail_student.products p
    JOIN retail_student.order_items i ON i.product_id = p.product_id
    JOIN retail_student.orders o ON o.invoice_no = i.invoice_no
    WHERE o.transaction_type = 'Sale'
    GROUP BY p.product_id, p.description
)
SELECT *, RANK() OVER (ORDER BY sales_value DESC) AS sales_rank
FROM product_sales ORDER BY sales_rank, product_id LIMIT 10;

-- 3. Customer purchase frequency
SELECT c.customer_id, c.country,
       COUNT(DISTINCT o.invoice_no) AS purchase_count,
       SUM(i.quantity * i.unit_price) AS sales_value,
       CASE WHEN COUNT(DISTINCT o.invoice_no) > 1
            THEN 'Repeat' ELSE 'One purchase' END AS customer_type
FROM retail_student.customers c
JOIN retail_student.orders o ON o.customer_id = c.customer_id
JOIN retail_student.order_items i ON i.invoice_no = o.invoice_no
WHERE o.transaction_type = 'Sale'
GROUP BY c.customer_id, c.country
ORDER BY purchase_count DESC, sales_value DESC;

-- 4. Top 10 products by cancellation value
SELECT p.product_id, p.description,
       COUNT(DISTINCT o.invoice_no) AS cancellation_invoices,
       SUM(-i.quantity) AS cancelled_units,
       SUM(-i.quantity * i.unit_price) AS cancellation_value
FROM retail_student.products p
JOIN retail_student.order_items i ON i.product_id = p.product_id
JOIN retail_student.orders o ON o.invoice_no = i.invoice_no
WHERE o.transaction_type = 'Cancellation'
GROUP BY p.product_id, p.description
ORDER BY cancellation_value DESC LIMIT 10;

-- Check loaded row count and signed transaction value.
SELECT COUNT(*) AS line_count,
       SUM(quantity * unit_price) AS signed_transaction_value
FROM retail_student.order_items;

-- Expected: zero rows. Sale quantities should be positive, cancellations negative.
SELECT i.line_id
FROM retail_student.order_items i
JOIN retail_student.orders o ON o.invoice_no = i.invoice_no
WHERE (o.transaction_type = 'Sale' AND i.quantity < 0)
   OR (o.transaction_type = 'Cancellation' AND i.quantity > 0);

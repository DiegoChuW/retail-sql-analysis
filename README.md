# Retail Sales & Cancellation Analysis

SQL analysis of retail transactions, with Python for data preparation and Power BI for reporting.

## Analysis

- Monthly sales, cancellation value, and month-over-month sales changes
- Top 10 products by sales value
- Customer purchase frequency and repeat purchases
- Top 10 products by cancellation value

## Findings

The findings below describe the dashboard's cleaned, known-customer transaction subset. Chart values are approximate where labels are not displayed.

1. **Sales strengthened towards the end of 2011.** Monthly sales rose from roughly £0.6 million in July to a peak of about £1.1 million in November. This suggests a stronger late-year trading period, but one year of data is insufficient to establish a recurring seasonal pattern. 

2. **The leading sales product also had unusually high cancellations.** PAPER CRAFT, LITTLE BIRDIE generated approximately £170,000 in sales and a similar cancellation value. REGENCY CAKESTAND 3 TIER was the next-largest sales product at roughly £140,000. 

3. **Two products stand out in the cancellation ranking.** PAPER CRAFT, LITTLE BIRDIE and MEDIUM CERAMIC TOP STORAGE JAR had cancellation values of approximately £170,000 and £80,000 respectively, far above the other displayed products. 

4. **The customer summary reports 18,372 purchase invoices and about £8.72 million in sales.** These are purchase counts and sales before cancellations, not unique customer counts or net revenue. Both repeat and one-purchase customers are visible, but the displayed rows do not establish the overall repeat-customer share.

### Follow-up

Investigate the large sales and cancellations for the two standout products, calculate repeat-customer share across the full customer summary, and compare complete months when evaluating sales trends. Avoid stock or product-quality decisions based solely on the top-10 rankings.

## Files

| File | Purpose |
| --- | --- |
| `schema.sql` | PostgreSQL tables, keys, and constraints |
| `analysis.sql` | Four analysis queries and two validation queries |
| `data_preparation.ipynb` | Download, clean, and load the dataset |
| `requirements.txt` | Python dependencies |

## Run

1. Install Python 3.12 or later and PostgreSQL. Create a database named `retail_project`.
2. Open `data_preparation.ipynb` in a Jupyter-compatible editor with this folder as the working directory. Select a Python kernel and run the cells in order. The first code cell installs the dependencies.
3. Adjust the database connection settings in the loading cell. Enter the PostgreSQL password when prompted; it is not stored in the notebook.
4. Run the queries in `analysis.sql` individually in pgAdmin or another SQL client.

The loading cell replaces the contents of the four tables in the `retail_student` schema. It validates the row count and signed transaction value before committing.

## Power BI

Connect using **Get data → PostgreSQL database**. For a default local installation, use server `localhost:5432`, database `retail_project`, and **Import** mode.

Under **Advanced options → SQL statement**, paste the first analysis query without its final semicolon. Load it and repeat for the next three analysis queries. Do not include the validation queries.

| Query | Visual | Fields |
| --- | --- | --- |
| Monthly sales | Line chart | `month`, `sales_value`, `cancellation_value` |
| Top products | Bar chart | `description`, `sales_value` |
| Customer activity | Table | `customer_id`, `country`, `purchase_count`, `sales_value`, `customer_type` |
| Product cancellations | Bar chart | `description`, `cancellation_value` |

Format monetary values as GBP and customer IDs as identifiers rather than sums. These four summaries remain disconnected, so selections do not filter across tables. Refresh in Power BI reruns the SQL queries; PostgreSQL must be available.

## Data

[Chen, D. (2015), Online Retail, UCI Machine Learning Repository](https://doi.org/10.24432/C5BW33), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The source workbook contains 541,909 rows from December 2010 to December 2011. It is downloaded when the notebook runs and is not included in this repository.

Preparation removes exact duplicates, missing customer identifiers, invalid records, and non-merchandise stock codes. Customers and products use their first retained country and description. Cancellation invoices retain negative quantities.

## Limitations

- Excluding missing-customer records limits coverage. Identical source rows may represent legitimate repeated purchases.
- Cancellation values follow cancellation dates and are not matched to original sales or verified physical returns.
- Product costs and discounts are unavailable, so the analysis does not measure profit.
- December 2011 contains only nine days and should not be compared with full months.

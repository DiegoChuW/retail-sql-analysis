# Retail Sales & Cancellation Analysis

Which products drove sales, and which had the most money tied up in cancellations? This project uses Python to clean retail invoice lines, PostgreSQL to analyze sales and customer purchases, and Power BI to present the results.

**Explore the project:** [Open the Power BI report](Retail%20Sales%20%26%20Cancellations.pbix) in Power BI Desktop, [read the SQL queries](analysis.sql), or [walk through the data preparation notebook](data_preparation.ipynb). To reproduce the database behind the report, follow one of the two setup options below.

## What the analysis found

- **November 2011 was the peak sales month.** Sales rose from roughly £600,000 in July to £1.1 million in November. December covers only nine days, so its total is unsuitable for a full-month comparison.
- **The top-selling product also led cancellations.** PAPER CRAFT, LITTLE BIRDIE recorded about £170,000 each in sales and cancellations. MEDIUM CERAMIC TOP STORAGE JAR ranked second by cancellation value at about £80,000.
- **Customers placed 18,372 purchase invoices**, totaling about £8.72 million in sales before cancellations. The SQL groups purchases by customer to distinguish one-time and repeat buyers.

These findings cover the cleaned transactions with known customers. Product and monthly values are approximate readings from the dashboard.

## From workbook to database

The source workbook contains 541,909 rows from December 2010 to December 2011. Python removes exact duplicates and filters out rows with missing customer IDs, invalid records, or non-merchandise stock codes. It preserves negative quantities on cancellation invoices. Customers and products use their first retained country and description, respectively. [UCI Online Retail dataset](https://doi.org/10.24432/C5BW33) · [CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/)

The tested Docker run loaded **398,070 transaction lines** across **21,754 invoices**, **4,360 customers**, and **3,675 products**. Their signed value was **£8,246,437.56**. This includes cancellations, which reduce the total. Before committing the load, the pipeline checks that PostgreSQL has the same line count and signed value as the cleaned Python data.

## Reproduce the analysis

Choose **Docker** to run the complete data load or **the local notebook** to inspect the Python steps interactively. Either path prepares the four tables used by the same SQL queries. Rerunning a load replaces the contents of those tables in the selected database.

### Option 1 — Docker

1. Start Docker Desktop (or Docker Engine with Compose v2). Open a terminal in the folder containing `compose.yaml`.
2. In that folder, create a file named `.env` with this line. Replace the example password with your own. Git ignores this file.

   ```dotenv
   RETAIL_DB_PASSWORD=replace_with_your_password
   ```

3. Start PostgreSQL and wait for it to become healthy.

   ```sh
   docker compose up -d --wait db
   ```

4. Run the Python loader. The first run requires internet access to fetch the images, Python packages, and source workbook. The loader reuses the workbook in `data/` on subsequent runs.

   ```sh
   docker compose --profile etl run --build --rm etl
   ```

When the output ends with **`Checks passed.`**, the database is ready. Leave it running while you explore the SQL or refresh Power BI. When finished, run `docker compose down`. The named volume retains the data for your next session.

### Option 2 — Local notebook

1. Install Python 3.12 or later and PostgreSQL. Create a database named `retail_project`.
2. Open `data_preparation.ipynb` in a Jupyter-compatible editor with the project folder as the working directory. Select a Python kernel and run the cells in order. The first code cell installs the dependencies.
3. Before running the loading cell, check its connection settings. The defaults are `localhost`, port `5432`, and user `postgres`. Enter your PostgreSQL password when prompted.

## Explore the results

| Connection setting | Docker database | Local PostgreSQL defaults |
| --- | --- | --- |
| Server for Power BI | `localhost:5433` | `localhost:5432` |
| Database | `retail_project` | `retail_project` |
| User | `postgres` | `postgres` |
| Password | Value from `.env` | Your local PostgreSQL password |

**SQL.** Open [analysis.sql](analysis.sql) in pgAdmin or another SQL client. Run the four analysis queries individually to explore monthly sales, top-selling products, customer purchase frequency, and product cancellations. Two validation queries follow.

**Power BI.** Open the included report to explore the dashboard. To refresh it against your database, set the PostgreSQL connection in **Data source settings** to the server above. To rebuild the report, choose **Get data → PostgreSQL database → Import**. Under **Advanced options → SQL statement**, import each of the four analysis queries separately, omitting its final semicolon.

| Query | Visual | Fields |
| --- | --- | --- |
| Monthly sales | Line chart | `month`, `sales_value`, `cancellation_value` |
| Top products | Bar chart | `description`, `sales_value` |
| Customer activity | Table | `customer_id`, `country`, `purchase_count`, `sales_value`, `customer_type` |
| Product cancellations | Bar chart | `description`, `cancellation_value` |

Format monetary values as GBP and treat customer IDs as identifiers. The four summaries are independent, so selections in one visual do not filter the others.

## Reading the numbers

Removing records with missing customer IDs limits coverage. Removing exact duplicates can also discard legitimate repeated purchases. Cancellations are counted on their invoice date, and the dataset does not link them to an original sale or verify a physical return. The dataset covers about one year and omits product costs and discounts, which limits conclusions about seasonality and profit.

## Project files

| File | Purpose |
| --- | --- |
| `data_preparation.ipynb` | Interactive data preparation and loading |
| `run_pipeline.py` | Python version of the notebook workflow for Docker |
| `schema.sql` | PostgreSQL tables, keys, and constraints |
| `analysis.sql` | Analysis and validation queries |
| `Retail Sales & Cancellations.pbix` | Power BI dashboard |
| `requirements.txt` | Python dependencies |
| `Dockerfile` and `compose.yaml` | Python image, PostgreSQL service, and connection between them |
| `.dockerignore` and `.gitignore` | Files excluded from the Docker build and Git, respectively |

The notebook and Docker runner implement the same preparation steps. When changing a cleaning rule, update both.

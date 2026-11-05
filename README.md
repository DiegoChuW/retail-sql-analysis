# Retail Sales & Cancellation Analysis

Which products generated the most sales, and how much value did cancellations offset? This project uses Python to clean retail invoices, PostgreSQL to analyze sales and repeat purchases, and Power BI to report the results. [Power BI dashboard](Retail%20Sales%20%26%20Cancellations.pbix) · [SQL analysis](analysis.sql) · [Preparation notebook](data_preparation.ipynb)

## Key findings

- The top-selling product, PAPER CRAFT, LITTLE BIRDIE, recorded about £170,000 in sales and roughly the same amount in cancellations.
- Monthly sales rose from about £600,000 in July 2011 to a peak of £1.1 million in November. December covers only nine days.
- Across 18,372 purchase invoices, sales totaled about £8.72 million before cancellations. Subtracting the value of cancellations brought the total to £8,246,437.56.

These figures cover cleaned transactions linked to known customers. Cancellations count in the month of the cancellation invoice. [UCI Online Retail dataset](https://doi.org/10.24432/C5BW33) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Run with Docker

Start Docker Desktop and open a terminal in the folder containing `compose.yaml`. Create a file named `.env` in that folder, replacing the example password with your own. Keep this file local.

```dotenv
RETAIL_DB_PASSWORD=replace_with_your_password
```

Run these commands in order. The first starts PostgreSQL. The second downloads the workbook if needed, cleans the data, and loads it into the database.

```sh
docker compose up -d --wait db
docker compose --profile etl run --build --rm etl
```

The tested run loaded **398,070 transaction lines** and ended with **`Checks passed.`** after verifying the row count and signed transaction total. Rerunning the loader replaces the four project tables.

## Explore the analysis

Open the Power BI dashboard to view the results, or run the queries in `analysis.sql` individually. To query or refresh against the Docker database, connect to `localhost:5433`, database `retail_project`, as `postgres` with the password from `.env`.

For a step-by-step look at the cleaning decisions, open `data_preparation.ipynb`. When you finish querying, run `docker compose down`. The database volume retains the loaded data.

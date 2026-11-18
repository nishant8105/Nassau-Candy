# Nassau Candy Distributor Analysis

An interactive sales and profitability dashboard, supported by a notebook workflow
for data preparation, exploratory analysis, and monthly sales forecasting.

## What is included

- **Streamlit dashboard** — filter sales by date, division, region, ship mode, and
  product; explore product and division profitability, regional trends, pricing
  scenarios, and monthly sales forecasts.
- **Analysis notebook** — data cleaning, profitability analysis, visualizations,
  model evaluation, and model export.
- **Forecast model and metrics** — a saved scikit-learn model and its evaluation
  results.
- **Data and figures** — raw and processed CSV files, summary tables, and
  generated charts.

## Run the dashboard

Use Python 3.10 or later. From the repository root, install the dependencies and
start the app:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

The dashboard reads `data/processed/cleaned_data.csv` and uses the saved model
in `models/sales_forecast_model.joblib` for its forecast tab.

## Run the notebook

Open `notebook/Nassau_Candy_Project.ipynb` in Jupyter. The notebook expects the
input CSV at `data/raw/Nassau_Candy_Distributor.csv`; it prepares the cleaned
data, summary outputs, charts, and forecast model used by the dashboard.

## Repository layout

```text
app.py                              Streamlit dashboard
requirements.txt                   Python dependencies
data/raw/                          Input distributor data
data/processed/                    Cleaned data and summary tables
models/                            Forecast model and evaluation metrics
notebook/                          End-to-end analysis notebook
output/figures/                    Generated analysis charts
```

## Forecast interpretation

The saved model forecasts monthly sales from a 24-month history. Its recorded
test MAE is approximately 1,089, compared with approximately 4,272 for the
average-sales baseline. This is a short-history model and its forecasts should
be treated as a rough planning aid, not a guarantee.

## Data handling

The included source and cleaned transaction data contain customer identifiers
and location fields. Review the data owner's authorization and privacy
requirements before sharing or publishing the repository.

from pathlib import Path
import json

import joblib
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------
# Page setup
# ---------------------------------------------------------
st.set_page_config(page_title="Nassau Candy Dashboard", page_icon="🍫", layout="wide")
st.title("🍫 Nassau Candy Distributor")
st.caption("Product Line Profitability and Margin Analysis")

# Run this app from the main project folder.
DATA_FILE = Path("data/processed/cleaned_data.csv")
MODEL_FILE = Path("models/sales_forecast_model.joblib")
METRICS_FILE = Path("models/model_metrics.json")

# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------
if not DATA_FILE.exists():
    st.error(f"File not found: {DATA_FILE}")
    st.info("Run the notebook first. It creates data/processed/cleaned_data.csv.")
    st.stop()


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    return df


data = load_data()

# ---------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------
st.sidebar.header("Filters")

min_date = data["Order Date"].min().date()
max_date = data["Order Date"].max().date()
dates = st.sidebar.date_input("Order date range", value=(min_date, max_date),
                              min_value=min_date, max_value=max_date)

divisions = sorted(data["Division"].unique())
chosen_divisions = st.sidebar.multiselect("Division", divisions, default=divisions)

regions = sorted(data["Region"].unique())
chosen_regions = st.sidebar.multiselect("Region", regions, default=regions)

ship_modes = sorted(data["Ship Mode"].unique())
chosen_ship_modes = st.sidebar.multiselect("Ship Mode", ship_modes, default=ship_modes)

search = st.sidebar.text_input("Search product")

# The date picker gives one date until the user picks both ends
if len(dates) == 2:
    start_date, end_date = dates
else:
    start_date = end_date = dates[0]

filtered = data[
    (data["Order Date"].dt.date >= start_date)
    & (data["Order Date"].dt.date <= end_date)
    & (data["Division"].isin(chosen_divisions))
    & (data["Region"].isin(chosen_regions))
    & (data["Ship Mode"].isin(chosen_ship_modes))
]

if search:
    filtered = filtered[filtered["Product Name"].str.contains(search, case=False)]

if filtered.empty:
    st.warning("No data for these filters. Please change the filters.")
    st.stop()

# ---------------------------------------------------------
# KPI cards
# ---------------------------------------------------------
total_sales = filtered["Sales"].sum()
total_cost = filtered["Cost"].sum()
total_profit = filtered["Gross Profit"].sum()
margin = total_profit / total_sales * 100

st.subheader("Business Overview")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Sales", f"{total_sales:,.0f}")
k2.metric("Total Cost", f"{total_cost:,.0f}")
k3.metric("Gross Profit", f"{total_profit:,.0f}")
k4.metric("Gross Margin", f"{margin:.2f}%")
k5.metric("Products", filtered["Product Name"].nunique())

# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Products", "Divisions", "Region and Ship Mode",
    "Monthly Trend", "Price What-If", "Sales Forecast"
])

# ---------------------------------------------------------
# Tab 1: Products
# ---------------------------------------------------------
with tab1:
    product_summary = filtered.groupby("Product Name").agg(
        Sales=("Sales", "sum"),
        Cost=("Cost", "sum"),
        Gross_Profit=("Gross Profit", "sum"),
        Units=("Units", "sum")
    ).reset_index()

    product_summary["Gross Margin"] = product_summary["Gross_Profit"] / product_summary["Sales"] * 100
    product_summary["Profit Per Unit"] = product_summary["Gross_Profit"] / product_summary["Units"]
    product_summary["Revenue Share %"] = product_summary["Sales"] / product_summary["Sales"].sum() * 100
    product_summary["Profit Share %"] = product_summary["Gross_Profit"] / product_summary["Gross_Profit"].sum() * 100

    left, right = st.columns(2)

    top10 = product_summary.nlargest(10, "Gross_Profit").sort_values("Gross_Profit")
    fig = px.bar(top10, x="Gross_Profit", y="Product Name", orientation="h",
                 title="Top 10 Products by Gross Profit")
    left.plotly_chart(fig, width="stretch")

    fig = px.scatter(product_summary, x="Sales", y="Gross Margin", size="Gross_Profit",
                     hover_name="Product Name", title="Sales vs Gross Margin")
    right.plotly_chart(fig, width="stretch")

    # Pareto: how many products give 80% of sales
    pareto = product_summary.sort_values("Sales", ascending=False).copy()
    pareto["Cumulative Revenue %"] = pareto["Sales"].cumsum() / pareto["Sales"].sum() * 100
    products_for_80 = int((pareto["Cumulative Revenue %"] < 80).sum() + 1)

    fig = px.line(pareto, x="Product Name", y="Cumulative Revenue %", markers=True,
                  title="Cumulative Revenue by Product")
    fig.add_hline(y=80, line_dash="dash")
    st.plotly_chart(fig, width="stretch")
    st.metric("Products needed for 80% of sales", products_for_80)

    st.subheader("Product table")
    st.dataframe(product_summary.sort_values("Gross_Profit", ascending=False).round(2),
                 hide_index=True, width="stretch")

    st.subheader("Lowest margin products")
    st.dataframe(product_summary.sort_values("Gross Margin").head(5).round(2),
                 hide_index=True, width="stretch")

# ---------------------------------------------------------
# Tab 2: Divisions
# ---------------------------------------------------------
with tab2:
    division_summary = filtered.groupby("Division").agg(
        Sales=("Sales", "sum"),
        Gross_Profit=("Gross Profit", "sum")
    ).reset_index()
    division_summary["Gross Margin"] = division_summary["Gross_Profit"] / division_summary["Sales"] * 100

    left, right = st.columns(2)

    fig = px.bar(division_summary, x="Division", y=["Sales", "Gross_Profit"],
                 barmode="group", title="Sales and Gross Profit by Division")
    left.plotly_chart(fig, width="stretch")

    fig = px.bar(division_summary, x="Division", y="Gross Margin",
                 title="Gross Margin by Division (%)")
    right.plotly_chart(fig, width="stretch")

    st.dataframe(division_summary.round(2), hide_index=True, width="stretch")

# ---------------------------------------------------------
# Tab 3: Region and Ship Mode
# ---------------------------------------------------------
with tab3:
    region_summary = filtered.groupby("Region").agg(
        Sales=("Sales", "sum"),
        Gross_Profit=("Gross Profit", "sum")
    ).reset_index()
    region_summary["Gross Margin"] = region_summary["Gross_Profit"] / region_summary["Sales"] * 100

    ship_summary = filtered.groupby("Ship Mode").agg(
        Sales=("Sales", "sum"),
        Gross_Profit=("Gross Profit", "sum")
    ).reset_index()
    ship_summary["Gross Margin"] = ship_summary["Gross_Profit"] / ship_summary["Sales"] * 100

    left, right = st.columns(2)

    fig = px.bar(region_summary, x="Region", y="Sales", title="Sales by Region")
    left.plotly_chart(fig, width="stretch")

    fig = px.bar(ship_summary, x="Ship Mode", y="Sales", title="Sales by Ship Mode")
    right.plotly_chart(fig, width="stretch")

    st.dataframe(region_summary.round(2), hide_index=True, width="stretch")
    st.dataframe(ship_summary.round(2), hide_index=True, width="stretch")
    st.caption("Look at the Gross Margin column. It is almost the same for every region "
               "and ship mode, so place and ship mode do not change margin.")

    state_summary = filtered.groupby("State/Province")["Sales"].sum().reset_index()
    state_summary = state_summary.sort_values("Sales", ascending=False).head(10)
    fig = px.bar(state_summary, x="Sales", y="State/Province", orientation="h",
                 title="Top 10 States by Sales")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------
# Tab 4: Monthly trend
# ---------------------------------------------------------
with tab4:
    monthly = filtered.groupby(filtered["Order Date"].dt.to_period("M")).agg(
        Sales=("Sales", "sum"),
        Gross_Profit=("Gross Profit", "sum")
    ).reset_index()
    monthly["Order Date"] = monthly["Order Date"].astype(str)

    fig = px.line(monthly, x="Order Date", y=["Sales", "Gross_Profit"], markers=True,
                  title="Monthly Sales and Gross Profit")
    st.plotly_chart(fig, width="stretch")

    year_sales = filtered.groupby(["Order Year", "Order Month"])["Sales"].sum().reset_index()
    year_sales["Order Year"] = year_sales["Order Year"].astype(str)
    fig = px.line(year_sales, x="Order Month", y="Sales", color="Order Year", markers=True,
                  title="Monthly Sales by Year")
    st.plotly_chart(fig, width="stretch")

    peak_share = filtered[filtered["Order Month"] >= 9]["Sales"].sum() / total_sales * 100
    st.metric("Share of sales from September to December", f"{peak_share:.1f}%")

# ---------------------------------------------------------
# Tab 5: Price what-if
# Margin is fixed for each product, so a model is not needed.
# We calculate it directly from price and cost.
# ---------------------------------------------------------
with tab5:
    st.write("Each product has one fixed price and cost. Change them here to see what happens to margin and profit.")

    product_list = sorted(data["Product Name"].unique())
    product = st.selectbox("Product", product_list)

    product_rows = data[data["Product Name"] == product]
    current_price = float(product_rows["Unit Price"].iloc[0])
    current_cost = float(product_rows["Unit Cost"].iloc[0])
    units_per_year = float(product_rows["Units"].sum() / 2)

    c1, c2, c3 = st.columns(3)
    new_price = c1.number_input("New unit price", min_value=0.01, value=current_price, step=0.05)
    new_cost = c2.number_input("New unit cost", min_value=0.01, value=current_cost, step=0.05)
    units = c3.number_input("Units per year", min_value=1, value=int(units_per_year), step=10)

    current_profit = (current_price - current_cost) * units
    new_profit = (new_price - new_cost) * units
    current_margin = (current_price - current_cost) / current_price * 100
    new_margin = (new_price - new_cost) / new_price * 100

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Current margin", f"{current_margin:.2f}%")
    r2.metric("New margin", f"{new_margin:.2f}%", f"{new_margin - current_margin:.2f} points")
    r3.metric("Current profit per year", f"{current_profit:,.2f}")
    r4.metric("New profit per year", f"{new_profit:,.2f}", f"{new_profit - current_profit:,.2f}")

    st.caption("This assumes customers buy the same number of units after the price change. "
               "Test a price change on a small scale first.")

# ---------------------------------------------------------
# Tab 6: Sales forecast (uses the saved model)
# ---------------------------------------------------------
with tab6:
    if not MODEL_FILE.exists():
        st.warning("Saved model not found. Run the notebook first to create it.")
    else:
        model = joblib.load(MODEL_FILE)

        # Use all data (not the filtered data) to build the monthly history
        history = data.groupby(data["Order Date"].dt.to_period("M"))["Sales"].sum().reset_index()
        history["Month Number"] = range(1, len(history) + 1)
        last_number = int(history["Month Number"].max())
        last_month = history["Order Date"].iloc[-1]

        months_ahead = st.slider("Months to forecast", 1, 6, 3)

        future_months = pd.period_range(last_month + 1, periods=months_ahead, freq="M")
        future = pd.DataFrame({
            "Month Number": [last_number + i for i in range(1, months_ahead + 1)],
            "Month": future_months.month
        })
        future["Sales"] = model.predict(future)
        future["Order Date"] = future_months.astype(str)
        future["Type"] = "Forecast"

        history["Order Date"] = history["Order Date"].astype(str)
        history["Type"] = "Actual"

        both = pd.concat([history[["Order Date", "Sales", "Type"]],
                          future[["Order Date", "Sales", "Type"]]])

        fig = px.bar(both, x="Order Date", y="Sales", color="Type",
                     title="Actual and Forecast Monthly Sales")
        st.plotly_chart(fig, width="stretch")

        st.dataframe(future[["Order Date", "Sales"]].round(0), hide_index=True, width="stretch")

        if METRICS_FILE.exists():
            with open(METRICS_FILE) as file:
                metrics = json.load(file)
            st.caption(
                f"On the test months, the model was off by about {metrics['MAE']:,.0f} per month "
                f"(always guessing the average was off by {metrics['Baseline_MAE']:,.0f}). "
                "It learned from only two years, so use it as a rough guide."
            )

st.divider()
st.caption("Nassau Candy Distributor | Product Profitability Analysis")

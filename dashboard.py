import pandas as pd
import plotly.express as px
import dash
from dash import Dash, html, dcc, Input, Output
from dash.dash_table import DataTable   # safer than "from dash import dash_table"

# -----------------------------------------
# LOAD YOUR DATASET
# -----------------------------------------
# Change path if needed
df = pd.read_csv(r"C:\Users\ASUS\Desktop\swiggy\swiggy.csv")

# Clean column names
df.columns = (
    df.columns.str.strip()
              .str.lower()
              .str.replace(" ", "_")
)

# Ensure expected columns exist (basic checks)
required_cols = ["city", "area", "restaurant", "avg_ratings", "price", "delivery_time", "food_type"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"These required columns are missing in your CSV: {missing}")

# Clean delivery time like "35 mins"
df["delivery_time"] = (
    df["delivery_time"]
    .astype(str)
    .str.extract(r"(\d+)")
    .astype(float)
)

# Numeric price
df["price"] = pd.to_numeric(df["price"], errors="coerce")

# Drop rows without rating to avoid NaN issues
df = df.dropna(subset=["avg_ratings"])

# Basic numeric ranges
rating_min, rating_max = float(df["avg_ratings"].min()), float(df["avg_ratings"].max())
price_min, price_max   = float(df["price"].min()), float(df["price"].max())

# -----------------------------------------
# DASH APP
# -----------------------------------------
app = Dash(__name__)

# -----------------------------------------
# LAYOUT
# -----------------------------------------
app.layout = html.Div([

    html.H1("🍽 Swiggy Interactive Analytics Dashboard",
            style={"textAlign": "center", "color": "#2b3a55"}),

    html.Br(),

    # ===================== KPI CARDS =====================
    html.Div(id="kpi_cards", style={
        "display": "flex",
        "justifyContent": "space-between",
        "padding": "10px",
        "gap": "10px"
    }),

    html.Br(),

    # ===================== FILTERING ROW 1 =====================
    html.Div([
        html.Div([
            html.Label("Select City"),
            dcc.Dropdown(
                id="city_filter",
                options=[{"label": c, "value": c} for c in sorted(df["city"].dropna().unique())],
                placeholder="City",
                clearable=True
            )
        ], style={"width": "32%", "display": "inline-block"}),

        html.Div([
            html.Label("Select Area"),
            dcc.Dropdown(
                id="area_filter",
                placeholder="Area",
                clearable=True
            )
        ], style={"width": "32%", "display": "inline-block"}),

        html.Div([
            html.Label("Food Type"),
            dcc.Dropdown(
                id="food_filter",
                placeholder="Food Type",
                clearable=True
            )
        ], style={"width": "32%", "display": "inline-block"}),
    ], style={"padding": "10px"}),

    html.Br(),

    # ===================== FILTERING ROW 2 (SLIDERS) =====================
    html.Div([
        html.Div([
            html.Label("Rating Range"),
            dcc.RangeSlider(
                id="rating_range",
                min=rating_min,
                max=rating_max,
                step=0.1,
                value=[rating_min, rating_max],
                marks={round(r, 1): str(round(r, 1)) for r in
                       [rating_min, (rating_min + rating_max) / 2, rating_max]}
            )
        ], style={"width": "48%", "display": "inline-block", "padding": "0 10px"}),

        html.Div([
            html.Label("Price Range"),
            dcc.RangeSlider(
                id="price_range",
                min=price_min,
                max=price_max,
                step=max(1, (price_max - price_min) / 50),
                value=[price_min, price_max],
                marks={
                    int(price_min): str(int(price_min)),
                    int(price_max): str(int(price_max))
                }
            )
        ], style={"width": "48%", "display": "inline-block", "padding": "0 10px"}),
    ]),

    html.Br(),

    # ===================== MAP =====================
    dcc.Graph(id="map_chart"),

    html.Br(),

    # ===================== CHARTS SECTION =====================
    html.Div([
        dcc.Graph(id="rating_chart",  style={"width": "48%", "display": "inline-block"}),
        dcc.Graph(id="price_chart",   style={"width": "48%", "display": "inline-block"}),
    ]),

    html.Div([
        dcc.Graph(id="delivery_chart", style={"width": "48%", "display": "inline-block"}),
        dcc.Graph(id="foodtype_pie",   style={"width": "48%", "display": "inline-block"}),
    ]),

    html.Br(),

    # ===================== TOP RESTAURANTS TABLE =====================
    html.H2("📋 Top Restaurants (Filtered View)", style={"textAlign": "center"}),

    DataTable(
        id='restaurant_table',
        columns=[
            {"name": "Restaurant",   "id": "restaurant"},
            {"name": "City",         "id": "city"},
            {"name": "Area",         "id": "area"},
            {"name": "Food Type",    "id": "food_type"},
            {"name": "Price",        "id": "price"},
            {"name": "Rating",       "id": "avg_ratings"},
            {"name": "Delivery Time (mins)", "id": "delivery_time"},
        ],
        page_size=10,
        sort_action="native",
        filter_action="native",
        style_table={'overflowX': 'auto'},
        style_cell={'padding': '8px', 'textAlign': 'left'},
        style_header={'backgroundColor': '#4f6d7a', 'color': 'white', 'fontWeight': 'bold'}
    )

])


# -----------------------------------------
# CALLBACK – FULL DASHBOARD LOGIC
# -----------------------------------------
@app.callback(
    [
        # Dropdown options
        Output("area_filter", "options"),
        Output("food_filter", "options"),

        # KPI cards
        Output("kpi_cards", "children"),

        # Graphs
        Output("map_chart", "figure"),
        Output("rating_chart", "figure"),
        Output("price_chart", "figure"),
        Output("delivery_chart", "figure"),
        Output("foodtype_pie", "figure"),

        # Table data
        Output("restaurant_table", "data"),
    ],
    [
        Input("city_filter", "value"),
        Input("area_filter", "value"),
        Input("food_filter", "value"),
        Input("rating_range", "value"),
        Input("price_range", "value"),
    ]
)
def update_dashboard(city, area, food_type, rating_range, price_range):
    # Start with full data
    data = df.copy()

    # Apply filters
    if city:
        data = data[data["city"] == city]
    if area:
        data = data[data["area"] == area]
    if food_type:
        data = data[data["food_type"] == food_type]

    if rating_range is not None:
        data = data[
            (data["avg_ratings"] >= rating_range[0]) &
            (data["avg_ratings"] <= rating_range[1])
        ]

    if price_range is not None:
        data = data[
            (data["price"] >= price_range[0]) &
            (data["price"] <= price_range[1])
        ]

    # Avoid complete empty by falling back to 0-size figs if necessary
    if data.empty:
        # Empty figures to avoid crash
        empty_fig = px.scatter(title="No data for selected filters")
        return [], [], [], empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, []

    # ---------- Update dependent dropdowns ----------
    area_options = [{"label": a, "value": a} for a in sorted(data["area"].dropna().unique())]
    food_options = [{"label": f, "value": f} for f in sorted(data["food_type"].dropna().unique())]

    # ---------- KPI Cards ----------
    kpi_cards = [
        html.Div([
            html.H4("Cities"), html.H1(data["city"].nunique())
        ], style={"flex": 1, "padding": "15px", "background": "#cfe3ff",
                  "borderRadius": "10px", "textAlign": "center"}),

        html.Div([
            html.H4("Areas"), html.H1(data["area"].nunique())
        ], style={"flex": 1, "padding": "15px", "background": "#ffe9c7",
                  "borderRadius": "10px", "textAlign": "center"}),

        html.Div([
            html.H4("Restaurants"), html.H1(data["restaurant"].nunique())
        ], style={"flex": 1, "padding": "15px", "background": "#c5ffd1",
                  "borderRadius": "10px", "textAlign": "center"}),

        html.Div([
            html.H4("Food Types"), html.H1(data["food_type"].nunique())
        ], style={"flex": 1, "padding": "15px", "background": "#ffd0d0",
                  "borderRadius": "10px", "textAlign": "center"}),
    ]

    # ---------- MAP ----------
    if {"latitude", "longitude"}.issubset(data.columns):
        # If your CSV has lat/long, use real map
        fig_map = px.scatter_mapbox(
            data,
            lat="latitude",
            lon="longitude",
            color="avg_ratings",
            size="price",
            hover_name="restaurant",
            hover_data=["city", "area", "food_type", "price", "avg_ratings"],
            color_continuous_scale="Turbo",
            zoom=4,
            height=500
        )
        fig_map.update_layout(
            mapbox_style="open-street-map",
            title="🗺 Restaurant Locations (Filtered View)"
        )
    else:
        # Fallback if no lat/long available
        city_group = (
            data.groupby("city")
                .agg(avg_rating=("avg_ratings", "mean"),
                     count_rest=("restaurant", "nunique"),
                     avg_price=("price", "mean"))
                .reset_index()
        )
        fig_map = px.scatter(
            city_group,
            x="city",
            y="avg_rating",
            size="count_rest",
            hover_data=["avg_price"],
            title="📍 City-wise Ratings & Restaurant Count (No Geo Columns)",
        )

    # ---------- Rating Histogram ----------
    fig_rating = px.histogram(
        data,
        x="avg_ratings",
        nbins=20,
        title="⭐ Rating Distribution",
    )

    # ---------- Price Histogram ----------
    fig_price = px.histogram(
        data,
        x="price",
        nbins=20,
        title="💰 Price Distribution",
    )

    # ---------- Delivery Histogram ----------
    fig_delivery = px.histogram(
        data,
        x="delivery_time",
        nbins=20,
        title="🚚 Delivery Time Distribution (mins)",
    )

    # ---------- Food Type Pie Chart ----------
    fig_food_pie = px.pie(
        data,
        names="food_type",
        title="🥗 Food Type Share (Filtered)",
        hole=0.4
    )

    # ---------- Table Data ----------
    table_data = (
        data.sort_values("avg_ratings", ascending=False)
            .head(100)   # Top 100 based on filters
            .to_dict("records")
    )

    return area_options, food_options, kpi_cards, fig_map, fig_rating, fig_price, fig_delivery, fig_food_pie, table_data


# -----------------------------------------
# RUN APP
# -----------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

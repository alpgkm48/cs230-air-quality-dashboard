"""
Name: Alp Gokmen
CS230: Section 5
Data: World Air Quality Index
URL:
Description:
Using data from the World Air Quality Index, this program offers three primary summaries: Users can view and compare the AQI levels for each country,
filter by values above or below a chosen threshold, compare the AQI averages between the Northern and Southern Hemispheres, and examine PM2.5 levels across nations.
A globe map, bar and pie charts, and interactive tables are all included in the dashboard to make the data easy to understand and navigate.
"""

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import pydeck as pdk

# [ST4] Customized page design features (sidebar, fonts, colors)
st.set_page_config(page_title="Air Quality Dashboard", layout="wide")

st.markdown(
    """
<style>
    .main-title {
        color: #2e86c1;
        font-size: 36px;
        font-weight: bold;
        margin-bottom: 15px;
    }
    .section-header {
        color: #3498db;
        font-size: 24px;
        border-bottom: 2px solid #3498db;
        padding-bottom: 5px;
        margin-top: 25px;
    }
    .dataframe {
        font-size: 14px;
    }
    .metric-box {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="main-title">Global Air Quality Index (AQI) Analysis</p>',
    unsafe_allow_html=True,
)
st.markdown(
    "Analyze air quality data from cities worldwide. Explore AQI values and PM2.5 categories."
)

# ---- AQI & PM2.5 EXPLANATION BLOCK ----
with st.expander("What are AQI and PM2.5?"):
    st.markdown(
        """
The **Air Quality Index (AQI)** is a figure that ranges from **0 to 500** that indicates the level of air pollution.  
Greater pollution and increased health hazards are associated with higher levels, whereas lower values indicate healthier air.

**Common AQI ranges:**
- **0–50 – Good:** Air quality is adequate.
- **51–100 – Moderate:** Acceptable, but certain pollutants may affect sensitive individuals.
- **101–150 – Unhealthy for Sensitive Groups**
- **151–200 – Unhealthy:** Everyone may experience health effects.
- **201+ – Very Unhealthy or Hazardous**

**PM2.5** refers to airborne particles that are **2.5 micrometers or smaller** (about 1/30 the width of a human hair).  
Because of their tiny size, they can travel deep into the lungs and even enter the bloodstream.

**Elevated PM2.5 levels are associated with:**
- Eye, nose, and throat irritation  
- Breathing issues for individuals with asthma or lung disease  
- Increased long-term risk of heart and lung diseases  
"""
    )

# [DA1] clean or manipulate data
def load_data():
    df = pd.read_csv("air_quality_index.csv")
    df.columns = df.columns.str.strip()

    numeric_cols = ["AQI Value", "lat", "lng"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=numeric_cols)

    # [PY5] dictionary use
    country_mapping = {
        "United Kingdom of Great Britain and Northern Ireland": "UK",
        "United States Of America": "USA",
        "United States of America": "USA",
        "Russian Federation": "Russia",
    }
    df["Country"] = df["Country"].replace(country_mapping)

    # [DA8] iterate through rows of a dataframe with iterrows()
    df["Location_Info"] = ""
    for index, row in df.head(100).iterrows():
        df.at[index, "Location_Info"] = f"{row['City']} ({row['Country']})"

    # [DA7] add/drop/select/create new/group columns
    df["Hemisphere"] = np.where(df["lat"] >= 0, "Northern", "Southern")
    df["East_West"] = np.where(df["lng"] >= 0, "Eastern", "Western")

    return df


data = load_data()

# [DA1] clean or manipulate data (string cleaning)
data["PM2.5 AQI Category"] = data["PM2.5 AQI Category"].str.strip().str.title()

st.sidebar.header("Filter Options")
# [ST1] Streamlit widget 1 (slider)
aqi_threshold = st.sidebar.slider("AQI Threshold Value", 0, 500, 50, 10)
# [ST1] Streamlit widget 2 (slider)
min_cities = st.sidebar.slider("Minimum Cities per Country", 1, 50, 5)

# [DA2] Sort data in ascending or descending order, by one or more columns
country_stats = (
    data.groupby("Country")["AQI Value"]
    .agg(["count", "mean", "min", "max"])
)
country_stats = country_stats[country_stats["count"] >= min_cities].sort_values(
    "mean"
)

# [PY1] function with parameter with default + [PY3] error checking
def get_color(aqi, alpha=180):
    if aqi <= 50:
        return [0, 200, 0, alpha]
    elif aqi <= 100:
        return [255, 255, 0, alpha]
    elif aqi <= 150:
        return [255, 126, 0, alpha]
    elif aqi <= 200:
        return [255, 0, 0, alpha]
    elif aqi <= 300:
        return [153, 0, 76, alpha]
    else:
        return [126, 0, 35, alpha]


# [PY2] function returning multiple values
def calculate_hemisphere_stats(df):
    north = df[df["Hemisphere"] == "Northern"]["AQI Value"].mean()
    south = df[df["Hemisphere"] == "Southern"]["AQI Value"].mean()
    return north, south


north_avg, south_avg = calculate_hemisphere_stats(data)

# [PY4] at least one list comprehension
pm25_categories_list = [
    num
    for num in data["PM2.5 AQI Category"].unique().tolist()
    if str(num) != "nan"
]

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "AQI Statistics",
        "Threshold Comparison",
        "Hemisphere Analysis",
        "PM2.5 Analysis",
        "Global Map",
    ]
)

# TAB 1 – Country-Level AQI Statistics
with tab1:
    st.markdown(
        '<p class="section-header">AQI Value Analysis</p>',
        unsafe_allow_html=True,
    )

    st.subheader("Country-Level AQI Statistics")

    # [ST2] Streamlit widget 3 (text_input)
    search_country = st.text_input("Search for a country:", "")

    if search_country:
        filtered_stats = country_stats[
            country_stats.index.str.contains(search_country, case=False)
        ]
        display_stats = filtered_stats if not filtered_stats.empty else country_stats
        if filtered_stats.empty:
            st.warning(
                f"No countries found matching '{search_country}'. Showing all countries."
            )
    else:
        display_stats = country_stats

    # [VIZ1] Chart 1: table
    st.dataframe(
        display_stats.style.format(
            {
                "count": "{:.0f}",
                "mean": "{:.1f}",
                "min": "{:.0f}",
                "max": "{:.0f}",
            }
        ).background_gradient(cmap="YlOrRd", subset=["mean"]),
        height=400,
    )

# TAB 2 – Threshold Comparison
with tab2:
    st.markdown(
        '<p class="section-header">City Counts vs AQI Threshold</p>',
        unsafe_allow_html=True,
    )

    st.subheader(f"Cities Relative to AQI {aqi_threshold}")

    # [DA4] filter data by one condition
    below = data[data["AQI Value"] < aqi_threshold]["Country"].value_counts()

    # [DA5] Filter the data by two or more conditions (AND)
    below = below[below >= min_cities]

    # [VIZ2] Chart 2: bar chart (below threshold)
    if not below.empty:
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        below.head(10).plot(kind="barh", color="green", ax=ax1)
        ax1.set_title(f"Countries Below Threshold ({aqi_threshold})")
        ax1.set_xlabel("Number of Cities")
        st.pyplot(fig1)
    else:
        st.info("No countries meet the criteria for 'Below Threshold'.")

    above = data[data["AQI Value"] > aqi_threshold]["Country"].value_counts()
    above = above[above >= min_cities]

    # [VIZ2] Chart 3: bar chart (above threshold)
    if not above.empty:
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        above.head(10).plot(kind="barh", color="red", ax=ax2)
        ax2.set_title(f"Countries Above Threshold ({aqi_threshold})")
        ax2.set_xlabel("Number of Cities")
        st.pyplot(fig2)
    else:
        st.info("No countries meet the criteria for 'Above Threshold'.")

# TAB 3 – Hemisphere Analysis
with tab3:
    st.markdown(
        '<p class="section-header">Hemisphere Comparison</p>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Average AQI – Northern Hemisphere", f"{north_avg:.1f}")
    with col2:
        st.metric("Average AQI – Southern Hemisphere", f"{south_avg:.1f}")

    st.subheader("Northern vs Southern Hemisphere")
    hemi_stats = data.groupby("Hemisphere")["AQI Value"].agg(
        ["count", "mean", "std", "min", "max"]
    )
    hemi_stats.columns = ["Cities", "Average", "Std Dev", "Minimum", "Maximum"]

    st.dataframe(
        hemi_stats.style.format(
            {
                "Cities": "{:.0f}",
                "Average": "{:.1f}",
                "Std Dev": "{:.1f}",
                "Minimum": "{:.0f}",
                "Maximum": "{:.0f}",
            }
        ).background_gradient(cmap="YlOrRd", subset=["Average"])
    )

    st.subheader("Eastern vs Western Hemisphere")
    east_west_stats = data.groupby("East_West")["AQI Value"].agg(
        ["count", "mean", "std", "min", "max"]
    )
    east_west_stats.columns = ["Cities", "Average", "Std Dev", "Minimum", "Maximum"]

    st.dataframe(
        east_west_stats.style.format(
            {
                "Cities": "{:.0f}",
                "Average": "{:.1f}",
                "Std Dev": "{:.1f}",
                "Minimum": "{:.0f}",
                "Maximum": "{:.0f}",
            }
        ).background_gradient(cmap="YlOrRd", subset=["Average"])
    )

# TAB 4 – PM2.5 Analysis
with tab4:
    st.markdown(
        '<p class="section-header">PM2.5 Category Analysis</p>',
        unsafe_allow_html=True,
    )

    # [DA6] Analyze the data with pivot tables
    pm25_pivot = pd.pivot_table(
        data=data,
        index="Country",
        columns="PM2.5 AQI Category",
        values="AQI Value",
        aggfunc="count",
        fill_value=0,
    )

    # [DA3] Find the top largest values of a column
    pm25_pivot = pm25_pivot[pm25_pivot.sum(axis=1) >= min_cities]
    pm25_pivot["Total"] = pm25_pivot.sum(axis=1)
    pm25_pivot = pm25_pivot.sort_values("Total", ascending=False).drop(
        "Total", axis=1
    )

    st.subheader("PM2.5 Categories by Country")
    st.dataframe(
        pm25_pivot.head(20)
        .style.format("{:.0f}")
        .background_gradient(cmap="YlOrRd", axis=1)
    )

    # [VIZ3] Chart 4: pie chart
    st.subheader("Global PM2.5 Category Distribution")
    category_dist = data["PM2.5 AQI Category"].value_counts(normalize=True) * 100

    fig3, ax3 = plt.subplots(figsize=(8, 6))
    colors = ["#2ecc71", "#f39c12", "#e74c3c", "#9b59b6", "#1abc9c"]
    ax3.pie(
        category_dist,
        labels=category_dist.index,
        autopct="%1.1f%%",
        startangle=90,
        colors=colors,
        textprops={"fontsize": 8},
    )
    ax3.axis("equal")
    plt.title("PM2.5 Category Distribution", pad=20)
    st.pyplot(fig3)

    st.markdown(
        '<p class="section-header">PM2.5 Category Filter Analysis</p>',
        unsafe_allow_html=True,
    )

    # [ST3] Streamlit widget 4 (selectbox)
    pm25_categories_sorted = sorted(pm25_categories_list)
    selected_category = st.selectbox(
        "Select PM2.5 Category to Analyze:", pm25_categories_sorted
    )

    valid_countries = country_stats[country_stats["count"] >= min_cities].index
    country_totals = data["Country"].value_counts()
    category_counts = data[
        data["PM2.5 AQI Category"] == selected_category
    ]["Country"].value_counts()

    country_percentages = (category_counts / country_totals * 100).dropna()
    country_percentages = country_percentages[
        country_percentages.index.isin(valid_countries)
    ]
    country_percentages = country_percentages.sort_values(ascending=False)

    st.subheader(
        f"Top 10 Countries by % of Cities with {selected_category} PM2.5 Levels"
    )
    top_10 = country_percentages.head(10).reset_index()
    top_10.columns = ["Country", "Percentage"]
    top_10["Percentage"] = top_10["Percentage"].round(2)

    fig4, ax4 = plt.subplots(figsize=(10, 6))
    top_10.plot(kind="barh", x="Country", y="Percentage", color="#3498db", ax=ax4)
    ax4.set_title(f"% of Cities with {selected_category} PM2.5 by Country")
    ax4.set_xlabel("Percentage of Country's Cities in this Category")
    st.pyplot(fig4)

# TAB 5 – Global Map
with tab5:
    st.markdown(
        '<p class="section-header">Global Air Quality Map</p>',
        unsafe_allow_html=True,
    )

    map_data = data.reset_index()[
        [
            "City",
            "Country",
            "lat",
            "lng",
            "AQI Value",
            "PM2.5 AQI Category",
            "Hemisphere",
            "East_West",
            "Location_Info",
        ]
    ]
    map_data.rename(columns={"lng": "lon"}, inplace=True)
    map_data["color"] = map_data["AQI Value"].apply(get_color)

    # [MAP] detailed map with hover
    map_data["radius"] = np.where(
        map_data["AQI Value"] < 100,
            2000,
            np.where(map_data["AQI Value"] < 200, 3000, 4000),
    )

    view_state = pdk.ViewState(
        latitude=map_data["lat"].mean(),
        longitude=map_data["lon"].mean(),
        zoom=1,
        pitch=0,
    )

    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position="[lon, lat]",
        get_color="color",
        get_radius="radius",
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=0.5,
        radius_min_pixels=3,
        radius_max_pixels=30,
    )

    tooltip = {
        "html": "<b>{City}</b>, {Country}<br/>"
        "<b>Location Info:</b> {Location_Info}<br/>"
        "<b>AQI:</b> {AQI Value}<br/>"
        "<b>Category:</b> {PM2.5 AQI Category}<br/>"
        "<b>Hemisphere:</b> {Hemisphere} ({East_West})",
        "style": {
            "backgroundColor": "#2e86c1",
            "color": "white",
            "font-family": "Arial",
            "z-index": "10000",
        },
    }

    deck = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v10",
        initial_view_state=view_state,
        layers=[scatter_layer],
        tooltip=tooltip,
    )

    st.pydeck_chart(deck)


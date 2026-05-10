import pandas as pd
import geopandas as gpd
import streamlit as st
import folium as f
from streamlit_folium import st_folium
import json

df_lang = pd.read_csv('countrylanguage.csv')
lang_to_menu = df_lang['Language'].unique().tolist()
lang_to_menu.sort()

def search(language, official):
    rows = df_lang.loc[df_lang['Language'] == language]
    trues = rows.loc[rows['IsOfficial'] == 'T']
    falses = rows.loc[rows['IsOfficial'] == 'F']
    if official == 'T':
        if not trues.empty:
            codes = df_lang.loc[(df_lang['Language'] == language) & (df_lang['IsOfficial'] == 'T'), 'CountryCode']
        else:
            return []
    else:
        if not falses.empty:
            codes = df_lang.loc[(df_lang['Language'] == language) & (df_lang["IsOfficial"] == 'F'), 'CountryCode']
        else:
            return []
    codes_list = [c for c in codes]
    return codes_list

st.set_page_config(layout="wide")

st.sidebar.title("World languages on a map")

language = st.sidebar.selectbox("Select a language", lang_to_menu, index=None, placeholder="Select a language...", label_visibility="hidden")

st.write("Selected language:", language)

spoken_iso = search(language, 'F')
official_iso = search(language, 'T')

world = gpd.read_file("COUNTRIES.shp")
world = world[["ISO_A3", "NAME", "languages", "geometry"]]
world["languages"] = world["languages"].apply(json.loads)

def make_tooltip_html(row):
    languages = row["languages"]
    if not isinstance(languages, list):
        languages = []
    list_items = "".join(f"<li>{lang}</li>" for lang in languages) or "<li>No data</li>"
    return f"""
        <div style="font-family: Arial; min-width: 150px;">
            Country:
            <b>{row["NAME"]}</b>
            <br>
            Languages spoken here:
            <ul style="margin: 4px 0 0 0; padding-left: 18px;">
                {list_items}
            </ul>
        </div>
    """

world["tooltip_html"] = world.apply(make_tooltip_html, axis=1)
world["languages"] = json.loads(world.to_json())

all_countries = world.copy()
spoken_countries = world[world["ISO_A3"].isin(spoken_iso)]
official_countries = world[world["ISO_A3"].isin(official_iso)]

all_geojson = json.loads(all_countries.to_json())
spoken_geojson = json.loads(spoken_countries.to_json())
official_geojson = json.loads(official_countries.to_json())

map = f.Map(location=[20, 0], zoom_start=2, tiles=None)

legend_html = """
<div style="
    position: fixed;
    bottom: 150px;
    left: 15px;
    z-index: 1000;
    font-family: Arial;
    font-size: 15px;
">
    <div style="margin-top: 5px;">
        <span style="
            background: #82a6e0;
            opacity: 0.7;
            display: inline-block;
            width: 23px;
            height: 23px;
            margin-right: 6px;
            vertical-align: middle;
            border-radius: 3px;
        "></span>
        Where the language is spoken in
    </div>
    <div style="margin-top: 15px;">
        <span style="
            background: #82a6e0;
            border: 2px solid #3B5181;
            opacity: 0.7;
            display: inline-block;
            width: 23px;
            height: 23px;
            margin-right: 6px;
            vertical-align: middle;
            border-radius: 3px;
        "></span>
        Where it is also an official language
    </div>
</div>
"""

with st.sidebar:
    spacer = st.empty()
    spacer.markdown(legend_html, unsafe_allow_html=True)

f.GeoJson(
    all_geojson,
    style_function=lambda feature: {
        "fillColor": "white",
        "color": "#676767",
        "weight": 0.5,
        "fillOpacity": 0.7,
    },
).add_to(map)

if not spoken_countries.empty:
    f.GeoJson(
        spoken_geojson,
        style_function=lambda feature: {
            "fillColor": "#82a6e0",
            "color": "#676767",
            "weight": 0.5,
            "fillOpacity": 0.7,
        },
        tooltip=f.GeoJsonTooltip(
            fields=["tooltip_html"],
            aliases=[""],
            labels=False,
            parse_html=True,
            sticky=True
        ),
    ).add_to(map)

if not official_countries.empty:
    f.GeoJson(
        official_geojson,
        style_function=lambda feature: {
            "fillColor": "#82a6e0",
            "color": "#3B5181",
            "weight": 1.5,
            "fillOpacity": 0.7,
        },
        tooltip=f.GeoJsonTooltip(
            fields=["tooltip_html"],
            aliases=[""],
            labels=False,
            parse_html=True,
            sticky=True
        ),
    ).add_to(map)

st_folium(map, height=600, use_container_width=True)

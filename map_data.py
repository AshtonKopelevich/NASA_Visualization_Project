"""
map_data.py
-----------
Geometry preparation for the world map tab.
No Tkinter, no Matplotlib — pure data only.

Public API
----------
NAME_MAP                  : dict[str, str]
    Alias table: your pollution dict country name → GeoPandas name.

build_merged_geodataframe(pollution: dict) -> geopandas.GeoDataFrame
    Loads the world shapefile, normalises country names, and left-joins
    all 16 years of pollution data.  Call once at startup; pass the
    result to map_view for all subsequent rendering.
"""

import geopandas as gpd
import pandas as pd

# ── Years axis ─────────────────────────────────────────────────────────────────

YEARS = list(range(2003, 2019))
KG_TO_UG = 1e9          # kg/m³  →  µg/m³

# ── Name normalisation ─────────────────────────────────────────────────────────
# Maps names as they appear in the NASA SEDAC dataset to the names used in
# Natural Earth's admin_0_countries shapefile.
# Only entries that actually differ are listed; everything else matches as-is.

NAME_MAP: dict[str, str] = {
    # Spelling / diacritic differences
    "Cote d'Ivoire":                "Ivory Coast",
    "Viet Nam":                     "Vietnam",

    # Political naming differences
    "Czech Republic":               "Czechia",
    "Republic of Congo":            "Congo",
    "Dem. Rep. Congo":              "Democratic Republic of the Congo",   # already matches
    "Eswatini":                     "eSwatini",
    "North Macedonia":              "North Macedonia",   # matches in newer builds
    "State of Palestine":           "Palestine",
    "Timor-Leste":                  "East Timor",       # matches in newer builds
    "Myanmar":                      "Myanmar",           # matches; older = "Burma"
    "Tanzania":                     "United Republic of Tanzania",
    "Serbia":                       "Republic of Serbia",

    # Abbreviations / alternate forms
    "Brunei Darussalam":            "Brunei",
    "Cabo Verde":                   "Cape Verde",
    "Kosovo":                       "Kosovo",            # absent in lowres; will be NaN
}

# Countries in the NASA dataset that the shapefile has no polygon for.
# Listed here for documentation; they will silently become NaN rows and render
# as the neutral "no data" colour on the map.
_MISSING_FROM_SHAPEFILE = {
    "Anguilla", "Aruba", "Bermuda", "British Virgin Islands",
    "Cayman Islands", "Cook Islands", "Curacao", "Faeroe Islands",
    "Falkland Islands", "French Polynesia", "Guernsey", "Isle of Man",
    "Jersey", "Kiribati", "Kosovo", "Liechtenstein", "Marshall Islands",
    "Micronesia", "Monaco", "Nauru", "New Caledonia", "Niue", "Palau",
    "Saint Barthelemy", "Saint Kitts and Nevis", "San Marino",
    "Sint Maarten", "Taiwan", "Tonga", "Turks and Caicos Islands",
    "Wallis and Futuna Islands",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _normalise_name(name: str) -> str:
    """Return the GeoPandas-canonical name for a NASA SEDAC country name."""
    return NAME_MAP.get(name, name)


def _pollution_to_dataframe(pollution: dict) -> pd.DataFrame:
    """
    Flatten the pollution dict into a tidy DataFrame.

    Parameters
    ----------
    pollution : dict
        {country_name: [val_2003, val_2004, ..., val_2018]}  (kg/m³)

    Returns
    -------
    pd.DataFrame with columns: geo_name, year, pm_ug
    """
    rows = []
    for country, values in pollution.items():
        geo_name = _normalise_name(country)
        for i, year in enumerate(YEARS):
            rows.append({
                "geo_name": geo_name,
                "year":     year,
                "pm_ug":    values[i] * KG_TO_UG,
            })
    return pd.DataFrame(rows)


# ── Public API ─────────────────────────────────────────────────────────────────

def build_merged_geodataframe(pollution: dict) -> gpd.GeoDataFrame:
    """
    Load the world shapefile and join all 16 years of pollution data onto it.

    The returned GeoDataFrame has one row per (country, year). Filter by `year` 
    column to get a single-year slice for rendering.

    Columns of interest
    -------------------
    geometry  : country polygon
    name      : country name (Natural Earth canonical)
    year      : int, 2003–2018
    pm_ug     : float, PM2.5 µg/m³  (NaN where no data)

    Parameters
    ----------
    pollution : dict
        Raw pollution dict from data_processing, keyed by NASA SEDAC names.

    Returns
    -------
    geopandas.GeoDataFrame
    """
    # Fetch the low-resolution country boundaries directly from Natural Earth
    url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    world = gpd.read_file(url)

    # Keep only the columns we need. 'ADMIN' contains the country name.
    # We rename it to 'name' to keep compatibility with the rest of the script.
    world = world[["ADMIN", "geometry"]].rename(columns={"ADMIN": "name"}).copy()

    # Build the tidy pollution DataFrame
    pm_df = _pollution_to_dataframe(pollution)

    # Cross-join world geometry with the full year range so every country
    # has a row for every year (geometry repeated), then merge pollution in.
    # This ensures countries with no pollution data still appear on the map.
    year_df  = pd.DataFrame({"year": YEARS})
    world_expanded = world.merge(year_df, how="cross")   # requires pandas ≥ 1.2

    merged = world_expanded.merge(
        pm_df,
        left_on=["name", "year"],
        right_on=["geo_name", "year"],
        how="left",
    ).drop(columns=["geo_name"])

    # Restore GeoDataFrame type (merge can strip it)
    merged = gpd.GeoDataFrame(merged, geometry="geometry", crs=world.crs)

    return merged
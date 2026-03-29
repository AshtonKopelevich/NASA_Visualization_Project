# 🌍 Global Air Pollution Explorer

A desktop data visualisation tool built for **Build4Good 2026** that lets you explore how PM2.5 air pollution has affected populations worldwide from 2003 to 2018.

---

## What It Does

Air pollution is the world's leading environmental health risk, responsible for an estimated 7 million premature deaths every year. Yet the data behind that number is rarely accessible to the general public in a meaningful way.

**Global Air Pollution Explorer** turns a decade and a half of satellite-derived pollution data into an interactive desktop dashboard. You can watch pollution levels rise and fall across the globe year by year, compare countries, trace individual trends over time, and understand what those numbers actually mean for human health.

### Features

| Tab | Description |
|---|---|
| **About** | Plain-language introduction to PM2.5, the WHO guideline, a health risk table, and links to further reading |
| **Top Countries** | Animated horizontal bar chart ranking the 15 most polluted countries for any year from 2003–2018 |
| **Country Trend** | Line chart showing how a single country's PM2.5 exposure has changed over the full 16-year period |
| **Population vs Exposure** | Scatter plot comparing population size against pollution exposure — click any dot to pin a country's details |
| **World Map** | Animated choropleth map with play/pause controls, a year scrubber, and a toggle between absolute exposure and change-since-2003 views — click any country for a popup with full details |

All charts use population-weighted PM2.5 values, meaning the figures reflect the actual exposure of residents rather than a simple geographic average.

---

## How to Run

### Requirements

- Python 3.9 or later
- The following packages:

```
pip install -r requirements.txt
```

> **Note:** GeoPandas on Windows may require manual installation of its dependencies (GDAL, Fiona). The easiest path is via [conda](https://anaconda.org/conda-forge/geopandas):
> ```
> conda install -c conda-forge geopandas
> ```


### Running

```
python main.py
```

---

## Data Source

**NASA SEDAC — Country Trends in Major Air Pollutants**
https://data.nasa.gov/dataset/country-trends-in-major-air-pollutants/resource/8409ae1d-7626-4d4b-bbdd-3fb055c2c24f

This dataset provides population-weighted annual mean PM2.5 concentrations derived from satellite retrievals (MODIS, MISR, SeaWiFS) combined with ground-level monitoring data, covering 2003–2018 for countries worldwide.

Country boundary geometries are loaded at runtime from [Natural Earth](https://www.naturalearthdata.com/) via GeoPandas.

The WHO annual PM2.5 guideline of **5 µg/m³** used throughout this dashboard is drawn from the [WHO Global Air Quality Guidelines (2021)](https://www.who.int/news-room/fact-sheets/detail/ambient-(outdoor)-air-quality-and-health).

---

## Built With

- [Tkinter](https://docs.python.org/3/library/tkinter.html) — desktop UI
- [Matplotlib](https://matplotlib.org/) — all charts and the choropleth map
- [GeoPandas](https://geopandas.org/) — country geometries and spatial joins
- [NumPy](https://numpy.org/) & [Pandas](https://pandas.pydata.org/) — data processing
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel ingestion

---

*Built for Build4Good 2026.*
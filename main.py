import tkinter as tk
 
from data_processing import pm_pop_weighted_by_country, country_series_by_country
from visualizer import AirPollutionApp
 
# ── Data source ────────────────────────────────────────────────────────────────
 
PATH             = "data.xlsx"
PM_SHEET         = "PM Pop.-Weighted (kg m^-3)"
POP_SHEET        = "Population (GPWv4.11)"
POP_SCALING      = 10000   # per 10,000 people
 
# ── Entry point ────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    pollution = pm_pop_weighted_by_country(PATH, PM_SHEET)
    pop       = country_series_by_country(PATH, POP_SHEET, POP_SCALING)
 
    root = tk.Tk()
    AirPollutionApp(root, pollution, pop)
    root.mainloop()

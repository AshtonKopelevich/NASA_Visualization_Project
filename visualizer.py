import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from map_data import build_merged_geodataframe
from map_view import build_tab_map
from intro_view import build_tab_intro

# ── Constants ──────────────────────────────────────────────────────────────────

YEARS = list(range(2003, 2019))
TOP_N = 15          # countries shown in bar chart
KG_TO_UG = 1e9      # convert kg/m³ → µg/m³ for display
WHO_LIMIT = 5.0     # WHO annual PM2.5 guideline (µg/m³)

# Palette
BG        = "#0f1117"
SURFACE   = "#1a1d27"
ACCENT    = "#e8614d"
ACCENT2   = "#f0a500"
TEXT      = "#e8e8e8"
SUBTEXT   = "#8b8fa8"
GRID      = "#2a2d3a"
SAFE_LINE = "#4caf84"

FONT_TITLE  = ("Courier New", 13, "bold")
FONT_LABEL  = ("Courier New", 10)
FONT_SMALL  = ("Courier New", 9)
FONT_HEADER = ("Courier New", 16, "bold")

# ── Helpers ────────────────────────────────────────────────────────────────────

def _to_ug(value: float) -> float:
    """Convert kg/m³ to µg/m³."""
    return value * KG_TO_UG


def _styled_fig(figsize=(9, 5)):
    fig, ax = plt.subplots(figsize=figsize, facecolor=BG)
    ax.set_facecolor(SURFACE)
    ax.tick_params(colors=SUBTEXT, labelsize=8)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)
    ax.grid(color=GRID, linestyle="--", linewidth=0.6, alpha=0.7)
    fig.tight_layout(pad=2.0)   # only here, never in the plot functions
    return fig, ax


def _embed(fig, parent) -> FigureCanvasTkAgg:
    """Embed a Matplotlib figure into a Tkinter parent widget."""
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    return canvas


# ── Graph functions ────────────────────────────────────────────────────────────

def plot_top_countries_bar(pollution: dict, ax, fig, year_idx: int = -1):
    """
    Bar chart: top TOP_N countries by PM2.5 exposure for a given year index.
    year_idx maps directly into each country's data list (0 = 2003, -1 = 2018).
    Draws a WHO guideline line for context.
    """
    ax.cla()
    ax.set_facecolor(SURFACE)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)
    ax.grid(color=GRID, linestyle="--", linewidth=0.6, alpha=0.7)
    ax.tick_params(colors=SUBTEXT, labelsize=8)

    ranked = sorted(
        pollution.items(),
        key=lambda kv: kv[1][year_idx],
        reverse=True
    )[:TOP_N]

    countries = [item[0] for item in ranked]
    values    = [_to_ug(item[1][year_idx]) for item in ranked]
    colors    = [ACCENT if v > WHO_LIMIT else SAFE_LINE for v in values]

    # Fix x-axis to the global max so bars don't jump between years
    global_max = max(_to_ug(v) for vals in pollution.values() for v in vals)

    y_pos = np.arange(len(countries))
    bars  = ax.barh(y_pos, values, color=colors, edgecolor="none", height=0.65)

    # Value labels
    for bar, val in zip(bars, values):
        ax.text(
            val + global_max * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}", va="center", ha="left",
            color=TEXT, fontsize=7, fontfamily="Courier New"
        )

    # WHO guideline
    ax.axvline(WHO_LIMIT, color=SAFE_LINE, linewidth=1.5,
               linestyle="--", label=f"WHO limit ({WHO_LIMIT} µg/m³)")
    ax.legend(fontsize=8, facecolor=SURFACE, edgecolor=GRID,
              labelcolor=TEXT, loc="lower right")

    ax.set_xlim(0, global_max * 1.15)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(countries, fontsize=8, color=TEXT, fontfamily="Courier New")
    ax.invert_yaxis()
    ax.set_xlabel("PM2.5 Exposure (µg/m³)", color=TEXT, fontsize=9)
    ax.set_title(
        f"Top {TOP_N} Countries by PM2.5 Exposure — {YEARS[year_idx]}",
        color=TEXT, fontsize=11, fontfamily="Courier New", pad=10
    )


def plot_country_timeseries(pollution: dict, country: str, ax, fig):
    """
    Time-series line chart: PM2.5 exposure for a single country over 2003–2018.
    Annotates first and last data points, draws WHO guideline.
    """
    ax.cla()
    ax.set_facecolor(SURFACE)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)
    ax.grid(color=GRID, linestyle="--", linewidth=0.6, alpha=0.7)
    ax.tick_params(colors=SUBTEXT, labelsize=8)

    values = [_to_ug(v) for v in pollution[country]]
    color  = ACCENT if values[-1] > WHO_LIMIT else SAFE_LINE

    ax.plot(YEARS, values, color=color, linewidth=2.2, marker="o",
            markersize=4, markerfacecolor=BG, markeredgecolor=color)
    ax.fill_between(YEARS, values, alpha=0.12, color=color)

    # Annotate first and last
    for idx, label in [(0, str(YEARS[0])), (-1, str(YEARS[-1]))]:
        ax.annotate(
            f"{values[idx]:.1f} µg/m³",
            xy=(YEARS[idx], values[idx]),
            xytext=(8, 6), textcoords="offset points",
            color=TEXT, fontsize=8, fontfamily="Courier New"
        )

    ax.axhline(WHO_LIMIT, color=SAFE_LINE, linewidth=1.3, linestyle="--",
               label=f"WHO limit ({WHO_LIMIT} µg/m³)")
    ax.legend(fontsize=8, facecolor=SURFACE, edgecolor=GRID, labelcolor=TEXT)

    ax.set_xlabel("Year", color=TEXT, fontsize=9)
    ax.set_ylabel("PM2.5 Exposure (µg/m³)", color=TEXT, fontsize=9)
    ax.set_title(f"PM2.5 Trend — {country}", color=TEXT,
                 fontsize=11, fontfamily="Courier New", pad=10)
    ax.set_xticks(YEARS)
    ax.set_xticklabels([str(y) for y in YEARS], rotation=45, fontsize=7, color=SUBTEXT)
    ax.yaxis.label.set_color(TEXT)


def plot_population_scatter(pollution: dict, pop: dict, ax, fig, year_idx: int = -1):
    """
    Scatter plot: population vs PM2.5 exposure for a given year index.
    year_idx maps into each country's data list (0 = 2003, -1 = 2018).
    Point size scales with population. High-risk countries are labelled.
    Returns the PathCollection so the caller can wire pick events.
    """
    ax.cla()
    ax.set_facecolor(SURFACE)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)
    ax.grid(color=GRID, linestyle="--", linewidth=0.6, alpha=0.7)
    ax.tick_params(colors=SUBTEXT, labelsize=8)

    countries = list(pop.keys())
    pm_vals   = [_to_ug(pollution[c][year_idx]) for c in countries]
    pop_vals  = [pop[c][year_idx] * 10_000 for c in countries]

    pm_arr  = np.array(pm_vals)
    pop_arr = np.array(pop_vals)

    global_max_pm  = max(_to_ug(v) for vals in pollution.values() for v in vals)
    global_max_pop = max(pop[c][i] * 10_000 for c in pop for i in range(len(YEARS)))
    global_min_pop = min(p for p in pop_arr if p > 0)

    sizes  = ((pop_arr / global_max_pop) ** 0.5) * 600 + 20
    colors = [ACCENT if p > WHO_LIMIT else SAFE_LINE for p in pm_vals]

    sc = ax.scatter(pop_arr, pm_arr, s=sizes, c=colors,
                    alpha=0.65, edgecolors="none", picker=6)

    ax.axhline(WHO_LIMIT, color=SAFE_LINE, linewidth=1.3, linestyle="--",
               label=f"WHO limit ({WHO_LIMIT} µg/m³)")

    pop_threshold = np.percentile(pop_arr, 75)
    for c, pm, pop_v in zip(countries, pm_vals, pop_arr):
        if pm > WHO_LIMIT and pop_v >= pop_threshold:
            ax.annotate(c, xy=(pop_v, pm), xytext=(5, 4),
                        textcoords="offset points",
                        color=TEXT, fontsize=7, fontfamily="Courier New")

    ax.set_xscale("log")
    ax.set_xlim(global_min_pop * 0.5, global_max_pop * 2)
    ax.set_ylim(0, global_max_pm * 1.1)
    ax.set_autoscale_on(False)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x/1e6:.0f}M" if x >= 1e6 else f"{x/1e3:.0f}K"
    ))
    ax.set_xlabel("Population (log scale)", color=TEXT, fontsize=9)
    ax.set_ylabel("PM2.5 Exposure (µg/m³)", color=TEXT, fontsize=9)
    ax.set_title(
        f"Population vs PM2.5 Exposure — {YEARS[year_idx]}  (dot size = population)",
        color=TEXT, fontsize=11, fontfamily="Courier New", pad=10
    )
    ax.legend(fontsize=8, facecolor=SURFACE, edgecolor=GRID, labelcolor=TEXT)

    # Attach metadata for pick-event lookup by the caller
    sc._countries = countries
    sc._pm_vals   = pm_vals
    sc._pop_vals  = pop_vals
    return sc

# ── Main App ───────────────────────────────────────────────────────────────────

class AirPollutionApp:
    def __init__(self, root: tk.Tk, pollution: dict, pop: dict):
        self.root      = root
        self.pollution = pollution
        self.pop       = pop
        self.countries = sorted(pollution.keys())
        self.gdf       = build_merged_geodataframe(pollution)

        root.title("Global Air Pollution Explorer")
        root.configure(bg=BG)
        root.geometry("1050x660")
        root.minsize(900, 580)

        self._build_ui()

    # ── Layout ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ──
        header = tk.Frame(self.root, bg=BG, pady=8)
        header.pack(fill=tk.X, padx=18)

        tk.Label(
            header, text="🌍  Global Air Pollution Explorer",
            bg=BG, fg=ACCENT, font=FONT_HEADER
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text="Population-weighted PM2.5 exposure  |  2003 – 2018",
            bg=BG, fg=SUBTEXT, font=FONT_SMALL
        ).pack(side=tk.LEFT, padx=16)

        # ── Tab notebook ──
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook",       background=BG,      borderwidth=0)
        style.configure("TNotebook.Tab",   background=SURFACE, foreground=SUBTEXT,
                        font=FONT_LABEL,   padding=[14, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", BG)])

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        build_tab_intro(notebook)
        self._build_tab_bar(notebook)
        self._build_tab_timeseries(notebook)
        self._build_tab_scatter(notebook)
        build_tab_map(notebook, self.gdf, self.root, self.pop)

    # ── Tab 1 – Bar chart ──────────────────────────────────────────────────────

    def _build_tab_bar(self, notebook):
        frame = tk.Frame(notebook, bg=BG)
        notebook.add(frame, text="  Top Countries  ")

        # ── Caption (updates with slider) ──
        self._bar_caption_var = tk.StringVar()
        tk.Label(frame, textvariable=self._bar_caption_var, bg=BG, fg=SUBTEXT,
                 font=FONT_SMALL, justify=tk.LEFT).pack(anchor=tk.W, padx=14, pady=(8, 0))

        # ── Slider row ──
        slider_row = tk.Frame(frame, bg=BG)
        slider_row.pack(fill=tk.X, padx=14, pady=(4, 2))

        tk.Label(slider_row, text="Year:", bg=BG, fg=TEXT,
                 font=FONT_LABEL).pack(side=tk.LEFT)

        self._bar_year_label = tk.Label(
            slider_row, text=str(YEARS[-1]),
            bg=BG, fg=ACCENT, font=FONT_LABEL, width=5
        )
        self._bar_year_label.pack(side=tk.LEFT, padx=(4, 8))

        self._bar_slider = tk.Scale(
            slider_row,
            from_=0, to=len(YEARS) - 1,
            orient=tk.HORIZONTAL,
            command=self._on_bar_slider,
            bg=BG, fg=TEXT, troughcolor=SURFACE,
            activebackground=ACCENT, highlightthickness=0,
            sliderlength=18, length=400,
            showvalue=False, bd=0
        )
        self._bar_slider.set(len(YEARS) - 1)   # start at 2018
        self._bar_slider.pack(side=tk.LEFT)

        # ── Chart ──
        self._bar_fig, self._bar_ax = _styled_fig(figsize=(9, 5.2))
        self._bar_canvas = _embed(self._bar_fig, frame)

        # Draw initial state (2018)
        self._on_bar_slider(len(YEARS) - 1)

    def _on_bar_slider(self, val):
        idx  = int(val)
        year = YEARS[idx]
        self._bar_year_label.config(text=str(year))
        self._bar_caption_var.set(
            f"Countries ranked by population-weighted PM2.5 exposure in {year}.  "
            f"Red bars exceed the WHO annual guideline of {WHO_LIMIT} µg/m³."
        )
        plot_top_countries_bar(self.pollution, self._bar_ax, self._bar_fig, year_idx=idx)
        self._bar_canvas.draw_idle()

    # ── Tab 2 – Time series ────────────────────────────────────────────────────

    def _build_tab_timeseries(self, notebook):
        frame = tk.Frame(notebook, bg=BG)
        notebook.add(frame, text="  Country Trend  ")

        # Controls row
        ctrl = tk.Frame(frame, bg=BG)
        ctrl.pack(fill=tk.X, padx=14, pady=8)

        tk.Label(ctrl, text="Select country:", bg=BG, fg=TEXT,
                 font=FONT_LABEL).pack(side=tk.LEFT)

        self._ts_var = tk.StringVar(value=self.countries[0])
        combo = ttk.Combobox(
            ctrl, textvariable=self._ts_var,
            values=self.countries, state="readonly", width=30,
            font=FONT_LABEL
        )
        combo.pack(side=tk.LEFT, padx=8)

        style = ttk.Style()
        style.configure("TCombobox", fieldbackground=SURFACE,
                        background=SURFACE, foreground=TEXT,
                        selectbackground=ACCENT, font=FONT_LABEL)

        tk.Button(
            ctrl, text="Update Chart →",
            command=self._refresh_timeseries,
            bg=ACCENT, fg=BG, font=FONT_LABEL,
            relief=tk.FLAT, padx=10, cursor="hand2"
        ).pack(side=tk.LEFT, padx=4)

        caption = "Shows how annual PM2.5 exposure has changed over time for the selected country."
        tk.Label(frame, text=caption, bg=BG, fg=SUBTEXT,
                 font=FONT_SMALL, justify=tk.LEFT).pack(anchor=tk.W, padx=14)

        # Chart area
        self._ts_fig, self._ts_ax = _styled_fig(figsize=(9, 5))
        plot_country_timeseries(self.pollution, self.countries[0],
                                self._ts_ax, self._ts_fig)
        self._ts_canvas = _embed(self._ts_fig, frame)

    def _refresh_timeseries(self):
        country = self._ts_var.get()
        plot_country_timeseries(self.pollution, country,
                                self._ts_ax, self._ts_fig)
        self._ts_canvas.draw()

    # ── Tab 3 – Scatter plot ───────────────────────────────────────────────────

    def _build_tab_scatter(self, notebook):
        frame = tk.Frame(notebook, bg=BG)
        notebook.add(frame, text="  Population vs Exposure  ")

        self._sc_pinned_country = None   # track which dot is pinned

        # ── Caption ──
        self._sc_caption_var = tk.StringVar()
        tk.Label(frame, textvariable=self._sc_caption_var, bg=BG, fg=SUBTEXT,
                font=FONT_SMALL, justify=tk.LEFT).pack(anchor=tk.W, padx=14, pady=(8, 0))

        # ── Slider row ──
        slider_row = tk.Frame(frame, bg=BG)
        slider_row.pack(fill=tk.X, padx=14, pady=(4, 2))

        tk.Label(slider_row, text="Year:", bg=BG, fg=TEXT,
                font=FONT_LABEL).pack(side=tk.LEFT)

        self._sc_year_label = tk.Label(slider_row, text=str(YEARS[-1]),
                                    bg=BG, fg=ACCENT, font=FONT_LABEL, width=5)
        self._sc_year_label.pack(side=tk.LEFT, padx=(4, 8))

        self._sc_slider = tk.Scale(
            slider_row, from_=0, to=len(YEARS) - 1, orient=tk.HORIZONTAL,
            command=self._on_scatter_slider,
            bg=BG, fg=TEXT, troughcolor=SURFACE,
            activebackground=ACCENT, highlightthickness=0,
            sliderlength=18, length=400, showvalue=False, bd=0
        )
        self._sc_slider.set(len(YEARS) - 1)
        self._sc_slider.pack(side=tk.LEFT)

        # ── Body: chart + info panel side by side ──
        body = tk.Frame(frame, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 8))

        # Chart (left, expands)
        chart_frame = tk.Frame(body, bg=BG)
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._sc_fig, self._sc_ax = _styled_fig(figsize=(7.5, 5.2))
        self._sc_canvas = FigureCanvasTkAgg(self._sc_fig, master=chart_frame)
        self._sc_canvas.draw()
        self._sc_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Info panel (right, fixed width)
        panel = tk.Frame(body, bg=SURFACE, width=190, padx=14, pady=14)
        panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        panel.pack_propagate(False)

        tk.Label(panel, text="SELECTED COUNTRY", bg=SURFACE, fg=SUBTEXT,
                font=("Courier New", 8)).pack(anchor=tk.W)

        self._sc_info_name = tk.Label(panel, text="—", bg=SURFACE, fg=TEXT,
                                    font=("Courier New", 13, "bold"),
                                    wraplength=160, justify=tk.LEFT)
        self._sc_info_name.pack(anchor=tk.W, pady=(4, 12))

        for attr, label in [
            ("_sc_info_pm_lbl",  "PM2.5 EXPOSURE"),
            ("_sc_info_pm",      "—"),
            ("_sc_info_pop_lbl", "POPULATION"),
            ("_sc_info_pop",     "—"),
            ("_sc_info_who_lbl", "WHO STATUS"),
            ("_sc_info_who",     "—"),
        ]:
            is_header = attr.endswith("_lbl")
            lbl = tk.Label(
                panel,
                text=label,
                bg=SURFACE,
                fg=SUBTEXT if is_header else TEXT,
                font=("Courier New", 8 if is_header else 11,
                    "normal" if is_header else "bold"),
                justify=tk.LEFT,
            )
            lbl.pack(anchor=tk.W, pady=(6 if is_header else 0, 0))
            setattr(self, attr, lbl)

        tk.Label(panel, text="Click a dot to pin details.\nClick again to dismiss.",
                bg=SURFACE, fg=SUBTEXT, font=("Courier New", 8),
                justify=tk.LEFT, wraplength=160).pack(anchor=tk.W, pady=(20, 0))

        # Draw initial frame and wire pick event
        self._on_scatter_slider(len(YEARS) - 1)


    def _on_scatter_slider(self, val):
        idx  = int(val)
        year = YEARS[idx]
        self._sc_year_label.config(text=str(year))
        self._sc_caption_var.set(
            f"Each dot is a country in {year}. Dot size reflects population.  "
            f"Red = above WHO limit. Click a dot to pin its details."
        )

        # Disconnect old pick handler before redrawing
        if hasattr(self, "_sc_pick_cid") and self._sc_pick_cid:
            self._sc_fig.canvas.mpl_disconnect(self._sc_pick_cid)

        sc = plot_population_scatter(self.pollution, self.pop,
                             self._sc_ax, self._sc_fig, year_idx=idx)
        self._sc_scatter_obj = sc
        self._sc_year_idx    = idx

        # Re-wire pick event
        self._sc_pick_cid = self._sc_fig.canvas.mpl_connect(
            "pick_event", self._on_scatter_pick
        )

        # Re-highlight pinned dot if it still exists in new year
        if self._sc_pinned_country:
            self._highlight_pinned(self._sc_pinned_country)
            self._update_info_panel(self._sc_pinned_country, idx)

        self._sc_canvas.draw_idle()


    def _on_scatter_pick(self, event):
        if event.artist is not self._sc_scatter_obj:
            return
        if not event.ind:
            return

        # Nearest dot by index
        idx_in_data = event.ind[0]
        sc          = self._sc_scatter_obj
        country     = sc._countries[idx_in_data]

        if self._sc_pinned_country == country:
            # Same dot clicked → dismiss
            self._sc_pinned_country = None
            self._clear_info_panel()
            self._reset_dot_colors()
        else:
            # New dot clicked → pin it
            self._sc_pinned_country = country
            self._highlight_pinned(country)
            self._update_info_panel(country, self._sc_year_idx)

        self._sc_canvas.draw_idle()


    def _highlight_pinned(self, country: str):
        """Dim all dots; make the pinned dot full-opacity with a white ring."""
        sc        = self._sc_scatter_obj
        countries = sc._countries
        pm_vals   = sc._pm_vals

        base_colors  = [ACCENT if p > WHO_LIMIT else SAFE_LINE for p in pm_vals]
        alphas       = [1.0 if c == country else 0.18 for c in countries]
        edges        = ["white" if c == country else "none" for c in countries]
        linewidths   = [1.8 if c == country else 0.0 for c in countries]

        sc.set_facecolor([(*mcolors.to_rgb(base_colors[i]), alphas[i])
                        for i in range(len(countries))])
        sc.set_edgecolor(edges)
        sc.set_linewidth(linewidths)


    def _reset_dot_colors(self):
        sc      = self._sc_scatter_obj
        pm_vals = sc._pm_vals
        colors  = [ACCENT if p > WHO_LIMIT else SAFE_LINE for p in pm_vals]
        sc.set_facecolor([(*mcolors.to_rgb(c), 0.65) for c in colors])
        sc.set_edgecolor("none")
        sc.set_linewidth(0)


    def _update_info_panel(self, country: str, year_idx: int):
        pm  = self._sc_scatter_obj._pm_vals[
            self._sc_scatter_obj._countries.index(country)
        ]
        pop = self._sc_scatter_obj._pop_vals[
            self._sc_scatter_obj._countries.index(country)
        ]
        who_ok  = pm <= WHO_LIMIT
        who_txt = "✓ Below limit" if who_ok else "✗ Exceeds limit"
        who_col = SAFE_LINE if who_ok else ACCENT

        self._sc_info_name.config(text=country)
        self._sc_info_pm.config(text=f"{pm:.2f} µg/m³")
        self._sc_info_pop.config(text=f"{pop/1e6:.2f}M" if pop >= 1e6
                                else f"{pop/1e3:.1f}K")
        self._sc_info_who.config(text=who_txt, fg=who_col)


    def _clear_info_panel(self):
        self._sc_info_name.config(text="—")
        self._sc_info_pm.config(text="—")
        self._sc_info_pop.config(text="—")
        self._sc_info_who.config(text="—", fg=TEXT)


# ── Entry point ────────────────────────────────────────────────────────────────

def launch(pollution: dict, pop: dict):
    """
    Call this from your main script after loading data:

        from visualizer import launch
        launch(pollution, pop)
    """
    root = tk.Tk()
    AirPollutionApp(root, pollution, pop)
    root.mainloop()
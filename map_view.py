"""
map_view.py
-----------
Rendering and UI for the world map tab.
Imports from map_data and map_player; no knowledge of other visualizer tabs.
 
Public API
----------
build_tab_map(notebook, gdf, root)
    Builds the full "World Map" tab and wires up MapPlayer.
    Call from AirPollutionApp._build_ui().
 
render_map_frame(gdf, year_idx, ax, fig, canvas)
    Draws one year's choropleth onto the given axes.
    Called by MapPlayer's on_frame_change callback.
"""
 
import tkinter as tk
from tkinter import ttk
 
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as mcm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import pandas as pd
 
from map_data import YEARS
from map_player import MapPlayer
 
# ── Theme (mirrors visualizer.py constants) ────────────────────────────────────
 
BG        = "#0f1117"
SURFACE   = "#1a1d27"
ACCENT    = "#e8614d"
TEXT      = "#e8e8e8"
SUBTEXT   = "#8b8fa8"
GRID      = "#2a2d3a"
SAFE_LINE = "#4caf84"
 
FONT_LABEL  = ("Courier New", 10)
FONT_SMALL  = ("Courier New", 9)
FONT_LARGE  = ("Courier New", 14, "bold")
 
# ── Colour scale ───────────────────────────────────────────────────────────────
 
WHO_LIMIT  = 5.0    # µg/m³ — colour scale anchor
VMAX       = 75.0   # µg/m³ — cap (≈15× WHO); anything above maps to deepest red
 
NO_DATA_COLOR   = "#2a2d3a"   # countries with no pollution data
BELOW_WHO_COLOR = "#3d4052"   # countries below the WHO limit
 
# Absolute mode: gray → rose → crimson
_CMAP_ABS  = mcolors.LinearSegmentedColormap.from_list(
    "pm_risk",
    ["#7a3a3a", "#c0392b", "#8b0000"],
)
_NORM_ABS  = mcolors.LogNorm(vmin=WHO_LIMIT, vmax=VMAX)
 
# Delta mode: blue (improving) → white (flat) → red (worsening)
_DELTA_MAX = 20.0   # µg/m³ — symmetric cap; beyond ±20 maps to deepest colour
_CMAP_DELTA = mcolors.LinearSegmentedColormap.from_list(
    "pm_delta",
    ["#2166ac", "#92c5de", "#f7f7f7", "#f4a582", "#b2182b"],
)
_NORM_DELTA = mcolors.TwoSlopeNorm(vmin=-_DELTA_MAX, vcenter=0, vmax=_DELTA_MAX)
 
 
# ── Rendering ──────────────────────────────────────────────────────────────────
 
def render_map_frame(gdf, year_idx: int, ax, fig, canvas, cbar_ax, mode: str = "absolute"):
    """
    Dispatch to the correct render function based on mode.
 
    Parameters
    ----------
    mode : "absolute" | "delta"
    """
    if mode == "delta":
        _render_delta(gdf, year_idx, ax, fig, canvas, cbar_ax)
    else:
        _render_absolute(gdf, year_idx, ax, fig, canvas, cbar_ax)
 
 
def _render_absolute(gdf, year_idx, ax, fig, canvas, cbar_ax):
    """Choropleth of raw PM2.5 exposure relative to the WHO limit."""
    year  = YEARS[year_idx]
    frame = gdf[gdf["year"] == year].copy()
 
    ax.cla()
    ax.set_facecolor(BG)
    ax.set_axis_off()
 
    no_data = frame[frame["pm_ug"].isna()]
    below   = frame[frame["pm_ug"].notna() & (frame["pm_ug"] <= WHO_LIMIT)]
    above   = frame[frame["pm_ug"].notna() & (frame["pm_ug"] >  WHO_LIMIT)]
 
    if not no_data.empty:
        no_data.plot(ax=ax, color=NO_DATA_COLOR, edgecolor=BG, linewidth=0.3)
    if not below.empty:
        below.plot(ax=ax, color=BELOW_WHO_COLOR, edgecolor=BG, linewidth=0.3)
    if not above.empty:
        above = above.copy()
        above["pm_capped"] = above["pm_ug"].clip(upper=VMAX)
        above.plot(ax=ax, column="pm_capped", cmap=_CMAP_ABS,
                   norm=_NORM_ABS, edgecolor=BG, linewidth=0.3)
 
    _draw_colorbar(fig, cbar_ax, _CMAP_ABS, _NORM_ABS,
                   ticks=[WHO_LIMIT, 10, 20, 40, VMAX],
                   tick_labels=[f"{v/WHO_LIMIT:.0f}× WHO" for v in [WHO_LIMIT, 10, 20, 40, VMAX]],
                   label="PM2.5 vs WHO limit")
    _draw_watermark(ax, year)
    canvas.draw_idle()
 
 
def _render_delta(gdf, year_idx, ax, fig, canvas, cbar_ax):
    """Choropleth of PM2.5 change in µg/m³ relative to the 2003 baseline."""
    year     = YEARS[year_idx]
    baseline = gdf[gdf["year"] == YEARS[0]][["name", "pm_ug"]].rename(
        columns={"pm_ug": "pm_base"}
    )
    frame = gdf[gdf["year"] == year].copy()
    frame = frame.merge(baseline, on="name", how="left")
    frame["delta"] = frame["pm_ug"] - frame["pm_base"]
 
    ax.cla()
    ax.set_facecolor(BG)
    ax.set_axis_off()
 
    no_data = frame[frame["delta"].isna()]
    has_data = frame[frame["delta"].notna()].copy()
 
    if not no_data.empty:
        no_data.plot(ax=ax, color=NO_DATA_COLOR, edgecolor=BG, linewidth=0.3)
    if not has_data.empty:
        has_data["delta_capped"] = has_data["delta"].clip(
            lower=-_DELTA_MAX, upper=_DELTA_MAX
        )
        has_data.plot(ax=ax, column="delta_capped", cmap=_CMAP_DELTA,
                      norm=_NORM_DELTA, edgecolor=BG, linewidth=0.3)
 
    tick_vals   = [-_DELTA_MAX, -10, 0, 10, _DELTA_MAX]
    tick_labels = [f"{v:+.0f} µg/m³" for v in tick_vals]
    _draw_colorbar(fig, cbar_ax, _CMAP_DELTA, _NORM_DELTA,
                   ticks=tick_vals, tick_labels=tick_labels,
                   label="Change since 2003")
    _draw_watermark(ax, year)
    canvas.draw_idle()
 
 
def _draw_colorbar(fig, cbar_ax, cmap, norm, ticks, tick_labels, label):
    cbar_ax.cla()
    sm = mcm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax)
    cbar.ax.yaxis.set_tick_params(color=SUBTEXT, labelsize=7)
    cbar.outline.set_edgecolor(GRID)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=SUBTEXT, fontfamily="Courier New")
    cbar.set_ticks(ticks)
    cbar.set_ticklabels(tick_labels)
    cbar.set_label(label, color=SUBTEXT, fontsize=8, fontfamily="Courier New")
 
 
def _draw_watermark(ax, year: int):
    ax.text(
        0.97, 0.05, str(year),
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=36, fontfamily="Courier New", fontweight="bold",
        color=TEXT, alpha=0.15,
    )
 
 
# ── Tab builder ────────────────────────────────────────────────────────────────
 
def build_tab_map(notebook, gdf, root, pop: dict):
    """
    Build the World Map tab and attach it to notebook.

    Parameters
    ----------
    notebook : ttk.Notebook
    gdf      : merged GeoDataFrame from map_data.build_merged_geodataframe()
    root     : tk.Tk root window (needed by MapPlayer for root.after scheduling)
    pop      : dict[str, list[float]] — population per 10,000 people, 2003–2018
    """

    
    frame = tk.Frame(notebook, bg=BG)
    notebook.add(frame, text="  World Map  ")
    notebook.bind("<<NotebookTabChanged>>", lambda e: _hide_popup())

    # ── Caption ───────────────────────────────────────────────────────────────
    caption_var = tk.StringVar(value=(
        "Colour intensity shows how far above the WHO PM2.5 limit each country is.  "
        "Dark gray = below the limit or no data."
    ))
    tk.Label(frame, textvariable=caption_var, bg=BG, fg=SUBTEXT,
             font=FONT_SMALL, justify=tk.LEFT).pack(anchor=tk.W, padx=14, pady=(8, 0))

    # ── Figure ────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(10, 5.0), facecolor=BG)
    ax      = fig.add_axes([0.02, 0.02, 0.88, 0.96])
    cbar_ax = fig.add_axes([0.91, 0.15, 0.02, 0.70])
    ax.set_facecolor(BG)
    ax.set_axis_off()
    cbar_ax.set_facecolor(BG)

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ── Popup (Tkinter Toplevel, hidden until a country is clicked) ───────────
    popup = tk.Toplevel(root)
    popup.withdraw()
    popup.overrideredirect(True)          # no title bar / border
    popup.configure(bg=SURFACE)
    popup.attributes("-topmost", True)

    # Thin coloured border via a 1-px frame wrapper
    border = tk.Frame(popup, bg=GRID, padx=1, pady=1)
    border.pack(fill=tk.BOTH, expand=True)

    inner = tk.Frame(border, bg=SURFACE, padx=12, pady=10)
    inner.pack(fill=tk.BOTH, expand=True)

    _lbl = dict(bg=SURFACE, justify=tk.LEFT, fontfamily="Courier New")

    popup_country = tk.Label(inner, text="", fg=TEXT,
                             font=("Courier New", 11, "bold"), **{k: v for k, v in _lbl.items() if k != "fontfamily"})
    popup_country.pack(anchor=tk.W)

    popup_year = tk.Label(inner, text="", fg=SUBTEXT,
                          font=("Courier New", 8), bg=SURFACE)
    popup_year.pack(anchor=tk.W, pady=(0, 6))

    def _row(header: str):
        tk.Label(inner, text=header, fg=SUBTEXT,
                 font=("Courier New", 7), bg=SURFACE).pack(anchor=tk.W, pady=(4, 0))
        val = tk.Label(inner, text="", fg=TEXT,
                       font=("Courier New", 10, "bold"), bg=SURFACE)
        val.pack(anchor=tk.W)
        return val

    popup_pm   = _row("PM2.5 EXPOSURE")
    popup_who  = _row("WHO STATUS")
    popup_delta = _row("CHANGE SINCE 2003")
    popup_pop  = _row("POPULATION")

    # ── Shared mutable state ──────────────────────────────────────────────────
    state = {
        "pinned_country": None,
        "year_idx":       len(YEARS) - 1,
        "mode":           "absolute",
    }

    def _show_popup(country: str, year_idx: int, x_root: int, y_root: int):
        """Populate and position the popup near the click."""
        year = YEARS[year_idx]
        row  = gdf[(gdf["name"] == country) & (gdf["year"] == year)]
        if row.empty:
            return

        pm_ug = row["pm_ug"].values[0]

        # Delta vs 2003 baseline
        base_row = gdf[(gdf["name"] == country) & (gdf["year"] == YEARS[0])]
        if not base_row.empty and not base_row["pm_ug"].isna().values[0]:
            delta     = pm_ug - base_row["pm_ug"].values[0]
            delta_txt = f"{delta:+.2f} µg/m³"
            delta_col = "#2166ac" if delta < 0 else ACCENT
        else:
            delta_txt = "N/A"
            delta_col = SUBTEXT

        # Population (look up by matching name in pop dict, tolerating slight mismatches)
        pop_val = None
        for k in pop:
            if k.strip().lower() == country.strip().lower():
                raw = pop[k][year_idx]
                pop_val = raw * 10_000   # back to raw people
                break
        pop_txt = (
            f"{pop_val/1e6:.2f} M" if pop_val and pop_val >= 1e6
            else f"{pop_val/1e3:.1f} K" if pop_val
            else "N/A"
        )

        # WHO status
        if pd.isna(pm_ug):
            pm_txt  = "No data"
            who_txt = "N/A"
            who_col = SUBTEXT
        else:
            pm_txt  = f"{pm_ug:.2f} µg/m³"
            who_ok  = pm_ug <= WHO_LIMIT
            who_txt = "✓ Below limit" if who_ok else "✗ Exceeds limit"
            who_col = SAFE_LINE if who_ok else ACCENT

        popup_country.config(text=country)
        popup_year.config(text=f"Year: {year}")
        popup_pm.config(text=pm_txt)
        popup_who.config(text=who_txt, fg=who_col)
        popup_delta.config(text=delta_txt, fg=delta_col)
        popup_pop.config(text=pop_txt)

        # Position near click, nudge so it doesn't sit under the cursor
        popup.update_idletasks()
        w = popup.winfo_reqwidth()
        h = popup.winfo_reqheight()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        # Flip left/up if too close to screen edge
        px = x_root + 14 if x_root + 14 + w < sw else x_root - w - 14
        py = y_root + 14 if y_root + 14 + h < sh else y_root - h - 14
        popup.geometry(f"+{px}+{py}")
        popup.deiconify()
        popup.lift()

    def _hide_popup():
        state["pinned_country"] = None
        popup.withdraw()

    # ── Click handler ─────────────────────────────────────────────────────────
    def _on_map_click(event):
        if event.inaxes is not ax:
            _hide_popup()
            return
        if event.xdata is None or event.ydata is None:
            _hide_popup()
            return

        from shapely.geometry import Point
        click_pt = Point(event.xdata, event.ydata)
        year     = YEARS[state["year_idx"]]
        frame    = gdf[gdf["year"] == year].copy()

        hit = frame[frame.geometry.contains(click_pt)]
        if hit.empty:
            # Try nearest within a small buffer for thin countries
            frame["dist"] = frame.geometry.boundary.distance(click_pt)
            nearest = frame.nsmallest(1, "dist")
            if nearest["dist"].values[0] < 2.0:   # degrees tolerance
                hit = nearest
            else:
                _hide_popup()
                return

        country = hit["name"].values[0]

        if state["pinned_country"] == country:
            _hide_popup()
            return

        state["pinned_country"] = country
        x_root = canvas.get_tk_widget().winfo_rootx() + int(event.x)
        y_root = canvas.get_tk_widget().winfo_rooty() + int(
            canvas.get_tk_widget().winfo_height() - event.y
        )
        _show_popup(country, state["year_idx"], x_root, y_root)

    canvas.mpl_connect("button_press_event", _on_map_click)

    # ── Controls ──────────────────────────────────────────────────────────────
    ctrl_frame = tk.Frame(frame, bg=BG)
    ctrl_frame.pack(fill=tk.X, padx=14, pady=(4, 2))

    year_label = tk.Label(ctrl_frame, text=str(YEARS[0]),
                          bg=BG, fg=ACCENT, font=FONT_LARGE, width=5)

    slider_var = tk.IntVar(value=len(YEARS) - 1)
    mode       = tk.StringVar(value="absolute")

    def on_frame_change(year_idx: int):
        state["year_idx"] = year_idx
        year_label.config(text=str(YEARS[year_idx]))
        slider_var.set(year_idx)
        # Update popup if one is pinned
        if state["pinned_country"]:
            _update_pinned_popup()
        render_map_frame(gdf, year_idx, ax, fig, canvas, cbar_ax, mode.get())

    def _update_pinned_popup():
        """Refresh popup data for the current year without moving it."""
        country  = state["pinned_country"]
        year_idx = state["year_idx"]
        year     = YEARS[year_idx]
        row      = gdf[(gdf["name"] == country) & (gdf["year"] == year)]
        if row.empty:
            return

        pm_ug = row["pm_ug"].values[0]

        base_row = gdf[(gdf["name"] == country) & (gdf["year"] == YEARS[0])]
        if not base_row.empty and not base_row["pm_ug"].isna().values[0]:
            delta     = pm_ug - base_row["pm_ug"].values[0]
            delta_txt = f"{delta:+.2f} µg/m³"
            delta_col = "#2166ac" if delta < 0 else ACCENT
        else:
            delta_txt = "N/A"
            delta_col = SUBTEXT

        pop_val = None
        for k in pop:
            if k.strip().lower() == country.strip().lower():
                pop_val = pop[k][year_idx] * 10_000
                break
        pop_txt = (
            f"{pop_val/1e6:.2f} M" if pop_val and pop_val >= 1e6
            else f"{pop_val/1e3:.1f} K" if pop_val
            else "N/A"
        )

        if pd.isna(pm_ug):
            pm_txt  = "No data"
            who_txt = "N/A"
            who_col = SUBTEXT
        else:
            pm_txt  = f"{pm_ug:.2f} µg/m³"
            who_ok  = pm_ug <= WHO_LIMIT
            who_txt = "✓ Below limit" if who_ok else "✗ Exceeds limit"
            who_col = SAFE_LINE if who_ok else ACCENT

        popup_year.config(text=f"Year: {year}")
        popup_pm.config(text=pm_txt)
        popup_who.config(text=who_txt, fg=who_col)
        popup_delta.config(text=delta_txt, fg=delta_col)
        popup_pop.config(text=pop_txt)

    player = MapPlayer(root, on_frame_change=on_frame_change, speed_ms=800)
    player.jump_to(len(YEARS) - 1)

    # ── Button row ────────────────────────────────────────────────────────────
    btn_cfg = dict(bg=SURFACE, fg=TEXT, font=("Courier New", 12),
                   relief=tk.FLAT, bd=0, padx=6, cursor="hand2",
                   activebackground=GRID, activeforeground=ACCENT)

    btn_row = tk.Frame(ctrl_frame, bg=BG)
    btn_row.pack(side=tk.LEFT)

    tk.Button(btn_row, text="⏮", command=lambda: player.jump_to(0),
              **btn_cfg).pack(side=tk.LEFT, padx=2)
    tk.Button(btn_row, text="⏪", command=player.step_back,
              **btn_cfg).pack(side=tk.LEFT, padx=2)

    play_btn = tk.Button(btn_row, text="▶", command=player.toggle, **btn_cfg)
    play_btn.pack(side=tk.LEFT, padx=2)

    tk.Button(btn_row, text="⏩", command=player.step_forward,
              **btn_cfg).pack(side=tk.LEFT, padx=2)
    tk.Button(btn_row, text="⏭", command=lambda: player.jump_to(len(YEARS) - 1),
              **btn_cfg).pack(side=tk.LEFT, padx=2)

    player.on_play_state_change = lambda playing: play_btn.config(
        text="⏸" if playing else "▶"
    )

    year_label.pack(side=tk.LEFT, padx=(16, 0))

    # ── Mode toggle ───────────────────────────────────────────────────────────
    _CAPTIONS = {
        "absolute": (
            "Colour intensity shows how far above the WHO PM2.5 limit each country is.  "
            "Dark gray = below the limit or no data."
        ),
        "delta": (
            "Blue = improving since 2003 · White = unchanged · Red = worsening.  "
            "Intensity shows magnitude of change in µg/m³."
        ),
    }

    def toggle_mode():
        new_mode = "delta" if mode.get() == "absolute" else "absolute"
        mode.set(new_mode)
        state["mode"] = new_mode
        mode_btn.config(
            text="Mode: Absolute" if new_mode == "absolute" else "Mode: Δ since 2003",
            fg=BG if new_mode == "absolute" else ACCENT,
            bg=ACCENT if new_mode == "absolute" else SURFACE,
        )
        caption_var.set(_CAPTIONS[new_mode])
        on_frame_change(player._year_idx)

    mode_btn = tk.Button(
        ctrl_frame, text="Mode: Absolute",
        command=toggle_mode,
        bg=ACCENT, fg=BG, font=FONT_LABEL,
        relief=tk.FLAT, padx=10, cursor="hand2",
        activebackground=GRID, activeforeground=TEXT,
    )
    mode_btn.pack(side=tk.RIGHT, padx=(0, 4))

    # ── Speed control ─────────────────────────────────────────────────────────
    speed_row = tk.Frame(ctrl_frame, bg=BG)
    speed_row.pack(side=tk.LEFT, padx=(24, 0))

    tk.Label(speed_row, text="Slow", bg=BG, fg=SUBTEXT,
             font=FONT_SMALL).pack(side=tk.LEFT)

    def on_speed(val):
        player.speed_ms = int(1500 - (int(val) / 100) * 1350)

    tk.Scale(
        speed_row, from_=0, to=100, orient=tk.HORIZONTAL,
        command=on_speed,
        bg=BG, fg=TEXT, troughcolor=SURFACE,
        activebackground=ACCENT, highlightthickness=0,
        sliderlength=14, length=120, showvalue=False, bd=0,
    ).pack(side=tk.LEFT, padx=4)

    tk.Label(speed_row, text="Fast", bg=BG, fg=SUBTEXT,
             font=FONT_SMALL).pack(side=tk.LEFT)

    # ── Year scrubber ─────────────────────────────────────────────────────────
    scrubber_row = tk.Frame(frame, bg=BG)
    scrubber_row.pack(fill=tk.X, padx=14, pady=(0, 6))

    tk.Label(scrubber_row, text=str(YEARS[0]), bg=BG, fg=SUBTEXT,
             font=FONT_SMALL).pack(side=tk.LEFT)

    def on_scrub(val):
        player.pause()
        player.jump_to(int(val))

    tk.Scale(
        scrubber_row, variable=slider_var,
        from_=0, to=len(YEARS) - 1,
        orient=tk.HORIZONTAL, command=on_scrub,
        bg=BG, fg=TEXT, troughcolor=SURFACE,
        activebackground=ACCENT, highlightthickness=0,
        sliderlength=18, showvalue=False, bd=0,
    ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

    tk.Label(scrubber_row, text=str(YEARS[-1]), bg=BG, fg=SUBTEXT,
             font=FONT_SMALL).pack(side=tk.LEFT)

    # Draw initial frame
    render_map_frame(gdf, len(YEARS) - 1, ax, fig, canvas, cbar_ax, mode.get())
 
    # ── Speed control ─────────────────────────────────────────────────────────
    speed_row = tk.Frame(ctrl_frame, bg=BG)
    speed_row.pack(side=tk.LEFT, padx=(24, 0))
 
    tk.Label(speed_row, text="Slow", bg=BG, fg=SUBTEXT,
             font=FONT_SMALL).pack(side=tk.LEFT)
 
    def on_speed(val):
        # Slider left = slow (1500 ms), right = fast (150 ms)
        player.speed_ms = int(1500 - (int(val) / 100) * 1350)
 
    tk.Scale(
        speed_row, from_=0, to=100, orient=tk.HORIZONTAL,
        command=on_speed,
        bg=BG, fg=TEXT, troughcolor=SURFACE,
        activebackground=ACCENT, highlightthickness=0,
        sliderlength=14, length=120, showvalue=False, bd=0,
    ).pack(side=tk.LEFT, padx=4)
 
    tk.Label(speed_row, text="Fast", bg=BG, fg=SUBTEXT,
             font=FONT_SMALL).pack(side=tk.LEFT)
    
    # Draw initial frame
    render_map_frame(gdf, len(YEARS) - 1, ax, fig, canvas, cbar_ax, mode.get())
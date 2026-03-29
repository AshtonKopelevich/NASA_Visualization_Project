"""
intro_view.py
-------------
Intro / About tab for the Air Pollution Explorer.
No data processing — pure static UI.

Public API
----------
build_tab_intro(notebook)
    Builds the intro tab and inserts it at position 0 in the notebook.
"""

import tkinter as tk
from tkinter import ttk
import webbrowser

# ── Theme (mirrors visualizer.py constants) ────────────────────────────────────

BG       = "#0f1117"
SURFACE  = "#1a1d27"
ACCENT   = "#e8614d"
ACCENT2  = "#f0a500"
TEXT     = "#e8e8e8"
SUBTEXT  = "#8b8fa8"
GRID     = "#2a2d3a"
SAFE     = "#4caf84"

FONT_HEADER  = ("Courier New", 18, "bold")
FONT_SECTION = ("Courier New", 12, "bold")
FONT_BODY    = ("Courier New", 10)
FONT_SMALL   = ("Courier New", 9)
FONT_LINK    = ("Courier New", 9, "underline")

# ── Health risk table data ─────────────────────────────────────────────────────

HEALTH_TABLE = [
    ("PM2.5 Level",        "Air Quality",   "Potential Health Effects"),
    ("0 – 5 µg/m³",        "✓  Safe",        "Little to no risk. WHO annual guideline met."),
    ("5 – 15 µg/m³",       "⚠  Moderate",    "Minor irritation for sensitive groups (asthma, elderly)."),
    ("15 – 35 µg/m³",      "⚠  Unhealthy",   "Increased risk of respiratory and cardiovascular stress."),
    ("35 – 55 µg/m³",      "✗  Very Unhealthy", "Significant aggravation of heart and lung disease."),
    ("55 – 75 µg/m³",      "✗  Hazardous",   "Serious risk for everyone; emergency conditions likely."),
    ("75 µg/m³ +",         "✗  Severe",      "Premature death risk; linked to lung cancer and stroke."),
]

COL_WIDTHS  = (18, 18, 52)
ROW_COLORS  = [SURFACE, GRID]          # alternating row bg
HEADER_FG   = [TEXT, SAFE, ACCENT]     # per-column header colour

# ── Links ──────────────────────────────────────────────────────────────────────

LINKS = [
    (
        "WHO Air Quality Guidelines",
        "https://www.who.int/news-room/fact-sheets/detail/ambient-(outdoor)-air-quality-and-health",
        "The global standard this dashboard uses as its safety benchmark.",
    ),
    (
        "NASA SEDAC — Source Dataset",
        "https://search.earthdata.nasa.gov/search/granules?p=C3540917642-ESDIS&pg[0][v]=f&pg[0][gsk]=-start_date&lat=10.779086780684333&long=-6.232911688088495&zoom=2.666666666666667",
        "The population-weighted PM2.5 dataset (2003–2018) powering this tool.",
    ),
    (
        "Health Effects Institute (HEI)",
        "https://www.healtheffects.org",
        "Independent research on the health impacts of air pollution worldwide.",
    ),
]


# ── Tab builder ────────────────────────────────────────────────────────────────

def build_tab_intro(notebook):
    """
    Build the intro tab and insert it at index 0 in the notebook.

    Parameters
    ----------
    notebook : ttk.Notebook
    """
    frame = tk.Frame(notebook, bg=BG)
    notebook.add(frame, text="  About  ")

    # Scrollable canvas so content is never clipped on small windows
    canvas = tk.Canvas(frame, bg=BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    content = tk.Frame(canvas, bg=BG)
    content_window = canvas.create_window((0, 0), window=content, anchor=tk.NW)

    def _on_resize(event):
        canvas.itemconfig(content_window, width=event.width)

    def _on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    canvas.bind("<Configure>", _on_resize)
    content.bind("<Configure>", _on_frame_configure)

    # Mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    pad = dict(padx=40, pady=6)

    # ── Hero ──────────────────────────────────────────────────────────────────
    tk.Frame(content, bg=ACCENT, height=3).pack(fill=tk.X)

    hero = tk.Frame(content, bg=BG, pady=24)
    hero.pack(fill=tk.X)

    tk.Label(
        hero,
        text="🌍  Global Air Pollution Explorer",
        bg=BG, fg=ACCENT, font=FONT_HEADER,
    ).pack(**pad, anchor=tk.W)

    tk.Label(
        hero,
        text="An interactive look at how PM2.5 air pollution has affected populations worldwide from 2003 to 2018.",
        bg=BG, fg=SUBTEXT, font=FONT_BODY, wraplength=800, justify=tk.LEFT,
    ).pack(**pad, anchor=tk.W)

    _divider(content)

    # ── What is PM2.5 ─────────────────────────────────────────────────────────
    _section(content, "What is PM2.5?")

    _body(content, (
        "PM2.5 refers to fine airborne particles smaller than 2.5 micrometres in diameter — "
        "roughly 30 times thinner than a human hair. These particles are produced by vehicle "
        "exhaust, industrial burning, wildfires, and the chemical reactions of gases in the "
        "atmosphere."
    ))
    _body(content, (
        "Because they are so small, PM2.5 particles bypass the nose and throat and travel "
        "deep into the lungs. From there, some particles even enter the bloodstream. This "
        "makes PM2.5 one of the most dangerous forms of air pollution — and the one most "
        "strongly linked to premature death worldwide."
    ))

    _divider(content)

    # ── Why it matters ────────────────────────────────────────────────────────
    _section(content, "Why Does It Matter?")

    _body(content, (
        "The World Health Organization estimates that air pollution causes around 7 million "
        "premature deaths every year. PM2.5 is the leading environmental health risk globally, "
        "contributing to heart disease, stroke, lung cancer, and chronic respiratory illness."
    ))
    _body(content, (
        "Exposure is not equal. Low- and middle-income countries — particularly in South Asia "
        "and sub-Saharan Africa — carry a disproportionate burden, often with PM2.5 levels "
        "ten to fifteen times above the WHO safe limit."
    ))

    _divider(content)

    # ── WHO guideline ─────────────────────────────────────────────────────────
    _section(content, "The WHO Guideline")

    who_frame = tk.Frame(content, bg=SURFACE, padx=18, pady=14)
    who_frame.pack(fill=tk.X, padx=40, pady=6)

    tk.Label(
        who_frame,
        text="5 µg/m³",
        bg=SURFACE, fg=SAFE, font=("Courier New", 22, "bold"),
    ).pack(anchor=tk.W)

    tk.Label(
        who_frame,
        text="WHO recommended annual mean PM2.5 limit (2021 guidelines)",
        bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL,
    ).pack(anchor=tk.W, pady=(2, 6))

    tk.Label(
        who_frame,
        text=(
            "In 2021 the WHO tightened its annual guideline from 10 µg/m³ to 5 µg/m³, "
            "reflecting new evidence on the health effects of long-term exposure. The data "
            "in this dashboard covers 2003–2018, so the 5 µg/m³ threshold is used throughout "
            "as the benchmark, even though it post-dates much of the data."
        ),
        bg=SURFACE, fg=TEXT, font=FONT_BODY, wraplength=780, justify=tk.LEFT,
    ).pack(anchor=tk.W)

    _divider(content)

    # ── Health risk table ─────────────────────────────────────────────────────
    _section(content, "PM2.5 Levels and Health Risk")

    _body(content, (
        "The table below summarises the health implications at different exposure levels. "
        "Values are annual averages; short-term spikes can cause harm at lower concentrations."
    ))

    _health_table(content)

    _divider(content)

    # ── About the data ────────────────────────────────────────────────────────
    _section(content, "About the Data")

    _body(content, (
    "This dashboard uses the NASA SEDAC 'Country Trends in Major Air Pollutants' dataset, "
    "which provides population-weighted annual PM2.5 exposure estimates for countries "
    "from 2003 to 2018. The underlying air quality data are derived from atmospheric "
    "reanalysis models that integrate satellite observations and ground-based measurements."
    ))

    _body(content, (
    "Population weighting means each country's value reflects the average exposure experienced "
    "by its residents — not just a geographic average. A polluted but sparsely populated region "
    "has less impact on the national value than a densely populated area with the same pollution level."
    ))

    _divider(content)

    # ── Links ─────────────────────────────────────────────────────────────────
    _section(content, "Further Reading")

    for title, url, description in LINKS:
        _link_row(content, title, url, description)

    # Bottom padding
    tk.Frame(content, bg=BG, height=30).pack()


# ── Reusable widget helpers ────────────────────────────────────────────────────

def _divider(parent):
    tk.Frame(parent, bg=GRID, height=1).pack(fill=tk.X, padx=40, pady=14)


def _section(parent, text: str):
    tk.Label(
        parent, text=text,
        bg=BG, fg=ACCENT2, font=FONT_SECTION,
    ).pack(anchor=tk.W, padx=40, pady=(6, 2))


def _body(parent, text: str):
    tk.Label(
        parent, text=text,
        bg=BG, fg=TEXT, font=FONT_BODY,
        wraplength=820, justify=tk.LEFT,
    ).pack(anchor=tk.W, padx=40, pady=3)


def _health_table(parent):
    table_frame = tk.Frame(parent, bg=BG)
    table_frame.pack(anchor=tk.W, padx=40, pady=(4, 6))

    for r_idx, row in enumerate(HEALTH_TABLE):
        is_header = r_idx == 0
        row_bg    = SURFACE if is_header else ROW_COLORS[r_idx % 2]

        row_frame = tk.Frame(table_frame, bg=row_bg)
        row_frame.pack(fill=tk.X, pady=(0, 1))

        for c_idx, (cell, width) in enumerate(zip(row, COL_WIDTHS)):
            if is_header:
                fg   = HEADER_FG[c_idx]
                font = ("Courier New", 9, "bold")
            elif c_idx == 1:
                fg = (
                    SAFE    if "Safe"     in cell else
                    ACCENT2 if "Moderate" in cell else
                    ACCENT
                )
                font = ("Courier New", 9, "bold")
            else:
                fg   = TEXT
                font = FONT_SMALL

            if c_idx == 2:
                # Last column: no fixed width, wraps instead
                tk.Label(
                    row_frame, text=cell,
                    bg=row_bg, fg=fg, font=font,
                    anchor=tk.W, padx=8, pady=5,
                    justify=tk.LEFT, wraplength=480,
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)
            else:
                tk.Label(
                    row_frame, text=cell,
                    bg=row_bg, fg=fg, font=font,
                    width=width, anchor=tk.W, padx=8, pady=5,
                    justify=tk.LEFT,
                ).pack(side=tk.LEFT)


def _link_row(parent, title: str, url: str, description: str):
    row = tk.Frame(parent, bg=SURFACE, padx=16, pady=10)
    row.pack(fill=tk.X, padx=40, pady=3)

    link = tk.Label(
        row, text=f"↗  {title}",
        bg=SURFACE, fg=ACCENT, font=FONT_LINK,
        cursor="hand2",
    )
    link.pack(anchor=tk.W)
    link.bind("<Button-1>", lambda e: webbrowser.open(url))

    tk.Label(
        row, text=description,
        bg=SURFACE, fg=SUBTEXT, font=FONT_SMALL,
        justify=tk.LEFT,
    ).pack(anchor=tk.W, pady=(2, 0))
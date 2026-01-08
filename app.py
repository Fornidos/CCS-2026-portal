import streamlit as st
import pandas as pd
from pathlib import Path

# Paths
APP_DIR = Path(__file__).parent
IMAGE_FOLDER = APP_DIR / "images"
MASTER_COUNTS = APP_DIR / "data" / "CCS_Master_Panel_Counts_2026_11.1_ABE.xlsx"

# Debug sidebar
st.sidebar.title("Debug Info")
st.sidebar.write(f"Images folder: {IMAGE_FOLDER.exists()}")
st.sidebar.write(f"Excel exists: {MASTER_COUNTS.exists()}")

if not MASTER_COUNTS.exists():
    st.error("Excel file not found — check path.")
    st.stop()

# Load data
df_restr = pd.read_excel(MASTER_COUNTS, sheet_name="Restrictions", header=0)
df_restr = df_restr.astype(str).apply(lambda x: x.str.strip())

category_pairs = {}
for i in range(len(df_restr.columns) - 1):
    cat_col = df_restr.columns[i]
    allowed_col = df_restr.columns[i + 1]
    if "ALLOWED" in allowed_col.upper():
        category_pairs[cat_col.upper()] = (cat_col, allowed_col)

valid_performance_raw = set()
valid_plan = set()
valid_ceiling = set()
valid_framing = set()
valid_wall_raw = set()

for cat_upper, (cat_col, allowed_col) in category_pairs.items():
    valid_rows = df_restr[df_restr[allowed_col].str.upper() == "Y"]
    values = valid_rows[cat_col].dropna().unique()
    if "PERFORMANCE" in cat_upper:
        valid_performance_raw.update(values)
    elif "PLAN" in cat_upper:
        valid_plan.update(values)
    elif "CEILING" in cat_upper:
        valid_ceiling.update(values)
    elif "FRAMING" in cat_upper:
        valid_framing.update(values)
    elif "WALL" in cat_upper:
        valid_wall_raw.update(values)

PERFORMANCE_DISPLAY = {"STD": "Standard", "HWS": "High Winds and Seismic", "HEE": "High Energy Efficiency", "FIRE": "Fire"}
valid_performance = sorted([PERFORMANCE_DISPLAY.get(v.upper(), v) for v in valid_performance_raw])
valid_plan = sorted(valid_plan)
valid_ceiling = sorted(valid_ceiling)
valid_framing = sorted(valid_framing)
valid_wall = sorted(valid_wall_raw)

if not valid_performance: valid_performance = ["Standard"]
if not valid_ceiling: valid_ceiling = ["8", "9"]
if not valid_framing: valid_framing = ["Wood", "Steel/CFS"]
if not valid_wall: valid_wall = ["4\"", "6\""]

STUDIO_PLANS = {"168", "252", "336"}
ADU_PLANS = {"420", "504", "588"}
FRAMING_TO_HEADER = {"Wood": "WOOD", "WOOD": "WOOD", "Steel": "CFS", "CFS": "CFS", "Steel/CFS": "CFS"}

# App setup
st.set_page_config(page_title="Fornidos Client Portal", layout="centered")

# Logo
logo_path = IMAGE_FOLDER / "Fornidos Logo PNG.png"
if logo_path.exists():
    st.image(str(logo_path), width=300)
else:
    st.warning("Logo not found in images folder.")

st.title("Fornidos Client Portal - Select Your Home")

if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.selections = {}

st.progress((st.session_state.step - 1) / 4)

# Flexible image picker
def img_pick(plan: str, kind: str) -> Path | None:
    candidates = [
        IMAGE_FOLDER / f"{plan}_{kind}_sidebyside.jpeg",
        IMAGE_FOLDER / f"{plan}_{kind}_sidebyside.jpg",
        IMAGE_FOLDER / f"{plan}_{kind}_stacked.jpeg",
        IMAGE_FOLDER / f"{plan}_{kind}_stacked.jpg",
        IMAGE_FOLDER / f"{plan}_{kind}.jpeg",
        IMAGE_FOLDER / f"{plan}_{kind}.jpg",
    ]
    return next((p for p in candidates if p.exists()), None)

if st.session_state.step == 1:
    st.header("1. Select Home Type")
    cols = st.columns(4)
    if cols[0].button("Studios"):
        st.session_state.selections["home_type"] = "Studios"
        st.session_state.step = 2
        st.rerun()
    if cols[1].button("ADU"):
        st.session_state.selections["home_type"] = "ADU"
        st.session_state.step = 2
        st.rerun()
    if cols[2].button("Single Family"):
        st.session_state.selections["home_type"] = "Single Family"
        st.session_state.step = 2
        st.rerun()
    if cols[3].button("Duplex"):
        st.session_state.selections["home_type"] = "Duplex"
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    st.header("2. Select Plan")
    home_type = st.session_state.selections["home_type"]
    if home_type == "Studios":
        plans = [p for p in valid_plan if p in STUDIO_PLANS]
    elif home_type == "ADU":
        plans = [p for p in valid_plan if p in ADU_PLANS]
    else:
        plans = valid_plan
    plans = sorted(plans)
    for plan in plans:
        if st.button(f"Plan {plan} sq ft"):
            st.session_state.selections["plan"] = plan
            st.session_state.step = 3
            st.rerun()
    if st.button("← Back"):
        st.session_state.step = 1
        st.rerun()

elif st.session_state.step == 3 or st.session_state.step == 4:
    plan = st.session_state.selections["plan"]
    header_text = "3. Performance Package" if st.session_state.step == 3 else "4. Details"
    st.header(f"{header_text} — Plan {plan}")

    # Elevation on top
    elevation = img_pick(plan, "elevation")
    if elevation:
        st.image(str(elevation), caption="Elevation", width=800)
    else:
        st.info("Elevation image missing")

    # Floorplan below
    floorplan = img_pick(plan, "floorplan")
    if floorplan:
        st.image(str(floorplan), caption="Floorplan", width=800)
    else:
        st.info("Floorplan image missing")

    if st.session_state.step == 3:
        performance = st.radio("Performance:", valid_performance, horizontal=True)
        st.session_state.selections["performance"] = performance
        cols = st.columns([1, 1, 3])
        if cols[0].button("← Back"):
            st.session_state.step = 2
            st.rerun()
        if cols[1].button("Next →"):
            st.session_state.step = 4
            st.rerun()
    else:
        ceiling = st.radio("Ceiling Height:", [f"{c} ft" for c in valid_ceiling], horizontal=True)
        framing = st.radio("Framing Type:", valid_framing, horizontal=True)
        wall = st.radio("Wall Thickness:", valid_wall, horizontal=True)
        st.session_state.selections["ceiling"] = ceiling.replace(" ft", "")
        st.session_state.selections["framing"] = framing
        st.session_state.selections["wall"] = wall
        cols = st.columns([1, 1, 3])
        if cols[0].button("← Back"):
            st.session_state.step = 3
            st.rerun()
        if cols[1].button("Confirm → Summary"):
            st.session_state.step = 5
            st.rerun()

elif st.session_state.step == 5:
    s = st.session_state.selections
    framing_header = FRAMING_TO_HEADER.get(s["framing"], "WOOD")
    panel_key = f"{s['plan']} {s['ceiling']} {framing_header}"
    try:
        panel_df = pd.read_excel(MASTER_COUNTS, sheet_name="Panel Counts", nrows=1, header=None)
        key_exists = panel_key in panel_df.iloc[0].astype(str).values
    except:
        key_exists = False
    st.header("Selection Summary")
    st.markdown(f"""
**Home Type:** {s['home_type']}  
**Plan:** {s['plan']} sq ft  
**Performance:** {s['performance']}  
**Ceiling:** {s['ceiling']} ft  
**Framing:** {s['framing']}  
**Wall:** {s['wall']}  

**Panel Key:** {panel_key}  
{'✓ Valid configuration' if key_exists else '⚠ Not available'}
""")
    cols = st.columns([1, 1, 3])
    if cols[0].button("← Back"):
        st.session_state.step = 4
        st.rerun()
    if cols[1].button("Start Over"):
        st.session_state.step = 1
        st.session_state.selections = {}
        st.rerun()

st.caption("Fornidos Client Portal — January 2026")
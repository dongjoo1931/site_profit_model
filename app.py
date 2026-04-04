import math
from io import BytesIO
from typing import List, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="세종 6-3 모듈러 분석 프로그램",
    page_icon="🏗️",
    layout="wide"
)

PROJECT_INFO = {
    "project_name": "행복도시 6-3생활권 UR1·2BL 모듈러 공공주택건설사업",
    "site_area_m2": 4178.0,
    "gross_floor_area_m2": 20363.508,
    "building_area_m2": 2371.011,
    "num_buildings": 2,
    "num_units": 216,
    "above_floors": 7,
    "basement_floors": 4,
    "north_road_m": 18.0,
    "south_road_m": 43.0,
    "east_road_m": 6.0,
    "west_road_m": 10.0,
    "module_width_m": 3.3,
    "module_length_repr_m": 8.0,
    "module_height_m": 3.1,
    "module_weight_est_t": 12.0,
    "total_project_cost_krw": 55_789_400_000,
    "net_construction_cost_krw": 50_481_520_337,
}

UNIT_TYPE_DB = pd.DataFrame([
    {"unit_type": "21A",   "exclusive_area_m2": 21.0287, "contract_area_m2": 30.2830, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 7.8},
    {"unit_type": "21A2",  "exclusive_area_m2": 21.0287, "contract_area_m2": 30.2830, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 7.8},
    {"unit_type": "21A1S", "exclusive_area_m2": 21.0287, "contract_area_m2": 30.2830, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 7.8},
    {"unit_type": "22T",   "exclusive_area_m2": 22.8664, "contract_area_m2": 39.0008, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 8.0},
    {"unit_type": "24A",   "exclusive_area_m2": 24.7765, "contract_area_m2": 34.6070, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 8.0},
    {"unit_type": "24AS",  "exclusive_area_m2": 24.7765, "contract_area_m2": 34.6070, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 8.0},
    {"unit_type": "30T2",  "exclusive_area_m2": 30.1872, "contract_area_m2": 46.8949, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 8.0},
    {"unit_type": "35TD1", "exclusive_area_m2": 36.5384, "contract_area_m2": 49.6634, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 8.0},
    {"unit_type": "37A1",  "exclusive_area_m2": 37.4018, "contract_area_m2": 52.4428, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 8.0},
    {"unit_type": "38T",   "exclusive_area_m2": 38.1678, "contract_area_m2": 56.6243, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 8.0},
])

UNIT_COUNTS = pd.DataFrame([
    {"unit_type": "21A1", "count": 55},
    {"unit_type": "21A2", "count": 42},
    {"unit_type": "21A1S", "count": 6},
    {"unit_type": "22T", "count": 2},
    {"unit_type": "24A", "count": 40},
    {"unit_type": "24AS", "count": 6},
    {"unit_type": "30T2", "count": 4},
    {"unit_type": "35TD1", "count": 21},
    {"unit_type": "37A1", "count": 33},
    {"unit_type": "38T", "count": 7},
])

KNOWN_COSTS = pd.DataFrame([
    ["총 공사비", 55_789_400_000],
    ["순공사비", 50_481_520_337],
    ["일반관리비", 2_775_909_982],
    ["매입부가세(면세)", 2_338_615_135],
    ["부가가치세(과세)", 193_354_546],
    ["UR1BL 지상(3~7층) 재료비", 4_134_104_031],
    ["UR1BL 지상(3~7층) 노무비", 2_880_372_833],
    ["UR1BL 지상(3~7층) 경비", 1_927_062_986],
    ["UR2BL 지상(3~7층) 재료비", 5_131_881_531],
    ["UR2BL 지상(3~7층) 노무비", 3_503_636_821],
    ["UR2BL 지상(3~7층) 경비", 2_351_392_462],
], columns=["항목", "금액_원"])

BUILDING_SPECS = {
    "201": {
        "origin": (0.0, 0.0, 0.0),
        "floors": {3: {"rows": [9, 6, 9]}, 4: {"rows": [9, 6, 9]}, 5: {"rows": [9, 7, 9]}, 6: {"rows": [9, 7, 9]}, 7: {"rows": [9, 5, 9]}}
    },
    "202": {
        "origin": (86.0, 0.0, 0.0),
        "floors": {3: {"rows": [9, 7, 9]}, 4: {"rows": [9, 7, 9]}, 5: {"rows": [9, 8, 9]}, 6: {"rows": [9, 8, 9]}, 7: {"rows": [7, 6, 8]}}
    },
}

SITE_BOX = {"x": -12.0, "y": -12.0, "z": -0.2, "dx": 136.0, "dy": 62.0, "dz": 0.2}
ROADS = [
    {"name": "북측 18M 도로", "x": -12.0, "y": 50.0, "z": -0.05, "dx": 136.0, "dy": 18.0, "dz": 0.05, "color": "#9e9e9e"},
    {"name": "남측 43M 도로", "x": -12.0, "y": -55.0, "z": -0.05, "dx": 136.0, "dy": 43.0, "dz": 0.05, "color": "#8d8d8d"},
    {"name": "서측 10M 도로", "x": -22.0, "y": -12.0, "z": -0.05, "dx": 10.0, "dy": 62.0, "dz": 0.05, "color": "#969696"},
    {"name": "동측 6M 도로", "x": 124.0, "y": -12.0, "z": -0.05, "dx": 6.0, "dy": 62.0, "dz": 0.05, "color": "#a8a8a8"},
]
SURROUNDING_BUILDINGS = [
    {"name": "주변건물 A", "x": -32.0, "y": 12.0, "z": 0.0, "dx": 12.0, "dy": 18.0, "dz": 18.0, "color": "#bdbdbd"},
    {"name": "주변건물 B", "x": 128.0, "y": 8.0, "z": 0.0, "dx": 10.0, "dy": 16.0, "dz": 15.0, "color": "#c7c7c7"},
    {"name": "주변건물 C", "x": 42.0, "y": 72.0, "z": 0.0, "dx": 18.0, "dy": 14.0, "dz": 12.0, "color": "#c9c9c9"},
]

def format_krw(v: float) -> str:
    return f"{v:,.0f} 원"

def clean_value(v):
    if pd.isna(v):
        return None
    if isinstance(v, str):
        t = v.replace(",", "").replace("원", "").strip()
        if t == "":
            return None
        try:
            return float(t)
        except Exception:
            return v
    return v

def row_to_text(row: pd.Series) -> str:
    vals = []
    for v in row.tolist():
        if pd.notna(v):
            s = str(v).strip()
            if s:
                vals.append(s)
    return " | ".join(vals)

def add_box(fig, x, y, z, dx, dy, dz, color, name="", opacity=0.92, show_edges=False):
    xs = [x, x+dx, x+dx, x, x, x+dx, x+dx, x]
    ys = [y, y, y+dy, y+dy, y, y, y+dy, y+dy]
    zs = [z, z, z, z, z+dz, z+dz, z+dz, z+dz]
    i = [0, 0, 0, 1, 2, 4, 4, 5, 6, 4, 0, 1]
    j = [1, 2, 3, 2, 3, 5, 6, 6, 7, 0, 4, 5]
    k = [2, 3, 1, 5, 7, 6, 7, 2, 3, 5, 1, 6]
    fig.add_trace(go.Mesh3d(
        x=xs, y=ys, z=zs, i=i, j=j, k=k,
        color=color, opacity=opacity, flatshading=True,
        hoverinfo="text", text=name, showscale=False
    ))
    if show_edges:
        edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
        for a, b in edges:
            fig.add_trace(go.Scatter3d(
                x=[xs[a], xs[b]], y=[ys[a], ys[b]], z=[zs[a], zs[b]],
                mode="lines", line=dict(color="rgba(30,30,30,0.55)", width=3),
                hoverinfo="skip", showlegend=False
            ))
    return fig

def add_cylinder(fig, center_x, center_y, z0, height, radius, color, name="", steps=24):
    for i in range(steps):
        ang1 = 2 * math.pi * i / steps
        ang2 = 2 * math.pi * (i + 1) / steps
        x1, y1 = center_x + radius * math.cos(ang1), center_y + radius * math.sin(ang1)
        x2, y2 = center_x + radius * math.cos(ang2), center_y + radius * math.sin(ang2)
        fig.add_trace(go.Scatter3d(x=[x1, x2], y=[y1, y2], z=[z0, z0], mode="lines",
                                   line=dict(color=color, width=5), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter3d(x=[x1, x2], y=[y1, y2], z=[z0+height, z0+height], mode="lines",
                                   line=dict(color=color, width=5), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter3d(x=[x1, x1], y=[y1, y1], z=[z0, z0+height], mode="lines",
                                   line=dict(color=color, width=5), hoverinfo="text", text=name, showlegend=False))

def add_boom(fig, x0, y0, z0, x1, y1, z1, color="#d6a300", width=10, name="붐"):
    fig.add_trace(go.Scatter3d(
        x=[x0, x1], y=[y0, y1], z=[z0, z1],
        mode="lines", line=dict(color=color, width=width),
        hoverinfo="text", text=name, showlegend=False
    ))

def add_hook_line(fig, x0, y0, z0, x1, y1, z1):
    fig.add_trace(go.Scatter3d(
        x=[x0, x1], y=[y0, y1], z=[z0, z1],
        mode="lines", line=dict(color="#222222", width=5),
        hoverinfo="skip", showlegend=False
    ))

def add_circle_on_ground(fig, center_x, center_y, radius, color="#ff9800", z=0.02, name="작업반경"):
    pts = 80
    xs = [center_x + radius * math.cos(2*math.pi*i/pts) for i in range(pts+1)]
    ys = [center_y + radius * math.sin(2*math.pi*i/pts) for i in range(pts+1)]
    zs = [z] * (pts+1)
    fig.add_trace(go.Scatter3d(
        x=xs, y=ys, z=zs, mode="lines",
        line=dict(color=color, width=4), hoverinfo="text", text=name, showlegend=False
    ))

def generate_modules(building_key: str, module_w: float, module_l: float, module_h: float) -> pd.DataFrame:
    spec = BUILDING_SPECS[building_key]
    ox, oy, oz = spec["origin"]
    gap_x = 0.15
    row_gap_y = 10.2
    floor_gap = 0.15
    rows = []
    for floor, f in spec["floors"].items():
        z = oz + (floor - 3) * (module_h + floor_gap)
        row_counts = f["rows"]
        for row_idx, count in enumerate(row_counts):
            y = oy + row_idx * row_gap_y
            depth = module_l * (0.72 if row_idx == 1 else 0.52)
            for n in range(count):
                x = ox + n * (module_w + gap_x)
                rows.append({
                    "building": building_key,
                    "floor": floor,
                    "row_idx": row_idx + 1,
                    "module_idx": n + 1,
                    "x": x, "y": y, "z": z,
                    "dx": module_w, "dy": depth, "dz": module_h,
                    "cx": x + module_w / 2, "cy": y + depth / 2, "cz": z + module_h / 2,
                    "name": f"{building_key}-{floor}F-{row_idx+1}-{n+1}"
                })
    return pd.DataFrame(rows)

@st.cache_data(show_spinner=False)
def build_module_dataframe(module_h: float) -> pd.DataFrame:
    parts = []
    for b in BUILDING_SPECS.keys():
        parts.append(generate_modules(b, PROJECT_INFO["module_width_m"], PROJECT_INFO["module_length_repr_m"], module_h))
    return pd.concat(parts, ignore_index=True)

def ensure_module_columns(module_df: pd.DataFrame) -> pd.DataFrame:
    df = module_df.copy()
    # 구버전 캐시 데이터 방어
    if "row_idx" not in df.columns:
        if "row" in df.columns:
            df["row_idx"] = df["row"]
        else:
            df["row_idx"] = 1
    if "module_idx" not in df.columns:
        df["module_idx"] = df.groupby(["building", "floor", "row_idx"]).cumcount() + 1
    if "cx" not in df.columns:
        df["cx"] = df["x"] + df["dx"] / 2
    if "cy" not in df.columns:
        df["cy"] = df["y"] + df["dy"] / 2
    if "cz" not in df.columns:
        df["cz"] = df["z"] + df["dz"] / 2
    return df

def get_target_module(module_df: pd.DataFrame, building: str, floor: int, target_row: int, target_module_idx: int) -> Optional[pd.Series]:
    df = ensure_module_columns(module_df)
    selected = df[
        (df["building"].astype(str) == str(building)) &
        (df["floor"].astype(int) == int(floor)) &
        (df["row_idx"].astype(int) == int(target_row)) &
        (df["module_idx"].astype(int) == int(target_module_idx))
    ]
    if selected.empty:
        return None
    return selected.iloc[0]

def add_crane_and_lifting_scene(fig, target_module: pd.Series):
    tx, ty, tz = float(target_module["x"]), float(target_module["y"]), float(target_module["z"])
    tdx, tdy, tdz = float(target_module["dx"]), float(target_module["dy"]), float(target_module["dz"])
    tcx, tcy = float(target_module["cx"]), float(target_module["cy"])
    building = str(target_module["building"])

    if building == "201":
        crane_x, crane_y = -8.5, -28.0
        trailer_x, trailer_y = 3.0, -38.0
        radius = 42.0
    else:
        crane_x, crane_y = 77.5, -28.0
        trailer_x, trailer_y = 90.0, -38.0
        radius = 42.0

    add_box(fig, crane_x, crane_y, 0.0, 7.0, 3.2, 2.0, color="#f2c037", name="450t 크롤러 크레인 본체", opacity=0.98)
    add_box(fig, crane_x-2.2, crane_y+0.5, 0.0, 2.2, 2.2, 1.0, color="#3f3f3f", name="크롤러 좌측")
    add_box(fig, crane_x+7.0, crane_y+0.5, 0.0, 2.2, 2.2, 1.0, color="#3f3f3f", name="크롤러 우측")
    add_cylinder(fig, crane_x+3.5, crane_y+1.6, 2.0, 3.4, 0.48, "#6d6d6d", name="턴테이블")
    add_circle_on_ground(fig, crane_x+3.5, crane_y+1.6, radius, color="#f39c12", name="크레인 작업반경")

    boom_base_x, boom_base_y, boom_base_z = crane_x + 3.5, crane_y + 1.6, 5.2
    boom_tip_x, boom_tip_y, boom_tip_z = tcx, tcy, tz + tdz + 7.0
    add_boom(fig, boom_base_x, boom_base_y, boom_base_z, boom_tip_x, boom_tip_y, boom_tip_z, name="크레인 붐")

    add_box(fig, trailer_x, trailer_y, 0.0, 14.0, 3.2, 1.0, color="#2f4f4f", name="트레일러", opacity=0.95)
    add_box(fig, trailer_x-3.2, trailer_y+0.4, 0.0, 3.2, 2.4, 1.8, color="#607d8b", name="트랙터 헤드", opacity=0.95)

    lifted_x = tx
    lifted_y = ty
    lifted_z = tz + tdz + 1.2
    add_hook_line(fig, boom_tip_x, boom_tip_y, boom_tip_z, lifted_x + tdx/2, lifted_y + tdy/2, lifted_z + tdz)
    add_box(fig, lifted_x, lifted_y, lifted_z, tdx, tdy, tdz, color="#00acc1", name="인양 중 모듈", opacity=0.92, show_edges=True)
    add_box(fig, tx, ty, tz, tdx, tdy, 0.12, color="#ff5252", name="설치 목표 위치", opacity=0.72)
    fig.add_trace(go.Scatter3d(
        x=[trailer_x + 7.0, crane_x + 3.5, lifted_x + tdx/2],
        y=[trailer_y + 1.6, crane_y + 1.6, lifted_y + tdy/2],
        z=[0.1, 0.1, lifted_z + tdz],
        mode="lines",
        line=dict(color="#1565c0", width=4, dash="dash"),
        hoverinfo="text", text="반입/인양 동선", showlegend=False
    ))

def make_3d_figure(module_df: pd.DataFrame, show_roads: bool, show_surroundings: bool, show_edges: bool, target_module: Optional[pd.Series]):
    fig = go.Figure()
    add_box(fig, SITE_BOX["x"], SITE_BOX["y"], SITE_BOX["z"], SITE_BOX["dx"], SITE_BOX["dy"], SITE_BOX["dz"],
            color="#d9e8d0", name="대지", opacity=0.55)
    if show_roads:
        for r in ROADS:
            add_box(fig, r["x"], r["y"], r["z"], r["dx"], r["dy"], r["dz"], color=r["color"], name=r["name"], opacity=0.8)
    if show_surroundings:
        for b in SURROUNDING_BUILDINGS:
            add_box(fig, b["x"], b["y"], b["z"], b["dx"], b["dy"], b["dz"], color=b["color"], name=b["name"], opacity=0.55)

    add_box(fig, -1.5, -1.5, -4.8, 35.5, 32.0, 4.4, color="#c8c8c8", name="201 저층부/지하", opacity=0.60)
    add_box(fig, 84.5, -1.5, -4.8, 35.5, 32.0, 4.4, color="#c8c8c8", name="202 저층부/지하", opacity=0.60)

    floor_colors = {3: "#4e79a7", 4: "#f28e2b", 5: "#59a14f", 6: "#e15759", 7: "#9c755f"}
    for floor, df_floor in module_df.groupby("floor"):
        color = floor_colors.get(int(floor), "#76b7b2")
        for _, row in df_floor.iterrows():
            add_box(fig, row["x"], row["y"], row["z"], row["dx"], row["dy"], row["dz"],
                    color=color, name=row["name"], opacity=0.95, show_edges=show_edges)

    if target_module is not None:
        add_crane_and_lifting_scene(fig, target_module)

    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            aspectmode="data",
            bgcolor="white",
            camera=dict(eye=dict(x=1.65, y=1.35, z=1.05))
        )
    )
    return fig

@st.cache_data(show_spinner=False)
def get_excel_sheet_names(file_bytes: bytes) -> List[str]:
    bio = BytesIO(file_bytes)
    xls = pd.ExcelFile(bio, engine="openpyxl")
    return xls.sheet_names

@st.cache_data(show_spinner=False)
def read_excel_sheet(file_bytes: bytes, sheet_name: str) -> pd.DataFrame:
    bio = BytesIO(file_bytes)
    return pd.read_excel(bio, sheet_name=sheet_name, header=None, engine="openpyxl")

def summarize_selected_sheet(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for idx in range(len(df)):
        row = df.iloc[idx]
        text = row_to_text(row)
        if not text:
            continue
        numeric_values = []
        for v in row.tolist():
            cleaned = clean_value(v)
            if isinstance(cleaned, (int, float)):
                numeric_values.append(float(cleaned))
        rows.append({
            "row_index": idx,
            "text": text[:400],
            "numeric_count": len(numeric_values),
            "numeric_sum": sum(numeric_values) if numeric_values else 0.0
        })
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["numeric_count", "numeric_sum"], ascending=[False, False])
    return out

st.sidebar.title("설정")
uploaded_excel = st.sidebar.file_uploader("준공내역서 업로드 (.xlsx)", type=["xlsx"])

show_201 = st.sidebar.checkbox("201동 표시", True)
show_202 = st.sidebar.checkbox("202동 표시", True)
show_roads = st.sidebar.checkbox("주변 도로 표시", True)
show_surroundings = st.sidebar.checkbox("주변 건물 매스 표시", True)
show_edges = st.sidebar.checkbox("모듈 외곽선 표시", False)

floor_min, floor_max = st.sidebar.slider("표시 층 범위", 3, 7, (3, 7))
module_h = st.sidebar.slider("모듈 높이 (m)", 2.8, 3.6, float(PROJECT_INFO["module_height_m"]), 0.1)

st.sidebar.markdown("---")
show_crane = st.sidebar.checkbox("양중장비/인양 장면 표시", True)
crane_building = st.sidebar.selectbox("설치 대상 동", ["201", "202"], index=0)
crane_floor = st.sidebar.selectbox("설치 대상 층", [3, 4, 5, 6, 7], index=2)
crane_row = st.sidebar.selectbox("설치 대상 열(row)", [1, 2, 3], index=1)
crane_module_idx = st.sidebar.slider("설치 대상 모듈 번호", 1, 9, 1)

st.title("세종 6-3 UR1·2BL 모듈러 사례 분석 프로그램")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("총 세대수", f'{PROJECT_INFO["num_units"]} 세대')
c2.metric("동수", f'{PROJECT_INFO["num_buildings"]} 개동')
c3.metric("지상층수", f'{PROJECT_INFO["above_floors"]} 층')
c4.metric("대표 모듈", f'{PROJECT_INFO["module_width_m"]:.1f} × {PROJECT_INFO["module_length_repr_m"]:.1f} m')
c5.metric("총 공사비", format_krw(PROJECT_INFO["total_project_cost_krw"]))

st.markdown("---")
tabs = st.tabs(["3D 분석", "프로젝트 정보", "세대/모듈 DB", "층별 분석", "양중장비 해석", "준공내역서 분석"])

with tabs[0]:
    st.subheader("3D 매스 모델")
    module_df = ensure_module_columns(build_module_dataframe(module_h))
    building_filter = []
    if show_201:
        building_filter.append("201")
    if show_202:
        building_filter.append("202")
    module_df = module_df[
        (module_df["building"].isin(building_filter)) &
        (module_df["floor"] >= floor_min) &
        (module_df["floor"] <= floor_max)
    ].copy()

    target_module = None
    if show_crane:
        target_module = get_target_module(module_df, crane_building, crane_floor, crane_row, crane_module_idx)
        if target_module is None:
            st.warning("선택한 동/층/열/모듈 번호 조합이 현재 표시 범위에 없습니다. 다른 조합을 선택해 주세요.")

    fig = make_3d_figure(module_df, show_roads, show_surroundings, show_edges, target_module)
    st.plotly_chart(fig, use_container_width=True)

    if target_module is not None:
        st.dataframe(pd.DataFrame([{
            "building": target_module["building"],
            "floor": int(target_module["floor"]),
            "row_idx": int(target_module["row_idx"]),
            "module_idx": int(target_module["module_idx"]),
            "x": round(float(target_module["x"]), 2),
            "y": round(float(target_module["y"]), 2),
            "dx": round(float(target_module["dx"]), 2),
            "dy": round(float(target_module["dy"]), 2),
            "dz": round(float(target_module["dz"]), 2),
        }]), use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("프로젝트 정보")
    st.dataframe(pd.DataFrame([
        ["사업명", PROJECT_INFO["project_name"]],
        ["대지면적", f'{PROJECT_INFO["site_area_m2"]:,.3f} ㎡'],
        ["연면적", f'{PROJECT_INFO["gross_floor_area_m2"]:,.3f} ㎡'],
        ["건축면적", f'{PROJECT_INFO["building_area_m2"]:,.3f} ㎡'],
        ["동수", PROJECT_INFO["num_buildings"]],
        ["세대수", PROJECT_INFO["num_units"]],
        ["지상층수", PROJECT_INFO["above_floors"]],
        ["지하층수", f'B{PROJECT_INFO["basement_floors"]}'],
    ], columns=["항목", "값"]), use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("세대/모듈 DB")
    df = UNIT_TYPE_DB.copy()
    df["module_width_m"] = PROJECT_INFO["module_width_m"]
    df["module_length_repr_m"] = PROJECT_INFO["module_length_repr_m"]
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.dataframe(UNIT_COUNTS, use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("층별 분석")
    floor_rows = []
    for b_key, spec in BUILDING_SPECS.items():
        for floor, floor_info in spec["floors"].items():
            module_count = sum(floor_info["rows"])
            floor_rows.append({
                "building": b_key,
                "floor": floor,
                "row_pattern": str(floor_info["rows"]),
                "module_count_est": module_count,
                "unit_count_est": math.floor(module_count / 2),
            })
    floor_df = pd.DataFrame(floor_rows).sort_values(["building", "floor"])
    st.dataframe(floor_df, use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("양중장비 해석")
    st.write("현장 주 양중장비: 450톤 크롤러 크레인")
    st.write("공장/야드 상차장비: O/H 크레인")

with tabs[5]:
    st.subheader("준공내역서 분석")
    known = KNOWN_COSTS.copy()
    known["금액표시"] = known["금액_원"].apply(format_krw)
    st.dataframe(known[["항목", "금액표시"]], use_container_width=True, hide_index=True)

    if uploaded_excel is not None:
        try:
            file_bytes = uploaded_excel.getvalue()
            sheet_names = get_excel_sheet_names(file_bytes)
            selected_sheet = st.selectbox("확인할 시트 선택", sheet_names)
            if selected_sheet:
                df_sheet = read_excel_sheet(file_bytes, selected_sheet)
                c1, c2 = st.columns(2)
                with c1:
                    st.dataframe(df_sheet.head(50), use_container_width=True)
                with c2:
                    st.dataframe(summarize_selected_sheet(df_sheet).head(30), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"엑셀 분석 중 오류가 발생했습니다: {e}")

st.markdown("---")
st.caption("KeyError 수정본: module_idx / row_idx / 중심좌표가 없을 때 자동으로 생성하도록 바꿨습니다.")

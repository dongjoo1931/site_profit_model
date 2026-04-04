import math
from io import BytesIO
from typing import Dict, List, Tuple

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# 세종 6-3 UR1·2BL 모듈러 사례 분석 프로그램 (최적화 버전)
# - 실제 사례 전용
# - 3D 중심
# - 엑셀은 "전체 자동 스캔" 대신 "시트 선택형"
# - 캐시 사용
# ============================================================

st.set_page_config(
    page_title="세종 6-3 모듈러 분석 프로그램",
    page_icon="🏗️",
    layout="wide"
)

# ------------------------------------------------------------
# 0. 기본 데이터
# ------------------------------------------------------------
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

# 도면 기반 단순화 3D 배치
BUILDING_SPECS = {
    "201": {
        "origin": (0.0, 0.0, 0.0),
        "floors": {
            3: {"rows": [9, 6, 9]},
            4: {"rows": [9, 6, 9]},
            5: {"rows": [9, 7, 9]},
            6: {"rows": [9, 7, 9]},
            7: {"rows": [9, 5, 9]},
        },
    },
    "202": {
        "origin": (86.0, 0.0, 0.0),
        "floors": {
            3: {"rows": [9, 7, 9]},
            4: {"rows": [9, 7, 9]},
            5: {"rows": [9, 8, 9]},
            6: {"rows": [9, 8, 9]},
            7: {"rows": [7, 6, 8]},
        },
    },
}

# 전체 부지/도로/주변건물 매스 배치
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


# ------------------------------------------------------------
# 1. 공통 함수
# ------------------------------------------------------------
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
        x=xs, y=ys, z=zs,
        i=i, j=j, k=k,
        color=color,
        opacity=opacity,
        flatshading=True,
        hoverinfo="text",
        text=name,
        showscale=False
    ))

    if show_edges:
        edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
        for a, b in edges:
            fig.add_trace(go.Scatter3d(
                x=[xs[a], xs[b]],
                y=[ys[a], ys[b]],
                z=[zs[a], zs[b]],
                mode="lines",
                line=dict(color="rgba(30,30,30,0.55)", width=3),
                hoverinfo="skip",
                showlegend=False
            ))
    return fig


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
                    "x": x, "y": y, "z": z,
                    "dx": module_w, "dy": depth, "dz": module_h,
                    "name": f"{building_key}-{floor}F-{row_idx+1}-{n+1}"
                })
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def build_module_dataframe(module_h: float) -> pd.DataFrame:
    parts = []
    for b in BUILDING_SPECS.keys():
        parts.append(generate_modules(
            b,
            PROJECT_INFO["module_width_m"],
            PROJECT_INFO["module_length_repr_m"],
            module_h
        ))
    return pd.concat(parts, ignore_index=True)


def make_3d_figure(module_df: pd.DataFrame, show_roads: bool, show_surroundings: bool, show_edges: bool):
    fig = go.Figure()

    # 부지
    add_box(fig, SITE_BOX["x"], SITE_BOX["y"], SITE_BOX["z"], SITE_BOX["dx"], SITE_BOX["dy"], SITE_BOX["dz"],
            color="#d9e8d0", name="대지", opacity=0.55, show_edges=False)

    # 도로
    if show_roads:
        for r in ROADS:
            add_box(fig, r["x"], r["y"], r["z"], r["dx"], r["dy"], r["dz"],
                    color=r["color"], name=r["name"], opacity=0.8, show_edges=False)

    # 주변 건물
    if show_surroundings:
        for b in SURROUNDING_BUILDINGS:
            add_box(fig, b["x"], b["y"], b["z"], b["dx"], b["dy"], b["dz"],
                    color=b["color"], name=b["name"], opacity=0.55, show_edges=False)

    # 포디움/저층부
    add_box(fig, -1.5, -1.5, -4.8, 35.5, 32.0, 4.4, color="#c8c8c8", name="201 저층부/지하", opacity=0.60)
    add_box(fig, 84.5, -1.5, -4.8, 35.5, 32.0, 4.4, color="#c8c8c8", name="202 저층부/지하", opacity=0.60)

    floor_colors = {
        3: "#4e79a7",
        4: "#f28e2b",
        5: "#59a14f",
        6: "#e15759",
        7: "#9c755f",
    }

    for floor, df_floor in module_df.groupby("floor"):
        color = floor_colors.get(int(floor), "#76b7b2")
        for _, row in df_floor.iterrows():
            add_box(
                fig,
                row["x"], row["y"], row["z"],
                row["dx"], row["dy"], row["dz"],
                color=color, name=row["name"], opacity=0.95, show_edges=show_edges
            )

    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            aspectmode="data",
            bgcolor="white",
            camera=dict(eye=dict(x=1.7, y=1.4, z=1.1))
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


# ------------------------------------------------------------
# 2. 사이드바
# ------------------------------------------------------------
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
st.sidebar.caption("엑셀은 시트 선택 후에만 읽습니다.")
st.sidebar.caption("3D는 분석용 매스 모델입니다.")

# ------------------------------------------------------------
# 3. 상단 요약
# ------------------------------------------------------------
st.title("세종 6-3 UR1·2BL 모듈러 사례 분석 프로그램")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("총 세대수", f'{PROJECT_INFO["num_units"]} 세대')
c2.metric("동수", f'{PROJECT_INFO["num_buildings"]} 개동')
c3.metric("지상층수", f'{PROJECT_INFO["above_floors"]} 층')
c4.metric("대표 모듈", f'{PROJECT_INFO["module_width_m"]:.1f} × {PROJECT_INFO["module_length_repr_m"]:.1f} m')
c5.metric("총 공사비", format_krw(PROJECT_INFO["total_project_cost_krw"]))

st.markdown("---")

tabs = st.tabs(["3D 분석", "프로젝트 정보", "세대/모듈 DB", "층별 분석", "준공내역서 분석"])

# ------------------------------------------------------------
# 4. 3D 분석
# ------------------------------------------------------------
with tabs[0]:
    st.subheader("3D 매스 모델")

    module_df = build_module_dataframe(module_h).copy()
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

    fig = make_3d_figure(module_df, show_roads, show_surroundings, show_edges)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    total_modules_view = len(module_df)
    col1.metric("현재 표시 모듈 수", f"{total_modules_view} 개")
    col2.metric("예상 운송 횟수", f"{total_modules_view} 회")
    col3.metric("표시 모듈 총 추정중량", f'{total_modules_view * PROJECT_INFO["module_weight_est_t"]:,.0f} t')
    col4.metric("모듈 1개 대표 면적", f'{PROJECT_INFO["module_width_m"] * PROJECT_INFO["module_length_repr_m"]:.1f} ㎡')

    if not module_df.empty:
        summary = (
            module_df.groupby(["building", "floor"])
            .size()
            .reset_index(name="module_count")
            .sort_values(["building", "floor"])
        )
        st.dataframe(summary, use_container_width=True, hide_index=True)

    st.info(
        "이 3D는 실제 도면의 반복 구조를 바탕으로 만든 사례 분석용 모델입니다. "
        "주변 도로와 주변 건물은 코드로 단순 mass 형태로 구현했습니다."
    )

# ------------------------------------------------------------
# 5. 프로젝트 정보
# ------------------------------------------------------------
with tabs[1]:
    st.subheader("프로젝트 개요")

    left, right = st.columns([1.2, 1])

    with left:
        basic_df = pd.DataFrame([
            ["사업명", PROJECT_INFO["project_name"]],
            ["대지면적", f'{PROJECT_INFO["site_area_m2"]:,.3f} ㎡'],
            ["연면적", f'{PROJECT_INFO["gross_floor_area_m2"]:,.3f} ㎡'],
            ["건축면적", f'{PROJECT_INFO["building_area_m2"]:,.3f} ㎡'],
            ["동수", PROJECT_INFO["num_buildings"]],
            ["세대수", PROJECT_INFO["num_units"]],
            ["지상층수", PROJECT_INFO["above_floors"]],
            ["지하층수", f'B{PROJECT_INFO["basement_floors"]}'],
        ], columns=["항목", "값"])
        st.dataframe(basic_df, use_container_width=True, hide_index=True)

    with right:
        road_df = pd.DataFrame([
            ["북측 도로", f'{PROJECT_INFO["north_road_m"]} m'],
            ["남측 도로", f'{PROJECT_INFO["south_road_m"]} m'],
            ["동측 도로", f'{PROJECT_INFO["east_road_m"]} m'],
            ["서측 도로", f'{PROJECT_INFO["west_road_m"]} m'],
        ], columns=["방향", "폭"])
        st.dataframe(road_df, use_container_width=True, hide_index=True)

    st.markdown(
        """
### 현재 사례 해석 기준
- 기본 세대 폭은 **6.6m**
- 기본 모듈 폭은 **3.3m**
- 세대당 기본 모듈 수는 **2개**
- 반복층은 **3층~7층**
- 이 프로그램은 **실제 도면 + 실제 내역서 연결용 실증 분석 프로그램**으로 구성됨
        """
    )

# ------------------------------------------------------------
# 6. 세대/모듈 DB
# ------------------------------------------------------------
with tabs[2]:
    st.subheader("세대 타입 및 모듈 DB")

    df = UNIT_TYPE_DB.copy()
    df["module_width_m"] = PROJECT_INFO["module_width_m"]
    df["module_length_repr_m"] = PROJECT_INFO["module_length_repr_m"]
    df["module_area_repr_m2"] = PROJECT_INFO["module_width_m"] * PROJECT_INFO["module_length_repr_m"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### 세대수 집계")
    st.dataframe(UNIT_COUNTS, use_container_width=True, hide_index=True)

    total_modules = PROJECT_INFO["num_units"] * 2
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("세대당 모듈 수", "2 개")
    cc2.metric("총 추정 모듈 수", f"{total_modules} 개")
    cc3.metric("모듈 대표 footprint", f'{PROJECT_INFO["module_width_m"] * PROJECT_INFO["module_length_repr_m"]:.1f} ㎡')

# ------------------------------------------------------------
# 7. 층별 분석
# ------------------------------------------------------------
with tabs[3]:
    st.subheader("층별 구성 분석")

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
                "층 성격": "주거 반복층"
            })

    floor_df = pd.DataFrame(floor_rows).sort_values(["building", "floor"])
    st.dataframe(floor_df, use_container_width=True, hide_index=True)

    pivot = floor_df.pivot(index="floor", columns="building", values="module_count_est")
    st.bar_chart(pivot)

    st.markdown(
        """
- **1층**: 판매시설 / 공용부 / 부대복리시설 비중이 큼  
- **2층**: 전이층 성격  
- **3층~7층**: 모듈러 반복층  
- 따라서 현재 3D는 **3층~7층의 모듈 스택 구조 분석**에 초점을 맞춤
        """
    )

# ------------------------------------------------------------
# 8. 준공내역서 분석
# ------------------------------------------------------------
with tabs[4]:
    st.subheader("준공내역서 분석")

    known = KNOWN_COSTS.copy()
    known["금액표시"] = known["금액_원"].apply(format_krw)
    st.markdown("### 현재 확보된 핵심 공사비")
    st.dataframe(known[["항목", "금액표시"]], use_container_width=True, hide_index=True)

    u1, u2, u3 = st.columns(3)
    u1.metric("세대당 총 공사비", format_krw(PROJECT_INFO["total_project_cost_krw"] / PROJECT_INFO["num_units"]))
    u2.metric("연면적 ㎡당 총 공사비", format_krw(PROJECT_INFO["total_project_cost_krw"] / PROJECT_INFO["gross_floor_area_m2"]))
    u3.metric("모듈당 단순 환산 공사비", format_krw(PROJECT_INFO["total_project_cost_krw"] / (PROJECT_INFO["num_units"] * 2)))

    st.markdown("### 업로드한 준공내역서 읽기")

    if uploaded_excel is None:
        st.info("좌측에서 준공내역서를 업로드하면 시트명을 불러옵니다.")
    else:
        try:
            file_bytes = uploaded_excel.getvalue()
            sheet_names = get_excel_sheet_names(file_bytes)
            selected_sheet = st.selectbox("확인할 시트 선택", sheet_names)

            if selected_sheet:
                df_sheet = read_excel_sheet(file_bytes, selected_sheet)

                col_a, col_b = st.columns([1, 1])
                with col_a:
                    st.markdown("#### 선택 시트 원본 (상위 50행)")
                    st.dataframe(df_sheet.head(50), use_container_width=True)

                with col_b:
                    st.markdown("#### 선택 시트 요약")
                    summary_df = summarize_selected_sheet(df_sheet).head(30)
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)

                csv_bytes = df_sheet.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "선택 시트 CSV 다운로드",
                    data=csv_bytes,
                    file_name=f"{selected_sheet}.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"엑셀 분석 중 오류가 발생했습니다: {e}")
            st.caption("배포 환경에는 requirements.txt에 openpyxl이 반드시 포함되어 있어야 합니다.")


st.markdown("---")
st.caption(
    "이 앱은 세종 6-3 실제 사례의 도면·내역서 기반 분석용입니다. "
    "3D는 주변 도로/대지/주변 건물/두 개 동/반복층 모듈을 코드로 구현한 분석용 매스 모델입니다."
)

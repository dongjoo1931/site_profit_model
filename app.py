
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from openpyxl import load_workbook


# ============================================================
# 세종 6-3 UR1,2BL 모듈러 사례 분석 프로그램
# - 실제 도면/내역서 기반 실증용 Streamlit 앱
# - 3D 시각화 중심
# ============================================================

st.set_page_config(
    page_title="세종 6-3 모듈러 분석 프로그램",
    page_icon="🏗️",
    layout="wide",
)

# ------------------------------------------------------------
# 0. 기본 데이터 (현재까지 확보된 도면 기준)
# ------------------------------------------------------------
PROJECT_INFO = {
    "project_name": "행복도시 6-3생활권 UR1,2BL 모듈러 공공주택건설사업",
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
    "module_length_m": 8.0,   # 대표값
    "module_height_m": 3.1,   # 시각화용 대표값
    "module_weight_t_est": 12.0,  # 추정값, 실제 구조자료 입수 시 수정 권장
}

UNIT_TYPES = pd.DataFrame([
    {"unit_type": "21A", "exclusive_area_m2": 21.0287, "contract_area_m2": 30.2830, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 7.8},
    {"unit_type": "21A2", "exclusive_area_m2": 21.0287, "contract_area_m2": 30.2830, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 7.8},
    {"unit_type": "21A1S", "exclusive_area_m2": 21.0287, "contract_area_m2": 30.2830, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 7.8},
    {"unit_type": "22T", "exclusive_area_m2": 22.8664, "contract_area_m2": 39.0008, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 8.0},
    {"unit_type": "24A", "exclusive_area_m2": 24.7765, "contract_area_m2": 34.6070, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 8.0},
    {"unit_type": "30T2", "exclusive_area_m2": 30.1872, "contract_area_m2": 46.8949, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 8.0},
    {"unit_type": "35TD1", "exclusive_area_m2": 36.5384, "contract_area_m2": 49.6634, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 8.0},
    {"unit_type": "37A1", "exclusive_area_m2": 37.4018, "contract_area_m2": 52.4428, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 8.0},
    {"unit_type": "38T", "exclusive_area_m2": 38.1678, "contract_area_m2": 56.6243, "module_count": 2, "unit_width_m": 6.6, "unit_depth_m": 8.0},
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

# 도면 기반으로 단순화한 동별/층별 3D 배치
# 실제 평면을 완벽 BIM 수준으로 재현하는 것이 아니라, 분석용 3D box model이다.
BUILDING_SPECS = {
    "201": {
        "origin": (0.0, 0.0, 0.0),
        "floors": {
            3: {"rows": [9, 6, 9], "corridor_width": 2.4},
            4: {"rows": [9, 6, 9], "corridor_width": 2.4},
            5: {"rows": [9, 7, 9], "corridor_width": 2.4},
            6: {"rows": [9, 7, 9], "corridor_width": 2.4},
            7: {"rows": [9, 5, 9], "corridor_width": 2.4},
        },
    },
    "202": {
        "origin": (85.0, 0.0, 0.0),
        "floors": {
            3: {"rows": [9, 7, 9], "corridor_width": 2.4},
            4: {"rows": [9, 7, 9], "corridor_width": 2.4},
            5: {"rows": [9, 8, 9], "corridor_width": 2.4},
            6: {"rows": [9, 8, 9], "corridor_width": 2.4},
            7: {"rows": [7, 6, 8], "corridor_width": 2.4},
        },
    },
}


# ------------------------------------------------------------
# 1. 도우미 함수
# ------------------------------------------------------------
def safe_number(x):
    try:
        if pd.isna(x):
            return None
        if isinstance(x, str):
            x = x.replace(",", "").replace("원", "").strip()
        return float(x)
    except Exception:
        return None


def format_currency_krw(x: float) -> str:
    return f"{x:,.0f} 원"


def add_box(fig: go.Figure, x: float, y: float, z: float, dx: float, dy: float, dz: float,
            color: str, name: Optional[str] = None, opacity: float = 0.95,
            line_color: str = "rgba(40,40,40,0.65)") -> go.Figure:
    # Plotly Mesh3d용 box vertices
    vertices = [
        (x, y, z), (x+dx, y, z), (x+dx, y+dy, z), (x, y+dy, z),
        (x, y, z+dz), (x+dx, y, z+dz), (x+dx, y+dy, z+dz), (x, y+dy, z+dz)
    ]
    X, Y, Z = zip(*vertices)
    i = [0, 0, 0, 1, 2, 4, 4, 5, 6, 4, 0, 1]
    j = [1, 2, 3, 2, 3, 5, 6, 6, 7, 0, 4, 5]
    k = [2, 3, 1, 5, 7, 6, 7, 2, 3, 5, 1, 6]

    fig.add_trace(go.Mesh3d(
        x=X, y=Y, z=Z, i=i, j=j, k=k,
        color=color, opacity=opacity, flatshading=True,
        hoverinfo="text",
        text=name if name else "module"
    ))

    # 외곽선
    edges = [
        (0,1),(1,2),(2,3),(3,0),
        (4,5),(5,6),(6,7),(7,4),
        (0,4),(1,5),(2,6),(3,7)
    ]
    for a, b in edges:
        fig.add_trace(go.Scatter3d(
            x=[X[a], X[b]], y=[Y[a], Y[b]], z=[Z[a], Z[b]],
            mode="lines",
            line=dict(color=line_color, width=4),
            hoverinfo="skip",
            showlegend=False
        ))
    return fig


def generate_building_modules(building_key: str,
                              module_w: float,
                              module_l: float,
                              module_h: float) -> List[Dict]:
    """
    도면 기반 반복 패턴을 단순화하여 3D box 좌표 생성.
    rows = [상단열, 중앙열, 하단열]의 모듈 개수
    """
    spec = BUILDING_SPECS[building_key]
    origin_x, origin_y, origin_z = spec["origin"]
    modules = []

    gap_x = 0.18
    gap_y = 0.30
    row_spacing = 10.5
    floor_gap = 0.15

    for floor, floor_info in spec["floors"].items():
        z = origin_z + (floor - 3) * (module_h + floor_gap)
        counts = floor_info["rows"]

        for row_idx, count in enumerate(counts):
            # 상단/중앙/하단 row 배치
            y = origin_y + row_idx * row_spacing
            # 중앙 row는 세로 배치 느낌, 나머지는 가로 배치
            if row_idx == 1:
                for n in range(count):
                    x = origin_x + n * (module_w + gap_x)
                    modules.append({
                        "building": building_key,
                        "floor": floor,
                        "x": x, "y": y, "z": z,
                        "dx": module_w, "dy": module_l * 0.72, "dz": module_h,
                        "name": f"{building_key}-{floor}F-middle-{n+1}"
                    })
            else:
                for n in range(count):
                    x = origin_x + n * (module_w + gap_x)
                    modules.append({
                        "building": building_key,
                        "floor": floor,
                        "x": x, "y": y, "z": z,
                        "dx": module_w, "dy": module_l * 0.52, "dz": module_h,
                        "name": f"{building_key}-{floor}F-row{row_idx+1}-{n+1}"
                    })

    return modules


def make_3d_figure(show_building_201: bool, show_building_202: bool,
                   floor_min: int, floor_max: int,
                   module_h: float) -> Tuple[go.Figure, pd.DataFrame]:
    fig = go.Figure()
    module_w = PROJECT_INFO["module_width_m"]
    module_l = PROJECT_INFO["module_length_m"]

    all_modules = []
    if show_building_201:
        all_modules.extend(generate_building_modules("201", module_w, module_l, module_h))
    if show_building_202:
        all_modules.extend(generate_building_modules("202", module_w, module_l, module_h))

    df = pd.DataFrame(all_modules)
    if df.empty:
        return fig, df

    df = df[(df["floor"] >= floor_min) & (df["floor"] <= floor_max)].copy()

    colors = {
        3: "#4e79a7",
        4: "#f28e2b",
        5: "#59a14f",
        6: "#e15759",
        7: "#9c755f",
    }

    for _, row in df.iterrows():
        fig = add_box(
            fig,
            row["x"], row["y"], row["z"],
            row["dx"], row["dy"], row["dz"],
            color=colors.get(int(row["floor"]), "#76b7b2"),
            name=row["name"]
        )

    # 저층부 podium/parking box (단순화)
    if show_building_201:
        fig = add_box(fig, -1.5, -2.0, -4.8, 36.0, 33.0, 4.4, color="#c7c7c7", opacity=0.55, name="201 저층부/포디움")
    if show_building_202:
        fig = add_box(fig, 83.5, -2.0, -4.8, 36.0, 33.0, 4.4, color="#c7c7c7", opacity=0.55, name="202 저층부/포디움")

    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            aspectmode="data",
            bgcolor="white",
            camera=dict(eye=dict(x=1.8, y=1.5, z=1.15)),
        ),
        showlegend=False,
    )
    return fig, df


def load_workbook_sheets(file) -> Dict[str, pd.DataFrame]:
    xls = pd.ExcelFile(file)
    sheets = {}
    for s in xls.sheet_names:
        try:
            sheets[s] = pd.read_excel(file, sheet_name=s, header=None)
        except Exception:
            pass
    return sheets


def summarize_sheet_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    숫자 비중이 큰 행들만 빠르게 요약.
    """
    rows = []
    for idx in range(len(df)):
        row = df.iloc[idx].tolist()
        nums = [safe_number(v) for v in row]
        nums = [v for v in nums if v is not None]
        text = " | ".join([str(v) for v in row if pd.notna(v) and str(v).strip() != ""])
        if len(nums) >= 2 and text:
            rows.append({
                "row_index": idx,
                "text": text[:300],
                "numeric_count": len(nums),
                "numeric_sum": sum(nums),
            })
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["numeric_count", "numeric_sum"], ascending=[False, False])
    return out


def extract_known_costs_from_uploaded_excel(file) -> pd.DataFrame:
    """
    현재 확보한 시트 구조를 자동 추적하려고 시도하되,
    완전히 자동화가 안 되는 경우를 대비해 키워드 기반 후보만 뽑는다.
    """
    xls = pd.ExcelFile(file)
    candidates = []

    keywords = ["원(총)", "집(건1)", "집(건2)", "내(건1)", "내(건2)", "원(1)", "원(2)"]

    for s in xls.sheet_names:
        if any(k in s for k in keywords):
            try:
                df = pd.read_excel(file, sheet_name=s, header=None)
                summarized = summarize_sheet_numeric(df).head(20).copy()
                summarized["sheet"] = s
                candidates.append(summarized)
            except Exception:
                continue

    if not candidates:
        return pd.DataFrame()

    out = pd.concat(candidates, ignore_index=True)
    return out[["sheet", "row_index", "numeric_count", "numeric_sum", "text"]]


# ------------------------------------------------------------
# 2. 사이드바
# ------------------------------------------------------------
st.sidebar.title("세종 6-3 분석 설정")

uploaded_excel = st.sidebar.file_uploader(
    "준공내역서 업로드 (.xlsx)", type=["xlsx", "xls"]
)

show_201 = st.sidebar.checkbox("201동 표시", value=True)
show_202 = st.sidebar.checkbox("202동 표시", value=True)

floor_range = st.sidebar.slider(
    "3D 표시 층 범위", min_value=3, max_value=7, value=(3, 7)
)

module_height = st.sidebar.slider(
    "3D 모듈 높이 (시각화용, m)",
    min_value=2.8, max_value=3.6, value=float(PROJECT_INFO["module_height_m"]), step=0.1
)

st.sidebar.markdown("---")
st.sidebar.caption("현재 앱은 세종 6-3 실제 사례 분석용입니다.")
st.sidebar.caption("3D는 분석용 block model이며, BIM 정밀모형은 아닙니다.")


# ------------------------------------------------------------
# 3. 상단 요약
# ------------------------------------------------------------
st.title("세종 6-3 UR1·2BL 모듈러 분석 프로그램")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("총 세대수", f'{PROJECT_INFO["num_units"]} 세대')
c2.metric("동수", f'{PROJECT_INFO["num_buildings"]} 개동')
c3.metric("지상층수", f'{PROJECT_INFO["above_floors"]} 층')
c4.metric("기준 모듈", f'{PROJECT_INFO["module_width_m"]:.1f} × {PROJECT_INFO["module_length_m"]:.1f} m')
c5.metric("추정 모듈중량", f'{PROJECT_INFO["module_weight_t_est"]:.0f} t')

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "3D 모델", "프로젝트 개요", "세대/모듈 DB", "층별 분석", "공사비 분석"
])


# ------------------------------------------------------------
# 4. 3D 모델 탭
# ------------------------------------------------------------
with tab1:
    st.subheader("3D 모듈 스택 모델")

    fig, module_df = make_3d_figure(
        show_building_201=show_201,
        show_building_202=show_202,
        floor_min=floor_range[0],
        floor_max=floor_range[1],
        module_h=module_height
    )
    st.plotly_chart(fig, use_container_width=True)

    if not module_df.empty:
        total_modules = len(module_df)
        est_total_weight = total_modules * PROJECT_INFO["module_weight_t_est"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("표시 모듈 수", f"{total_modules} 개")
        col2.metric("예상 운송횟수", f"{total_modules} 회")
        col3.metric("표시 구간 총 추정중량", f"{est_total_weight:,.0f} t")
        col4.metric("모듈 평균 footprint", f'{PROJECT_INFO["module_width_m"] * PROJECT_INFO["module_length_m"]:.1f} ㎡')

        summary = (
            module_df.groupby(["building", "floor"])
            .size()
            .reset_index(name="module_count")
            .sort_values(["building", "floor"])
        )
        st.dataframe(summary, use_container_width=True, hide_index=True)

    st.info(
        "이 3D 모델은 도면에 나타난 반복 배치를 기반으로 만든 분석용 block model입니다. "
        "실제 구조 프레임, 접합부, 발코니, 코어 상세, 지붕경사까지 완전 재현한 BIM 모델은 아닙니다."
    )


# ------------------------------------------------------------
# 5. 프로젝트 개요 탭
# ------------------------------------------------------------
with tab2:
    st.subheader("프로젝트 기본 정보")

    left, right = st.columns([1.2, 1])
    with left:
        info_df = pd.DataFrame([
            ["사업명", PROJECT_INFO["project_name"]],
            ["대지면적", f'{PROJECT_INFO["site_area_m2"]:,.3f} ㎡'],
            ["연면적", f'{PROJECT_INFO["gross_floor_area_m2"]:,.3f} ㎡'],
            ["건축면적", f'{PROJECT_INFO["building_area_m2"]:,.3f} ㎡'],
            ["동수", f'{PROJECT_INFO["num_buildings"]}'],
            ["세대수", f'{PROJECT_INFO["num_units"]}'],
            ["지상층수", f'{PROJECT_INFO["above_floors"]}층'],
            ["지하층수", f'B{PROJECT_INFO["basement_floors"]}'],
        ], columns=["항목", "값"])
        st.dataframe(info_df, use_container_width=True, hide_index=True)

    with right:
        road_df = pd.DataFrame([
            ["북측 도로", f'{PROJECT_INFO["north_road_m"]} m'],
            ["남측 도로", f'{PROJECT_INFO["south_road_m"]} m'],
            ["동측 도로", f'{PROJECT_INFO["east_road_m"]} m'],
            ["서측 도로", f'{PROJECT_INFO["west_road_m"]} m'],
        ], columns=["방향", "폭"])
        st.dataframe(road_df, use_container_width=True, hide_index=True)

    st.markdown("### 해석 포인트")
    st.markdown(
        """
- 본 사례는 **실제 모듈러 공공주택 준공 사례**로서, 도면과 준공내역서를 함께 연결할 수 있다는 점이 핵심입니다.
- 도면상 반복되는 세대 폭은 **6.6m**, 기본 모듈 폭은 **3.3m**로 읽히며, 기본적으로 **2-module 조합 세대**로 볼 수 있습니다.
- 부지 외곽 도로 폭은 **18m / 43m / 6m / 10m**로 확인되어, 특수 운송차량 및 대형 장비 접근성 검토의 기준이 됩니다.
        """
    )


# ------------------------------------------------------------
# 6. 세대/모듈 DB 탭
# ------------------------------------------------------------
with tab3:
    st.subheader("세대 타입 및 모듈 데이터베이스")

    df = UNIT_TYPES.copy()
    df["module_width_m"] = PROJECT_INFO["module_width_m"]
    df["module_length_m_repr"] = PROJECT_INFO["module_length_m"]
    df["module_area_m2"] = PROJECT_INFO["module_width_m"] * PROJECT_INFO["module_length_m"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### 세대수 집계")
    st.dataframe(UNIT_COUNTS, use_container_width=True, hide_index=True)

    total_modules_est = 216 * 2
    col1, col2, col3 = st.columns(3)
    col1.metric("1세대당 기본 모듈 수", "2 개")
    col2.metric("총 추정 모듈 수", f"{total_modules_est} 개")
    col3.metric("모듈 1개 면적 대표값", f'{PROJECT_INFO["module_width_m"] * PROJECT_INFO["module_length_m"]:.1f} ㎡')

    st.markdown(
        """
### 현재 정리 방식
- **기준 모듈 폭**: 3.3m
- **기준 세대 폭**: 6.6m
- **세대당 기본 모듈 수**: 2개
- **대표 모듈 길이**: 8.0m  
- 추후 구조도/제작도에서 실제 모듈 길이 및 중량이 확인되면 이 값들을 갱신하면 됩니다.
        """
    )


# ------------------------------------------------------------
# 7. 층별 분석 탭
# ------------------------------------------------------------
with tab4:
    st.subheader("층별 구성 분석")

    floor_rows = []
    for b_key, spec in BUILDING_SPECS.items():
        for floor, floor_info in spec["floors"].items():
            module_count = sum(floor_info["rows"])
            est_units = math.floor(module_count / 2)
            floor_rows.append({
                "building": b_key,
                "floor": floor,
                "row_pattern": floor_info["rows"],
                "module_count_est": module_count,
                "unit_count_est": est_units,
                "use": "주거 반복층" if floor >= 3 else "기타",
            })

    floor_df = pd.DataFrame(floor_rows).sort_values(["building", "floor"])
    st.dataframe(floor_df, use_container_width=True, hide_index=True)

    pivot = floor_df.pivot(index="floor", columns="building", values="module_count_est").fillna(0)
    if not pivot.empty:
        st.bar_chart(pivot)

    st.markdown(
        """
### 층별 해석
- **1층**: 공용부 / 판매시설 / 부대시설 비중이 큼  
- **2층**: 전이 성격 및 공용부 조정층  
- **3층~7층**: 모듈러 주거 반복층  
- 따라서 지금 프로그램의 3D 표현은 **3층~7층 반복층부**를 중심으로 만들었습니다.
        """
    )


# ------------------------------------------------------------
# 8. 공사비 분석 탭
# ------------------------------------------------------------
with tab5:
    st.subheader("준공내역서 기반 공사비 분석")

    st.markdown("### 현재 확보된 핵심 비용값")
    known_costs = pd.DataFrame([
        ["총 공사비", 55789400000],
        ["순공사비", 50481520337],
        ["일반관리비", 2775909982],
        ["매입부가세(면세)", 2338615135],
        ["부가가치세(과세)", 193354546],
        ["UR1BL 지상(3~7층) 재료비", 4134104031],
        ["UR1BL 지상(3~7층) 노무비", 2880372833],
        ["UR1BL 지상(3~7층) 경비", 1927062986],
        ["UR2BL 지상(3~7층) 재료비", 5131881531],
        ["UR2BL 지상(3~7층) 노무비", 3503636821],
        ["UR2BL 지상(3~7층) 경비", 2351392462],
    ], columns=["항목", "금액_원"])

    known_costs["금액표시"] = known_costs["금액_원"].apply(format_currency_krw)
    st.dataframe(known_costs[["항목", "금액표시"]], use_container_width=True, hide_index=True)

    total_cost = 55789400000
    cost_per_unit = total_cost / PROJECT_INFO["num_units"]
    cost_per_gfa = total_cost / PROJECT_INFO["gross_floor_area_m2"]
    cost_per_module = total_cost / (PROJECT_INFO["num_units"] * 2)

    c1, c2, c3 = st.columns(3)
    c1.metric("세대당 총 공사비", format_currency_krw(cost_per_unit))
    c2.metric("연면적 ㎡당 총 공사비", format_currency_krw(cost_per_gfa))
    c3.metric("모듈당 단순 환산 공사비", format_currency_krw(cost_per_module))

    st.markdown("### 업로드한 준공내역서 자동 탐색")
    if uploaded_excel is not None:
        try:
            candidate_df = extract_known_costs_from_uploaded_excel(uploaded_excel)
            if candidate_df.empty:
                st.warning("자동 탐색에서 뚜렷한 비용 후보를 찾지 못했습니다. 시트명을 직접 확인해 주세요.")
            else:
                st.dataframe(candidate_df, use_container_width=True, hide_index=True)

            with st.expander("업로드한 엑셀의 전체 시트명 보기"):
                xls = pd.ExcelFile(uploaded_excel)
                st.write(xls.sheet_names)

        except Exception as e:
            st.error(f"엑셀 분석 중 오류가 발생했습니다: {e}")
    else:
        st.info("좌측 사이드바에서 준공내역서 파일을 업로드하면, 비용 관련 시트 후보를 자동 탐색합니다.")


st.markdown("---")
st.caption(
    "주의: 이 앱의 3D 모델은 분석용 block model입니다. "
    "정밀 구조/BIM 재현을 위해서는 모듈 중량, 구조 프레임, 접합 상세, 실제 층별 타입 배열을 추가 확보해 갱신해야 합니다."
)

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="수익성극대화를위한부지맞춤형신축매입임대사업모델제안",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None


# ============================================================
# STYLE
# ============================================================
st.markdown(
    """
<style>
:root {
    --bg: #f5f6f8;
    --card: #ffffff;
    --line: #d8dde6;
    --text: #1f2937;
    --muted: #6b7280;
    --primary: #1f3a5f;
    --primary-soft: #eef4fb;
    --accent: #3b82f6;
    --ok-bg: #ecfdf3;
    --ok-text: #166534;
    --warn-bg: #fffbeb;
    --warn-text: #a16207;
    --bad-bg: #fef2f2;
    --bad-text: #b91c1c;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg);
    color: var(--text);
}

.block-container {
    max-width: 1650px;
    padding-top: 0.8rem;
    padding-bottom: 2rem;
}

[data-testid="stSidebar"] {
    background: #eceff3;
    border-right: 1px solid #cfd6df;
    min-width: 430px !important;
    max-width: 430px !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding: 1rem 1rem 1.5rem 1rem;
}

[data-testid="stSidebar"] .stNumberInput input,
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] textarea {
    min-height: 46px !important;
    border-radius: 10px !important;
    border: 1px solid #cfd6df !important;
    background: #ffffff !important;
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] > div {
    min-height: 46px !important;
    border-radius: 10px !important;
    border: 1px solid #cfd6df !important;
    background: #ffffff !important;
    color: #111827 !important;
}

[data-testid="stSidebar"] .stRadio,
[data-testid="stSidebar"] .stSlider,
[data-testid="stSidebar"] .stNumberInput,
[data-testid="stSidebar"] .stTextInput,
[data-testid="stSidebar"] .stSelectbox {
    margin-bottom: 0.55rem;
}

.sidebar-group {
    background: #ffffff;
    border: 1px solid #d7dde6;
    border-radius: 16px;
    padding: 0.95rem 0.95rem 0.3rem 0.95rem;
    margin-bottom: 0.95rem;
}

.sidebar-group-title {
    font-size: 16px;
    font-weight: 800;
    color: var(--primary);
    margin-bottom: 0.8rem;
}

.section-card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1.1rem 1.15rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
}

.section-title {
    font-size: 18px;
    font-weight: 800;
    color: var(--primary);
    margin-bottom: 0.8rem;
}

.section-subtitle {
    font-size: 14px;
    font-weight: 700;
    color: #334155;
    margin-bottom: 0.4rem;
}

.metric-card {
    background: white;
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 1rem;
    min-height: 115px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.03);
    margin-bottom: 1rem;
}

.metric-label {
    font-size: 13px;
    color: var(--muted);
    margin-bottom: 0.35rem;
    font-weight: 700;
}

.metric-value {
    font-size: 24px;
    font-weight: 900;
    color: var(--text);
    line-height: 1.2;
}

.metric-note {
    font-size: 12px;
    color: var(--muted);
    margin-top: 0.35rem;
    line-height: 1.45;
}

.big-result {
    background: white;
    border: 1px solid var(--line);
    border-left: 6px solid var(--accent);
    border-radius: 18px;
    padding: 1.1rem 1.2rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
}

.big-result-title {
    font-size: 14px;
    color: var(--muted);
    font-weight: 700;
    margin-bottom: 0.2rem;
}

.big-result-value {
    font-size: 31px;
    font-weight: 900;
    color: var(--primary);
}

.badge {
    display: inline-block;
    padding: 0.28rem 0.68rem;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
}
.badge-ok { background: var(--ok-bg); color: var(--ok-text); }
.badge-warn { background: var(--warn-bg); color: var(--warn-text); }
.badge-bad { background: var(--bad-bg); color: var(--bad-text); }
.badge-neutral { background: #eff6ff; color: #1d4ed8; }

.stTabs [data-baseweb="tab-list"] {
    gap: 0.35rem;
}
.stTabs [data-baseweb="tab"] {
    background: white;
    border: 1px solid var(--line);
    border-radius: 10px;
    padding-left: 0.9rem;
    padding-right: 0.9rem;
}
.stTabs [aria-selected="true"] {
    background: var(--primary-soft) !important;
    color: var(--primary) !important;
    border-color: #c6d5e7 !important;
}

.stButton > button {
    width: 100%;
    min-height: 3rem;
    border-radius: 12px;
    border: 1px solid #cfd6df;
    background: #ffffff;
    color: #1f3a5f;
    font-weight: 800;
    font-size: 16px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
}
.stButton > button:hover {
    background: #f8fafc;
    border-color: #94a3b8;
    color: #16324f;
}

.small-note {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.55;
}

hr {
    border: 0;
    height: 1px;
    background: #e5e7eb;
    margin: 1rem 0 1rem 0;
}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# DATA MODELS
# ============================================================
@dataclass
class ModuleType:
    name: str
    structure: str
    width_m: float
    length_m: float
    height_m: float
    weight_t_min: float
    weight_t_max: float
    openness: str
    desc: str
    recommended_floor_range: str
    representative_trailer: str
    recommended_crane_group: str
    prefab_rate_min: float
    prefab_rate_max: float
    install_difficulty_coeff: float
    transport_difficulty_coeff: float
    large_opening: bool
    repeatability_score: int
    public_space_score: int
    open_plan_score: int
    floor_min: int
    floor_max: int
    base_efficiency_ratio: float

    @property
    def weight_t_default(self) -> float:
        return round((self.weight_t_min + self.weight_t_max) / 2, 2)

    @property
    def prefab_rate_text(self) -> str:
        return f"{int(self.prefab_rate_min * 100)}~{int(self.prefab_rate_max * 100)}%"


@dataclass
class TrailerSpec:
    name: str
    trailer_type: str
    deck_length_m: float
    deck_width_m: float
    deck_height_m: float
    payload_t: float
    total_vehicle_length_m: float
    permit_width_limit_m: float
    permit_height_limit_m: float
    permit_length_limit_m: float
    note: str


@dataclass
class CraneSpec:
    name: str
    crane_group: str
    max_capacity_t: float
    max_radius_m: float
    tip_load_t: float
    max_hook_height_m: float
    setup_type: str
    monthly_rent_krw: Optional[float] = None
    setup_cost_krw: Optional[float] = None
    hourly_cost_krw: Optional[float] = None
    footprint_desc: str = ""


# ============================================================
# DATABASES
# ============================================================
MODULE_DB: Dict[str, ModuleType] = {
    "Small load-bearing wall module": ModuleType(
        name="Small load-bearing wall module",
        structure="내력벽형",
        width_m=3.0,
        length_m=8.0,
        height_m=3.2,
        weight_t_min=8.0,
        weight_t_max=10.0,
        openness="corner-supported",
        desc="소형 반복형 세대에 적합하고 운송·설치 리스크가 낮은 기본형 모듈",
        recommended_floor_range="저층~중층",
        representative_trailer="저상 트레일러",
        recommended_crane_group="트럭크레인, 소형 타워크레인",
        prefab_rate_min=0.70,
        prefab_rate_max=0.90,
        install_difficulty_coeff=1.00,
        transport_difficulty_coeff=1.00,
        large_opening=False,
        repeatability_score=5,
        public_space_score=2,
        open_plan_score=1,
        floor_min=1,
        floor_max=8,
        base_efficiency_ratio=0.88,
    ),
    "Corner-supported standard module": ModuleType(
        name="Corner-supported standard module",
        structure="코너지지 표준형",
        width_m=3.2,
        length_m=10.0,
        height_m=3.4,
        weight_t_min=10.0,
        weight_t_max=14.0,
        openness="corner-supported",
        desc="표준 주거 세대 대응이 쉬운 범용형 모듈",
        recommended_floor_range="저층~중층",
        representative_trailer="저상 트레일러",
        recommended_crane_group="트럭크레인, 타워크레인",
        prefab_rate_min=0.60,
        prefab_rate_max=0.85,
        install_difficulty_coeff=1.20,
        transport_difficulty_coeff=1.15,
        large_opening=False,
        repeatability_score=4,
        public_space_score=3,
        open_plan_score=2,
        floor_min=1,
        floor_max=12,
        base_efficiency_ratio=0.82,
    ),
    "Corner-supported stacked module": ModuleType(
        name="Corner-supported stacked module",
        structure="코너지지 적층형",
        width_m=3.3,
        length_m=10.5,
        height_m=3.4,
        weight_t_min=12.0,
        weight_t_max=18.0,
        openness="corner-supported",
        desc="적층 안정성을 우선하는 다층 모듈러 대응형",
        recommended_floor_range="중층",
        representative_trailer="저상 트레일러",
        recommended_crane_group="타워크레인",
        prefab_rate_min=0.60,
        prefab_rate_max=0.80,
        install_difficulty_coeff=1.25,
        transport_difficulty_coeff=1.20,
        large_opening=False,
        repeatability_score=4,
        public_space_score=3,
        open_plan_score=2,
        floor_min=4,
        floor_max=15,
        base_efficiency_ratio=0.80,
    ),
    "Open-sided module": ModuleType(
        name="Open-sided module",
        structure="오픈사이드 / 라멘형",
        width_m=3.5,
        length_m=12.0,
        height_m=3.5,
        weight_t_min=16.0,
        weight_t_max=22.0,
        openness="open-sided",
        desc="측면 개방성이 커서 공용공간이나 대공간 조합에 유리한 모듈",
        recommended_floor_range="저층~중층",
        representative_trailer="특수 저상/더블드롭 검토",
        recommended_crane_group="중대형 타워크레인, 크롤러크레인",
        prefab_rate_min=0.50,
        prefab_rate_max=0.70,
        install_difficulty_coeff=1.50,
        transport_difficulty_coeff=1.35,
        large_opening=True,
        repeatability_score=2,
        public_space_score=5,
        open_plan_score=5,
        floor_min=1,
        floor_max=10,
        base_efficiency_ratio=0.68,
    ),
    "Open-ended module": ModuleType(
        name="Open-ended module",
        structure="오픈엔드 프레임형",
        width_m=3.3,
        length_m=9.0,
        height_m=3.4,
        weight_t_min=11.0,
        weight_t_max=16.0,
        openness="open-ended",
        desc="단부 개방을 통해 연결성과 내부 연속 공간 확보에 유리한 모듈",
        recommended_floor_range="저층~중층",
        representative_trailer="저상 트레일러",
        recommended_crane_group="타워크레인",
        prefab_rate_min=0.60,
        prefab_rate_max=0.80,
        install_difficulty_coeff=1.20,
        transport_difficulty_coeff=1.20,
        large_opening=True,
        repeatability_score=3,
        public_space_score=3,
        open_plan_score=3,
        floor_min=1,
        floor_max=10,
        base_efficiency_ratio=0.76,
    ),
    "Corridor-type combined module": ModuleType(
        name="Corridor-type combined module",
        structure="복도형 조합 모듈",
        width_m=3.0,
        length_m=8.5,
        height_m=3.2,
        weight_t_min=8.0,
        weight_t_max=12.0,
        openness="corner-supported",
        desc="복도형 또는 중복도형 반복 배치에 적합한 유형",
        recommended_floor_range="저층~중층",
        representative_trailer="저상 트레일러",
        recommended_crane_group="트럭크레인, 타워크레인",
        prefab_rate_min=0.70,
        prefab_rate_max=0.90,
        install_difficulty_coeff=1.10,
        transport_difficulty_coeff=1.05,
        large_opening=False,
        repeatability_score=5,
        public_space_score=3,
        open_plan_score=1,
        floor_min=1,
        floor_max=12,
        base_efficiency_ratio=0.86,
    ),
    "Large-span institutional module": ModuleType(
        name="Large-span institutional module",
        structure="라멘형 / 하이브리드 보강형",
        width_m=3.6,
        length_m=12.0,
        height_m=3.6,
        weight_t_min=18.0,
        weight_t_max=25.0,
        openness="open-sided",
        desc="대공간 수요가 큰 시설형 프로젝트에 대응하는 고중량 모듈",
        recommended_floor_range="저층~중층",
        representative_trailer="특수 트레일러",
        recommended_crane_group="중대형 타워크레인, 크롤러크레인",
        prefab_rate_min=0.45,
        prefab_rate_max=0.65,
        install_difficulty_coeff=1.60,
        transport_difficulty_coeff=1.45,
        large_opening=True,
        repeatability_score=2,
        public_space_score=5,
        open_plan_score=5,
        floor_min=1,
        floor_max=8,
        base_efficiency_ratio=0.62,
    ),
    "Hybrid / podium + modular upper floors": ModuleType(
        name="Hybrid / podium + modular upper floors",
        structure="하부 RC + 상부 모듈러",
        width_m=3.35,
        length_m=19.0,
        height_m=4.5,
        weight_t_min=30.0,
        weight_t_max=40.0,
        openness="hybrid",
        desc="하부 포디움과 상부 모듈러를 결합하는 도심형 하이브리드 대안",
        recommended_floor_range="중층 이상",
        representative_trailer="특수 트레일러",
        recommended_crane_group="타워크레인, 러핑크레인",
        prefab_rate_min=0.40,
        prefab_rate_max=0.70,
        install_difficulty_coeff=1.80,
        transport_difficulty_coeff=1.60,
        large_opening=True,
        repeatability_score=4,
        public_space_score=4,
        open_plan_score=4,
        floor_min=6,
        floor_max=20,
        base_efficiency_ratio=0.74,
    ),
}

TRAILER_DB: List[TrailerSpec] = [
    TrailerSpec(
        name="평판 트레일러",
        trailer_type="Flat trailer",
        deck_length_m=12.41,
        deck_width_m=2.50,
        deck_height_m=1.41,
        payload_t=24.5,
        total_vehicle_length_m=16.0,
        permit_width_limit_m=2.50,
        permit_height_limit_m=4.00,
        permit_length_limit_m=16.7,
        note="일반 운행 기준에 가장 근접한 기본형",
    ),
    TrailerSpec(
        name="평판 트레일러 40FT",
        trailer_type="Flat trailer 40FT",
        deck_length_m=12.38,
        deck_width_m=2.47,
        deck_height_m=1.40,
        payload_t=24.5,
        total_vehicle_length_m=16.0,
        permit_width_limit_m=2.50,
        permit_height_limit_m=4.00,
        permit_length_limit_m=16.7,
        note="컨테이너형 운송 기반",
    ),
    TrailerSpec(
        name="저상 트레일러 (Single-drop deck)",
        trailer_type="Low-bed",
        deck_length_m=12.97,
        deck_width_m=2.75,
        deck_height_m=0.55,
        payload_t=26.0,
        total_vehicle_length_m=17.0,
        permit_width_limit_m=3.50,
        permit_height_limit_m=4.30,
        permit_length_limit_m=17.0,
        note="특수허가 활용 시 가장 현실적인 모듈 운송 장비",
    ),
    TrailerSpec(
        name="저상 트레일러 (Double-drop deck)",
        trailer_type="Double-drop",
        deck_length_m=13.42,
        deck_width_m=2.75,
        deck_height_m=0.50,
        payload_t=26.0,
        total_vehicle_length_m=17.0,
        permit_width_limit_m=3.50,
        permit_height_limit_m=4.30,
        permit_length_limit_m=17.0,
        note="높이 여유 확보에 유리",
    ),
    TrailerSpec(
        name="풀트레일러 특수형",
        trailer_type="Full trailer",
        deck_length_m=16.00,
        deck_width_m=2.50,
        deck_height_m=1.00,
        payload_t=28.0,
        total_vehicle_length_m=20.0,
        permit_width_limit_m=3.50,
        permit_height_limit_m=4.30,
        permit_length_limit_m=20.0,
        note="장척물·특수허가 검토용",
    ),
]

CRANE_DB: List[CraneSpec] = [
    CraneSpec("Truck Crane 25t", "트럭크레인", 25.0, 30.0, 2.5, 45.0, "단기/이동식", hourly_cost_krw=60000, footprint_desc="아웃트리거 전개 공간 필요"),
    CraneSpec("Truck Crane 40t", "트럭크레인", 40.0, 39.0, 4.0, 44.0, "단기/이동식", hourly_cost_krw=70000, footprint_desc="아웃트리거 전개 공간 필요"),
    CraneSpec("Tower Crane 8t", "타워크레인", 8.0, 60.0, 1.5, 60.0, "고정식", monthly_rent_krw=14500000, setup_cost_krw=28000000, footprint_desc="기초 및 설치해체 계획 필요"),
    CraneSpec("Tower Crane 10t", "타워크레인", 10.0, 65.0, 2.0, 70.0, "고정식", monthly_rent_krw=15700000, setup_cost_krw=28000000, footprint_desc="기초 및 설치해체 계획 필요"),
    CraneSpec("Tower Crane 12t", "타워크레인", 12.0, 70.0, 2.4, 80.0, "고정식", monthly_rent_krw=16900000, setup_cost_krw=28000000, footprint_desc="기초 및 설치해체 계획 필요"),
    CraneSpec("Luffing Crane 12t", "러핑크레인", 12.0, 60.0, 2.6, 200.0, "도심 고층형", monthly_rent_krw=21000000, setup_cost_krw=35000000, footprint_desc="좁은 회전공간에 유리"),
    CraneSpec("Luffing Crane 24t", "러핑크레인", 24.0, 60.0, 4.0, 210.0, "도심 고층형", monthly_rent_krw=26000000, setup_cost_krw=40000000, footprint_desc="고층·도심형"),
    CraneSpec("Crawler Crane 100t", "크롤러크레인", 100.0, 52.0, 8.0, 64.0, "대형/야적장형", hourly_cost_krw=120000, footprint_desc="넓은 작업장 필요"),
]


# ============================================================
# UTILS
# ============================================================
def format_krw(value: float) -> str:
    return f"{int(round(value)):,}원"


def format_area(value: float) -> str:
    return f"{value:,.2f}㎡"


def badge_html(label: str) -> str:
    if label in ["가능", "모듈러 우세", "낮음", "안전한 편"]:
        cls = "badge badge-ok"
    elif label in ["조건부 가능", "조건부 모듈러 우세", "중간", "주의 필요", "허가 필요"]:
        cls = "badge badge-warn"
    elif label in ["불가", "RC 우세", "높음", "매우 높음", "부적합"]:
        cls = "badge badge-bad"
    else:
        cls = "badge badge-neutral"
    return f"<span class='{cls}'>{label}</span>"


def metric_box(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def transport_risk_bucket(score: float) -> str:
    if score < 9:
        return "낮음"
    if score < 17:
        return "중간"
    if score < 26:
        return "높음"
    return "매우 높음"


def lifting_margin_grade(margin: float) -> str:
    if margin >= 1.30:
        return "안전한 편"
    if margin >= 1.10:
        return "주의 필요"
    if margin >= 1.00:
        return "매우 민감"
    return "불가"


def interpolate_allowable_load(crane: CraneSpec, radius_m: float) -> float:
    radius = min(radius_m, crane.max_radius_m)
    if radius <= 5:
        return crane.max_capacity_t
    slope = (crane.tip_load_t - crane.max_capacity_t) / max(crane.max_radius_m - 5, 1)
    allowable = crane.max_capacity_t + slope * (radius - 5)
    return max(0.0, allowable)


def estimate_module_count(gross_area_m2: float, length_m: float, width_m: float, efficiency: float) -> int:
    module_effective_area = length_m * width_m * efficiency
    if module_effective_area <= 0:
        return 0
    return max(1, math.ceil(gross_area_m2 / module_effective_area))


def auto_select_module(
    building_use: str,
    floors: int,
    repeatability_score: int,
    public_space_ratio: int,
    open_plan_need: int,
    road_width_m: float,
    staging_area_m2: float,
) -> Tuple[ModuleType, List[Dict[str, object]]]:
    rows = []
    for module in MODULE_DB.values():
        score = 0.0
        reasons = []

        repeat_fit = 5 - abs(module.repeatability_score - repeatability_score)
        public_fit = 5 - abs(module.public_space_score - public_space_ratio)
        open_fit = 5 - abs(module.open_plan_score - open_plan_need)

        score += repeat_fit * 3
        score += public_fit * 2
        score += open_fit * 2

        reasons.append(f"반복형 적합도 {repeat_fit}/5")
        reasons.append(f"공용공간 적합도 {public_fit}/5")
        reasons.append(f"개방형 적합도 {open_fit}/5")

        if module.floor_min <= floors <= module.floor_max:
            score += 10
            reasons.append("권장 층수 범위 적합")
        else:
            penalty = min(abs(floors - module.floor_min), abs(floors - module.floor_max))
            score -= penalty
            reasons.append(f"권장 층수 이탈 -{penalty}")

        if road_width_m < 4:
            score -= 10
            reasons.append("도로폭 부족")
        elif road_width_m < 6 and module.transport_difficulty_coeff > 1.3:
            score -= 4
            reasons.append("좁은 도로폭에서 불리")

        if staging_area_m2 < 150 and module.install_difficulty_coeff >= 1.5:
            score -= 3
            reasons.append("적치공간 부족")

        if building_use in ["공동주택", "기숙사"] and module.repeatability_score >= 4:
            score += 5
        if building_use in ["학교", "병원", "업무시설"] and module.public_space_score >= 4:
            score += 5
        if building_use == "복합용도" and module.name == "Hybrid / podium + modular upper floors":
            score += 6

        rows.append(
            {
                "module": module,
                "score": round(score, 2),
                "reasons": reasons,
            }
        )

    rows.sort(key=lambda x: x["score"], reverse=True)
    return rows[0]["module"], rows


def recommend_structure(module_name: str, repeatability_score: int, open_plan_need: int, public_space_ratio: int) -> str:
    if module_name == "Small load-bearing wall module":
        return "내력벽형"
    if module_name in ["Corner-supported standard module", "Corner-supported stacked module", "Corridor-type combined module"]:
        return "코너지지형"
    if module_name in ["Open-sided module", "Large-span institutional module"]:
        return "오픈사이드 / 라멘형"
    if module_name == "Open-ended module":
        return "오픈엔드형"
    if module_name == "Hybrid / podium + modular upper floors":
        return "하부 RC + 상부 모듈러"
    if repeatability_score >= 4 and open_plan_need <= 2:
        return "내력벽형"
    if public_space_ratio >= 4 or open_plan_need >= 4:
        return "라멘형"
    return "코너지지형"


def recommend_trailer(module_length_m: float, module_width_m: float, module_height_m: float, module_weight_t: float) -> List[Dict[str, object]]:
    rows = []
    for trailer in TRAILER_DB:
        transport_height_m = trailer.deck_height_m + module_height_m
        permit_needed = (
            module_width_m > 2.5
            or transport_height_m > 4.0
            or trailer.total_vehicle_length_m > 16.7
        )
        feasible = (
            module_length_m <= trailer.deck_length_m + 1.0
            and module_width_m <= trailer.permit_width_limit_m
            and transport_height_m <= trailer.permit_height_limit_m
            and module_weight_t <= trailer.payload_t
            and trailer.total_vehicle_length_m <= trailer.permit_length_limit_m + 3.0
        )

        suitability = 0
        if feasible:
            suitability += 10
        suitability -= max(0.0, module_width_m - 2.5) * 10
        suitability -= max(0.0, transport_height_m - 4.0) * 8
        suitability -= max(0.0, module_weight_t - trailer.payload_t) * 5

        rows.append(
            {
                "운송장비": trailer.name,
                "장비유형": trailer.trailer_type,
                "적재길이(m)": trailer.deck_length_m,
                "적재폭(m)": trailer.deck_width_m,
                "적재높이(m)": trailer.deck_height_m,
                "최대적재량(t)": trailer.payload_t,
                "운송높이(m)": round(transport_height_m, 2),
                "특수허가필요": "예" if permit_needed else "아니오",
                "적합성": "적합" if feasible else "부적합",
                "점수": round(suitability, 1),
                "비고": trailer.note,
            }
        )
    rows.sort(key=lambda x: (x["적합성"] != "적합", -x["점수"]))
    return rows


def evaluate_transport_legal(
    module_width_m: float,
    module_length_m: float,
    module_height_m: float,
    module_weight_t: float,
    trailer_row: Dict[str, object],
    road_width_m: float,
    turn_condition: str,
    obstacle_level: str,
    bridge_tunnel_height_limit_m: float,
    managed_road_42m: bool,
    illegal_parking_constant: str,
) -> Dict[str, object]:
    transport_height_m = float(trailer_row["운송높이(m)"])
    legal_height = 4.2 if managed_road_42m else 4.0

    permit_reasons = []
    impossible_reasons = []

    if module_width_m > 2.5:
        permit_reasons.append("폭 2.5m 초과")
    if transport_height_m > legal_height:
        permit_reasons.append(f"운송높이 {legal_height:.1f}m 초과")
    if module_length_m > 16.7:
        permit_reasons.append("모듈 길이 16.7m 초과")
    if module_weight_t > 40.0:
        permit_reasons.append("총중량 40t 초과 가능성")
    if road_width_m < 4.0:
        impossible_reasons.append("도로폭 4m 미만")
    if turn_condition == "협소 코너 다수/U턴 필요":
        impossible_reasons.append("회전 조건이 매우 불리")
    if obstacle_level == "전면부 장애 심함":
        impossible_reasons.append("전면부 장애 심함")
    if bridge_tunnel_height_limit_m > 0 and transport_height_m > bridge_tunnel_height_limit_m:
        impossible_reasons.append("교량/터널 높이 제한 초과")

    caution_reasons = []
    if road_width_m < 6.0 and road_width_m >= 4.0:
        caution_reasons.append("도로폭 4~6m")
    if turn_condition == "코너 2개 이상":
        caution_reasons.append("코너 2개 이상")
    if obstacle_level == "전선/가로수 일부":
        caution_reasons.append("전선/가로수 일부")
    if illegal_parking_constant == "중간":
        caution_reasons.append("상시 불법주정차 중간")
    elif illegal_parking_constant == "높음":
        caution_reasons.append("상시 불법주정차 높음")

    if impossible_reasons:
        status = "불가"
    elif permit_reasons:
        status = "조건부 가능"
    else:
        status = "가능"

    return {
        "status": status,
        "permit_needed": len(permit_reasons) > 0,
        "transport_height_m": transport_height_m,
        "legal_height_limit_m": legal_height,
        "permit_reasons": permit_reasons,
        "impossible_reasons": impossible_reasons,
        "caution_reasons": caution_reasons,
        "all_reasons": permit_reasons + impossible_reasons + caution_reasons if (permit_reasons + impossible_reasons + caution_reasons) else ["주요 제약 없음"],
    }


def transport_risk_score(
    module_width_m: float,
    module_length_m: float,
    transport_height_m: float,
    module_weight_t: float,
    turn_condition: str,
    obstacle_level: str,
    pavement_level: str,
    module_form: str,
    transport_difficulty_coeff: float,
) -> Tuple[int, List[str]]:
    score = 0
    reasons = []

    width_score = 0 if module_width_m <= 2.5 else 1 if module_width_m <= 3.0 else 2 if module_width_m <= 3.5 else 3
    length_score = 0 if module_length_m <= 10 else 1 if module_length_m <= 14 else 2 if module_length_m <= 18 else 3
    height_score = 0 if transport_height_m <= 4.0 else 2 if transport_height_m <= 4.3 else 3
    weight_score = 0 if module_weight_t <= 15 else 1 if module_weight_t <= 25 else 2 if module_weight_t <= 35 else 3

    turn_map = {"직진 위주": 0, "코너 1개": 1, "코너 2개 이상": 2, "협소 코너 다수/U턴 필요": 3}
    obstacle_map = {"없음": 0, "경미": 1, "전선/가로수 일부": 2, "전면부 장애 심함": 3}
    pavement_map = {"양호": 0, "보통": 1, "경사/포장불량 일부": 2, "급경사/불량 심함": 3}
    form_map = {"corner-supported": 0, "open-ended": 1, "open-sided": 2, "hybrid": 3, "대개구부/비정형": 3}

    score += width_score
    score += length_score
    score += height_score
    score += weight_score
    score += turn_map[turn_condition]
    score += obstacle_map[obstacle_level]
    score += pavement_map[pavement_level]
    score += form_map.get(module_form, 2)

    coeff_bonus = round((transport_difficulty_coeff - 1.0) * 10)
    score += max(0, coeff_bonus)

    reasons.extend(
        [
            f"폭 리스크 {width_score}점",
            f"길이 리스크 {length_score}점",
            f"높이 리스크 {height_score}점",
            f"중량 리스크 {weight_score}점",
            f"회전 리스크 {turn_map[turn_condition]}점",
            f"장애물 리스크 {obstacle_map[obstacle_level]}점",
            f"노면/경사 리스크 {pavement_map[pavement_level]}점",
            f"형식 리스크 {form_map.get(module_form, 2)}점",
        ]
    )
    if coeff_bonus > 0:
        reasons.append(f"운송 난이도 계수 +{coeff_bonus}점")

    return score, reasons


def installation_risk_score(
    module_length_m: float,
    module_weight_t: float,
    floors: int,
    required_radius_m: float,
    staging_area_m2: float,
    jit_install: bool,
    module_form: str,
    install_difficulty_coeff: float,
) -> Tuple[int, List[str]]:
    length_score = 0 if module_length_m <= 10 else 1 if module_length_m <= 14 else 2 if module_length_m <= 18 else 3
    weight_score = 0 if module_weight_t <= 15 else 1 if module_weight_t <= 25 else 2 if module_weight_t <= 35 else 3
    floor_score = 0 if floors <= 5 else 1 if floors <= 8 else 2 if floors <= 15 else 3
    radius_score = 0 if required_radius_m <= 15 else 1 if required_radius_m <= 25 else 2 if required_radius_m <= 40 else 3
    staging_score = 0 if staging_area_m2 >= 400 else 1 if staging_area_m2 >= 200 else 2 if staging_area_m2 > 0 else 3
    jit_score = 2 if jit_install else 0
    form_score = {"corner-supported": 0, "open-ended": 1, "open-sided": 2, "hybrid": 3, "대개구부/비정형": 3}.get(module_form, 2)

    score = length_score + weight_score + floor_score + radius_score + staging_score + jit_score + form_score
    coeff_bonus = round((install_difficulty_coeff - 1.0) * 10)
    score += max(0, coeff_bonus)

    reasons = [
        f"길이 {length_score}점",
        f"중량 {weight_score}점",
        f"층수 {floor_score}점",
        f"작업반경 {radius_score}점",
        f"적치공간 {staging_score}점",
        f"JIT 설치 {jit_score}점",
        f"형식 {form_score}점",
    ]
    if coeff_bonus > 0:
        reasons.append(f"설치 난이도 계수 +{coeff_bonus}점")

    return score, reasons


def evaluate_cranes(
    needed_lifting_t: float,
    required_radius_m: float,
    required_hook_height_m: float,
    site_frontage_m: float,
    available_staging_m2: float,
) -> List[Dict[str, object]]:
    rows = []
    for crane in CRANE_DB:
        allowable = interpolate_allowable_load(crane, required_radius_m)
        load_ok = allowable >= needed_lifting_t
        radius_ok = required_radius_m <= crane.max_radius_m
        height_ok = required_hook_height_m <= crane.max_hook_height_m
        margin = safe_div(allowable, needed_lifting_t)

        note_list = []
        if crane.crane_group == "트럭크레인" and site_frontage_m < 12:
            note_list.append("전면부 부족 시 아웃트리거 제약")
        if crane.crane_group == "크롤러크레인" and available_staging_m2 < 500:
            note_list.append("야적장/작업장 부족")
        if crane.crane_group in ["타워크레인", "러핑크레인"]:
            note_list.append("기초/설치해체 계획 필요")

        rows.append(
            {
                "장비": crane.name,
                "장비군": crane.crane_group,
                "해당반경 허용하중(t)": round(allowable, 2),
                "필요양중하중(t)": round(needed_lifting_t, 2),
                "최대반경(m)": crane.max_radius_m,
                "필요반경(m)": required_radius_m,
                "최대Hook높이(m)": crane.max_hook_height_m,
                "필요Hook높이(m)": required_hook_height_m,
                "여유율": round(margin, 2),
                "판정": "가능" if (load_ok and radius_ok and height_ok) else "불가",
                "비고": "; ".join(note_list) if note_list else "-",
                "월임대료(원)": crane.monthly_rent_krw or 0,
                "설치해체비(원)": crane.setup_cost_krw or 0,
                "시간당손료(원)": crane.hourly_cost_krw or 0,
            }
        )

    rows.sort(key=lambda x: (x["판정"] != "가능", -x["여유율"]))
    return rows


def estimate_crane_cost(selected_row: Dict[str, object], months: float, road_side_short_term: bool) -> float:
    monthly = float(selected_row["월임대료(원)"])
    setup = float(selected_row["설치해체비(원)"])
    hourly = float(selected_row["시간당손료(원)"])

    if monthly > 0:
        return monthly * months + setup
    if hourly > 0:
        extra = 1.15 if road_side_short_term else 1.0
        return hourly * 8 * 20 * months * extra
    return 0.0


def cost_model(
    gross_area_m2: float,
    rc_unit_cost_krw_per_m2: float,
    modular_factory_unit_cost_krw_per_m2: float,
    module_count: int,
    transport_cost_per_module_krw: float,
    installation_cost_per_module_krw: float,
    permit_cost_per_module_krw: float,
    prefab_rate: float,
    schedule_reduction_months: float,
    monthly_financing_saving_krw: float,
    small_project_penalty_rate: float,
    modular_direct_premium_rate: float,
    crane_cost_krw: float,
    rc_equipment_cost_krw: float,
) -> Dict[str, float]:
    rc_total = gross_area_m2 * rc_unit_cost_krw_per_m2 + rc_equipment_cost_krw

    prefab_discount = max(0.0, (prefab_rate - 0.60) * 0.10)
    adjusted_modular_unit = modular_factory_unit_cost_krw_per_m2 * (1.0 - prefab_discount)
    adjusted_modular_unit *= (1.0 + modular_direct_premium_rate)
    adjusted_modular_unit *= (1.0 + small_project_penalty_rate)

    logistics_total = module_count * (
        transport_cost_per_module_krw + installation_cost_per_module_krw + permit_cost_per_module_krw
    )
    schedule_saving_total = schedule_reduction_months * monthly_financing_saving_krw
    modular_total = gross_area_m2 * adjusted_modular_unit + logistics_total + crane_cost_krw - schedule_saving_total

    return {
        "rc_total": rc_total,
        "modular_total": modular_total,
        "difference": modular_total - rc_total,
        "schedule_saving_total": schedule_saving_total,
        "logistics_total": logistics_total,
        "adjusted_modular_unit": adjusted_modular_unit,
    }


def recommend_method(
    transport_status: str,
    best_lifting_margin: float,
    transport_score: int,
    install_score: int,
    rc_total: float,
    modular_total: float,
    floors: int,
    repeatability_score: int,
    road_width_m: float,
) -> Tuple[str, List[str]]:
    reasons = []

    if transport_status == "불가":
        reasons.append("운송 경로 검토상 불가")
        return "RC 우세", reasons

    if best_lifting_margin < 1.0:
        reasons.append("필요 양중하중을 만족하는 장비 여유가 부족")
        return "RC 우세", reasons

    if modular_total < rc_total:
        reasons.append("총비용 기준 모듈러가 RC보다 저렴")
        if road_width_m >= 6 and repeatability_score >= 4 and floors <= 12:
            reasons.append("도로폭·반복성·층수 조건이 모듈러에 우호적")
            return "모듈러 우세", reasons
        return "조건부 모듈러 우세", reasons

    gap_ratio = safe_div(modular_total - rc_total, rc_total)
    if gap_ratio <= 0.05 and transport_score <= 16 and install_score <= 16:
        reasons.append("비용 차이가 작고 운송/설치 리스크가 관리 가능")
        return "조건부 모듈러 우세", reasons

    reasons.append("비용 또는 시공 안정성 측면에서 RC가 우세")
    return "RC 우세", reasons


def build_module_db_dataframe() -> pd.DataFrame:
    rows = []
    for module in MODULE_DB.values():
        rows.append(
            {
                "모듈 타입": module.name,
                "구조": module.structure,
                "폭(m)": module.width_m,
                "길이(m)": module.length_m,
                "높이(m)": module.height_m,
                "기본 자중(t)": module.weight_t_default,
                "권장 층수": module.recommended_floor_range,
                "대표 트레일러": module.representative_trailer,
                "권장 크레인군": module.recommended_crane_group,
                "공장제작률": module.prefab_rate_text,
                "기본 효율계수": module.base_efficiency_ratio,
            }
        )
    return pd.DataFrame(rows)


# ============================================================
# SIDEBAR INPUT
# ============================================================
st.sidebar.markdown("## 입력 패널")
st.sidebar.caption("왼쪽에서 값을 입력하고 분석 실행을 누르면 오른쪽에 결과가 표시됩니다.")

with st.sidebar:
    st.markdown('<div class="sidebar-group"><div class="sidebar-group-title">기본 정보</div>', unsafe_allow_html=True)
    project_name = st.text_input("사업명", value="")
    site_address = st.text_input("부지 도로명주소", value="")
    building_use = st.selectbox("건물 용도", ["공동주택", "기숙사", "학교", "병원", "업무시설", "복합용도"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-group"><div class="sidebar-group-title">부지 조건</div>', unsafe_allow_html=True)
    site_area_m2 = st.number_input("대지면적 (㎡)", min_value=0.0, value=9088.60, step=10.0)
    site_frontage_m = st.number_input("전면도로 길이 / 정차 가능 길이 (m)", min_value=0.0, value=40.0, step=1.0)
    road_width_m = st.number_input("전면 도로폭 (m)", min_value=0.0, value=6.0, step=0.5)
    turn_condition = st.selectbox("회전 조건", ["직진 위주", "코너 1개", "코너 2개 이상", "협소 코너 다수/U턴 필요"])
    obstacle_level = st.selectbox("장애물 수준", ["없음", "경미", "전선/가로수 일부", "전면부 장애 심함"])
    pavement_level = st.selectbox("노면/경사 수준", ["양호", "보통", "경사/포장불량 일부", "급경사/불량 심함"])
    illegal_parking_constant = st.radio("상시 불법주정차 영향", ["낮음", "중간", "높음"], horizontal=True)
    staging_area_m2 = st.number_input("적치 가능 면적 (㎡)", min_value=0.0, value=150.0, step=10.0)
    trailer_stop_zone_m = st.number_input("트레일러 정차 가능 구간 (m)", min_value=0.0, value=20.0, step=1.0)
    crane_candidate_offset_m = st.number_input("크레인 설치 후보점 이격거리 (m)", min_value=0.0, value=10.0, step=1.0)
    bridge_tunnel_height_limit_m = st.number_input("경로상 교량/터널 높이 제한 (m, 없으면 0)", min_value=0.0, value=0.0, step=0.1)
    managed_road_42m = st.radio("관리도로 4.2m 적용 여부", ["아니오", "예"], horizontal=True)
    road_side_short_term = st.radio("도로변 단기 설치 중심 현장인가?", ["예", "아니오"], horizontal=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-group"><div class="sidebar-group-title">건물 조건</div>', unsafe_allow_html=True)
    gross_area_m2 = st.number_input("연면적 (㎡)", min_value=0.0, value=22698.26, step=10.0)
    floors = st.number_input("층수", min_value=1, max_value=80, value=20, step=1)
    building_length_m = st.number_input("건물 길이 (m)", min_value=1.0, value=60.0, step=1.0)
    building_width_m = st.number_input("건물 폭 (m)", min_value=1.0, value=18.0, step=1.0)
    top_install_height_m = st.number_input("최고 설치 높이 (m)", min_value=1.0, value=57.1, step=0.5)
    obstacle_height_m = st.number_input("간섭 장애물 최고 높이 (m)", min_value=0.0, value=0.0, step=0.5)
    repeatability_score = st.slider("반복형 평면 정도", 1, 5, 4)
    public_space_ratio = st.slider("공용공간 비중", 1, 5, 3)
    open_plan_need = st.slider("개방형 평면 요구", 1, 5, 2)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-group"><div class="sidebar-group-title">모듈 조건</div>', unsafe_allow_html=True)
    module_input_mode = st.radio("모듈 선정 방식", ["자동 추천", "DB 선택", "직접 입력"], horizontal=True)

    module_ranking = []
    if module_input_mode == "자동 추천":
        selected_module, module_ranking = auto_select_module(
            building_use=building_use,
            floors=int(floors),
            repeatability_score=repeatability_score,
            public_space_ratio=public_space_ratio,
            open_plan_need=open_plan_need,
            road_width_m=road_width_m,
            staging_area_m2=staging_area_m2,
        )
    elif module_input_mode == "DB 선택":
        module_name_from_db = st.selectbox("모듈 타입", list(MODULE_DB.keys()))
        selected_module = MODULE_DB[module_name_from_db]
    else:
        selected_module = None

    if selected_module is not None:
        module_name = selected_module.name
        module_length_m = st.number_input("모듈 길이 (m)", value=float(selected_module.length_m), step=0.1)
        module_width_m = st.number_input("모듈 폭 (m)", value=float(selected_module.width_m), step=0.1)
        module_height_m = st.number_input("모듈 높이 (m)", value=float(selected_module.height_m), step=0.1)
        module_weight_t = st.number_input("모듈 자중 (t)", value=float(selected_module.weight_t_default), step=0.1)
        module_form = selected_module.openness
        module_eff_default = selected_module.base_efficiency_ratio
        prefab_rate_default = round((selected_module.prefab_rate_min + selected_module.prefab_rate_max) / 2, 2)
        transport_difficulty_coeff = selected_module.transport_difficulty_coeff
        install_difficulty_coeff = selected_module.install_difficulty_coeff
    else:
        module_name = "사용자 정의 모듈"
        module_length_m = st.number_input("모듈 길이 (m)", value=10.0, step=0.1)
        module_width_m = st.number_input("모듈 폭 (m)", value=3.2, step=0.1)
        module_height_m = st.number_input("모듈 높이 (m)", value=3.4, step=0.1)
        module_weight_t = st.number_input("모듈 자중 (t)", value=12.0, step=0.1)
        module_form = st.selectbox("모듈 형식", ["corner-supported", "open-ended", "open-sided", "hybrid", "대개구부/비정형"])
        module_eff_default = 0.80
        prefab_rate_default = 0.70
        transport_difficulty_coeff = 1.15
        install_difficulty_coeff = 1.20

    count_mode = st.radio("모듈 개수 입력 방식", ["자동 산정", "직접 입력"], horizontal=True)
    module_efficiency_ratio = st.slider("모듈 면적 효율계수", min_value=0.50, max_value=0.95, value=float(module_eff_default), step=0.01)

    if count_mode == "자동 산정":
        module_count = estimate_module_count(gross_area_m2, module_length_m, module_width_m, module_efficiency_ratio)
        st.caption(f"자동 산정 결과: 약 {module_count}개")
    else:
        module_count = st.number_input("총 모듈 개수", min_value=1, value=100, step=1)

    lifting_extra_t = st.number_input("인양보조구/슬링 등 추가 하중 (t)", min_value=0.0, value=0.8, step=0.1)
    safety_factor = st.number_input("안전계수", min_value=1.0, value=1.15, step=0.01)
    jit_install = st.radio("JIT(Just-In-Time) 설치 계획", ["예", "아니오"], horizontal=True)
    prefab_rate = st.slider("공장 제작 비율", min_value=0.30, max_value=0.95, value=float(prefab_rate_default), step=0.01)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-group"><div class="sidebar-group-title">비용 · 공기 가정</div>', unsafe_allow_html=True)
    rc_unit_cost_krw_per_m2 = st.number_input("RC 기준 공사비 (원/㎡)", min_value=0.0, value=2400000.0, step=10000.0)
    modular_factory_unit_cost_krw_per_m2 = st.number_input("모듈러 공장 제작 공사비 (원/㎡)", min_value=0.0, value=2550000.0, step=10000.0)
    modular_direct_premium_rate = st.slider("모듈러 직접공사비 할증률", min_value=0.0, max_value=0.30, value=0.08, step=0.01)
    small_project_penalty_rate = st.slider("소규모 프로젝트 불리율", min_value=0.0, max_value=0.20, value=0.05, step=0.01)
    transport_cost_per_module_krw = st.number_input("모듈 1개당 운송비 (원)", min_value=0.0, value=1200000.0, step=10000.0)
    installation_cost_per_module_krw = st.number_input("모듈 1개당 설치비 (원)", min_value=0.0, value=800000.0, step=10000.0)
    permit_cost_per_module_krw = st.number_input("모듈 1개당 특수운행/통제 비용 (원)", min_value=0.0, value=200000.0, step=10000.0)
    schedule_reduction_months = st.number_input("모듈러 공기 단축 예상 (개월)", min_value=0.0, value=2.5, step=0.1)
    monthly_financing_saving_krw = st.number_input("공기단축 1개월당 금융/간접비 절감액 (원)", min_value=0.0, value=25000000.0, step=100000.0)
    rc_equipment_cost_krw = st.number_input("RC 장비/현장 추가비 (원)", min_value=0.0, value=60000000.0, step=100000.0)
    crane_rent_months = st.number_input("타워크레인/주요 양중장비 사용 개월 수", min_value=0.0, value=3.0, step=0.5)
    st.markdown("</div>", unsafe_allow_html=True)

    analyze_clicked = st.button("분석 실행")


# ============================================================
# ANALYSIS
# ============================================================
if analyze_clicked:
    required_radius_m = max(building_width_m / 2 + crane_candidate_offset_m, 5.0)
    required_lifting_t = (module_weight_t + lifting_extra_t) * safety_factor
    required_hook_height_m = max(top_install_height_m + 5.0, obstacle_height_m + 5.0)

    trailer_candidates = recommend_trailer(
        module_length_m=module_length_m,
        module_width_m=module_width_m,
        module_height_m=module_height_m,
        module_weight_t=module_weight_t,
    )
    best_trailer = trailer_candidates[0]

    route_eval = evaluate_transport_legal(
        module_width_m=module_width_m,
        module_length_m=module_length_m,
        module_height_m=module_height_m,
        module_weight_t=module_weight_t,
        trailer_row=best_trailer,
        road_width_m=road_width_m,
        turn_condition=turn_condition,
        obstacle_level=obstacle_level,
        bridge_tunnel_height_limit_m=bridge_tunnel_height_limit_m,
        managed_road_42m=(managed_road_42m == "예"),
        illegal_parking_constant=illegal_parking_constant,
    )

    transport_score, transport_reasons = transport_risk_score(
        module_width_m=module_width_m,
        module_length_m=module_length_m,
        transport_height_m=route_eval["transport_height_m"],
        module_weight_t=module_weight_t,
        turn_condition=turn_condition,
        obstacle_level=obstacle_level,
        pavement_level=pavement_level,
        module_form=module_form,
        transport_difficulty_coeff=transport_difficulty_coeff,
    )

    install_score, install_reasons = installation_risk_score(
        module_length_m=module_length_m,
        module_weight_t=module_weight_t,
        floors=int(floors),
        required_radius_m=required_radius_m,
        staging_area_m2=staging_area_m2,
        jit_install=(jit_install == "예"),
        module_form=module_form,
        install_difficulty_coeff=install_difficulty_coeff,
    )

    crane_rows = evaluate_cranes(
        needed_lifting_t=required_lifting_t,
        required_radius_m=required_radius_m,
        required_hook_height_m=required_hook_height_m,
        site_frontage_m=site_frontage_m,
        available_staging_m2=staging_area_m2,
    )
    selected_crane = crane_rows[0]
    best_lifting_margin = float(selected_crane["여유율"])

    crane_cost_krw = estimate_crane_cost(
        selected_row=selected_crane,
        months=float(crane_rent_months),
        road_side_short_term=(road_side_short_term == "예"),
    )

    model_cost = cost_model(
        gross_area_m2=gross_area_m2,
        rc_unit_cost_krw_per_m2=rc_unit_cost_krw_per_m2,
        modular_factory_unit_cost_krw_per_m2=modular_factory_unit_cost_krw_per_m2,
        module_count=int(module_count),
        transport_cost_per_module_krw=transport_cost_per_module_krw,
        installation_cost_per_module_krw=installation_cost_per_module_krw,
        permit_cost_per_module_krw=permit_cost_per_module_krw,
        prefab_rate=prefab_rate,
        schedule_reduction_months=schedule_reduction_months,
        monthly_financing_saving_krw=monthly_financing_saving_krw,
        small_project_penalty_rate=small_project_penalty_rate,
        modular_direct_premium_rate=modular_direct_premium_rate,
        crane_cost_krw=crane_cost_krw,
        rc_equipment_cost_krw=rc_equipment_cost_krw,
    )

    final_method, final_reasons = recommend_method(
        transport_status=route_eval["status"],
        best_lifting_margin=best_lifting_margin,
        transport_score=transport_score,
        install_score=install_score,
        rc_total=model_cost["rc_total"],
        modular_total=model_cost["modular_total"],
        floors=int(floors),
        repeatability_score=repeatability_score,
        road_width_m=road_width_m,
    )

    structure_name = recommend_structure(
        module_name=module_name,
        repeatability_score=repeatability_score,
        open_plan_need=open_plan_need,
        public_space_ratio=public_space_ratio,
    )

    st.session_state.analysis_result = {
        "project_name": project_name,
        "site_address": site_address,
        "building_use": building_use,
        "gross_area_m2": gross_area_m2,
        "floors": floors,
        "module_name": module_name,
        "module_count": module_count,
        "module_length_m": module_length_m,
        "module_width_m": module_width_m,
        "module_height_m": module_height_m,
        "module_weight_t": module_weight_t,
        "prefab_rate": prefab_rate,
        "structure_name": structure_name,
        "required_radius_m": required_radius_m,
        "required_lifting_t": required_lifting_t,
        "required_hook_height_m": required_hook_height_m,
        "best_trailer": best_trailer,
        "trailer_candidates": trailer_candidates,
        "route_eval": route_eval,
        "transport_score": transport_score,
        "transport_reasons": transport_reasons,
        "install_score": install_score,
        "install_reasons": install_reasons,
        "selected_crane": selected_crane,
        "crane_rows": crane_rows,
        "best_lifting_margin": best_lifting_margin,
        "crane_cost_krw": crane_cost_krw,
        "model_cost": model_cost,
        "final_method": final_method,
        "final_reasons": final_reasons,
        "module_ranking": module_ranking,
    }
    st.session_state.analysis_done = True


# ============================================================
# MAIN VIEW
# ============================================================
result = st.session_state.analysis_result

if not st.session_state.analysis_done or result is None:
    st.markdown(
        """
        <div class="section-card" style="min-height:520px; display:flex; align-items:center; justify-content:center; text-align:center;">
            <div>
                <div style="font-size:34px; font-weight:900; color:#1f3a5f; line-height:1.45;">
                    수익성극대화를위한부지맞춤형신축매입대사업모델제안<br>
                    : 민간사업자관점의 OSC 공법 적용 임계점 도출
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div class="big-result">
            <div class="big-result-title">최종 추천 공법</div>
            <div class="big-result-value">{result["final_method"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_box("운송 법규 판정", result["route_eval"]["status"], "운송 경로 법적·물리적 가능성")
    with k2:
        metric_box("운송 리스크", f'{result["transport_score"]}점', transport_risk_bucket(result["transport_score"]))
    with k3:
        metric_box("설치 리스크", f'{result["install_score"]}점', transport_risk_bucket(result["install_score"]))
    with k4:
        metric_box("최고 양중 여유율", f'{result["best_lifting_margin"]:.2f}', lifting_margin_grade(result["best_lifting_margin"]))

    diff_abs = abs(result["model_cost"]["difference"])
    diff_note = "모듈러가 더 비쌈" if result["model_cost"]["difference"] > 0 else "모듈러가 더 저렴"
    metric_cols = st.columns(3)
    with metric_cols[0]:
        metric_box("RC 총비용", format_krw(result["model_cost"]["rc_total"]))
    with metric_cols[1]:
        metric_box("모듈러 총비용", format_krw(result["model_cost"]["modular_total"]))
    with metric_cols[2]:
        metric_box("RC 대비 비용 차이", format_krw(diff_abs), diff_note)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["개요", "부지·운송", "모듈·양중", "비용 비교", "DB/후보"])

    with tab1:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>프로젝트 요약</div>", unsafe_allow_html=True)

        left, right = st.columns([1.15, 1])
        with left:
            summary_df = pd.DataFrame(
                {
                    "항목": [
                        "사업명", "건물 용도", "부지 주소", "연면적", "층수",
                        "선정 모듈", "모듈 길이", "모듈 폭", "모듈 높이", "모듈 자중",
                        "총 모듈 개수", "공장 제작 비율", "추천 구조방식",
                        "추천 트레일러", "추천 양중장비"
                    ],
                    "값": [
                        result["project_name"] if result["project_name"] else "미입력",
                        result["building_use"],
                        result["site_address"] if result["site_address"] else "미입력",
                        format_area(result["gross_area_m2"]),
                        f'{int(result["floors"])}층',
                        result["module_name"],
                        f'{result["module_length_m"]:.2f}m',
                        f'{result["module_width_m"]:.2f}m',
                        f'{result["module_height_m"]:.2f}m',
                        f'{result["module_weight_t"]:.2f}t',
                        f'{int(result["module_count"])}개',
                        f'{int(result["prefab_rate"] * 100)}%',
                        result["structure_name"],
                        result["best_trailer"]["운송장비"],
                        result["selected_crane"]["장비"],
                    ],
                }
            )
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

        with right:
            st.markdown("<div class='section-subtitle'>최종 판단 사유</div>", unsafe_allow_html=True)
            for reason in result["final_reasons"]:
                st.markdown(f"- {reason}")
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("<div class='section-subtitle'>핵심 조건</div>", unsafe_allow_html=True)
            st.markdown(
                f"""
                - 필요 작업반경: **{result["required_radius_m"]:.2f}m**  
                - 필요 양중하중: **{result["required_lifting_t"]:.2f}t**  
                - 필요 Hook 높이: **{result["required_hook_height_m"]:.2f}m**
                """
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>운송 법규 및 트레일러 검토</div>", unsafe_allow_html=True)

        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("**국내 일반 운행 제한 기준**")
            law_df = pd.DataFrame(
                {
                    "항목": ["폭", "높이", "길이", "총중량", "축하중"],
                    "일반 기준": ["2.5m", "4.0m", "16.7m", "40t", "10t"],
                    "특수허가 활용 시 참고": ["3.5m", "4.3m", "17.0m 전후", "개별 검토", "개별 검토"],
                }
            )
            st.dataframe(law_df, use_container_width=True, hide_index=True)

        with c2:
            st.markdown("**최종 운송 판정**")
            st.markdown(badge_html(result["route_eval"]["status"]), unsafe_allow_html=True)
            st.markdown(
                f"""
                - 선택 트레일러: **{result["best_trailer"]["운송장비"]}**
                - 운송 높이: **{result["route_eval"]["transport_height_m"]:.2f}m**
                - 법정 기준 높이: **{result["route_eval"]["legal_height_limit_m"]:.1f}m**
                - 특수허가 필요 여부: **{"예" if result["route_eval"]["permit_needed"] else "아니오"}**
                """
            )
            for reason in result["route_eval"]["all_reasons"]:
                st.markdown(f"- {reason}")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("**트레일러 후보 비교**")
        trailer_df = pd.DataFrame(result["trailer_candidates"])
        st.dataframe(trailer_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>모듈 및 양중 검토</div>", unsafe_allow_html=True)

        m1, m2 = st.columns([1, 1])
        with m1:
            st.markdown("**모듈 정보**")
            module_df = pd.DataFrame(
                {
                    "항목": ["모듈 타입", "길이", "폭", "높이", "자중", "총 모듈 수", "구조방식"],
                    "값": [
                        result["module_name"],
                        f'{result["module_length_m"]:.2f}m',
                        f'{result["module_width_m"]:.2f}m',
                        f'{result["module_height_m"]:.2f}m',
                        f'{result["module_weight_t"]:.2f}t',
                        int(result["module_count"]),
                        result["structure_name"],
                    ],
                }
            )
            st.dataframe(module_df, use_container_width=True, hide_index=True)

            st.markdown("**운송 리스크 세부**")
            for item in result["transport_reasons"]:
                st.markdown(f"- {item}")

            st.markdown("**설치 리스크 세부**")
            for item in result["install_reasons"]:
                st.markdown(f"- {item}")

        with m2:
            st.markdown("**양중장비 후보 비교**")
            crane_df = pd.DataFrame(result["crane_rows"])
            st.dataframe(crane_df, use_container_width=True, hide_index=True)

            st.markdown("**선정 장비 요약**")
            st.markdown(
                f"""
                - 장비명: **{result["selected_crane"]["장비"]}**
                - 장비군: **{result["selected_crane"]["장비군"]}**
                - 여유율: **{result["selected_crane"]["여유율"]:.2f}**
                - 추정 장비비: **{format_krw(result["crane_cost_krw"])}**
                """
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with tab4:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>비용 비교</div>", unsafe_allow_html=True)

        cost_df = pd.DataFrame(
            {
                "구분": ["RC", "모듈러"],
                "총비용(원)": [result["model_cost"]["rc_total"], result["model_cost"]["modular_total"]],
            }
        )
        st.bar_chart(cost_df.set_index("구분"))

        detail_df = pd.DataFrame(
            {
                "항목": [
                    "RC 총비용",
                    "모듈러 총비용",
                    "모듈러 조정 단가(원/㎡)",
                    "물류/설치 총액",
                    "공기 단축 절감액",
                    "양중장비비",
                ],
                "값": [
                    format_krw(result["model_cost"]["rc_total"]),
                    format_krw(result["model_cost"]["modular_total"]),
                    format_krw(result["model_cost"]["adjusted_modular_unit"]),
                    format_krw(result["model_cost"]["logistics_total"]),
                    format_krw(result["model_cost"]["schedule_saving_total"]),
                    format_krw(result["crane_cost_krw"]),
                ],
            }
        )
        st.dataframe(detail_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab5:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>DB 및 자동추천 후보</div>", unsafe_allow_html=True)

        st.markdown("**모듈 DB**")
        st.dataframe(build_module_db_dataframe(), use_container_width=True, hide_index=True)

        if result["module_ranking"]:
            st.markdown("**자동추천 후보 순위**")
            ranking_rows = []
            for rank, item in enumerate(result["module_ranking"][:5], start=1):
                ranking_rows.append(
                    {
                        "순위": rank,
                        "모듈": item["module"].name,
                        "점수": item["score"],
                        "대표 사유": "; ".join(item["reasons"][:3]),
                    }
                )
            st.dataframe(pd.DataFrame(ranking_rows), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### ")
    if st.button("다시 입력하기"):
        st.session_state.analysis_done = False
        st.session_state.analysis_result = None
        st.rerun()

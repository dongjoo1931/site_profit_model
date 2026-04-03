from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from geopy.geocoders import Nominatim


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="도심 노후 부지 모듈러 시공 가능성 분석 도구",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION
# ============================================================
if "analysis_ready" not in st.session_state:
    st.session_state.analysis_ready = False


# ============================================================
# STYLE
# ============================================================
st.markdown(
    """
<style>
:root {
    --bg: #f6f7fb;
    --card: #ffffff;
    --line: #e5e7eb;
    --text: #111827;
    --muted: #6b7280;
    --primary: #1f3a5f;
    --primary-soft: #eef3f8;
    --accent: #3b82f6;
    --ok: #166534;
    --warn: #a16207;
    --bad: #b91c1c;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg);
    color: var(--text);
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1700px;
}

[data-testid="stSidebar"] {
    background: #f3f4f6;
    border-right: 1px solid #d1d5db;
    min-width: 420px !important;
    max-width: 420px !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding: 1.05rem 1rem 2rem 1rem;
}

.hero {
    background: #ffffff;
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 1.5rem 1.6rem;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
    margin-bottom: 1.2rem;
}

.section-card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1.1rem 1.2rem;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
    margin-bottom: 1.2rem;
}

.section-title {
    font-size: 18px;
    font-weight: 800;
    color: var(--primary);
    margin-bottom: 0.55rem;
}

.section-desc {
    font-size: 13px;
    color: var(--muted);
    margin-bottom: 0.85rem;
    line-height: 1.6;
}

.metric-card {
    background: white;
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 1rem;
    min-height: 116px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.03);
    margin-bottom: 1.05rem;
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

.badge-ok, .badge-warn, .badge-bad, .badge-neutral {
    display: inline-block;
    border-radius: 999px;
    padding: 0.3rem 0.65rem;
    font-size: 12px;
    font-weight: 800;
}
.badge-ok { background: #ecfdf3; color: var(--ok); }
.badge-warn { background: #fffbeb; color: var(--warn); }
.badge-bad { background: #fef2f2; color: var(--bad); }
.badge-neutral { background: #eff6ff; color: #1d4ed8; }

.result-hero {
    background: #ffffff;
    border: 1px solid var(--line);
    border-left: 6px solid var(--accent);
    border-radius: 18px;
    padding: 1.2rem 1.25rem;
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
    margin-top: 0.4rem;
    margin-bottom: 1.25rem;
}

.result-title {
    font-size: 15px;
    color: var(--muted);
    font-weight: 700;
}

.result-value {
    font-size: 30px;
    font-weight: 900;
    color: var(--primary);
    margin-top: 0.15rem;
}

.sidebar-group {
    background: #ffffff;
    border: 1px solid #dfe3e8;
    border-radius: 14px;
    padding: 0.9rem 0.9rem 0.25rem 0.9rem;
    margin-bottom: 0.9rem;
}

.sidebar-group-title {
    font-size: 15px;
    font-weight: 800;
    color: #1f3a5f;
    margin-bottom: 0.7rem;
}

.stButton > button {
    width: 100%;
    height: 3.05rem;
    border-radius: 12px;
    border: 1px solid #d1d5db;
    background: #ffffff;
    color: #1f3a5f;
    font-weight: 800;
    font-size: 16px;
}

.small-note {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.6;
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
    install_difficulty_coeff: float
    transport_difficulty_coeff: float
    large_opening: bool
    repeatability_score: int
    public_space_score: int
    floor_min: int
    floor_max: int
    open_plan_score: int
    base_efficiency_ratio: float

    @property
    def weight_t_default(self) -> float:
        return round((self.weight_t_min + self.weight_t_max) / 2.0, 2)


@dataclass
class TrailerSpec:
    name: str
    deck_length_m: float
    deck_width_m: float
    deck_height_m: float
    vehicle_weight_t: float
    payload_t: float
    steering: str
    min_turn_width_m: float


@dataclass
class CraneSpec:
    name: str
    crane_group: str
    max_capacity_t: float
    max_radius_m: float
    tip_load_t: float
    max_hook_height_m: float
    setup_type: str
    min_setup_width_m: float
    min_staging_m2: float
    swing_radius_note: str = ""


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
        desc="소형 반복형 세대에 적합하고 운송 리스크가 낮은 기본형 모듈",
        recommended_floor_range="저층~중층",
        representative_trailer="2축/3축 저상 트레일러",
        recommended_crane_group="트럭크레인, 중소형 타워크레인",
        install_difficulty_coeff=1.00,
        transport_difficulty_coeff=1.00,
        large_opening=False,
        repeatability_score=5,
        public_space_score=2,
        floor_min=1,
        floor_max=8,
        open_plan_score=1,
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
        representative_trailer="3축 저상 트레일러",
        recommended_crane_group="트럭크레인, 타워크레인",
        install_difficulty_coeff=1.20,
        transport_difficulty_coeff=1.15,
        large_opening=False,
        repeatability_score=4,
        public_space_score=3,
        floor_min=1,
        floor_max=12,
        open_plan_score=2,
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
        desc="적층 안정성을 우선하는 다층 대응형 모듈",
        recommended_floor_range="중층",
        representative_trailer="3축 저상 트레일러",
        recommended_crane_group="타워크레인",
        install_difficulty_coeff=1.25,
        transport_difficulty_coeff=1.20,
        large_opening=False,
        repeatability_score=4,
        public_space_score=3,
        floor_min=4,
        floor_max=15,
        open_plan_score=2,
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
        desc="측면 개방성이 커서 공용공간과 대공간에 유리한 모듈",
        recommended_floor_range="저층~중층",
        representative_trailer="3축 저상 또는 특수 트레일러",
        recommended_crane_group="중대형 타워크레인, 크롤러크레인",
        install_difficulty_coeff=1.50,
        transport_difficulty_coeff=1.35,
        large_opening=True,
        repeatability_score=2,
        public_space_score=5,
        floor_min=1,
        floor_max=10,
        open_plan_score=5,
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
        desc="단부 개방을 통한 세대 연결에 유리한 모듈",
        recommended_floor_range="저층~중층",
        representative_trailer="3축 저상 트레일러",
        recommended_crane_group="타워크레인",
        install_difficulty_coeff=1.20,
        transport_difficulty_coeff=1.20,
        large_opening=True,
        repeatability_score=3,
        public_space_score=3,
        floor_min=1,
        floor_max=10,
        open_plan_score=3,
        base_efficiency_ratio=0.76,
    ),
    "Corridor-type combined module": ModuleType(
        name="Corridor-type combined module",
        structure="복도형 조합",
        width_m=3.0,
        length_m=8.5,
        height_m=3.2,
        weight_t_min=8.0,
        weight_t_max=12.0,
        openness="corner-supported",
        desc="복도형 반복 배치에 적합한 주거형 모듈",
        recommended_floor_range="저층~중층",
        representative_trailer="2축/3축 저상 트레일러",
        recommended_crane_group="트럭크레인, 타워크레인",
        install_difficulty_coeff=1.10,
        transport_difficulty_coeff=1.05,
        large_opening=False,
        repeatability_score=5,
        public_space_score=3,
        floor_min=1,
        floor_max=12,
        open_plan_score=1,
        base_efficiency_ratio=0.86,
    ),
    "Hybrid / podium + modular upper floors": ModuleType(
        name="Hybrid / podium + modular upper floors",
        structure="하부 RC + 상부 모듈러",
        width_m=3.35,
        length_m=11.0,
        height_m=3.5,
        weight_t_min=13.0,
        weight_t_max=19.0,
        openness="hybrid",
        desc="하부 RC 포디움 위에 상부 모듈러를 올리는 하이브리드형",
        recommended_floor_range="중층 이상",
        representative_trailer="3축 저상 또는 특수 트레일러",
        recommended_crane_group="타워크레인, 러핑크레인",
        install_difficulty_coeff=1.40,
        transport_difficulty_coeff=1.25,
        large_opening=True,
        repeatability_score=4,
        public_space_score=4,
        floor_min=4,
        floor_max=20,
        open_plan_score=4,
        base_efficiency_ratio=0.78,
    ),
}

TRAILER_DB: List[TrailerSpec] = [
    TrailerSpec("2축 저상 트레일러 A", 12.0, 2.44, 0.90, 5.05, 22.0, "일반", 6.0),
    TrailerSpec("2축 저상 트레일러 B", 13.3, 2.75, 0.50, 7.51, 23.0, "일반", 6.5),
    TrailerSpec("3축 저상 트레일러 A", 12.83, 2.75, 0.65, 7.57, 23.0, "일반", 7.0),
    TrailerSpec("3축 저상 트레일러 B", 13.51, 2.75, 0.90, 8.37, 22.5, "일반", 7.5),
    TrailerSpec("가변조향 트레일러", 13.39, 2.75, 0.20, 18.39, 12.5, "가변조향", 5.5),
]

CRANE_DB: List[CraneSpec] = [
    CraneSpec("Truck Crane 25t", "트럭크레인", 25.0, 30.0, 2.5, 45.0, "단기/이동식", 8.0, 80.0, "아웃트리거 전개 필요"),
    CraneSpec("Truck Crane 40t", "트럭크레인", 40.0, 39.0, 4.0, 44.0, "단기/이동식", 10.0, 100.0, "아웃트리거 전개 필요"),
    CraneSpec("Tower Crane 8t", "타워크레인", 8.0, 60.0, 1.5, 60.0, "고정식", 6.0, 120.0, "고정식 기초 필요"),
    CraneSpec("Tower Crane 10t", "타워크레인", 10.0, 65.0, 2.0, 70.0, "고정식", 6.5, 140.0, "고정식 기초 필요"),
    CraneSpec("Tower Crane 12t", "타워크레인", 12.0, 70.0, 2.4, 80.0, "고정식", 7.0, 150.0, "고정식 기초 필요"),
    CraneSpec("Luffing Crane 12t", "러핑크레인", 12.0, 60.0, 2.6, 120.0, "도심 고층형", 7.0, 150.0, "좁은 회전공간에 상대적으로 유리"),
    CraneSpec("Crawler Crane 100t", "크롤러크레인", 100.0, 52.0, 8.0, 64.0, "대형/야적장형", 14.0, 500.0, "넓은 작업장과 지반 확보 필요"),
]


# ============================================================
# HELPERS
# ============================================================
def grade_badge(label: str) -> str:
    mapping = {
        "가능": "badge-ok",
        "조건부 가능": "badge-warn",
        "불가": "badge-bad",
        "낮음": "badge-ok",
        "중간": "badge-warn",
        "높음": "badge-bad",
        "매우 높음": "badge-bad",
        "안전": "badge-ok",
        "주의": "badge-warn",
        "위험": "badge-bad",
    }
    klass = mapping.get(label, "badge-neutral")
    return f'<span class="{klass}">{label}</span>'


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


def geocode_address(address: str) -> Tuple[Optional[float], Optional[float]]:
    if not address.strip():
        return None, None
    try:
        geolocator = Nominatim(user_agent="modular_feasibility_app")
        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
    except Exception:
        pass
    return None, None


def interpolate_allowable_load(crane: CraneSpec, radius_m: float) -> float:
    radius = max(0.0, min(radius_m, crane.max_radius_m))
    if radius <= 5.0:
        return crane.max_capacity_t
    slope = (crane.tip_load_t - crane.max_capacity_t) / max(crane.max_radius_m - 5.0, 1.0)
    allowable = crane.max_capacity_t + slope * (radius - 5.0)
    return max(0.0, allowable)


def estimate_module_count(gross_area_m2: float, module_length_m: float, module_width_m: float, efficiency_ratio: float) -> int:
    module_area = module_length_m * module_width_m * efficiency_ratio
    if module_area <= 0:
        return 0
    return max(1, math.ceil(gross_area_m2 / module_area))


def estimate_modules_per_floor(building_length_m: float, building_width_m: float, module_length_m: float, module_width_m: float) -> int:
    count_x = max(1, int(building_length_m // module_length_m))
    count_y = max(1, int(building_width_m // module_width_m))
    return count_x * count_y


def compute_required_radius(site_depth_m: float, front_setback_m: float, crane_offset_m: float, building_width_m: float) -> float:
    return max(8.0, front_setback_m + crane_offset_m + building_width_m * 0.5)


def compute_required_hook_height(top_install_height_m: float, extra_clearance_m: float) -> float:
    return top_install_height_m + extra_clearance_m


def transport_risk_bucket(score: int) -> str:
    if score < 8:
        return "낮음"
    if score < 14:
        return "중간"
    if score < 20:
        return "높음"
    return "매우 높음"


def installation_risk_bucket(score: int) -> str:
    if score < 8:
        return "안전"
    if score < 14:
        return "주의"
    return "위험"


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
        reasons: List[str] = []

        score += (5 - abs(module.repeatability_score - repeatability_score)) * 3.0
        score += (5 - abs(module.public_space_score - public_space_ratio)) * 2.0
        score += (5 - abs(module.open_plan_score - open_plan_need)) * 2.0

        if module.floor_min <= floors <= module.floor_max:
            score += 8.0
            reasons.append("권장 층수 범위 적합")
        else:
            score -= 5.0
            reasons.append("권장 층수 범위 이탈")

        if building_use in ["공동주택", "기숙사"] and module.repeatability_score >= 4:
            score += 4.0
            reasons.append("주거 반복형에 유리")
        if building_use in ["학교", "병원", "업무시설"] and module.public_space_score >= 4:
            score += 4.0
            reasons.append("공용공간 요구에 유리")
        if building_use == "복합용도" and module.openness == "hybrid":
            score += 5.0
            reasons.append("복합용도에 하이브리드 적합")

        if road_width_m < 6.0 and module.transport_difficulty_coeff >= 1.3:
            score -= 4.0
            reasons.append("좁은 도로에서 운송 부담")
        if staging_area_m2 < 150 and module.install_difficulty_coeff >= 1.4:
            score -= 3.0
            reasons.append("적치공간 부족 시 설치 부담")

        rows.append({"module": module, "score": round(score, 2), "reasons": reasons})

    rows.sort(key=lambda x: x["score"], reverse=True)
    return rows[0]["module"], rows


def select_vehicle_specs(module_length_m: float, module_width_m: float, module_height_m: float, module_weight_t: float, road_width_m: float) -> List[Dict[str, object]]:
    rows = []
    for trailer in TRAILER_DB:
        transport_height = trailer.deck_height_m + module_height_m
        total_weight_t = trailer.vehicle_weight_t + module_weight_t
        length_ok = module_length_m <= trailer.deck_length_m
        width_ok = module_width_m <= trailer.deck_width_m or module_width_m <= 3.5
        payload_ok = module_weight_t <= trailer.payload_t
        turn_ok = road_width_m >= trailer.min_turn_width_m
        if length_ok and width_ok and payload_ok and turn_ok:
            status = "가능"
        elif payload_ok and width_ok:
            status = "조건부 가능"
        else:
            status = "불가"
        rows.append(
            {
                "운송 차량": trailer.name,
                "적재면 길이(m)": trailer.deck_length_m,
                "적재면 폭(m)": trailer.deck_width_m,
                "적재면 높이(m)": trailer.deck_height_m,
                "최대 적재량(t)": trailer.payload_t,
                "운송 높이(m)": round(transport_height, 2),
                "총중량 추정(t)": round(total_weight_t, 2),
                "조향 방식": trailer.steering,
                "최소 회전 필요 도로폭(m)": trailer.min_turn_width_m,
                "판정": status,
            }
        )
    rows.sort(key=lambda x: (x["판정"] != "가능", x["총중량 추정(t)"]))
    return rows


def evaluate_route_permit(
    module_width_m: float,
    transport_height_m: float,
    total_weight_t: float,
    road_width_m: float,
    turn_condition: str,
    obstacle_level: str,
    bridge_tunnel_height_limit_m: float,
    managed_road_42m: bool,
    illegal_parking_constant: str,
    road_occupation_possible: bool,
) -> Dict[str, object]:
    reasons: List[str] = []
    permit_needed = False
    route_ok = True
    legal_height_limit = 4.2 if managed_road_42m else 4.0

    if module_width_m > 2.5:
        permit_needed = True
        reasons.append("폭 2.5m 초과로 특수 운송 허가 검토 필요")
    if transport_height_m > legal_height_limit:
        permit_needed = True
        reasons.append(f"운송 높이 {legal_height_limit:.1f}m 초과")
    if total_weight_t > 40.0:
        permit_needed = True
        reasons.append("총중량 40t 초과 가능성")

    effective_road_width = road_width_m + (2.5 if road_occupation_possible else 0.0)
    if effective_road_width < 4.0:
        route_ok = False
        reasons.append("유효 도로폭 4m 미만")
    elif effective_road_width < 6.0:
        reasons.append("유효 도로폭 4~6m 구간")

    turn_map = {
        "직진 위주": 0,
        "코너 1개": 1,
        "코너 2개 이상": 2,
        "협소 코너 다수/U턴 필요": 3,
    }
    if turn_map[turn_condition] >= 3:
        route_ok = False
        reasons.append("협소 코너/U턴 필요")
    elif turn_map[turn_condition] == 2:
        reasons.append("코너 2개 이상")

    if obstacle_level == "전면부 장애 심함":
        route_ok = False
        reasons.append("전면부 장애 심함")
    elif obstacle_level == "전선/가로수 일부":
        reasons.append("전선/가로수 일부 간섭")

    if bridge_tunnel_height_limit_m > 0 and transport_height_m > bridge_tunnel_height_limit_m:
        route_ok = False
        reasons.append("교량/터널 높이 제한 초과")

    if illegal_parking_constant == "높음":
        reasons.append("상시 불법주정차 영향 높음")
    elif illegal_parking_constant == "중간":
        reasons.append("상시 불법주정차 영향 중간")

    if not reasons:
        reasons.append("주요 경로 제약 없음")

    if not route_ok:
        route_status = "불가"
    elif permit_needed or road_occupation_possible:
        route_status = "조건부 가능"
    else:
        route_status = "가능"

    return {
        "route_ok": route_ok,
        "permit_needed": permit_needed,
        "route_status": route_status,
        "effective_road_width": round(effective_road_width, 2),
        "legal_height_limit": legal_height_limit,
        "reasons": reasons,
    }


def transport_risk_score(
    module_width_m: float,
    transport_height_m: float,
    module_weight_t: float,
    module_length_m: float,
    turn_condition: str,
    obstacle_level: str,
    pavement_level: str,
    module_form: str,
    transport_difficulty_coeff: float,
) -> Tuple[int, List[str]]:
    score = 0
    reasons = []

    s = 0 if module_width_m <= 2.5 else 2 if module_width_m <= 3.2 else 3
    score += s
    reasons.append(f"모듈 폭 리스크 {s}점")

    s = 0 if transport_height_m <= 4.0 else 2 if transport_height_m <= 4.5 else 3
    score += s
    reasons.append(f"운송 높이 리스크 {s}점")

    s = 0 if module_weight_t <= 12 else 1 if module_weight_t <= 18 else 2 if module_weight_t <= 25 else 3
    score += s
    reasons.append(f"중량 리스크 {s}점")

    s = 0 if module_length_m <= 10 else 1 if module_length_m <= 12 else 2 if module_length_m <= 15 else 3
    score += s
    reasons.append(f"길이 리스크 {s}점")

    turn_map = {"직진 위주": 0, "코너 1개": 1, "코너 2개 이상": 2, "협소 코너 다수/U턴 필요": 3}
    obstacle_map = {"없음": 0, "경미": 1, "전선/가로수 일부": 2, "전면부 장애 심함": 3}
    pavement_map = {"양호": 0, "보통": 1, "경사/포장불량 일부": 2, "급경사/불량 심함": 3}
    form_map = {"corner-supported": 0, "open-ended": 1, "open-sided": 2, "hybrid": 2, "대개구부/비정형": 3}

    score += turn_map[turn_condition]
    score += obstacle_map[obstacle_level]
    score += pavement_map[pavement_level]
    score += form_map.get(module_form, 2)

    reasons.append(f"회전 조건 리스크 {turn_map[turn_condition]}점")
    reasons.append(f"장애물 리스크 {obstacle_map[obstacle_level]}점")
    reasons.append(f"노면/경사 리스크 {pavement_map[pavement_level]}점")
    reasons.append(f"모듈 형식 리스크 {form_map.get(module_form, 2)}점")

    coeff_bonus = round((transport_difficulty_coeff - 1.0) * 10)
    if coeff_bonus > 0:
        score += coeff_bonus
        reasons.append(f"운송 난이도 계수 반영 +{coeff_bonus}점")

    return score, reasons


def installation_risk_score(
    module_length_m: float,
    module_weight_t: float,
    floors: int,
    required_radius_m: float,
    staging_area_m2: float,
    module_form: str,
    install_difficulty_coeff: float,
) -> Tuple[int, List[str]]:
    score = 0
    reasons = []

    s = 0 if module_length_m <= 10 else 1 if module_length_m <= 12 else 2 if module_length_m <= 15 else 3
    score += s
    reasons.append(f"모듈 길이 {s}점")

    s = 0 if module_weight_t <= 12 else 1 if module_weight_t <= 18 else 2 if module_weight_t <= 25 else 3
    score += s
    reasons.append(f"모듈 중량 {s}점")

    s = 0 if floors <= 4 else 1 if floors <= 8 else 2 if floors <= 12 else 3
    score += s
    reasons.append(f"층수 {s}점")

    s = 0 if required_radius_m <= 15 else 1 if required_radius_m <= 25 else 2 if required_radius_m <= 35 else 3
    score += s
    reasons.append(f"작업반경 {s}점")

    s = 0 if staging_area_m2 >= 300 else 1 if staging_area_m2 >= 150 else 2 if staging_area_m2 > 0 else 3
    score += s
    reasons.append(f"적치공간 {s}점")

    form_map = {"corner-supported": 0, "open-ended": 1, "open-sided": 2, "hybrid": 2, "대개구부/비정형": 3}
    s = form_map.get(module_form, 2)
    score += s
    reasons.append(f"모듈 형식 {s}점")

    coeff_bonus = round((install_difficulty_coeff - 1.0) * 10)
    if coeff_bonus > 0:
        score += coeff_bonus
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
        radius_ok = required_radius_m <= crane.max_radius_m
        hook_ok = required_hook_height_m <= crane.max_hook_height_m
        load_ok = allowable >= needed_lifting_t
        setup_ok = site_frontage_m >= crane.min_setup_width_m and available_staging_m2 >= crane.min_staging_m2
        margin = allowable / needed_lifting_t if needed_lifting_t > 0 else 0.0

        if load_ok and radius_ok and hook_ok and setup_ok:
            status = "가능"
        elif load_ok and radius_ok and hook_ok:
            status = "조건부 가능"
        else:
            status = "불가"

        rows.append(
            {
                "장비": crane.name,
                "장비군": crane.crane_group,
                "최대하중(t)": crane.max_capacity_t,
                "최대반경(m)": crane.max_radius_m,
                "끝단하중(t)": crane.tip_load_t,
                "최대Hook높이(m)": crane.max_hook_height_m,
                "해당반경 허용하중(t)": round(allowable, 2),
                "필요양중하중(t)": round(needed_lifting_t, 2),
                "여유율": round(margin, 2),
                "설치 필요 최소 폭(m)": crane.min_setup_width_m,
                "설치 필요 적치장(㎡)": crane.min_staging_m2,
                "판정": status,
                "비고": crane.swing_radius_note,
            }
        )
    rows.sort(key=lambda x: (x["판정"] == "불가", x["판정"] == "조건부 가능", -x["여유율"]))
    return rows


def compute_max_feasible_floors(
    crane_rows: List[Dict[str, object]],
    selected_module: ModuleType,
    floor_to_floor_m: float,
    crane_extra_clearance_m: float,
) -> int:
    feasible_cranes = [r for r in crane_rows if r["판정"] in ["가능", "조건부 가능"]]
    if not feasible_cranes:
        return 0
    max_hook_height = max(r["최대Hook높이(m)"] for r in feasible_cranes)
    hook_based = max(0, int((max_hook_height - crane_extra_clearance_m) // floor_to_floor_m))
    return max(0, min(selected_module.floor_max, hook_based))


def final_decision(route_status: str, best_crane_status: str, max_feasible_floors: int, target_floors: int) -> Tuple[str, List[str]]:
    reasons = []
    if route_status == "불가":
        reasons.append("운송 경로 검토에서 불가 판정")
        return "불가", reasons
    if best_crane_status == "불가":
        reasons.append("양중 장비 검토에서 불가 판정")
        return "불가", reasons
    if max_feasible_floors < target_floors:
        reasons.append(f"장비 및 높이 조건상 최대 가능 층수는 {max_feasible_floors}층 수준")
        return "조건부 가능", reasons
    if route_status == "조건부 가능" or best_crane_status == "조건부 가능":
        reasons.append("도로 점유, 허가, 설치 여건 등 추가 검토 필요")
        return "조건부 가능", reasons
    reasons.append("운송·양중·층수 조건이 모두 목표 범위 내")
    return "가능", reasons


def generate_improvement_actions(result_status: str, route_status: str, crane_rows: List[Dict[str, object]], target_floors: int, max_feasible_floors: int) -> List[str]:
    actions = []
    if route_status == "불가":
        actions.append("전면도로 점유 허가 또는 진입 동선 재설정 검토")
        actions.append("폭과 중량이 더 작은 모듈 규격으로 재검토")
        actions.append("가변조향 트레일러 및 야간 운송 조건 검토")
    if crane_rows and crane_rows[0]["판정"] == "불가":
        actions.append("크레인 설치 위치 변경 또는 상위 장비군 검토")
        actions.append("적치장 확보 및 전면부 설치 폭 확보 필요")
    if max_feasible_floors < target_floors:
        actions.append(f"목표 층수 {target_floors}층을 {max_feasible_floors}층 이하로 조정하거나 하이브리드 구조 검토")
    if result_status == "가능":
        actions.append("현재 조건 기준으로 실제 사례 부지 데이터 입력 후 비교 분석 확장 가능")
    return actions


def create_site_plan_figure(
    site_width_m: float,
    site_depth_m: float,
    road_width_m: float,
    building_length_m: float,
    building_width_m: float,
    front_setback_m: float,
    side_clearance_m: float,
    crane_offset_m: float,
    crane_radius_m: float,
    trailer_length_m: float,
    trailer_width_m: float,
    road_occupation_possible: bool,
) -> go.Figure:
    fig = go.Figure()

    road_x0 = -road_width_m
    road_x1 = 0
    site_x0 = 0
    site_x1 = site_depth_m
    site_y0 = 0
    site_y1 = site_width_m

    fig.add_shape(type="rect", x0=road_x0, x1=road_x1, y0=site_y0, y1=site_y1, fillcolor="#dbeafe", line=dict(color="#93c5fd"))
    fig.add_shape(type="rect", x0=site_x0, x1=site_x1, y0=site_y0, y1=site_y1, fillcolor="#ecfccb", line=dict(color="#84cc16", width=2))

    building_x0 = front_setback_m
    building_x1 = min(site_depth_m - front_setback_m, front_setback_m + building_width_m)
    building_y0 = side_clearance_m
    building_y1 = min(site_width_m - side_clearance_m, side_clearance_m + building_length_m)
    fig.add_shape(type="rect", x0=building_x0, x1=building_x1, y0=building_y0, y1=building_y1, fillcolor="#fde68a", line=dict(color="#f59e0b", width=2))

    crane_x = max(1.5, crane_offset_m)
    crane_y = site_width_m / 2
    fig.add_trace(go.Scatter(x=[crane_x], y=[crane_y], mode="markers+text", text=["Crane"], textposition="top center", marker=dict(size=12, color="#dc2626"), name="크레인"))

    theta = [i for i in range(361)]
    circle_x = [crane_x + crane_radius_m * math.cos(math.radians(t)) for t in theta]
    circle_y = [crane_y + crane_radius_m * math.sin(math.radians(t)) for t in theta]
    fig.add_trace(go.Scatter(x=circle_x, y=circle_y, mode="lines", line=dict(color="#dc2626", dash="dash"), name="작업 반경"))

    trailer_x0 = -road_width_m + 0.4
    trailer_x1 = trailer_x0 + max(2.0, min(trailer_length_m, road_width_m + 4.0))
    trailer_y0 = max(0.5, site_width_m / 2 - trailer_width_m / 2)
    trailer_y1 = min(site_width_m - 0.5, trailer_y0 + trailer_width_m)
    fig.add_shape(type="rect", x0=trailer_x0, x1=trailer_x1, y0=trailer_y0, y1=trailer_y1, fillcolor="#c7d2fe", line=dict(color="#4f46e5"))

    if road_occupation_possible:
        fig.add_shape(type="rect", x0=road_x0 - 2.5, x1=road_x0, y0=0, y1=site_width_m, fillcolor="#fee2e2", line=dict(color="#ef4444", dash="dot"))

    fig.add_annotation(x=(road_x0 + road_x1) / 2, y=site_width_m - 2, text="전면도로", showarrow=False)
    fig.add_annotation(x=(site_x0 + site_x1) / 2, y=site_width_m - 2, text="대지", showarrow=False)
    fig.add_annotation(x=(building_x0 + building_x1) / 2, y=(building_y0 + building_y1) / 2, text="계획 건물", showarrow=False)

    fig.update_xaxes(title="깊이 방향 (m)", scaleanchor="y", scaleratio=1)
    fig.update_yaxes(title="폭 방향 (m)")
    fig.update_layout(height=650, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h"))
    return fig


def cuboid_edges(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float):
    pts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), (x0, y0, z1),
        (x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1), (x0, y1, z0)
    ]
    return [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts]


def create_stack_3d_figure(
    building_length_m: float,
    building_width_m: float,
    floor_to_floor_m: float,
    floors_to_show: int,
    module_length_m: float,
    module_width_m: float,
) -> go.Figure:
    fig = go.Figure()

    count_x = max(1, int(building_width_m // module_width_m))
    count_y = max(1, int(building_length_m // module_length_m))

    for floor in range(floors_to_show):
        z0 = floor * floor_to_floor_m
        z1 = z0 + floor_to_floor_m * 0.9
        for ix in range(count_x):
            for iy in range(count_y):
                x0 = ix * module_width_m
                x1 = x0 + module_width_m * 0.95
                y0 = iy * module_length_m
                y1 = y0 + module_length_m * 0.95
                xs, ys, zs = cuboid_edges(x0, x1, y0, y1, z0, z1)
                fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", showlegend=False))

    fig.update_layout(
        height=650,
        margin=dict(l=10, r=10, t=20, b=10),
        scene=dict(
            xaxis_title="건물 폭 방향 (m)",
            yaxis_title="건물 길이 방향 (m)",
            zaxis_title="높이 (m)",
            aspectmode="data",
        ),
    )
    return fig


def make_reason_df(items: List[str], col_name: str) -> pd.DataFrame:
    return pd.DataFrame({col_name: items})


# ============================================================
# SIDEBAR INPUT
# ============================================================
st.sidebar.markdown("## 입력 패널")
st.sidebar.caption("도심 노후 부지에서 모듈러 운송·양중·적층이 가능한지 시각적으로 검토하는 Step1 분석 도구입니다.")

st.sidebar.markdown('<div class="sidebar-group"><div class="sidebar-group-title">기본 정보</div>', unsafe_allow_html=True)
project_name = st.sidebar.text_input("사업명", value="도심 노후 부지 모듈러 적용 검토")
site_address = st.sidebar.text_input("부지 도로명주소", value="")
building_use = st.sidebar.selectbox("건물 용도", ["공동주택", "기숙사", "학교", "병원", "업무시설", "복합용도"])
st.sidebar.markdown("</div>", unsafe_allow_html=True)

st.sidebar.markdown('<div class="sidebar-group"><div class="sidebar-group-title">부지 · 도로 조건</div>', unsafe_allow_html=True)
site_width_m = st.sidebar.number_input("대지 폭 (m)", min_value=5.0, value=24.0, step=1.0)
site_depth_m = st.sidebar.number_input("대지 깊이 (m)", min_value=5.0, value=32.0, step=1.0)
site_frontage_m = st.sidebar.number_input("접도 길이 / 전면부 작업 가능 길이 (m)", min_value=5.0, value=20.0, step=1.0)
road_width_m = st.sidebar.number_input("전면 도로폭 (m)", min_value=2.0, value=6.0, step=0.5)
turn_condition = st.sidebar.selectbox("회전 조건", ["직진 위주", "코너 1개", "코너 2개 이상", "협소 코너 다수/U턴 필요"])
obstacle_level = st.sidebar.selectbox("장애물 수준", ["없음", "경미", "전선/가로수 일부", "전면부 장애 심함"])
pavement_level = st.sidebar.selectbox("노면/경사 수준", ["양호", "보통", "경사/포장불량 일부", "급경사/불량 심함"])
illegal_parking_constant = st.sidebar.radio("상시 불법주정차 영향", ["낮음", "중간", "높음"], horizontal=True)
bridge_tunnel_height_limit_m = st.sidebar.number_input("경로상 교량/터널 높이 제한 (m, 없으면 0)", min_value=0.0, value=0.0, step=0.1)
road_occupation_possible = st.sidebar.radio("도로 점유 신청 가능 여부", ["불가", "가능"], horizontal=True)
managed_road_42m = st.sidebar.radio("관리도로 4.2m 적용 여부", ["아니오", "예"], horizontal=True)
staging_area_m2 = st.sidebar.number_input("적치 가능 면적 (㎡)", min_value=0.0, value=120.0, step=10.0)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

st.sidebar.markdown('<div class="sidebar-group"><div class="sidebar-group-title">건물 계획 조건</div>', unsafe_allow_html=True)
gross_area_m2 = st.sidebar.number_input("목표 연면적 (㎡)", min_value=50.0, value=900.0, step=10.0)
floors = st.sidebar.number_input("목표 층수", min_value=1, max_value=30, value=5, step=1)
building_length_m = st.sidebar.number_input("계획 건물 길이 (m)", min_value=6.0, value=24.0, step=1.0)
building_width_m = st.sidebar.number_input("계획 건물 폭 (m)", min_value=4.0, value=12.0, step=1.0)
front_setback_m = st.sidebar.number_input("전면 이격거리 (m)", min_value=0.0, value=3.0, step=0.5)
side_clearance_m = st.sidebar.number_input("측면 이격거리 (m)", min_value=0.0, value=2.0, step=0.5)
floor_to_floor_m = st.sidebar.number_input("층고/층간 높이 (m)", min_value=2.5, value=3.2, step=0.1)
extra_clearance_m = st.sidebar.number_input("설치 여유 높이 (m)", min_value=0.0, value=3.0, step=0.5)
repeatability_score = st.sidebar.slider("반복형 평면 정도", 1, 5, 4)
public_space_ratio = st.sidebar.slider("공용공간 비중", 1, 5, 2)
open_plan_need = st.sidebar.slider("개방형 평면 요구", 1, 5, 2)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

st.sidebar.markdown('<div class="sidebar-group"><div class="sidebar-group-title">모듈 및 장비 조건</div>', unsafe_allow_html=True)
module_mode = st.sidebar.radio("모듈 선정 방식", ["자동 추천", "DB 선택", "직접 입력"], horizontal=True)
recommended_module = None
module_ranking = []
if module_mode == "자동 추천":
    recommended_module, module_ranking = auto_select_module(
        building_use=building_use,
        floors=int(floors),
        repeatability_score=repeatability_score,
        public_space_ratio=public_space_ratio,
        open_plan_need=open_plan_need,
        road_width_m=road_width_m,
        staging_area_m2=staging_area_m2,
    )
    selected_module = recommended_module
elif module_mode == "DB 선택":
    selected_module = MODULE_DB[st.sidebar.selectbox("모듈 타입", list(MODULE_DB.keys()))]
else:
    selected_module = None

if selected_module:
    module_name = selected_module.name
    module_width_m = st.sidebar.number_input("모듈 폭 (m)", value=float(selected_module.width_m), step=0.1)
    module_length_m = st.sidebar.number_input("모듈 길이 (m)", value=float(selected_module.length_m), step=0.1)
    module_height_m = st.sidebar.number_input("모듈 높이 (m)", value=float(selected_module.height_m), step=0.1)
    module_weight_t = st.sidebar.number_input("모듈 자중 (t)", value=float(selected_module.weight_t_default), step=0.1)
    module_form = selected_module.openness
    module_floor_min = selected_module.floor_min
    module_floor_max = selected_module.floor_max
    transport_coeff = selected_module.transport_difficulty_coeff
    install_coeff = selected_module.install_difficulty_coeff
    module_eff = selected_module.base_efficiency_ratio
else:
    module_name = "사용자 정의 모듈"
    module_width_m = st.sidebar.number_input("모듈 폭 (m)", value=3.2, step=0.1)
    module_length_m = st.sidebar.number_input("모듈 길이 (m)", value=10.0, step=0.1)
    module_height_m = st.sidebar.number_input("모듈 높이 (m)", value=3.4, step=0.1)
    module_weight_t = st.sidebar.number_input("모듈 자중 (t)", value=12.0, step=0.1)
    module_form = st.sidebar.selectbox("모듈 형식", ["corner-supported", "open-ended", "open-sided", "hybrid", "대개구부/비정형"])
    module_floor_min = 1
    module_floor_max = 12
    transport_coeff = 1.2
    install_coeff = 1.2
    module_eff = 0.80

crane_offset_m = st.sidebar.number_input("크레인 설치 후보점 이격거리 (m)", min_value=0.0, value=4.0, step=0.5)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

run_analysis = st.sidebar.button("시공 가능성 분석 실행")

if run_analysis:
    st.session_state.analysis_ready = True


# ============================================================
# MAIN HEADER
# ============================================================
st.markdown(
    f"""
    <div class="hero">
        <div class="section-title">도심 노후 부지 모듈러 시공 가능성 시각화 분석</div>
        <div class="section-desc">
            부지 조건을 입력하면 도로·트레일러·크레인·모듈·적층 가능 층수를 함께 검토하여,
            모듈러가 실제로 들어갈 수 있는지 여부를 <b>가능 / 조건부 가능 / 불가</b>로 판정합니다.
        </div>
        <div class="small-note">현재 버전은 Step1 전용입니다. 공사비 및 RC 비교는 제외했습니다.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.analysis_ready:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">입력 후 분석 실행</div>
            <div class="section-desc">
                왼쪽 입력 패널에서 부지·도로·건물·모듈 조건을 입력한 뒤 <b>시공 가능성 분석 실행</b> 버튼을 눌러주세요.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


# ============================================================
# ANALYSIS
# ============================================================
lat, lon = geocode_address(site_address)
required_radius_m = compute_required_radius(site_depth_m, front_setback_m, crane_offset_m, building_width_m)
required_hook_height_m = compute_required_hook_height(floors * floor_to_floor_m, extra_clearance_m)
needed_lifting_t = round(module_weight_t * 1.15, 2)
modules_per_floor = estimate_modules_per_floor(building_length_m, building_width_m, module_length_m, module_width_m)
estimated_module_count = estimate_module_count(gross_area_m2, module_length_m, module_width_m, module_eff)

vehicle_rows = select_vehicle_specs(module_length_m, module_width_m, module_height_m, module_weight_t, road_width_m)
best_vehicle = vehicle_rows[0]
transport_height_m = best_vehicle["운송 높이(m)"]
total_weight_t = best_vehicle["총중량 추정(t)"]

route_result = evaluate_route_permit(
    module_width_m=module_width_m,
    transport_height_m=transport_height_m,
    total_weight_t=total_weight_t,
    road_width_m=road_width_m,
    turn_condition=turn_condition,
    obstacle_level=obstacle_level,
    bridge_tunnel_height_limit_m=bridge_tunnel_height_limit_m,
    managed_road_42m=(managed_road_42m == "예"),
    illegal_parking_constant=illegal_parking_constant,
    road_occupation_possible=(road_occupation_possible == "가능"),
)

transport_score, transport_reasons = transport_risk_score(
    module_width_m=module_width_m,
    transport_height_m=transport_height_m,
    module_weight_t=module_weight_t,
    module_length_m=module_length_m,
    turn_condition=turn_condition,
    obstacle_level=obstacle_level,
    pavement_level=pavement_level,
    module_form=module_form,
    transport_difficulty_coeff=transport_coeff,
)

install_score, install_reasons = installation_risk_score(
    module_length_m=module_length_m,
    module_weight_t=module_weight_t,
    floors=int(floors),
    required_radius_m=required_radius_m,
    staging_area_m2=staging_area_m2,
    module_form=module_form,
    install_difficulty_coeff=install_coeff,
)

crane_rows = evaluate_cranes(
    needed_lifting_t=needed_lifting_t,
    required_radius_m=required_radius_m,
    required_hook_height_m=required_hook_height_m,
    site_frontage_m=site_frontage_m,
    available_staging_m2=staging_area_m2,
)

best_crane = crane_rows[0]
if selected_module is not None:
    max_feasible_floors = compute_max_feasible_floors(crane_rows, selected_module, floor_to_floor_m, extra_clearance_m)
else:
    max_feasible_floors = max(0, int((max(r["최대Hook높이(m)"] for r in crane_rows if r["판정"] != "불가") - extra_clearance_m) // floor_to_floor_m)) if any(r["판정"] != "불가" for r in crane_rows) else 0
max_feasible_floors = min(max_feasible_floors, module_floor_max)
result_status, decision_reasons = final_decision(route_result["route_status"], best_crane["판정"], max_feasible_floors, int(floors))
improvement_actions = generate_improvement_actions(result_status, route_result["route_status"], crane_rows, int(floors), max_feasible_floors)


# ============================================================
# SUMMARY
# ============================================================
st.markdown(
    f"""
    <div class="result-hero">
        <div class="result-title">종합 판정</div>
        <div class="result-value">{project_name}</div>
        <div style="margin-top:0.5rem;">{grade_badge(result_status)}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_box("운송 경로 판정", route_result["route_status"], f"유효 도로폭 {route_result['effective_road_width']}m")
with c2:
    metric_box("추천 크레인", best_crane["장비"], f"판정 {best_crane['판정']} / 여유율 {best_crane['여유율']}")
with c3:
    metric_box("최대 가능 층수", f"{max_feasible_floors}층", f"목표 {int(floors)}층 대비")
with c4:
    metric_box("추천 모듈", module_name, f"{module_width_m}m × {module_length_m}m / {module_weight_t}t")


# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["부지 시각화", "운송 검토", "양중 검토", "모듈/적층 검토", "종합 결론"])

with tab1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">부지 · 도로 · 장비 배치 평면</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">전면도로, 대지, 계획 건물, 크레인 위치, 작업 반경, 트레일러 정차 위치를 단순화하여 시각적으로 표시합니다.</div>', unsafe_allow_html=True)

    fig_plan = create_site_plan_figure(
        site_width_m=site_width_m,
        site_depth_m=site_depth_m,
        road_width_m=road_width_m,
        building_length_m=building_length_m,
        building_width_m=building_width_m,
        front_setback_m=front_setback_m,
        side_clearance_m=side_clearance_m,
        crane_offset_m=crane_offset_m,
        crane_radius_m=required_radius_m,
        trailer_length_m=best_vehicle["적재면 길이(m)"],
        trailer_width_m=best_vehicle["적재면 폭(m)"],
        road_occupation_possible=(road_occupation_possible == "가능"),
    )
    st.plotly_chart(fig_plan, use_container_width=True)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown("#### 기본 부지 정보")
        st.dataframe(
            pd.DataFrame(
                {
                    "항목": ["대지 폭", "대지 깊이", "전면 도로폭", "접도 길이", "적치장 면적", "회전 조건"],
                    "값": [
                        f"{site_width_m} m",
                        f"{site_depth_m} m",
                        f"{road_width_m} m",
                        f"{site_frontage_m} m",
                        f"{staging_area_m2} ㎡",
                        turn_condition,
                    ],
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    with col_b:
        st.markdown("#### 주소 및 좌표")
        if lat is not None and lon is not None:
            st.success(f"지오코딩 성공: 위도 {lat:.6f}, 경도 {lon:.6f}")
            st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=15)
        else:
            st.info("주소를 입력하지 않았거나 좌표 변환에 실패했습니다. 시각화는 입력 수치 기준으로 계속 진행됩니다.")

    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">운송 가능성 검토</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">모듈 규격과 도로 조건을 기준으로 트레일러 후보와 경로 허가 필요 여부를 판단합니다.</div>', unsafe_allow_html=True)

    a1, a2, a3 = st.columns(3)
    with a1:
        metric_box("운송 리스크", transport_risk_bucket(transport_score), f"총점 {transport_score}점")
    with a2:
        metric_box("최적 트레일러", best_vehicle["운송 차량"], f"판정 {best_vehicle['판정']}")
    with a3:
        metric_box("운송 높이/총중량", f"{transport_height_m}m / {total_weight_t}t", "법적 허가 및 경로 제한 검토")

    st.markdown("#### 트레일러 후보표")
    st.dataframe(pd.DataFrame(vehicle_rows), use_container_width=True, hide_index=True)

    st.markdown("#### 경로 판정 사유")
    st.dataframe(make_reason_df(route_result["reasons"], "경로 검토 내용"), use_container_width=True, hide_index=True)

    st.markdown("#### 운송 리스크 세부 항목")
    st.dataframe(make_reason_df(transport_reasons, "운송 리스크 근거"), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">양중 장비 검토</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">필요 양중 하중, 작업 반경, 설치 폭, 훅 높이를 기준으로 장비 후보를 판정합니다.</div>', unsafe_allow_html=True)

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        metric_box("필요 양중 하중", f"{needed_lifting_t} t", "모듈 자중의 1.15배 기준")
    with b2:
        metric_box("필요 작업 반경", f"{round(required_radius_m, 1)} m", "전면부 설치 기준 단순 계산")
    with b3:
        metric_box("필요 훅 높이", f"{round(required_hook_height_m, 1)} m", "최고 층 + 설치 여유")
    with b4:
        metric_box("설치 리스크", installation_risk_bucket(install_score), f"총점 {install_score}점")

    st.markdown("#### 크레인 후보표")
    st.dataframe(pd.DataFrame(crane_rows), use_container_width=True, hide_index=True)

    st.markdown("#### 설치 리스크 세부 항목")
    st.dataframe(make_reason_df(install_reasons, "양중/설치 리스크 근거"), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">모듈 및 적층 검토</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">선정된 모듈의 규격과 적층 가능 범위를 기준으로 배치 밀도와 가능 층수를 검토합니다.</div>', unsafe_allow_html=True)

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        metric_box("모듈 규격", f"{module_width_m} × {module_length_m} m", f"높이 {module_height_m}m")
    with d2:
        metric_box("모듈 자중", f"{module_weight_t} t", f"형식 {module_form}")
    with d3:
        metric_box("층당 배치 가능 수", f"{modules_per_floor} 개", "단순 격자 배치 기준")
    with d4:
        metric_box("예상 총 모듈 수", f"{estimated_module_count} 개", "연면적 기준 추정")

    if module_mode == "자동 추천" and module_ranking:
        st.markdown("#### 자동 추천 모듈 순위")
        ranking_df = pd.DataFrame(
            {
                "모듈": [r["module"].name for r in module_ranking[:5]],
                "점수": [r["score"] for r in module_ranking[:5]],
                "주요 사유": ["; ".join(r["reasons"]) if r["reasons"] else "-" for r in module_ranking[:5]],
            }
        )
        st.dataframe(ranking_df, use_container_width=True, hide_index=True)

    floors_to_show = max(1, min(max_feasible_floors if max_feasible_floors > 0 else int(floors), 8))
    st.markdown("#### 모듈 적층 3D 표현")
    fig_3d = create_stack_3d_figure(
        building_length_m=building_length_m,
        building_width_m=building_width_m,
        floor_to_floor_m=floor_to_floor_m,
        floors_to_show=floors_to_show,
        module_length_m=module_length_m,
        module_width_m=module_width_m,
    )
    st.plotly_chart(fig_3d, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab5:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">종합 결론</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">현재 조건에서 모듈러의 실제 적용 가능 여부와, 불가 또는 조건부 가능 시 보완 방향을 제시합니다.</div>', unsafe_allow_html=True)

    st.markdown(f"### 최종 판정: {grade_badge(result_status)}", unsafe_allow_html=True)

    st.markdown("#### 최종 판단 근거")
    all_reasons = decision_reasons + route_result["reasons"][:3]
    if best_crane["판정"] != "가능":
        all_reasons.append(f"추천 크레인 {best_crane['장비']} 판정: {best_crane['판정']}")
    all_reasons.append(f"최대 가능 층수 추정: {max_feasible_floors}층")
    st.dataframe(make_reason_df(all_reasons, "최종 판단 근거"), use_container_width=True, hide_index=True)

    st.markdown("#### 추천 조합")
    summary_df = pd.DataFrame(
        {
            "항목": ["추천 모듈", "추천 트레일러", "추천 크레인", "목표 층수", "최대 가능 층수", "운송 경로 판정"],
            "값": [
                module_name,
                best_vehicle["운송 차량"],
                best_crane["장비"],
                f"{int(floors)}층",
                f"{max_feasible_floors}층",
                route_result["route_status"],
            ],
        }
    )
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.markdown("#### 보완 또는 다음 스터디 항목")
    if not improvement_actions:
        improvement_actions = ["현재 버전에서는 공사비를 제외하고 시공 가능성만 검토했습니다. 다음 단계에서 사업성 분석을 연결하면 됩니다."]
    st.dataframe(make_reason_df(improvement_actions, "개선/확장 방향"), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# FOOTNOTE
# ============================================================
st.caption(
    "현재 버전은 교수님 피드백에 맞춰 Step1 중심으로 재구성했습니다. 즉, RC/모듈러 우세 비교가 아니라, 도심 노후 부지에서 모듈러의 운송·양중·적층 가능 여부를 시각적으로 검토하는 앱입니다."
)

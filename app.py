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
    page_title="도심 노후 부지 모듈러 3D 시공 가능성 분석 도구",
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
# FIXED LH STANDARD MODULE
# ============================================================
# 필요하면 여기 숫자만 바꾸면 됨.
LH_STANDARD_MODULE = {
    "name": "LH 표준형 모듈",
    "structure": "코너지지 표준형",
    "width_m": 3.2,
    "length_m": 10.0,
    "height_m": 3.2,
    "weight_t": 12.0,
    "base_efficiency_ratio": 0.82,
    "transport_difficulty_coeff": 1.15,
    "install_difficulty_coeff": 1.15,
    "floor_min": 1,
    "floor_max": 12,
    "module_form": "corner-supported",
    "desc": "LH 표준형 단일 모듈 가정",
}


# ============================================================
# DATABASES
# ============================================================
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
    count_x = max(1, int(building_width_m // module_width_m))
    count_y = max(1, int(building_length_m // module_length_m))
    return max(1, count_x * count_y)


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
    floor_to_floor_m: float,
    crane_extra_clearance_m: float,
    module_floor_max: int,
) -> int:
    feasible_cranes = [r for r in crane_rows if r["판정"] in ["가능", "조건부 가능"]]
    if not feasible_cranes:
        return 0
    max_hook_height = max(r["최대Hook높이(m)"] for r in feasible_cranes)
    hook_based = max(0, int((max_hook_height - crane_extra_clearance_m) // floor_to_floor_m))
    return max(0, min(module_floor_max, hook_based))


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
        actions.append(f"목표 층수 {target_floors}층을 {max_feasible_floors}층 이하로 조정하거나 하부 RC + 상부 모듈러 검토")
    if result_status == "가능":
        actions.append("현재 조건 기준으로 실제 사례 부지 데이터를 넣어 시나리오 비교 분석 가능")
    return actions


def make_reason_df(items: List[str], col_name: str) -> pd.DataFrame:
    return pd.DataFrame({col_name: items})


# ============================================================
# 3D HELPERS
# ============================================================
def cuboid_edges(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float):
    pts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), (x0, y0, z1),
        (x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1), (x0, y1, z0)
    ]
    return [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts]


def add_box_wireframe(fig: go.Figure, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float, name: str, color: str = None, width: int = 4, showlegend: bool = False):
    xs, ys, zs = cuboid_edges(x0, x1, y0, y1, z0, z1)
    line_kwargs = {"width": width}
    if color is not None:
        line_kwargs["color"] = color

    fig.add_trace(
        go.Scatter3d(
            x=xs,
            y=ys,
            z=zs,
            mode="lines",
            line=line_kwargs,
            name=name,
            showlegend=showlegend,
            hoverinfo="name",
        )
    )


def add_ground_mesh(fig: go.Figure, x0: float, x1: float, y0: float, y1: float, z: float, color: str, name: str, opacity: float):
    fig.add_trace(
        go.Mesh3d(
            x=[x0, x1, x1, x0],
            y=[y0, y0, y1, y1],
            z=[z, z, z, z],
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            color=color,
            opacity=opacity,
            name=name,
            hoverinfo="name",
            showlegend=True,
        )
    )


def create_full_site_3d_figure(
    site_width_m: float,
    site_depth_m: float,
    road_width_m: float,
    building_length_m: float,
    building_width_m: float,
    floor_to_floor_m: float,
    floors_to_show: int,
    module_length_m: float,
    module_width_m: float,
    front_setback_m: float,
    side_clearance_m: float,
    crane_offset_m: float,
    trailer_length_m: float,
    trailer_width_m: float,
    display_modules_count: int,
) -> go.Figure:
    fig = go.Figure()

    # 좌표계
    # x = 대지 깊이 방향
    # y = 대지 폭 방향
    # z = 높이

    # 1) 도로
    add_ground_mesh(
        fig,
        x0=-road_width_m,
        x1=0,
        y0=0,
        y1=site_width_m,
        z=0,
        color="lightblue",
        name="전면도로",
        opacity=0.55,
    )

    # 2) 대지
    add_ground_mesh(
        fig,
        x0=0,
        x1=site_depth_m,
        y0=0,
        y1=site_width_m,
        z=0,
        color="lightgreen",
        name="대지",
        opacity=0.35,
    )

    # 3) 건물 경계
    building_x0 = front_setback_m
    building_x1 = min(site_depth_m - front_setback_m, front_setback_m + building_width_m)
    building_y0 = side_clearance_m
    building_y1 = min(site_width_m - side_clearance_m, side_clearance_m + building_length_m)

    add_box_wireframe(
        fig,
        building_x0,
        building_x1,
        building_y0,
        building_y1,
        0,
        max(0.1, floors_to_show * floor_to_floor_m),
        "건물 외곽",
        color="#f59e0b",
        width=5,
        showlegend=True,
    )

    # 4) 트레일러
    trailer_x0 = -road_width_m + 0.6
    trailer_x1 = min(-0.2, trailer_x0 + min(trailer_length_m, road_width_m + 3.0))
    trailer_y0 = max(0.8, site_width_m / 2 - trailer_width_m / 2)
    trailer_y1 = min(site_width_m - 0.8, trailer_y0 + trailer_width_m)

    add_box_wireframe(
        fig,
        trailer_x0,
        trailer_x1,
        trailer_y0,
        trailer_y1,
        0,
        1.2,
        "트레일러",
        color="#4f46e5",
        width=6,
        showlegend=True,
    )

    # 트레일러 적재 모듈 1개
    module_on_trailer_length = min(module_length_m * 0.85, max(1.0, trailer_x1 - trailer_x0 - 0.3))
    module_on_trailer_width = min(module_width_m * 0.90, max(0.8, trailer_y1 - trailer_y0 - 0.2))
    mtx0 = trailer_x0 + 0.15
    mtx1 = mtx0 + module_on_trailer_length
    mty0 = trailer_y0 + 0.10
    mty1 = mty0 + module_on_trailer_width

    add_box_wireframe(
        fig,
        mtx0,
        mtx1,
        mty0,
        mty1,
        1.2,
        1.2 + 2.3,
        "운송 중 모듈",
        color="#2563eb",
        width=4,
        showlegend=True,
    )

    # 5) 크레인 mast
    crane_x = max(1.5, crane_offset_m)
    crane_y = site_width_m / 2
    mast_half = 0.35
    mast_height = floors_to_show * floor_to_floor_m + 8.0

    add_box_wireframe(
        fig,
        crane_x - mast_half,
        crane_x + mast_half,
        crane_y - mast_half,
        crane_y + mast_half,
        0,
        mast_height,
        "크레인 마스트",
        color="#dc2626",
        width=7,
        showlegend=True,
    )

    # 6) 크레인 boom
    hook_target_x = building_x0 + (building_x1 - building_x0) / 2
    hook_target_y = building_y0 + (building_y1 - building_y0) / 2
    boom_z0 = mast_height
    boom_z1 = floors_to_show * floor_to_floor_m + 2.0

    fig.add_trace(
        go.Scatter3d(
            x=[crane_x, hook_target_x],
            y=[crane_y, hook_target_y],
            z=[boom_z0, boom_z1],
            mode="lines",
            line=dict(color="#dc2626", width=8),
            name="크레인 붐",
            showlegend=True,
            hoverinfo="name",
        )
    )

    # 7) 모듈 적층
    count_x = max(1, int(building_width_m // module_width_m))
    count_y = max(1, int(building_length_m // module_length_m))
    total_slots = count_x * count_y * max(1, floors_to_show)
    modules_to_draw = min(display_modules_count, total_slots)

    drawn = 0
    for floor in range(floors_to_show):
        z0 = floor * floor_to_floor_m
        z1 = z0 + floor_to_floor_m * 0.9

        for iy in range(count_y):
            for ix in range(count_x):
                if drawn >= modules_to_draw:
                    break

                x0 = building_x0 + ix * module_width_m
                x1 = x0 + module_width_m * 0.95
                y0 = building_y0 + iy * module_length_m
                y1 = y0 + module_length_m * 0.95

                if x1 <= building_x1 and y1 <= building_y1:
                    add_box_wireframe(
                        fig,
                        x0,
                        x1,
                        y0,
                        y1,
                        z0,
                        z1,
                        f"Module {drawn+1}",
                        color="#111827",
                        width=3,
                        showlegend=False,
                    )
                    drawn += 1
            if drawn >= modules_to_draw:
                break
        if drawn >= modules_to_draw:
            break

    # 8) 카메라 및 축
    max_z = max(mast_height, floors_to_show * floor_to_floor_m + 5)
    fig.update_layout(
        height=820,
        margin=dict(l=0, r=0, t=20, b=0),
        legend=dict(orientation="h"),
        scene=dict(
            xaxis_title="깊이 방향 (m)",
            yaxis_title="폭 방향 (m)",
            zaxis_title="높이 (m)",
            aspectmode="manual",
            aspectratio=dict(
                x=max(site_depth_m + road_width_m, 10) / 20,
                y=max(site_width_m, 10) / 20,
                z=max(max_z, 10) / 20,
            ),
            camera=dict(
                eye=dict(x=1.8, y=1.7, z=1.1)
            ),
        ),
    )

    return fig


# ============================================================
# SIDEBAR INPUT
# ============================================================
st.sidebar.markdown("## 입력 패널")
st.sidebar.caption("입력값을 바탕으로 LH 표준 모듈을 자동 적층하고, 도로·트레일러·크레인·모듈러를 하나의 3D 장면으로 보여줍니다.")

st.sidebar.markdown('<div class="sidebar-group"><div class="sidebar-group-title">기본 정보</div>', unsafe_allow_html=True)
project_name = st.sidebar.text_input("사업명", value="도심 노후 부지 모듈러 3D 적용 검토")
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
building_length_m = st.sidebar.number_input("계획 건물 길이 (m)", min_value=6.0, value=24.0, step=1.0)
building_width_m = st.sidebar.number_input("계획 건물 폭 (m)", min_value=4.0, value=12.0, step=1.0)
front_setback_m = st.sidebar.number_input("전면 이격거리 (m)", min_value=0.0, value=3.0, step=0.5)
side_clearance_m = st.sidebar.number_input("측면 이격거리 (m)", min_value=0.0, value=2.0, step=0.5)
floor_to_floor_m = st.sidebar.number_input("층고/층간 높이 (m)", min_value=2.5, value=3.2, step=0.1)
extra_clearance_m = st.sidebar.number_input("설치 여유 높이 (m)", min_value=0.0, value=3.0, step=0.5)

manual_target_floors = st.sidebar.number_input("비교용 목표 층수 (자동산정과 비교용)", min_value=1, max_value=30, value=5, step=1)
crane_offset_m = st.sidebar.number_input("크레인 설치 후보점 이격거리 (m)", min_value=0.0, value=4.0, step=0.5)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

run_analysis = st.sidebar.button("3D 시공 장면 생성 및 분석 실행")

if run_analysis:
    st.session_state.analysis_ready = True


# ============================================================
# MAIN HEADER
# ============================================================
st.markdown(
    f"""
    <div class="hero">
        <div class="section-title">LH 표준형 모듈 기반 도심 노후 부지 3D 시공 가능성 분석</div>
        <div class="section-desc">
            입력한 부지 및 건물 조건을 바탕으로 <b>필요 모듈 수</b>, <b>층당 배치 수</b>, <b>자동 필요 층수</b>를 계산하고,
            전면도로·트레일러·크레인·모듈 적층 건물을 <b>하나의 3D 장면</b>으로 통합 시각화합니다.
        </div>
        <div class="small-note">현재 버전은 LH 표준형 단일 모듈 가정이며, RC 공사비 비교는 제외하고 Step1 시공 가능성 중심으로 구성했습니다.</div>
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
                왼쪽 입력 패널에서 부지와 건물 조건을 입력한 뒤 <b>3D 시공 장면 생성 및 분석 실행</b> 버튼을 눌러주세요.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


# ============================================================
# FIXED MODULE VALUES
# ============================================================
module_name = LH_STANDARD_MODULE["name"]
module_width_m = LH_STANDARD_MODULE["width_m"]
module_length_m = LH_STANDARD_MODULE["length_m"]
module_height_m = LH_STANDARD_MODULE["height_m"]
module_weight_t = LH_STANDARD_MODULE["weight_t"]
module_eff = LH_STANDARD_MODULE["base_efficiency_ratio"]
module_form = LH_STANDARD_MODULE["module_form"]
transport_coeff = LH_STANDARD_MODULE["transport_difficulty_coeff"]
install_coeff = LH_STANDARD_MODULE["install_difficulty_coeff"]
module_floor_min = LH_STANDARD_MODULE["floor_min"]
module_floor_max = LH_STANDARD_MODULE["floor_max"]


# ============================================================
# ANALYSIS
# ============================================================
lat, lon = geocode_address(site_address)

required_radius_m = compute_required_radius(site_depth_m, front_setback_m, crane_offset_m, building_width_m)
needed_lifting_t = round(module_weight_t * 1.15, 2)

modules_per_floor = estimate_modules_per_floor(
    building_length_m=building_length_m,
    building_width_m=building_width_m,
    module_length_m=module_length_m,
    module_width_m=module_width_m,
)

estimated_module_count = estimate_module_count(
    gross_area_m2=gross_area_m2,
    module_length_m=module_length_m,
    module_width_m=module_width_m,
    efficiency_ratio=module_eff,
)

auto_required_floors = max(1, math.ceil(estimated_module_count / modules_per_floor))
required_hook_height_m = compute_required_hook_height(auto_required_floors * floor_to_floor_m, extra_clearance_m)

vehicle_rows = select_vehicle_specs(
    module_length_m=module_length_m,
    module_width_m=module_width_m,
    module_height_m=module_height_m,
    module_weight_t=module_weight_t,
    road_width_m=road_width_m,
)
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
    floors=auto_required_floors,
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
max_feasible_floors = compute_max_feasible_floors(
    crane_rows=crane_rows,
    floor_to_floor_m=floor_to_floor_m,
    crane_extra_clearance_m=extra_clearance_m,
    module_floor_max=module_floor_max,
)

display_floors = min(auto_required_floors, max_feasible_floors if max_feasible_floors > 0 else auto_required_floors)

# 최종 판정은 자동 필요 층수를 기준으로 평가
result_status, decision_reasons = final_decision(
    route_status=route_result["route_status"],
    best_crane_status=best_crane["판정"],
    max_feasible_floors=max_feasible_floors,
    target_floors=auto_required_floors,
)

improvement_actions = generate_improvement_actions(
    result_status=result_status,
    route_status=route_result["route_status"],
    crane_rows=crane_rows,
    target_floors=auto_required_floors,
    max_feasible_floors=max_feasible_floors,
)


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
    metric_box("필요 총 모듈 수", f"{estimated_module_count}개", f"층당 배치 {modules_per_floor}개")
with c2:
    metric_box("자동 필요 층수", f"{auto_required_floors}층", f"입력 연면적 기준")
with c3:
    metric_box("최대 가능 층수", f"{max_feasible_floors}층", f"크레인/높이 조건 기준")
with c4:
    metric_box("고정 모듈", module_name, f"{module_width_m}m × {module_length_m}m × {module_height_m}m / {module_weight_t}t")


# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(["통합 3D 시각화", "운송 검토", "양중 검토", "종합 결론"])

with tab1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">도로 · 트레일러 · 크레인 · 모듈러 적층 통합 3D 장면</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-desc">현재 입력 조건 기준으로 LH 표준형 모듈 {estimated_module_count}개가 필요하다고 보고, 실제 표현은 최대 가능 층수와 자동 필요 층수를 반영하여 {display_floors}개 층까지 적층 장면을 표시합니다.</div>',
        unsafe_allow_html=True,
    )

    fig_full_3d = create_full_site_3d_figure(
        site_width_m=site_width_m,
        site_depth_m=site_depth_m,
        road_width_m=road_width_m,
        building_length_m=building_length_m,
        building_width_m=building_width_m,
        floor_to_floor_m=floor_to_floor_m,
        floors_to_show=max(1, display_floors),
        module_length_m=module_length_m,
        module_width_m=module_width_m,
        front_setback_m=front_setback_m,
        side_clearance_m=side_clearance_m,
        crane_offset_m=crane_offset_m,
        trailer_length_m=float(best_vehicle["적재면 길이(m)"]),
        trailer_width_m=float(best_vehicle["적재면 폭(m)"]),
        display_modules_count=estimated_module_count,
    )
    st.plotly_chart(fig_full_3d, use_container_width=True)

    info_df = pd.DataFrame(
        {
            "항목": [
                "고정 모듈명",
                "모듈 크기",
                "모듈 중량",
                "층당 배치 수",
                "총 필요 모듈 수",
                "자동 필요 층수",
                "3D 표시 층수",
            ],
            "값": [
                module_name,
                f"{module_width_m}m × {module_length_m}m × {module_height_m}m",
                f"{module_weight_t}t",
                f"{modules_per_floor}개/층",
                f"{estimated_module_count}개",
                f"{auto_required_floors}층",
                f"{display_floors}층",
            ],
        }
    )
    st.dataframe(info_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">운송 검토</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">트레일러 적재 가능성과 도로 진입 가능성을 함께 검토합니다.</div>', unsafe_allow_html=True)

    c21, c22 = st.columns(2)
    with c21:
        metric_box("운송 경로 판정", route_result["route_status"], f"유효 도로폭 {route_result['effective_road_width']}m")
    with c22:
        metric_box("운송 리스크", transport_risk_bucket(transport_score), f"총점 {transport_score}점")

    st.markdown("#### 추천 트레일러")
    st.dataframe(pd.DataFrame(vehicle_rows), use_container_width=True, hide_index=True)

    st.markdown("#### 경로/허가 검토 근거")
    st.dataframe(make_reason_df(route_result["reasons"], "검토 근거"), use_container_width=True, hide_index=True)

    st.markdown("#### 운송 리스크 상세")
    st.dataframe(make_reason_df(transport_reasons, "운송 리스크 상세"), use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">양중 검토</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">필요 양중하중, 작업반경, Hook 높이 기준으로 크레인을 판정합니다.</div>', unsafe_allow_html=True)

    c31, c32, c33 = st.columns(3)
    with c31:
        metric_box("필요 양중하중", f"{needed_lifting_t}t", "모듈 자중 × 1.15")
    with c32:
        metric_box("필요 작업반경", f"{required_radius_m:.1f}m", "전면 이격 + 크레인 오프셋 + 건물 절반폭")
    with c33:
        metric_box("필요 Hook 높이", f"{required_hook_height_m:.1f}m", "자동 필요 층수 기준")

    st.markdown("#### 크레인 후보 판정")
    st.dataframe(pd.DataFrame(crane_rows), use_container_width=True, hide_index=True)

    st.markdown("#### 설치 리스크 상세")
    st.dataframe(make_reason_df(install_reasons, "설치 리스크 상세"), use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">종합 결론</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">현재 입력 조건에서 LH 표준형 모듈을 기준으로 실제 적용 가능 여부와 보완 방향을 제시합니다.</div>', unsafe_allow_html=True)

    st.markdown(f"### 최종 판정: {grade_badge(result_status)}", unsafe_allow_html=True)

    st.markdown("#### 자동 산정 결과 요약")
    auto_df = pd.DataFrame(
        {
            "항목": [
                "고정 모듈",
                "총 필요 모듈 수",
                "층당 배치 수",
                "자동 필요 층수",
                "최대 가능 층수",
                "비교용 수동 목표 층수",
                "운송 경로 판정",
                "추천 트레일러",
                "추천 크레인",
            ],
            "값": [
                module_name,
                f"{estimated_module_count}개",
                f"{modules_per_floor}개/층",
                f"{auto_required_floors}층",
                f"{max_feasible_floors}층",
                f"{manual_target_floors}층",
                route_result["route_status"],
                best_vehicle["운송 차량"],
                best_crane["장비"],
            ],
        }
    )
    st.dataframe(auto_df, use_container_width=True, hide_index=True)

    st.markdown("#### 최종 판단 근거")
    all_reasons = decision_reasons + route_result["reasons"][:3]
    all_reasons.append(f"추천 크레인 판정: {best_crane['장비']} / {best_crane['판정']}")
    all_reasons.append(f"자동 필요 층수: {auto_required_floors}층")
    all_reasons.append(f"최대 가능 층수: {max_feasible_floors}층")
    st.dataframe(make_reason_df(all_reasons, "최종 판단 근거"), use_container_width=True, hide_index=True)

    st.markdown("#### 보완 또는 다음 스터디 항목")
    if not improvement_actions:
        improvement_actions = ["현재 버전은 시공 가능성 중심입니다. 다음 단계에서 RC 대비 공사비, 공기, 사업성 분석을 연결하면 됩니다."]
    st.dataframe(make_reason_df(improvement_actions, "보완 항목"), use_container_width=True, hide_index=True)

    if lat is not None and lon is not None:
        st.markdown("#### 지오코딩 결과")
        geo_df = pd.DataFrame(
            {
                "항목": ["주소", "위도", "경도"],
                "값": [site_address, round(lat, 6), round(lon, 6)],
            }
        )
        st.dataframe(geo_df, use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)

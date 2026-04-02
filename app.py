
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim


st.set_page_config(
    page_title="STEP 1 - 부지별 RC 대비 모듈러 공사비 비교 프로그램",
    page_icon="🏗️",
    layout="wide",
)

st.markdown(
    """
<style>
.main-title {
    font-size: 34px;
    font-weight: 800;
    margin-bottom: 0.2rem;
}
.sub-title {
    font-size: 18px;
    color: #555;
    margin-bottom: 1.2rem;
}
.block-card {
    background-color: #f8f9fb;
    padding: 1.2rem 1.2rem 0.8rem 1.2rem;
    border-radius: 16px;
    border: 1px solid #e6e8ef;
    margin-bottom: 1rem;
}
.result-card {
    background-color: #ffffff;
    padding: 1.2rem;
    border-radius: 16px;
    border: 1px solid #e6e8ef;
    box-shadow: 0 4px 14px rgba(0,0,0,0.04);
    margin-bottom: 1rem;
}
.kpi {
    background: #ffffff;
    border: 1px solid #e6e8ef;
    border-radius: 16px;
    padding: 1rem;
    height: 100%;
}
.kpi-title {
    font-size: 14px;
    color: #666;
}
.kpi-value {
    font-size: 24px;
    font-weight: 800;
    margin-top: 0.2rem;
}
.stButton > button {
    width: 100%;
    border-radius: 12px;
    height: 3.2rem;
    font-size: 18px;
    font-weight: 700;
}
</style>
""",
    unsafe_allow_html=True,
)


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
    width_range_text: str
    length_range_text: str
    height_range_text: str
    weight_range_text: str
    recommended_floor_range: str
    recommended_joint: str
    representative_trailer: str
    recommended_crane_group: str
    prefab_rate_min: float
    prefab_rate_max: float
    install_difficulty_coeff: float
    transport_difficulty_coeff: float
    large_opening: bool
    repeatability_score: int
    public_space_score: int
    note_text: str
    floor_min: int
    floor_max: int
    open_plan_score: int
    base_efficiency_ratio: float

    @property
    def weight_t_default(self) -> float:
        return round((self.weight_t_min + self.weight_t_max) / 2.0, 2)

    @property
    def prefab_rate_text(self) -> str:
        return f"{int(round(self.prefab_rate_min * 100))}~{int(round(self.prefab_rate_max * 100))}%"

    @property
    def module_area_m2(self) -> float:
        return self.width_m * self.length_m


@dataclass
class TrailerSpec:
    name: str
    deck_length_m: float
    deck_width_m: float
    deck_height_m: float
    vehicle_weight_t: float
    payload_t: float
    steering: str


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
        width_range_text="2.7~3.2 m",
        length_range_text="6.0~8.5 m",
        height_range_text="3.0~3.3 m",
        weight_range_text="6~10 t",
        recommended_floor_range="저층~중층",
        recommended_joint="볼트",
        representative_trailer="2축/3축 저상 트레일러",
        recommended_crane_group="트럭크레인, 중소형 타워크레인",
        prefab_rate_min=0.70,
        prefab_rate_max=0.90,
        install_difficulty_coeff=1.00,
        transport_difficulty_coeff=1.00,
        large_opening=False,
        repeatability_score=5,
        public_space_score=2,
        note_text="반복형 평면에 가장 유리하고 경제성이 높은 대표 유형",
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
        width_range_text="3.0~3.5 m",
        length_range_text="8.0~10.5 m",
        height_range_text="3.1~3.5 m",
        weight_range_text="10~15 t",
        recommended_floor_range="저층~중층",
        recommended_joint="볼트 + 플레이트",
        representative_trailer="3축 저상 트레일러",
        recommended_crane_group="트럭크레인, 타워크레인",
        prefab_rate_min=0.60,
        prefab_rate_max=0.85,
        install_difficulty_coeff=1.20,
        transport_difficulty_coeff=1.15,
        large_opening=False,
        repeatability_score=4,
        public_space_score=3,
        note_text="주거형 프로젝트에서 가장 무난하게 적용 가능한 표준형",
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
        desc="적층 안정성을 우선하는 다층 모듈러 대응형",
        width_range_text="3.0~3.6 m",
        length_range_text="8.0~12.0 m",
        height_range_text="3.2~3.6 m",
        weight_range_text="12~18 t",
        recommended_floor_range="중층",
        recommended_joint="플레이트 + 볼트",
        representative_trailer="3축 저상 트레일러",
        recommended_crane_group="타워크레인",
        prefab_rate_min=0.60,
        prefab_rate_max=0.80,
        install_difficulty_coeff=1.25,
        transport_difficulty_coeff=1.20,
        large_opening=False,
        repeatability_score=4,
        public_space_score=3,
        note_text="적층 반복이 많은 프로젝트에 유리하고 상층 양중 검토가 중요",
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
        desc="측면 개방성이 커서 공용공간이나 대공간 조합에 유리한 모듈",
        width_range_text="3.2~4.0 m",
        length_range_text="9.0~12.0 m",
        height_range_text="3.4~3.8 m",
        weight_range_text="15~22 t",
        recommended_floor_range="저층~중층",
        recommended_joint="플레이트 + 볼트 + 보강",
        representative_trailer="3축 저상 또는 특수 트레일러",
        recommended_crane_group="중대형 타워크레인, 크롤러크레인",
        prefab_rate_min=0.50,
        prefab_rate_max=0.70,
        install_difficulty_coeff=1.50,
        transport_difficulty_coeff=1.35,
        large_opening=True,
        repeatability_score=2,
        public_space_score=5,
        note_text="대개구부로 인해 구조 보강과 운송 시 비틀림 관리가 중요",
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
        desc="단부 개방을 통해 세대 또는 복도 방향 연결성을 확보하는 모듈",
        width_range_text="3.0~3.5 m",
        length_range_text="8.0~10.0 m",
        height_range_text="3.2~3.5 m",
        weight_range_text="11~16 t",
        recommended_floor_range="저층~중층",
        recommended_joint="볼트 + 플레이트",
        representative_trailer="3축 저상 트레일러",
        recommended_crane_group="타워크레인",
        prefab_rate_min=0.60,
        prefab_rate_max=0.80,
        install_difficulty_coeff=1.20,
        transport_difficulty_coeff=1.20,
        large_opening=True,
        repeatability_score=3,
        public_space_score=3,
        note_text="내부 연속 공간 확보에 유리하지만 단부 보강 상세가 중요",
        floor_min=1,
        floor_max=10,
        open_plan_score=3,
        base_efficiency_ratio=0.76,
    ),
    "Corridor-type combined module": ModuleType(
        name="Corridor-type combined module",
        structure="내력벽형 또는 코너지지형",
        width_m=3.0,
        length_m=8.5,
        height_m=3.2,
        weight_t_min=8.0,
        weight_t_max=12.0,
        openness="corner-supported",
        desc="복도형 또는 중복도형 반복 배치에 적합한 세대 조합용 모듈",
        width_range_text="2.8~3.3 m",
        length_range_text="7.0~9.0 m",
        height_range_text="3.0~3.3 m",
        weight_range_text="8~12 t",
        recommended_floor_range="저층~중층",
        recommended_joint="볼트",
        representative_trailer="2축/3축 저상 트레일러",
        recommended_crane_group="트럭크레인, 타워크레인",
        prefab_rate_min=0.70,
        prefab_rate_max=0.90,
        install_difficulty_coeff=1.10,
        transport_difficulty_coeff=1.05,
        large_opening=False,
        repeatability_score=5,
        public_space_score=3,
        note_text="반복 배치 효율이 높고 모듈 수 산정이 비교적 단순한 유형",
        floor_min=1,
        floor_max=12,
        open_plan_score=1,
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
        width_range_text="3.4~4.2 m",
        length_range_text="10.0~14.0 m",
        height_range_text="3.4~3.9 m",
        weight_range_text="18~25 t",
        recommended_floor_range="저층~중층",
        recommended_joint="플레이트 + 그라우트 보강",
        representative_trailer="특수 트레일러 검토",
        recommended_crane_group="중대형 타워크레인, 크롤러크레인",
        prefab_rate_min=0.45,
        prefab_rate_max=0.65,
        install_difficulty_coeff=1.60,
        transport_difficulty_coeff=1.45,
        large_opening=True,
        repeatability_score=2,
        public_space_score=5,
        note_text="중량 증가와 대개구부 특성 때문에 운송·양중 민감도가 높음",
        floor_min=1,
        floor_max=8,
        open_plan_score=5,
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
        width_range_text="3.2~3.5 m",
        length_range_text="15.0~19.0 m",
        height_range_text="3.6~4.5 m",
        weight_range_text="30~40 t",
        recommended_floor_range="중층 이상",
        recommended_joint="볼트 + 플레이트 + 그라우트 혼합",
        representative_trailer="3축 또는 특수 트레일러",
        recommended_crane_group="타워크레인, 러핑크레인",
        prefab_rate_min=0.40,
        prefab_rate_max=0.70,
        install_difficulty_coeff=1.80,
        transport_difficulty_coeff=1.60,
        large_opening=True,
        repeatability_score=4,
        public_space_score=4,
        note_text="하부와 상부 인터페이스 상세가 핵심이며 중량·경로 조건에 민감",
        floor_min=6,
        floor_max=20,
        open_plan_score=4,
        base_efficiency_ratio=0.74,
    ),
}

TRAILER_DB: List[TrailerSpec] = [
    TrailerSpec("2축 저상 트레일러 A", 12.0, 2.44, 0.90, 5.05, 22.0, "일반"),
    TrailerSpec("2축 저상 트레일러 B", 13.3, 2.75, 0.50, 7.51, 23.0, "일반"),
    TrailerSpec("3축 저상 트레일러 A", 12.83, 2.75, 0.65, 7.57, 23.0, "일반"),
    TrailerSpec("3축 저상 트레일러 B", 13.51, 2.75, 0.90, 8.37, 22.5, "일반"),
    TrailerSpec("3축 저상 트레일러 C", 13.39, 2.75, 0.20, 15.69, 15.3, "일반"),
    TrailerSpec("가변조향 트레일러", 13.39, 2.75, 0.20, 18.39, 12.5, "가변조향"),
]

CRANE_DB: List[CraneSpec] = [
    CraneSpec("Truck Crane 25t", "트럭크레인", 25.0, 30.0, 2.5, 45.0, "단기/이동식", hourly_cost_krw=59751, footprint_desc="아웃트리거 전개 공간 필요"),
    CraneSpec("Truck Crane 40t", "트럭크레인", 40.0, 39.0, 4.0, 44.0, "단기/이동식", hourly_cost_krw=68913, footprint_desc="아웃트리거 전개 공간 필요"),
    CraneSpec("Tower Crane 8t", "타워크레인", 8.0, 60.0, 1.5, 60.0, "고정식", monthly_rent_krw=14458982, setup_cost_krw=27752267, footprint_desc="기초 필요"),
    CraneSpec("Tower Crane 10t", "타워크레인", 10.0, 65.0, 2.0, 70.0, "고정식", monthly_rent_krw=15744463, setup_cost_krw=27752267, footprint_desc="기초 필요"),
    CraneSpec("Tower Crane 12t", "타워크레인", 12.0, 70.0, 2.4, 80.0, "고정식", monthly_rent_krw=16885655, setup_cost_krw=27752267, footprint_desc="기초 필요"),
    CraneSpec("Liebherr 340 EC-B 16", "타워크레인", 16.0, 78.0, 2.1, 84.7, "탑슬루잉", footprint_desc="기초 필요"),
    CraneSpec("Potain MCT 565 M20", "타워크레인", 20.0, 80.0, 4.0, 84.2, "탑슬루잉", footprint_desc="기초 필요"),
    CraneSpec("Crawler Crane 100t", "크롤러크레인", 100.0, 52.0, 8.0, 64.0, "대형/야적장형", hourly_cost_krw=115612, footprint_desc="넓은 작업장과 지반 확보 필요"),
    CraneSpec("Crawler Crane 120t", "크롤러크레인", 120.0, 64.0, 11.0, 73.2, "대형/야적장형", footprint_desc="넓은 작업장과 지반 확보 필요"),
    CraneSpec("Crawler Crane 300t", "크롤러크레인", 300.0, 143.0, 18.0, 169.0, "초대형", hourly_cost_krw=502517, footprint_desc="매우 넓은 작업장과 고강도 지반 필요"),
    CraneSpec("Luffing Crane 12t", "러핑크레인", 12.0, 60.0, 2.6, 200.0, "도심 고층형", footprint_desc="좁은 회전공간에 상대적으로 유리"),
    CraneSpec("Luffing Crane 24t", "러핑크레인", 24.0, 60.0, 4.0, 210.0, "도심 고층형", footprint_desc="좁은 회전공간에 상대적으로 유리"),
    CraneSpec("Luffing Crane 64t", "러핑크레인", 64.0, 70.0, 10.0, 300.0, "도심 초고층형", footprint_desc="초고층 및 협소 회전조건 대응"),
]

PUMP_TRUCK_COSTS = {
    "21m": 51698, "28m": 61567, "32m": 72600, "36m": 90024,
    "41m": 93192, "43m": 118140, "47m": 129579, "52m": 137192,
}
MIXER_TRUCK_HOURLY = 25948
READYMIX_PRICE_PER_M3 = 95500


def geocode_address(address: str) -> Tuple[Optional[float], Optional[float]]:
    try:
        geolocator = Nominatim(user_agent="modular_rc_step1_app")
        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
        return None, None
    except Exception:
        return None, None


def render_simple_map(address: str) -> bool:
    lat, lon = geocode_address(address)
    if lat is None or lon is None:
        st.warning("주소를 찾지 못했습니다. 도로명주소를 다시 확인해 주세요.")
        return False
    st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))
    st.caption(f"위도: {lat:.6f} / 경도: {lon:.6f}")
    return True


def format_krw(value: float) -> str:
    return f"{int(round(value)):,}원"


def bool_ko(flag: bool) -> str:
    return "예" if flag else "아니오"


def module_db_dataframe() -> pd.DataFrame:
    rows = []
    for module in MODULE_DB.values():
        rows.append({
            "모듈 타입": module.name,
            "구조방식": module.structure,
            "폭 범위": module.width_range_text,
            "길이 범위": module.length_range_text,
            "높이 범위": module.height_range_text,
            "중량 범위": module.weight_range_text,
            "권장 층수": module.recommended_floor_range,
            "권장 접합": module.recommended_joint,
            "대표 트레일러": module.representative_trailer,
            "권장 크레인군": module.recommended_crane_group,
            "공장 제작률": module.prefab_rate_text,
            "설치 난이도 계수": module.install_difficulty_coeff,
            "운송 난이도 계수": module.transport_difficulty_coeff,
            "대개구부": bool_ko(module.large_opening),
            "반복형 적합도": module.repeatability_score,
            "공용공간 적합도": module.public_space_score,
            "개방형 적합도": module.open_plan_score,
            "기본 효율계수": module.base_efficiency_ratio,
            "특징": module.note_text,
        })
    return pd.DataFrame(rows)


def risk_level_from_margin(margin: float) -> str:
    if margin >= 1.30:
        return "안전한 편"
    if margin >= 1.10:
        return "주의 필요"
    if margin >= 1.00:
        return "매우 민감"
    return "불가"


def transport_risk_bucket(score: float) -> str:
    if score < 9:
        return "낮음"
    if score < 17:
        return "중간"
    if score < 26:
        return "높음"
    return "매우 높음"


def interpolate_allowable_load(crane: CraneSpec, radius_m: float) -> float:
    if radius_m <= 0:
        return crane.max_capacity_t
    radius = min(radius_m, crane.max_radius_m)
    r0 = 5.0
    if radius <= r0:
        return crane.max_capacity_t
    slope = (crane.tip_load_t - crane.max_capacity_t) / max(crane.max_radius_m - r0, 1.0)
    allowable = crane.max_capacity_t + slope * (radius - r0)
    return max(0.0, allowable)


def estimate_module_count(
    gross_area_m2: float,
    module_length_m: float,
    module_width_m: float,
    efficiency_ratio: float,
) -> int:
    module_area = module_length_m * module_width_m
    effective_area = module_area * efficiency_ratio
    if effective_area <= 0:
        return 0
    return max(1, math.ceil(gross_area_m2 / effective_area))


def select_feasible_trailers(module_length_m: float, module_width_m: float, module_height_m: float, module_weight_t: float) -> List[Dict[str, object]]:
    candidates: List[Dict[str, object]] = []
    for trailer in TRAILER_DB:
        transport_height = trailer.deck_height_m + module_height_m
        width_ok = module_width_m <= trailer.deck_width_m
        length_ok = module_length_m <= trailer.deck_length_m
        payload_ok = module_weight_t <= trailer.payload_t
        permit_needed = module_width_m > 2.5 or transport_height > 4.0
        total_weight_t = module_weight_t + trailer.vehicle_weight_t
        axle_check_note = "총중량 40t 초과 가능성 검토 필요" if total_weight_t > 40.0 else "총중량 기준 내"
        feasible = width_ok and length_ok and payload_ok
        candidates.append({
            "트레일러": trailer.name,
            "적재면 길이(m)": trailer.deck_length_m,
            "적재면 폭(m)": trailer.deck_width_m,
            "적재면 높이(m)": trailer.deck_height_m,
            "최대적재량(t)": trailer.payload_t,
            "운송 높이(m)": round(transport_height, 2),
            "총중량 추정(t)": round(total_weight_t, 2),
            "폭 적합": width_ok,
            "길이 적합": length_ok,
            "중량 적합": payload_ok,
            "특수허가 필요": permit_needed,
            "판정": "가능" if feasible else "불가",
            "비고": axle_check_note,
        })
    return candidates


def filter_feasible_trailers(candidates: List[Dict[str, object]]) -> List[Dict[str, object]]:
    return [c for c in candidates if c["판정"] == "가능"]


def evaluate_route_permit(
    module_width_m: float,
    transport_height_m: float,
    total_weight_t: float,
    min_road_width_m: float,
    turn_condition: str,
    obstacle_level: str,
    bridge_tunnel_height_limit_m: float,
    managed_road_42m: bool,
    illegal_parking_constant: str,
) -> Dict[str, object]:
    legal_height_limit = 4.2 if managed_road_42m else 4.0
    permit_needed = False
    route_ok = True
    reasons: List[str] = []

    if module_width_m > 2.5:
        permit_needed = True
        reasons.append("폭 2.5m 초과")
    if transport_height_m > legal_height_limit:
        permit_needed = True
        reasons.append(f"운송 높이 {legal_height_limit:.1f}m 초과")
    if total_weight_t > 40.0:
        permit_needed = True
        reasons.append("총중량 40t 초과 가능성")

    if min_road_width_m < 4.0:
        route_ok = False
        reasons.append("최소 도로폭 4m 미만")
    elif min_road_width_m < 6.0:
        reasons.append("최소 도로폭 4~6m")

    if turn_condition == "협소 코너 다수/U턴 필요":
        route_ok = False
        reasons.append("협소 코너/U턴 필요")
    elif turn_condition == "코너 2개 이상":
        reasons.append("코너 2개 이상")

    if obstacle_level == "전면부 장애 심함":
        route_ok = False
        reasons.append("전면부 장애 심함")
    elif obstacle_level == "전선/가로수 일부":
        reasons.append("전선/가로수 일부")

    if bridge_tunnel_height_limit_m > 0 and transport_height_m > bridge_tunnel_height_limit_m:
        route_ok = False
        reasons.append("교량/터널 높이 제한 초과")

    if illegal_parking_constant == "높음":
        reasons.append("상시 불법주정차 높음")
    elif illegal_parking_constant == "중간":
        reasons.append("상시 불법주정차 중간")

    if not reasons:
        reasons.append("주요 경로 제약 없음")

    if not route_ok:
        route_status = "불가"
    elif permit_needed:
        route_status = "조건부 가능"
    else:
        route_status = "가능"

    return {
        "route_ok": route_ok,
        "permit_needed": permit_needed,
        "legal_height_limit_m": legal_height_limit,
        "route_status": route_status,
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
    reasons: List[str] = []

    if module_width_m <= 2.5:
        s = 0
    elif module_width_m <= 3.0:
        s = 1
    elif module_width_m <= 3.5:
        s = 2
    else:
        s = 3
    score += s
    reasons.append(f"폭 리스크 {s}점")

    if transport_height_m <= 4.0:
        s = 0
    elif transport_height_m <= 4.5:
        s = 2
    else:
        s = 3
    score += s
    reasons.append(f"운송 높이 리스크 {s}점")

    if module_weight_t <= 15:
        s = 0
    elif module_weight_t <= 25:
        s = 1
    elif module_weight_t <= 35:
        s = 2
    else:
        s = 3
    score += s
    reasons.append(f"중량 리스크 {s}점")

    if module_length_m <= 10:
        s = 0
    elif module_length_m <= 14:
        s = 1
    elif module_length_m <= 18:
        s = 2
    else:
        s = 3
    score += s
    reasons.append(f"길이 리스크 {s}점")

    mapping_turn = {"직진 위주": 0, "코너 1개": 1, "코너 2개 이상": 2, "협소 코너 다수/U턴 필요": 3}
    mapping_obs = {"없음": 0, "경미": 1, "전선/가로수 일부": 2, "전면부 장애 심함": 3}
    mapping_pave = {"양호": 0, "보통": 1, "경사/포장불량 일부": 2, "급경사/불량 심함": 3}
    mapping_form = {"corner-supported": 0, "open-ended": 1, "open-sided": 2, "대개구부/비정형": 3, "hybrid": 3}

    s = mapping_turn[turn_condition]
    score += s
    reasons.append(f"회전 리스크 {s}점")

    s = mapping_obs[obstacle_level]
    score += s
    reasons.append(f"장애물 리스크 {s}점")

    s = mapping_pave[pavement_level]
    score += s
    reasons.append(f"노면/경사 리스크 {s}점")

    s = mapping_form.get(module_form, 2)
    score += s
    reasons.append(f"모듈 형식 리스크 {s}점")

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
    form_score = {"corner-supported": 0, "open-ended": 1, "open-sided": 2, "대개구부/비정형": 3, "hybrid": 3}.get(module_form, 2)

    parts = {
        "모듈 길이": length_score,
        "모듈 중량": weight_score,
        "층수": floor_score,
        "작업반경": radius_score,
        "적치공간": staging_score,
        "JIT 설치": jit_score,
        "모듈 형식": form_score,
    }
    score = sum(parts.values())
    coeff_bonus = round((install_difficulty_coeff - 1.0) * 10)
    if coeff_bonus > 0:
        parts["설치 난이도 계수"] = coeff_bonus
        score += coeff_bonus

    reasons = [f"{k} {v}점" for k, v in parts.items()]
    return score, reasons


def recommend_structure(
    building_use: str,
    repeatability_score: int,
    open_plan_need: int,
    public_space_ratio: int,
    selected_module_name: str,
) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    if selected_module_name == "Small load-bearing wall module":
        return "내력벽형", ["소형 반복형 임대주택에 적합"]
    if selected_module_name in ["Corner-supported standard module", "Corner-supported stacked module", "Corridor-type combined module"]:
        return "Corner-supported", ["표준 적층형 주거에 적합"]
    if selected_module_name in ["Open-sided module", "Large-span institutional module"]:
        return "오픈사이드 / 라멘형", ["개방형 공간과 공용공간 요구가 큼"]
    if selected_module_name == "Open-ended module":
        return "오픈엔드", ["세대 연결성과 내부 연속 공간 확보에 적합"]
    if selected_module_name == "Hybrid / podium + modular upper floors":
        return "하부 RC + 상부 모듈러", ["중층 도심형 복합 대안"]

    if repeatability_score >= 4 and open_plan_need <= 2:
        reasons.append("반복형 평면과 경제성을 우선")
        return "내력벽형", reasons
    if public_space_ratio >= 4 or open_plan_need >= 4 or building_use in ["학교", "병원", "업무시설"]:
        reasons.append("개방형 공간/공용공간 요구가 큼")
        return "라멘형 또는 오픈사이드", reasons
    reasons.append("일반 적층형 주거에 무난")
    return "Corner-supported", reasons


def recommend_joint(
    floors: int,
    speed_priority: int,
    reversibility_need: int,
    structural_integrity_need: int,
    module_name: str,
) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    if module_name in MODULE_DB:
        reasons.append("선정 모듈 기본 권장 접합방식 반영")
        return MODULE_DB[module_name].recommended_joint, reasons
    if structural_integrity_need >= 4 or floors >= 10:
        reasons.append("구조적 일체성과 강성 확보가 우선")
        return "그라우트드 + 볼트 보조", reasons
    if speed_priority >= 4 or reversibility_need >= 4:
        reasons.append("시공 속도와 유지관리/해체 가능성 우선")
        return "볼트", reasons
    reasons.append("표준 볼트 접합만으로 부족한 상세 보강 필요")
    return "플레이트 + 볼트", reasons


def evaluate_cranes(
    needed_lifting_t: float,
    required_radius_m: float,
    required_hook_height_m: float,
    site_frontage_m: float,
    available_staging_m2: float,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for crane in CRANE_DB:
        allowable = interpolate_allowable_load(crane, required_radius_m)
        radius_ok = required_radius_m <= crane.max_radius_m
        hook_ok = required_hook_height_m <= crane.max_hook_height_m
        load_ok = allowable >= needed_lifting_t
        margin = allowable / needed_lifting_t if needed_lifting_t > 0 else 0.0

        operational_note = []
        if crane.crane_group == "트럭크레인" and site_frontage_m < 12:
            operational_note.append("전면부 부족 시 아웃트리거 전개 제약")
        if crane.crane_group == "크롤러크레인" and available_staging_m2 < 500:
            operational_note.append("작업장/야적장 부족")
        if crane.crane_group in ["타워크레인", "러핑크레인"]:
            operational_note.append("기초/설치해체 계획 필요")

        rows.append({
            "장비": crane.name,
            "장비군": crane.crane_group,
            "최대하중(t)": crane.max_capacity_t,
            "최대반경(m)": crane.max_radius_m,
            "끝단하중(t)": crane.tip_load_t,
            "최대Hook높이(m)": crane.max_hook_height_m,
            "해당반경 허용하중(t)": round(allowable, 2),
            "필요양중하중(t)": round(needed_lifting_t, 2),
            "여유율": round(margin, 2),
            "여유율판정": risk_level_from_margin(margin),
            "반경적합": radius_ok,
            "높이적합": hook_ok,
            "하중적합": load_ok,
            "최종판정": "가능" if (radius_ok and hook_ok and load_ok) else "불가",
            "비고": "; ".join(operational_note) if operational_note else "-",
            "월임대료": crane.monthly_rent_krw or 0,
            "설치해체비": crane.setup_cost_krw or 0,
            "시간당손료": crane.hourly_cost_krw or 0,
        })
    rows.sort(key=lambda x: (x["최종판정"] != "가능", x["여유율"] if x["여유율"] else 999, x["최대하중(t)"]))
    return rows


def recommend_crane_type(
    module_weight_t: float,
    floors: int,
    required_radius_m: float,
    road_side_short_term: bool,
    available_staging_m2: float,
    module_name: str,
) -> str:
    if module_name in MODULE_DB:
        return MODULE_DB[module_name].recommended_crane_group
    if road_side_short_term and module_weight_t <= 25 and floors <= 8:
        return "트럭크레인 우선 검토"
    if available_staging_m2 >= 500 and module_weight_t >= 25:
        return "크롤러크레인 우선 검토"
    if floors >= 10:
        return "타워크레인 또는 러핑크레인 우선 검토"
    if required_radius_m <= 25 and module_weight_t <= 20:
        return "트럭크레인 또는 중소형 타워크레인 검토"
    return "타워크레인 우선 검토"


def cost_model(
    gross_area_m2: float,
    rc_unit_cost_krw_per_m2: float,
    modular_factory_unit_cost_krw_per_m2: float,
    module_count: int,
    transport_cost_per_module_krw: float,
    installation_cost_per_module_krw: float,
    joint_cost_per_module_krw: float,
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
        transport_cost_per_module_krw + installation_cost_per_module_krw + joint_cost_per_module_krw + permit_cost_per_module_krw
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
    transport_feasible: bool,
    best_lifting_margin: float,
    transport_risk_score_value: int,
    installation_risk_score_value: int,
    modular_cost_total: float,
    rc_cost_total: float,
    road_width_m: float,
    repeatability_score: int,
    floors: int,
) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    if not transport_feasible:
        reasons.append("적합 트레일러 기준으로 운송 자체가 성립하지 않음")
        return "RC 우세", reasons
    if best_lifting_margin < 1.0:
        reasons.append("후보 크레인 기준 필요 양중하중을 만족하지 못함")
        return "RC 우세", reasons
    if transport_risk_score_value >= 26:
        reasons.append("운송 리스크가 매우 높음")
    if installation_risk_score_value >= 17:
        reasons.append("설치 리스크가 높음")

    if modular_cost_total < rc_cost_total:
        reasons.append("총비용 비교에서 모듈러가 RC보다 낮음")
        if road_width_m >= 6 and repeatability_score >= 4 and floors <= 12:
            reasons.append("도로폭·반복성·층수 조건이 모듈러에 우호적")
            return "모듈러 우세", reasons
        return "조건부 모듈러 우세", reasons

    cost_gap_ratio = (modular_cost_total - rc_cost_total) / max(rc_cost_total, 1.0)
    if cost_gap_ratio <= 0.05 and best_lifting_margin >= 1.1 and transport_risk_score_value <= 16:
        reasons.append("비용 차이가 작고 양중/운송 조건이 허용 범위")
        return "조건부 모듈러 우세", reasons

    reasons.append("총비용 또는 설치 리스크 측면에서 RC가 더 안정적")
    return "RC 우세", reasons


def score_module_candidate(
    module: ModuleType,
    building_use: str,
    floors: int,
    repeatability_score: int,
    public_space_ratio: int,
    open_plan_need: int,
    road_width_m: float,
    staging_area_m2: float,
) -> Tuple[float, List[str]]:
    score = 0.0
    reasons: List[str] = []

    repeat_fit = 5 - abs(module.repeatability_score - repeatability_score)
    public_fit = 5 - abs(module.public_space_score - public_space_ratio)
    open_fit = 5 - abs(module.open_plan_score - open_plan_need)
    score += repeat_fit * 3.0
    score += public_fit * 2.0
    score += open_fit * 2.0
    reasons.append(f"반복형 적합도 반영 {repeat_fit}/5")
    reasons.append(f"공용공간 적합도 반영 {public_fit}/5")
    reasons.append(f"개방형 요구 적합도 반영 {open_fit}/5")

    if module.floor_min <= floors <= module.floor_max:
        score += 10
        reasons.append("권장 층수 범위 적합")
    else:
        gap = min(abs(floors - module.floor_min), abs(floors - module.floor_max))
        penalty = min(8, gap)
        score -= penalty
        reasons.append(f"권장 층수 범위 이탈 -{penalty:.0f}")

    if road_width_m >= 6.0:
        score += 4
    elif road_width_m >= 4.0:
        score += 1
        if module.transport_difficulty_coeff > 1.3:
            score -= 3
            reasons.append("도로폭이 좁아 고난도 운송 모듈 불리")
    else:
        score -= 10
        reasons.append("도로폭 부족")

    if staging_area_m2 < 150 and module.install_difficulty_coeff >= 1.5:
        score -= 4
        reasons.append("적치공간 부족으로 설치 난이도 높은 모듈 불리")

    score -= (module.transport_difficulty_coeff - 1.0) * 8
    score -= (module.install_difficulty_coeff - 1.0) * 8

    if building_use in ["학교", "병원", "업무시설"] and module.public_space_score >= 4:
        score += 5
        reasons.append("용도 특성상 공용공간 적합도 가점")
    if building_use in ["공동주택", "기숙사"] and module.repeatability_score >= 4:
        score += 5
        reasons.append("용도 특성상 반복형 적합도 가점")
    if building_use == "복합용도" and module.name == "Hybrid / podium + modular upper floors":
        score += 7
        reasons.append("복합용도에 하이브리드형 가점")

    return round(score, 2), reasons


def auto_select_module(
    building_use: str,
    gross_area_m2: float,
    floors: int,
    repeatability_score: int,
    public_space_ratio: int,
    open_plan_need: int,
    road_width_m: float,
    staging_area_m2: float,
) -> Tuple[ModuleType, List[Dict[str, object]]]:
    scored = []
    for module in MODULE_DB.values():
        score, reasons = score_module_candidate(
            module=module,
            building_use=building_use,
            floors=floors,
            repeatability_score=repeatability_score,
            public_space_ratio=public_space_ratio,
            open_plan_need=open_plan_need,
            road_width_m=road_width_m,
            staging_area_m2=staging_area_m2,
        )
        module_count_est = estimate_module_count(gross_area_m2, module.length_m, module.width_m, module.base_efficiency_ratio)
        scored.append({
            "module": module,
            "score": score,
            "reasons": reasons,
            "estimated_count": module_count_est,
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[0]["module"], scored


st.markdown('<div class="main-title">STEP 1. 부지별 RC 대비 모듈러 공사비 비교 프로그램</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">현장 접근성, 운송, 양중, 적치, 접합, 공장제작률, 공기단축을 반영한 STEP 1 비교 프로그램입니다.</div>', unsafe_allow_html=True)

st.markdown('<div class="block-card">', unsafe_allow_html=True)
st.subheader("1) 기본 정보")
col_a, col_b = st.columns(2)
with col_a:
    project_name = st.text_input("사업명", placeholder="예: 수원시 ○○동 신축매입임대 사업")
    site_address = st.text_input("부지 도로명주소", placeholder="예: 경기도 수원시 영통구 ○○로 00")
with col_b:
    building_use = st.selectbox("건물 용도", ["공동주택", "기숙사", "학교", "병원", "업무시설", "복합용도"])
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="block-card">', unsafe_allow_html=True)
st.subheader("2) 부지 위치 확인")
if site_address.strip():
    if render_simple_map(site_address.strip()):
        st.caption("입력 위치 확인")
else:
    st.info("도로명주소를 입력하면 지도가 표시됩니다.")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="block-card">', unsafe_allow_html=True)
st.subheader("3) 부지·동선·적치 조건")
col1, col2, col3 = st.columns(3)
with col1:
    site_area_m2 = st.number_input("대지면적 (㎡)", min_value=0.0, value=500.0, step=10.0)
    site_frontage_m = st.number_input("전면도로 길이 / 정차 가능 길이 (m)", min_value=0.0, value=18.0, step=1.0)
    road_width_m = st.number_input("전면 도로폭 (m)", min_value=0.0, value=6.0, step=0.5)
    corner_site = st.radio("코너 부지 여부", ["아니오", "예"], horizontal=True)
with col2:
    turn_condition = st.selectbox("회전 조건", ["직진 위주", "코너 1개", "코너 2개 이상", "협소 코너 다수/U턴 필요"])
    obstacle_level = st.selectbox("장애물 수준", ["없음", "경미", "전선/가로수 일부", "전면부 장애 심함"])
    pavement_level = st.selectbox("노면/경사 수준", ["양호", "보통", "경사/포장불량 일부", "급경사/불량 심함"])
    illegal_parking_constant = st.radio("상시 불법주정차 영향", ["낮음", "중간", "높음"], horizontal=True)
with col3:
    staging_area_m2 = st.number_input("적치 가능 면적 (㎡)", min_value=0.0, value=120.0, step=10.0)
    trailer_stop_zone_m = st.number_input("트레일러 정차 가능 구간 (m)", min_value=0.0, value=15.0, step=1.0)
    crane_candidate_offset_m = st.number_input("크레인 설치 후보점의 건물 외곽 이격거리 (m)", min_value=0.0, value=6.0, step=1.0)
    bridge_tunnel_height_limit_m = st.number_input("경로상 교량/터널 높이 제한 (m, 없으면 0)", min_value=0.0, value=0.0, step=0.1)
    managed_road_42m = st.radio("관리도로 4.2m 적용 여부", ["아니오", "예"], horizontal=True)
    road_side_short_term = st.radio("도로변 단기 설치 중심 현장인가?", ["예", "아니오"], horizontal=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="block-card">', unsafe_allow_html=True)
st.subheader("4) 건물 조건")
col1, col2, col3 = st.columns(3)
with col1:
    gross_area_m2 = st.number_input("연면적 (㎡)", min_value=0.0, value=1500.0, step=10.0)
    floors = st.number_input("층수", min_value=1, max_value=80, value=5, step=1)
    building_length_m = st.number_input("건물 길이 (m)", min_value=1.0, value=30.0, step=1.0)
with col2:
    building_width_m = st.number_input("건물 폭 (m)", min_value=1.0, value=14.0, step=1.0)
    top_install_height_m = st.number_input("최고 설치 높이 (m)", min_value=1.0, value=18.0, step=1.0)
    obstacle_height_m = st.number_input("간섭 장애물 최고 높이 (m)", min_value=0.0, value=0.0, step=1.0)
with col3:
    repeatability_score = st.slider("반복형 평면 정도", 1, 5, 3)
    public_space_ratio = st.slider("공용공간 비중", 1, 5, 3)
    open_plan_need = st.slider("개방형 평면 요구", 1, 5, 3)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="block-card">', unsafe_allow_html=True)
st.subheader("5) 모듈 조건")
module_input_mode = st.radio("모듈 선정 방식", ["자동 추천", "DB 선택", "직접 입력"], horizontal=True)

recommended_module = None
module_ranking = []
if module_input_mode == "자동 추천":
    recommended_module, module_ranking = auto_select_module(
        building_use=building_use,
        gross_area_m2=gross_area_m2,
        floors=int(floors),
        repeatability_score=repeatability_score,
        public_space_ratio=public_space_ratio,
        open_plan_need=open_plan_need,
        road_width_m=road_width_m,
        staging_area_m2=staging_area_m2,
    )
    module_name = recommended_module.name
    selected_module = recommended_module
elif module_input_mode == "DB 선택":
    module_name = st.selectbox("모듈 타입", list(MODULE_DB.keys()))
    selected_module = MODULE_DB[module_name]
else:
    module_name = "사용자 정의 모듈"
    selected_module = None

if selected_module is not None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        module_length_m = st.number_input("모듈 길이 (m)", value=float(selected_module.length_m), step=0.1)
    with col2:
        module_width_m = st.number_input("모듈 폭 (m)", value=float(selected_module.width_m), step=0.1)
    with col3:
        module_height_m = st.number_input("모듈 높이 (m)", value=float(selected_module.height_m), step=0.1)
    with col4:
        module_weight_t = st.number_input("모듈 자중 (t)", value=float(selected_module.weight_t_default), step=0.1)
    module_form = selected_module.openness
    module_desc = selected_module.desc
else:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        module_length_m = st.number_input("모듈 길이 (m)", value=10.0, step=0.1)
    with col2:
        module_width_m = st.number_input("모듈 폭 (m)", value=3.2, step=0.1)
    with col3:
        module_height_m = st.number_input("모듈 높이 (m)", value=3.4, step=0.1)
    with col4:
        module_weight_t = st.number_input("모듈 자중 (t)", value=12.0, step=0.1)
    module_form = st.selectbox("모듈 형식", ["corner-supported", "open-ended", "open-sided", "대개구부/비정형", "hybrid"])
    module_desc = "사용자 정의"
    module_eff_default = 0.80

if selected_module is not None:
    module_eff_default = selected_module.base_efficiency_ratio

count_mode = st.radio("모듈 개수 입력 방식", ["자동 산정", "직접 입력"], horizontal=True)
col1, col2, col3, col4 = st.columns(4)
with col1:
    if count_mode == "자동 산정":
        module_efficiency_ratio = st.slider("모듈 면적 효율계수", min_value=0.50, max_value=0.95, value=float(module_eff_default), step=0.01)
        module_count = estimate_module_count(gross_area_m2, module_length_m, module_width_m, module_efficiency_ratio)
    else:
        module_efficiency_ratio = float(module_eff_default)
        module_count = st.number_input("총 모듈 개수", min_value=1, value=20, step=1)
with col2:
    if selected_module is not None:
        prefab_default = round((selected_module.prefab_rate_min + selected_module.prefab_rate_max) / 2, 2)
    else:
        prefab_default = 0.70
    prefab_rate = st.slider("공장 제작 비율", min_value=0.30, max_value=0.95, value=float(prefab_default), step=0.05)
with col3:
    rigging_weight_t = st.number_input("인양보조구/슬링 등 추가 하중 (t)", min_value=0.0, value=0.8, step=0.1)
with col4:
    safety_factor = st.number_input("안전계수", min_value=1.00, value=1.15, step=0.05)

if count_mode == "자동 산정":
    st.caption(f"자동 산정 모듈 개수: {module_count}개 | 모듈 바닥면적 {module_length_m * module_width_m:.2f}㎡ | 효율계수 {module_efficiency_ratio:.2f}")
else:
    st.caption(f"총 모듈 개수: {int(module_count)}개")
st.caption(module_desc)

if selected_module is not None:
    st.caption(f"권장 층수: {selected_module.recommended_floor_range} | 권장 접합: {selected_module.recommended_joint} | 대표 트레일러: {selected_module.representative_trailer}")
    st.caption(f"권장 크레인군: {selected_module.recommended_crane_group} | 공장 제작률: {selected_module.prefab_rate_text} | 설치 난이도 계수: {selected_module.install_difficulty_coeff:.2f} | 운송 난이도 계수: {selected_module.transport_difficulty_coeff:.2f}")
    st.caption(f"대개구부: {bool_ko(selected_module.large_opening)} | 반복형 적합도: {selected_module.repeatability_score}/5 | 공용공간 적합도: {selected_module.public_space_score}/5 | 개방형 적합도: {selected_module.open_plan_score}/5")

if module_input_mode == "자동 추천" and module_ranking:
    st.write("**자동 추천 상위 후보**")
    ranking_df = pd.DataFrame([{
        "순위": i + 1,
        "모듈 타입": item["module"].name,
        "적합도 점수": item["score"],
        "예상 모듈 개수": item["estimated_count"],
        "폭(m)": item["module"].width_m,
        "길이(m)": item["module"].length_m,
        "높이(m)": item["module"].height_m,
        "자중(t)": item["module"].weight_t_default,
    } for i, item in enumerate(module_ranking[:5])])
    st.dataframe(ranking_df, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="block-card">', unsafe_allow_html=True)
st.subheader("6) 공사비/공기 입력")
col1, col2, col3 = st.columns(3)
with col1:
    rc_unit_cost_krw_per_m2 = st.number_input("RC 기준 공사비 (원/㎡)", min_value=0.0, value=2400000.0, step=50000.0)
    modular_factory_unit_cost_krw_per_m2 = st.number_input("모듈러 공장 제작 기준 공사비 (원/㎡)", min_value=0.0, value=2550000.0, step=50000.0)
    modular_direct_premium_rate = st.slider("모듈러 직접공사비 할증률", 0.0, 0.30, 0.08, 0.01)
with col2:
    transport_cost_per_module_krw = st.number_input("모듈 1개당 운송비 (원)", min_value=0.0, value=1200000.0, step=100000.0)
    installation_cost_per_module_krw = st.number_input("모듈 1개당 설치비 (원)", min_value=0.0, value=800000.0, step=50000.0)
    joint_cost_per_module_krw = st.number_input("모듈 1개당 접합부 비용 (원)", min_value=0.0, value=450000.0, step=50000.0)
with col3:
    permit_cost_per_module_krw = st.number_input("모듈 1개당 특수운행/통제 비용 (원)", min_value=0.0, value=200000.0, step=50000.0)
    schedule_reduction_months = st.number_input("모듈러 공기 단축 예상 (개월)", min_value=0.0, value=2.5, step=0.5)
    monthly_financing_saving_krw = st.number_input("공기단축 1개월당 금융/간접비 절감액 (원)", min_value=0.0, value=18000000.0, step=1000000.0)

col4, col5, col6 = st.columns(3)
with col4:
    small_project_penalty_rate = st.slider("소규모 사업 규모의 경제 미달 가산율", 0.0, 0.30, 0.06, 0.01)
with col5:
    rc_equipment_cost_krw = st.number_input("RC 장비/타설/운반 추가비 (원)", min_value=0.0, value=45000000.0, step=1000000.0)
with col6:
    tower_usage_months = st.number_input("타워크레인 사용 개월수(필요 시)", min_value=0.0, value=4.0, step=0.5)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="block-card">', unsafe_allow_html=True)
st.subheader("7) 접합/운영 전략")
col1, col2, col3 = st.columns(3)
with col1:
    speed_priority = st.slider("시공속도 우선도", 1, 5, 4)
with col2:
    reversibility_need = st.slider("해체/유지관리 고려 수준", 1, 5, 3)
with col3:
    structural_integrity_need = st.slider("구조 일체성 요구 수준", 1, 5, 4)
jit_install = st.radio("JIT(Just-In-Time) 설치 필요 여부", ["예", "아니오"], horizontal=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="block-card">', unsafe_allow_html=True)
st.subheader("8) 분석 실행")
run_clicked = st.button("STEP 1 전체 분석 실행")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="block-card">', unsafe_allow_html=True)
st.subheader("참고 모듈 DB")
st.dataframe(module_db_dataframe(), use_container_width=True, height=320)
st.markdown('</div>', unsafe_allow_html=True)

if run_clicked:
    trailer_candidates = select_feasible_trailers(module_length_m, module_width_m, module_height_m, module_weight_t)
    feasible_trailers = filter_feasible_trailers(trailer_candidates)

    representative_transport_height = min([row["운송 높이(m)"] for row in trailer_candidates]) if trailer_candidates else module_height_m
    representative_total_weight_t = min([row["총중량 추정(t)"] for row in trailer_candidates]) if trailer_candidates else module_weight_t
    route_eval = evaluate_route_permit(
        module_width_m=module_width_m,
        transport_height_m=representative_transport_height,
        total_weight_t=representative_total_weight_t,
        min_road_width_m=road_width_m,
        turn_condition=turn_condition,
        obstacle_level=obstacle_level,
        bridge_tunnel_height_limit_m=bridge_tunnel_height_limit_m,
        managed_road_42m=(managed_road_42m == "예"),
        illegal_parking_constant=illegal_parking_constant,
    )

    transport_coeff = selected_module.transport_difficulty_coeff if selected_module is not None else 1.0
    install_coeff = selected_module.install_difficulty_coeff if selected_module is not None else 1.0

    transport_score, transport_reasons = transport_risk_score(
        module_width_m=module_width_m,
        transport_height_m=representative_transport_height,
        module_weight_t=module_weight_t,
        module_length_m=module_length_m,
        turn_condition=turn_condition,
        obstacle_level=obstacle_level,
        pavement_level=pavement_level,
        module_form=module_form,
        transport_difficulty_coeff=transport_coeff,
    )
    if illegal_parking_constant == "중간":
        transport_score += 1
        transport_reasons.append("상시 불법주정차 중간 영향 +1점")
    elif illegal_parking_constant == "높음":
        transport_score += 2
        transport_reasons.append("상시 불법주정차 높음 영향 +2점")

    needed_lifting_t = (module_weight_t + rigging_weight_t) * safety_factor
    required_radius_m = crane_candidate_offset_m + max(building_width_m, building_length_m) / 2.0
    required_hook_height_m = top_install_height_m + obstacle_height_m + 3.0

    crane_results = evaluate_cranes(
        needed_lifting_t=needed_lifting_t,
        required_radius_m=required_radius_m,
        required_hook_height_m=required_hook_height_m,
        site_frontage_m=site_frontage_m,
        available_staging_m2=staging_area_m2,
    )
    feasible_cranes = [row for row in crane_results if row["최종판정"] == "가능"]
    best_lifting_margin = max([row["여유율"] for row in feasible_cranes], default=0.0)

    install_score, install_reasons = installation_risk_score(
        module_length_m=module_length_m,
        module_weight_t=module_weight_t,
        floors=int(floors),
        required_radius_m=required_radius_m,
        staging_area_m2=staging_area_m2,
        jit_install=(jit_install == "예"),
        module_form=module_form,
        install_difficulty_coeff=install_coeff,
    )

    recommended_structure, structure_reasons = recommend_structure(
        building_use=building_use,
        repeatability_score=repeatability_score,
        open_plan_need=open_plan_need,
        public_space_ratio=public_space_ratio,
        selected_module_name=module_name,
    )
    recommended_joint, joint_reasons = recommend_joint(
        floors=int(floors),
        speed_priority=speed_priority,
        reversibility_need=reversibility_need,
        structural_integrity_need=structural_integrity_need,
        module_name=module_name,
    )

    preferred_crane_type = recommend_crane_type(
        module_weight_t=module_weight_t,
        floors=int(floors),
        required_radius_m=required_radius_m,
        road_side_short_term=(road_side_short_term == "예"),
        available_staging_m2=staging_area_m2,
        module_name=module_name,
    )

    crane_cost_krw = 0.0
    if feasible_cranes:
        top_crane = feasible_cranes[0]
        if top_crane["장비군"] == "타워크레인":
            crane_cost_krw = top_crane["월임대료"] * tower_usage_months + top_crane["설치해체비"]
        elif top_crane["시간당손료"] > 0:
            assumed_hours_per_module = 1.5
            crane_cost_krw = top_crane["시간당손료"] * assumed_hours_per_module * int(module_count)
    else:
        top_crane = None

    model_cost = cost_model(
        gross_area_m2=gross_area_m2,
        rc_unit_cost_krw_per_m2=rc_unit_cost_krw_per_m2,
        modular_factory_unit_cost_krw_per_m2=modular_factory_unit_cost_krw_per_m2,
        module_count=int(module_count),
        transport_cost_per_module_krw=transport_cost_per_module_krw,
        installation_cost_per_module_krw=installation_cost_per_module_krw,
        joint_cost_per_module_krw=joint_cost_per_module_krw,
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
        transport_feasible=(len(feasible_trailers) > 0 and route_eval["route_ok"]),
        best_lifting_margin=best_lifting_margin,
        transport_risk_score_value=transport_score,
        installation_risk_score_value=install_score,
        modular_cost_total=model_cost["modular_total"],
        rc_cost_total=model_cost["rc_total"],
        road_width_m=road_width_m,
        repeatability_score=repeatability_score,
        floors=int(floors),
    )

    st.subheader("분석 결과")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi"><div class="kpi-title">최종 판단</div><div class="kpi-value">{final_method}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi"><div class="kpi-title">경로 허가 판정</div><div class="kpi-value">{route_eval["route_status"]}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi"><div class="kpi-title">운송 리스크</div><div class="kpi-value">{transport_score}점 ({transport_risk_bucket(transport_score)})</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi"><div class="kpi-title">최고 양중 여유율</div><div class="kpi-value">{best_lifting_margin:.2f}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### A. 핵심 판정")
    st.write(f"- 선택 모듈: **{module_name}**")
    st.write(f"- 총 모듈 개수: **{int(module_count)}개**")
    st.write(f"- 권장 치수: **폭 {module_width_m:.2f}m / 길이 {module_length_m:.2f}m / 높이 {module_height_m:.2f}m / 자중 {module_weight_t:.2f}t**")
    st.write(f"- 추천 구조방식: **{recommended_structure}**")
    st.write(f"- 추천 접합방식: **{recommended_joint}**")
    st.write(f"- 추천 장비 전략: **{preferred_crane_type}**")
    if top_crane:
        st.write(f"- 1순위 가능 장비: **{top_crane['장비']}** (여유율 {top_crane['여유율']}, 판정 {top_crane['여유율판정']})")
    else:
        st.write("- 가능 장비 후보가 없어 양중 성립성이 부족합니다.")
    st.markdown('</div>', unsafe_allow_html=True)

    if module_input_mode == "자동 추천" and module_ranking:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown("### B. 자동 추천 모듈 선정 근거")
        for line in module_ranking[0]["reasons"]:
            st.write(f"- {line}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### C. 최종 판단 근거")
    for reason in final_reasons:
        st.write(f"- {reason}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### D. 비용 비교")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("RC 총비용", format_krw(model_cost["rc_total"]))
    with c2:
        st.metric("모듈러 총비용", format_krw(model_cost["modular_total"]))
    with c3:
        st.metric("모듈러 - RC", format_krw(model_cost["difference"]))
    st.write(f"- 조정 후 모듈러 단가: **{format_krw(model_cost['adjusted_modular_unit'])}/㎡**")
    st.write(f"- 모듈 운송·설치·접합·허가 합계: **{format_krw(model_cost['logistics_total'])}**")
    st.write(f"- 공기단축 절감 반영액: **{format_krw(model_cost['schedule_saving_total'])}**")
    st.write(f"- 반영된 공장 제작 비율: **{prefab_rate:.0%}**")
    st.write(f"- 소규모 사업 규모의 경제 미달 가산율: **{small_project_penalty_rate:.0%}**")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### E. 운송 경로 허가 판정")
    st.write(f"- 경로 판정: **{route_eval['route_status']}**")
    st.write(f"- 특수허가 필요 여부: **{bool_ko(route_eval['permit_needed'])}**")
    st.write(f"- 적용 높이 기준: **{route_eval['legal_height_limit_m']:.1f}m**")
    for item in route_eval["reasons"]:
        st.write(f"- {item}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### F. 트레일러 검토")
    st.dataframe(pd.DataFrame(trailer_candidates), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### G. 양중 검토")
    st.write(f"- 필요 양중하중 = (모듈 자중 {module_weight_t:.2f}t + 인양보조구 {rigging_weight_t:.2f}t) × 안전계수 {safety_factor:.2f}")
    st.write(f"- 계산 결과 필요 양중하중: **{needed_lifting_t:.2f}t**")
    st.write(f"- 필요 작업반경: **{required_radius_m:.2f}m**")
    st.write(f"- 필요 Hook 높이: **{required_hook_height_m:.2f}m**")
    st.dataframe(pd.DataFrame(crane_results), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### H. 구조/접합 추천 근거")
    st.write("**구조방식 추천 근거**")
    for reason in structure_reasons:
        st.write(f"- {reason}")
    st.write("**접합방식 추천 근거**")
    for reason in joint_reasons:
        st.write(f"- {reason}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### I. 운송 리스크 세부")
    for reason in transport_reasons:
        st.write(f"- {reason}")
    st.write(f"- 종합 판정: **{transport_risk_bucket(transport_score)}**")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### J. 설치 리스크 세부")
    for reason in install_reasons:
        st.write(f"- {reason}")
    st.write(f"- 종합 판정: **{transport_risk_bucket(install_score)}**")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### K. RC 장비비 참고")
    st.write(f"- 펌프카 시간당 손료 예시: {', '.join([f'{k} {format_krw(v)}' for k, v in PUMP_TRUCK_COSTS.items()])}")
    st.write(f"- 콘크리트 믹서트럭 6.0㎥ 시간당 손료: **{format_krw(MIXER_TRUCK_HOURLY)}**")
    st.write(f"- 레미콘 시장 참고값: **{format_krw(READYMIX_PRICE_PER_M3)}/㎥**")
    st.markdown('</div>', unsafe_allow_html=True)

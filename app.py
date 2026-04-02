from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim


# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    page_title="STEP 1 - 부지별 RC 대비 모듈러 공사비 비교 프로그램",
    page_icon="🏗️",
    layout="wide",
)


# =========================================================
# 스타일
# =========================================================
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
.small-label {
    font-size: 14px;
    color: #666;
    margin-bottom: 0.2rem;
}
.big-value {
    font-size: 26px;
    font-weight: 800;
    word-break: break-word;
}
.caption-text {
    font-size: 14px;
    color: #666;
}
.section-note {
    background: #fff7e6;
    border: 1px solid #ffe3a3;
    border-radius: 12px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.8rem;
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


# =========================================================
# 데이터 정의
# =========================================================
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
        desc="소형 임대주택, 반복형 원룸/소형 세대, 운송/설치 리스크 낮음",
    ),
    "Corner-supported standard module": ModuleType(
        name="Corner-supported standard module",
        structure="Corner-supported",
        width_m=3.2,
        length_m=10.0,
        height_m=3.4,
        weight_t_min=10.0,
        weight_t_max=14.0,
        openness="corner-supported",
        desc="일반 주거, 적층형 표준 모듈러, 범용형",
    ),
    "Open-sided module": ModuleType(
        name="Open-sided module",
        structure="오픈사이드",
        width_m=3.5,
        length_m=12.0,
        height_m=3.5,
        weight_t_min=16.0,
        weight_t_max=22.0,
        openness="open-sided",
        desc="학교, 병원, 공용부, 거실 확장형, 구조/운송 민감도 증가",
    ),
    "Open-ended module": ModuleType(
        name="Open-ended module",
        structure="오픈엔드",
        width_m=3.5,
        length_m=12.0,
        height_m=3.5,
        weight_t_min=14.0,
        weight_t_max=18.0,
        openness="open-ended",
        desc="선형 연결형 세대, 내부 연속 공간 확보",
    ),
    "Hybrid / podium + modular upper floors": ModuleType(
        name="Hybrid / podium + modular upper floors",
        structure="하부 RC + 상부 모듈러",
        width_m=3.35,
        length_m=19.0,
        height_m=4.5,
        weight_t_min=40.0,
        weight_t_max=40.0,
        openness="hybrid",
        desc="하부 RC/철골 + 상부 모듈러, 도심형 중층 프로젝트 현실 대안",
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
    CraneSpec(
        name="Truck Crane 25t (XCMG QY25K5-I 수준)",
        crane_group="트럭크레인",
        max_capacity_t=25.0,
        max_radius_m=30.0,
        tip_load_t=2.5,
        max_hook_height_m=45.0,
        setup_type="단기/이동식",
        hourly_cost_krw=59751,
        footprint_desc="아웃트리거 전개 공간 필요",
    ),
    CraneSpec(
        name="Truck Crane 40t (Liebherr LTM 1040 수준)",
        crane_group="트럭크레인",
        max_capacity_t=40.0,
        max_radius_m=39.0,
        tip_load_t=4.0,
        max_hook_height_m=44.0,
        setup_type="단기/이동식",
        hourly_cost_krw=68913,
        footprint_desc="아웃트리거 전개 공간 필요",
    ),
    CraneSpec(
        name="Tower Crane 8t",
        crane_group="타워크레인",
        max_capacity_t=8.0,
        max_radius_m=60.0,
        tip_load_t=1.5,
        max_hook_height_m=60.0,
        setup_type="고정식",
        monthly_rent_krw=14458982,
        setup_cost_krw=27752267,
        footprint_desc="기초 필요",
    ),
    CraneSpec(
        name="Tower Crane 10t",
        crane_group="타워크레인",
        max_capacity_t=10.0,
        max_radius_m=65.0,
        tip_load_t=2.0,
        max_hook_height_m=70.0,
        setup_type="고정식",
        monthly_rent_krw=15744463,
        setup_cost_krw=27752267,
        footprint_desc="기초 필요",
    ),
    CraneSpec(
        name="Tower Crane 12t",
        crane_group="타워크레인",
        max_capacity_t=12.0,
        max_radius_m=70.0,
        tip_load_t=2.4,
        max_hook_height_m=80.0,
        setup_type="고정식",
        monthly_rent_krw=16885655,
        setup_cost_krw=27752267,
        footprint_desc="기초 필요",
    ),
    CraneSpec(
        name="Liebherr 340 EC-B 16",
        crane_group="타워크레인",
        max_capacity_t=16.0,
        max_radius_m=78.0,
        tip_load_t=2.1,
        max_hook_height_m=84.7,
        setup_type="탑슬루잉",
        footprint_desc="기초 필요",
    ),
    CraneSpec(
        name="Potain MCT 565 M20",
        crane_group="타워크레인",
        max_capacity_t=20.0,
        max_radius_m=80.0,
        tip_load_t=4.0,
        max_hook_height_m=84.2,
        setup_type="탑슬루잉",
        footprint_desc="기초 필요",
    ),
    CraneSpec(
        name="Crawler Crane 100t (SANY SCC1000A 수준)",
        crane_group="크롤러크레인",
        max_capacity_t=100.0,
        max_radius_m=52.0,
        tip_load_t=8.0,
        max_hook_height_m=64.0,
        setup_type="대형/야적장형",
        hourly_cost_krw=115612,
        footprint_desc="넓은 작업장과 지반 확보 필요",
    ),
    CraneSpec(
        name="Crawler Crane 120t (KOBELCO CKE1200 수준)",
        crane_group="크롤러크레인",
        max_capacity_t=120.0,
        max_radius_m=64.0,
        tip_load_t=11.0,
        max_hook_height_m=73.2,
        setup_type="대형/야적장형",
        footprint_desc="넓은 작업장과 지반 확보 필요",
    ),
    CraneSpec(
        name="Crawler Crane 300t (Liebherr LR 1300.1 SX 수준)",
        crane_group="크롤러크레인",
        max_capacity_t=300.0,
        max_radius_m=143.0,
        tip_load_t=18.0,
        max_hook_height_m=169.0,
        setup_type="초대형",
        hourly_cost_krw=502517,
        footprint_desc="매우 넓은 작업장과 고강도 지반 필요",
    ),
    CraneSpec(
        name="Luffing Crane 12t (Liebherr 280 EC-H 수준)",
        crane_group="러핑크레인",
        max_capacity_t=12.0,
        max_radius_m=60.0,
        tip_load_t=2.6,
        max_hook_height_m=200.0,
        setup_type="도심 고층형",
        footprint_desc="좁은 회전공간에 상대적으로 유리",
    ),
    CraneSpec(
        name="Luffing Crane 24t (Potain MR 418 수준)",
        crane_group="러핑크레인",
        max_capacity_t=24.0,
        max_radius_m=60.0,
        tip_load_t=4.0,
        max_hook_height_m=210.0,
        setup_type="도심 고층형",
        footprint_desc="좁은 회전공간에 상대적으로 유리",
    ),
    CraneSpec(
        name="Luffing Crane 64t (Favelle Favco M2480D 수준)",
        crane_group="러핑크레인",
        max_capacity_t=64.0,
        max_radius_m=70.0,
        tip_load_t=10.0,
        max_hook_height_m=300.0,
        setup_type="도심 초고층형",
        footprint_desc="초고층 및 협소 회전조건 대응",
    ),
]

PUMP_TRUCK_COSTS = {
    "21m": 51698,
    "28m": 61567,
    "32m": 72600,
    "36m": 90024,
    "41m": 93192,
    "43m": 118140,
    "47m": 129579,
    "52m": 137192,
}

MIXER_TRUCK_HOURLY = 25948
READYMIX_PRICE_PER_M3 = 95500


# =========================================================
# 유틸리티
# =========================================================
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
    map_df = pd.DataFrame({"lat": [lat], "lon": [lon]})
    st.map(map_df)
    st.caption(f"위도: {lat:.6f} / 경도: {lon:.6f}")
    return True



def format_krw(value: float) -> str:
    return f"{int(round(value)):,}원"



def bool_ko(flag: bool) -> str:
    return "예" if flag else "아니오"



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
    # 최소반경 데이터가 없으므로 5m에서 max_capacity, max_radius에서 tip_load로 선형 가정
    r0 = 5.0
    if radius <= r0:
        return crane.max_capacity_t
    slope = (crane.tip_load_t - crane.max_capacity_t) / max(crane.max_radius_m - r0, 1.0)
    allowable = crane.max_capacity_t + slope * (radius - r0)
    return max(0.0, allowable)



def transport_risk_score(
    module_width_m: float,
    transport_height_m: float,
    module_weight_t: float,
    module_length_m: float,
    turn_condition: str,
    obstacle_level: str,
    pavement_level: str,
    module_form: str,
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

    mapping_turn = {
        "직진 위주": 0,
        "코너 1개": 1,
        "코너 2개 이상": 2,
        "협소 코너 다수/U턴 필요": 3,
    }
    s = mapping_turn[turn_condition]
    score += s
    reasons.append(f"회전 리스크 {s}점")

    mapping_obs = {
        "없음": 0,
        "경미": 1,
        "전선/가로수 일부": 2,
        "전면부 장애 심함": 3,
    }
    s = mapping_obs[obstacle_level]
    score += s
    reasons.append(f"장애물 리스크 {s}점")

    mapping_pave = {
        "양호": 0,
        "보통": 1,
        "경사/포장불량 일부": 2,
        "급경사/불량 심함": 3,
    }
    s = mapping_pave[pavement_level]
    score += s
    reasons.append(f"노면/경사 리스크 {s}점")

    mapping_form = {
        "corner-supported": 0,
        "open-ended": 1,
        "open-sided": 2,
        "대개구부/비정형": 3,
        "hybrid": 3,
    }
    s = mapping_form.get(module_form, 2)
    score += s
    reasons.append(f"모듈 형식 리스크 {s}점")

    return score, reasons



def installation_risk_score(
    module_length_m: float,
    module_weight_t: float,
    floors: int,
    required_radius_m: float,
    staging_area_m2: float,
    jit_install: bool,
    module_form: str,
) -> Tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []

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
    if selected_module_name == "Corner-supported standard module":
        return "Corner-supported", ["표준 적층형 주거에 적합"]
    if selected_module_name == "Open-sided module":
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
) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    if structural_integrity_need >= 4 or floors >= 10:
        reasons.append("구조적 일체성과 강성 확보가 우선")
        return "그라우트드 + 볼트 보조", reasons
    if speed_priority >= 4 or reversibility_need >= 4:
        reasons.append("시공 속도와 유지관리/해체 가능성 우선")
        return "볼트", reasons
    reasons.append("표준 볼트 접합만으로 부족한 상세 보강 필요")
    return "플레이트 + 볼트", reasons



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
        candidates.append(
            {
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
            }
        )
    return candidates



def filter_feasible_trailers(candidates: List[Dict[str, object]]) -> List[Dict[str, object]]:
    return [c for c in candidates if c["판정"] == "가능"]



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
        if crane.crane_group == "트럭크레인":
            if site_frontage_m < 12:
                operational_note.append("전면부 부족 시 아웃트리거 전개 제약")
        if crane.crane_group == "크롤러크레인":
            if available_staging_m2 < 500:
                operational_note.append("작업장/야적장 부족")
        if crane.crane_group in ["타워크레인", "러핑크레인"]:
            operational_note.append("기초/설치해체 계획 필요")

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
                "여유율판정": risk_level_from_margin(margin),
                "반경적합": radius_ok,
                "높이적합": hook_ok,
                "하중적합": load_ok,
                "최종판정": "가능" if (radius_ok and hook_ok and load_ok) else "불가",
                "비고": "; ".join(operational_note) if operational_note else "-",
                "월임대료": crane.monthly_rent_krw or 0,
                "설치해체비": crane.setup_cost_krw or 0,
                "시간당손료": crane.hourly_cost_krw or 0,
            }
        )
    rows.sort(key=lambda x: (x["최종판정"] != "가능", x["여유율"] if x["여유율"] else 999, x["최대하중(t)"]))
    return rows



def recommend_crane_type(
    module_weight_t: float,
    floors: int,
    required_radius_m: float,
    road_side_short_term: bool,
    available_staging_m2: float,
) -> str:
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

    prefab_discount = (prefab_rate - 0.60) * 0.10  # 60% 기준, 10% 범위 보정
    adjusted_modular_unit = modular_factory_unit_cost_krw_per_m2 * (1.0 - prefab_discount)
    adjusted_modular_unit *= (1.0 + modular_direct_premium_rate)
    adjusted_modular_unit *= (1.0 + small_project_penalty_rate)

    logistics_total = module_count * (
        transport_cost_per_module_krw
        + installation_cost_per_module_krw
        + joint_cost_per_module_krw
        + permit_cost_per_module_krw
    )
    schedule_saving_total = schedule_reduction_months * monthly_financing_saving_krw

    modular_total = (
        gross_area_m2 * adjusted_modular_unit
        + logistics_total
        + crane_cost_krw
        - schedule_saving_total
    )

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


# =========================================================
# 헤더
# =========================================================
st.markdown('<div class="main-title">STEP 1. 부지별 RC 대비 모듈러 공사비 비교 프로그램</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">현장 접근성, 운송, 양중, 적치, 접합, 공장제작률, 공기단축을 반영한 STEP 1 비교 프로그램입니다.</div>',
    unsafe_allow_html=True,
)



# =========================================================
# 기본 정보
# =========================================================
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


# =========================================================
# 입력 패널
# =========================================================
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
module_mode = st.radio("모듈 입력 방식", ["DB 선택", "직접 입력"], horizontal=True)

if module_mode == "DB 선택":
    module_name = st.selectbox("모듈 타입", list(MODULE_DB.keys()))
    selected_module = MODULE_DB[module_name]
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
    module_name = "사용자 정의 모듈"
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

col1, col2, col3, col4 = st.columns(4)
with col1:
    module_count = st.number_input("총 모듈 개수", min_value=1, value=20, step=1)
with col2:
    prefab_rate = st.slider("공장 제작 비율", min_value=0.30, max_value=0.95, value=0.70, step=0.05)
with col3:
    rigging_weight_t = st.number_input("인양보조구/슬링 등 추가 하중 (t)", min_value=0.0, value=0.8, step=0.1)
with col4:
    safety_factor = st.number_input("안전계수", min_value=1.00, value=1.15, step=0.05)

st.caption(module_desc)
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


# =========================================================
# 분석 실행
# =========================================================
st.markdown('<div class="block-card">', unsafe_allow_html=True)
st.subheader("8) 분석 실행")
run_clicked = st.button("STEP 1 전체 분석 실행")
st.markdown('</div>', unsafe_allow_html=True)


if run_clicked:
    # 1. 트레일러 검토
    trailer_candidates = select_feasible_trailers(module_length_m, module_width_m, module_height_m, module_weight_t)
    feasible_trailers = filter_feasible_trailers(trailer_candidates)

    # 2. 운송 리스크
    representative_transport_height = min([row["운송 높이(m)"] for row in trailer_candidates]) if trailer_candidates else module_height_m
    transport_score, transport_reasons = transport_risk_score(
        module_width_m=module_width_m,
        transport_height_m=representative_transport_height,
        module_weight_t=module_weight_t,
        module_length_m=module_length_m,
        turn_condition=turn_condition,
        obstacle_level=obstacle_level,
        pavement_level=pavement_level,
        module_form=module_form,
    )
    if illegal_parking_constant == "중간":
        transport_score += 1
        transport_reasons.append("상시 불법주정차 중간 영향 +1점")
    elif illegal_parking_constant == "높음":
        transport_score += 2
        transport_reasons.append("상시 불법주정차 높음 영향 +2점")

    # 3. 양중 산정
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

    # 4. 설치 리스크
    install_score, install_reasons = installation_risk_score(
        module_length_m=module_length_m,
        module_weight_t=module_weight_t,
        floors=int(floors),
        required_radius_m=required_radius_m,
        staging_area_m2=staging_area_m2,
        jit_install=(jit_install == "예"),
        module_form=module_form,
    )

    # 5. 구조/접합 추천
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
    )

    # 6. 크레인 추천 및 비용 산정
    preferred_crane_type = recommend_crane_type(
        module_weight_t=module_weight_t,
        floors=int(floors),
        required_radius_m=required_radius_m,
        road_side_short_term=(road_side_short_term == "예"),
        available_staging_m2=staging_area_m2,
    )

    crane_cost_krw = 0.0
    if feasible_cranes:
        top_crane = feasible_cranes[0]
        if top_crane["장비군"] == "타워크레인":
            crane_cost_krw = top_crane["월임대료"] * tower_usage_months + top_crane["설치해체비"]
        elif top_crane["시간당손료"] > 0:
            assumed_hours_per_module = 1.5
            crane_cost_krw = top_crane["시간당손료"] * assumed_hours_per_module * module_count
    else:
        top_crane = None

    # 7. 비용 비교
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
        transport_feasible=len(feasible_trailers) > 0,
        best_lifting_margin=best_lifting_margin,
        transport_risk_score_value=transport_score,
        installation_risk_score_value=install_score,
        modular_cost_total=model_cost["modular_total"],
        rc_cost_total=model_cost["rc_total"],
        road_width_m=road_width_m,
        repeatability_score=repeatability_score,
        floors=int(floors),
    )

    # =====================================================
    # 결과 출력
    # =====================================================
    st.subheader("분석 결과")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown('<div class="kpi"><div class="kpi-title">최종 판단</div><div class="kpi-value">' + final_method + '</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi"><div class="kpi-title">운송 리스크</div><div class="kpi-value">' + f'{transport_score}점 ({transport_risk_bucket(transport_score)})' + '</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="kpi"><div class="kpi-title">설치 리스크</div><div class="kpi-value">' + f'{install_score}점 ({transport_risk_bucket(install_score)})' + '</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown('<div class="kpi"><div class="kpi-title">최고 양중 여유율</div><div class="kpi-value">' + (f'{best_lifting_margin:.2f}' if best_lifting_margin else '0.00') + '</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### A. 핵심 판정")
    st.write(f"- 선택 모듈: **{module_name}**")
    st.write(f"- 추천 구조방식: **{recommended_structure}**")
    st.write(f"- 추천 접합방식: **{recommended_joint}**")
    st.write(f"- 추천 장비 전략: **{preferred_crane_type}**")
    if top_crane:
        st.write(f"- 1순위 가능 장비: **{top_crane['장비']}** (여유율 {top_crane['여유율']}, 판정 {top_crane['여유율판정']})")
    else:
        st.write("- 가능 장비 후보가 없어 양중 성립성이 부족합니다.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### B. 최종 판단 근거")
    for reason in final_reasons:
        st.write(f"- {reason}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### C. 비용 비교")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("RC 총비용", format_krw(model_cost["rc_total"]))
    with c2:
        st.metric("모듈러 총비용", format_krw(model_cost["modular_total"]))
    with c3:
        diff_label = "모듈러 - RC"
        st.metric(diff_label, format_krw(model_cost["difference"]))

    st.write(f"- 조정 후 모듈러 단가: **{format_krw(model_cost['adjusted_modular_unit'])}/㎡**")
    st.write(f"- 모듈 운송·설치·접합·허가 합계: **{format_krw(model_cost['logistics_total'])}**")
    st.write(f"- 공기단축 절감 반영액: **{format_krw(model_cost['schedule_saving_total'])}**")
    st.write(f"- 반영된 공장 제작 비율: **{prefab_rate:.0%}**")
    st.write(f"- 소규모 사업 규모의 경제 미달 가산율: **{small_project_penalty_rate:.0%}**")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### D. 트레일러 검토")
    trailer_df = pd.DataFrame(trailer_candidates)
    st.dataframe(trailer_df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### E. 양중 검토")
    st.write(f"- 필요 양중하중 = (모듈 자중 {module_weight_t:.2f}t + 인양보조구 {rigging_weight_t:.2f}t) × 안전계수 {safety_factor:.2f}")
    st.write(f"- 계산 결과 필요 양중하중: **{needed_lifting_t:.2f}t**")
    st.write(f"- 필요 작업반경: **{required_radius_m:.2f}m**")
    st.write(f"- 필요 Hook 높이: **{required_hook_height_m:.2f}m**")
    crane_df = pd.DataFrame(crane_results)
    st.dataframe(crane_df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### F. 구조/접합 추천 근거")
    st.write("**구조방식 추천 근거**")
    for reason in structure_reasons:
        st.write(f"- {reason}")
    st.write("**접합방식 추천 근거**")
    for reason in joint_reasons:
        st.write(f"- {reason}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### G. 운송 리스크 세부")
    for reason in transport_reasons:
        st.write(f"- {reason}")
    st.write(f"- 종합 판정: **{transport_risk_bucket(transport_score)}**")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### H. 설치 리스크 세부")
    for reason in install_reasons:
        st.write(f"- {reason}")
    st.write(f"- 종합 판정: **{transport_risk_bucket(install_score)}**")
    st.markdown('</div>', unsafe_allow_html=True)


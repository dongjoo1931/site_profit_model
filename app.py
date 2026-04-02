
import math
from dataclasses import dataclass
from typing import Dict, Optional
import streamlit as st

st.set_page_config(page_title="STEP1 RC vs Modular Cost", layout="wide")

# -----------------------------
# 데이터 구조
# -----------------------------
@dataclass
class ModuleType:
    name: str
    width_m: float
    length_m: float
    height_m: float
    weight_t: float

@dataclass
class CraneSpec:
    name: str
    max_capacity_t: float
    max_radius_m: float
    tip_load_t: float

# -----------------------------
# 기본 DB
# -----------------------------
MODULE_DB: Dict[str, ModuleType] = {
    "Small module": ModuleType("Small module",3.0,8.0,3.2,9),
    "Standard module": ModuleType("Standard module",3.2,10.0,3.4,12),
    "Open module": ModuleType("Open module",3.5,12.0,3.5,19),
}

CRANE_DB = [
    CraneSpec("Truck Crane",25,30,5),
    CraneSpec("Crawler Crane",80,40,10),
    CraneSpec("Tower Crane",12,55,3),
]

# -----------------------------
# 양중 계산
# -----------------------------
def lifting_check(weight, radius, crane):
    required_load = weight * 1.15
    if radius > crane.max_radius_m:
        return False,0
    capacity = crane.tip_load_t
    margin = capacity / required_load
    return capacity >= required_load, margin

# -----------------------------
# 비용 계산
# -----------------------------
def modular_cost(factory_rate, transport_cost, lifting_cost, install_cost, joint_cost):
    return factory_rate + transport_cost + lifting_cost + install_cost + joint_cost

def rc_cost(base_cost, equipment_cost):
    return base_cost + equipment_cost

# -----------------------------
# UI
# -----------------------------
st.title("STEP 1 : RC vs Modular 공사비 비교")

module_name = st.selectbox("모듈 유형", list(MODULE_DB.keys()))
module = MODULE_DB[module_name]

radius = st.number_input("크레인 작업 반경 (m)",10.0,100.0,25.0)

st.subheader("모듈러 비용")
factory_rate = st.number_input("공장 제작비",0.0,1e9,100000000.0)
transport_cost = st.number_input("운송비",0.0,1e9,20000000.0)
lifting_cost = st.number_input("양중비",0.0,1e9,15000000.0)
install_cost = st.number_input("설치비",0.0,1e9,10000000.0)
joint_cost = st.number_input("접합부 비용",0.0,1e9,5000000.0)

st.subheader("RC 비용")
rc_base = st.number_input("RC 기본 공사비",0.0,1e9,130000000.0)
rc_equipment = st.number_input("RC 장비비",0.0,1e9,20000000.0)

if st.button("분석 실행"):

    st.subheader("양중 가능 장비")
    for crane in CRANE_DB:
        ok, margin = lifting_check(module.weight_t, radius, crane)
        if ok:
            st.write(f"{crane.name} : 가능 (여유율 {round(margin,2)})")
        else:
            st.write(f"{crane.name} : 불가")

    mod_cost = modular_cost(factory_rate,transport_cost,lifting_cost,install_cost,joint_cost)
    rc_total = rc_cost(rc_base,rc_equipment)

    st.subheader("공사비 비교")
    st.write("모듈러 공사비 :", mod_cost)
    st.write("RC 공사비 :", rc_total)

    if mod_cost < rc_total:
        st.success("모듈러 공법이 경제적")
    else:
        st.info("RC 공법이 경제적")

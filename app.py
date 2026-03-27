import json
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(
    page_title="STEP 1 - 부지 맞춤형 공법 선택 프로그램",
    page_icon="🏗️",
    layout="wide"
)

# 카카오 JavaScript 키
KAKAO_JS_KEY = "60f1615487b2e8ea7a600d8931158a1d"

# -----------------------------
# 커스텀 CSS
# -----------------------------
st.markdown("""
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
.map-caption {
    font-size: 14px;
    color: #666;
    margin-top: 0.5rem;
}
.stButton > button {
    width: 100%;
    border-radius: 12px;
    height: 3.2rem;
    font-size: 18px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 카카오맵 HTML 렌더 함수
# -----------------------------
def render_kakao_map(address: str, height: int = 430):
    safe_address = json.dumps(address)

    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <style>
        html, body {{
          margin: 0;
          padding: 0;
          background: white;
        }}
        #map {{
          width: 100%;
          height: {height - 10}px;
          border-radius: 14px;
        }}
        #msg {{
          font-family: sans-serif;
          font-size: 14px;
          color: #444;
          padding-top: 8px;
        }}
      </style>
      <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&libraries=services"></script>
    </head>
    <body>
      <div id="map"></div>
      <div id="msg"></div>

      <script>
        const inputAddress = {safe_address};
        const msg = document.getElementById("msg");

        const mapContainer = document.getElementById("map");
        const defaultCenter = new kakao.maps.LatLng(37.5665, 126.9780);

        const map = new kakao.maps.Map(mapContainer, {{
          center: defaultCenter,
          level: 3
        }});

        const geocoder = new kakao.maps.services.Geocoder();

        function showError(text) {{
          msg.innerHTML = text;
        }}

        geocoder.addressSearch(inputAddress, function(result, status) {{
          if (status === kakao.maps.services.Status.OK && result.length > 0) {{
            const lat = parseFloat(result[0].y);
            const lng = parseFloat(result[0].x);
            const coords = new kakao.maps.LatLng(lat, lng);

            const marker = new kakao.maps.Marker({{
              map: map,
              position: coords
            }});

            const infowindow = new kakao.maps.InfoWindow({{
              content: '<div style="padding:6px 10px;font-size:13px;">입력 부지</div>'
            }});

            infowindow.open(map, marker);
            map.setCenter(coords);

            msg.innerHTML = '위도: ' + lat.toFixed(6) + ' / 경도: ' + lng.toFixed(6);
          }} else {{
            showError("주소를 찾지 못했습니다. 도로명주소 또는 지번주소를 다시 확인해 주세요.");
          }}
        }});
      </script>
    </body>
    </html>
    """
    components.html(map_html, height=height)

# -----------------------------
# 헤더
# -----------------------------
st.markdown('<div class="main-title">STEP 1. 부지 맞춤형 공법 선택 프로그램</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">입력한 부지 조건을 바탕으로 RC와 OSC(모듈러) 중 어느 공법이 상대적으로 유리한지 판단하는 초기 의사결정 프로토타입입니다.</div>',
    unsafe_allow_html=True
)

# -----------------------------
# 기본 정보
# -----------------------------
st.markdown('<div class="block-card">', unsafe_allow_html=True)
st.subheader("기본 정보 입력")

info_col1, info_col2 = st.columns(2)

with info_col1:
    project_name = st.text_input(
        "사업명",
        value="",
        placeholder="예: 수원시 ○○동 신축매입임대 사업"
    )

with info_col2:
    site_address = st.text_input(
        "부지 도로명주소",
        value="",
        placeholder="예: 경기도 수원시 영통구 ○○로 00"
    )

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# 주소 입력 시 지도 표시
# -----------------------------
st.markdown('<div class="block-card">', unsafe_allow_html=True)
st.subheader("입력 부지 위치 확인")

if site_address.strip():
    render_kakao_map(site_address.strip(), height=460)
    st.markdown('<div class="map-caption">주소가 맞으면 아래 사업 조건을 계속 입력하면 됩니다.</div>', unsafe_allow_html=True)
else:
    st.info("부지 도로명주소를 입력하면 카카오 지도가 표시됩니다.")

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# 입력값
# -----------------------------
st.markdown('<div class="block-card">', unsafe_allow_html=True)
st.subheader("부지 및 사업 조건 입력")

col1, col2 = st.columns(2)

with col1:
    site_area = st.number_input("대지면적 (㎡)", min_value=0.0, value=500.0, step=10.0)
    gross_area = st.number_input("예상 연면적 (㎡)", min_value=0.0, value=1500.0, step=10.0)
    floors = st.number_input("층수", min_value=1, max_value=30, value=5, step=1)
    road_width = st.number_input("전면 도로폭 (m)", min_value=0.0, value=6.0, step=0.5)
    corner_site = st.radio("코너 부지 여부", ["아니오", "예"], horizontal=True)

with col2:
    obstacle_count = st.number_input("전신주·가로수·장애물 개수", min_value=0, max_value=20, value=1, step=1)
    adjacent_building_gap = st.number_input("인접 건물 평균 이격거리 (m)", min_value=0.0, value=2.5, step=0.5)
    target_duration = st.number_input("목표 공사기간 (개월)", min_value=1, max_value=60, value=12, step=1)
    official_land_price = st.number_input("공시지가 또는 토지가격 수준 (만원/㎡)", min_value=0.0, value=350.0, step=10.0)
    cost_premium_limit = st.number_input("허용 가능한 공사비 할증 한도 (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0)

plan_repeatability = st.slider(
    "평면 반복성 점수 (1=비정형, 5=반복형)",
    min_value=1,
    max_value=5,
    value=3,
    step=1
)

st.markdown("""
**입력 기준 예시**
- **전면 도로폭**: 4m 미만 / 4m 이상 6m 미만 / 6m 이상 8m 미만 / 8m 이상
- **연면적**: 600㎡ 미만 / 600㎡ 이상 1,200㎡ 미만 / 1,200㎡ 이상
- **층수**: 5층 이하 / 6~8층 / 9층 이상
- **장애물 개수**: 0개 / 1~2개 / 3개 이상
- **인접 건물 평균 이격거리**: 2m 미만 / 2m 이상 4m 미만 / 4m 이상
- **토지가격 수준**: 300만원/㎡ 미만 / 300만원/㎡ 이상 500만원/㎡ 미만 / 500만원/㎡ 이상
""")

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# 평가 함수
# -----------------------------
def evaluate_rc_vs_osc(
    site_area,
    gross_area,
    floors,
    road_width,
    corner_site,
    obstacle_count,
    adjacent_building_gap,
    target_duration,
    official_land_price,
    cost_premium_limit,
    plan_repeatability
):
    rc_score = 50
    osc_score = 50

    rc_reasons = []
    osc_reasons = []
    caution_list = []

    # 1. 도로폭
    if road_width < 4:
        rc_score += 18
        osc_score -= 12
        rc_reasons.append("전면 도로폭이 4m 미만이어서 대형 모듈 운송과 양중 계획에 불리합니다.")
        caution_list.append("도로폭 4m 미만 구간은 모듈 반입·회전 반경을 우선 검토해야 합니다.")
    elif 4 <= road_width < 6:
        rc_score += 6
        osc_score += 2
        rc_reasons.append("전면 도로폭이 4m 이상 6m 미만으로 경계 조건이어서 RC가 상대적으로 안정적입니다.")
        osc_reasons.append("전면 도로폭이 최소 반입 가능 범위에 가까워 조건부로 OSC 검토가 가능합니다.")
        caution_list.append("도로폭 4~6m 구간은 트레일러 진입, 회차, 크레인 위치를 별도 검토해야 합니다.")
    elif 6 <= road_width < 8:
        osc_score += 10
        osc_reasons.append("전면 도로폭이 6m 이상이어서 모듈 운송 및 설치 가능성이 높습니다.")
    else:
        osc_score += 15
        osc_reasons.append("전면 도로폭이 8m 이상으로 양중 및 반입 계획 측면에서 OSC에 유리합니다.")

    # 2. 연면적
    if gross_area < 600:
        rc_score += 12
        rc_reasons.append("연면적이 600㎡ 미만으로 작아 모듈러의 표준화 효과가 제한될 수 있습니다.")
    elif 600 <= gross_area < 1200:
        rc_score += 3
        osc_score += 4
        osc_reasons.append("연면적이 600㎡ 이상 1,200㎡ 미만으로 일정 수준의 반복 생산 효과를 기대할 수 있습니다.")
    else:
        osc_score += 12
        osc_reasons.append("연면적이 1,200㎡ 이상이어서 모듈러의 반복 생산과 공기 단축 효과를 기대할 수 있습니다.")

    # 3. 층수
    if floors <= 5:
        osc_score += 8
        osc_reasons.append("층수가 5층 이하로 비교적 낮아 OSC 적용에 유리한 조건입니다.")
    elif 6 <= floors <= 8:
        rc_score += 4
        osc_score += 3
        rc_reasons.append("층수가 6~8층 구간이어서 구조 및 시공 계획을 함께 비교 검토해야 합니다.")
        caution_list.append("중층 규모에서는 구조 안전성과 양중 계획을 함께 검토해야 합니다.")
    else:
        rc_score += 12
        osc_score -= 4
        rc_reasons.append("층수가 9층 이상으로 높아질수록 구조·접합·양중 검토 부담이 커집니다.")
        caution_list.append("9층 이상에서는 모듈러 적용 한계와 구조 시스템 검토가 중요합니다.")

    # 4. 코너 부지
    if corner_site == "예":
        osc_score += 4
        osc_reasons.append("코너 부지는 차량 접근과 회차 측면에서 일부 유리할 수 있습니다.")
    else:
        rc_score += 1

    # 5. 장애물 개수
    if obstacle_count == 0:
        osc_score += 8
        osc_reasons.append("전신주·가로수 등 장애물이 없어 모듈 설치에 유리합니다.")
    elif 1 <= obstacle_count <= 2:
        rc_score += 3
        osc_score += 1
        rc_reasons.append("장애물이 일부 존재하여 RC가 다소 유리할 수 있습니다.")
    else:
        rc_score += 12
        osc_score -= 6
        rc_reasons.append("장애물이 3개 이상으로 대형 장비 운영과 모듈 반입에 불리합니다.")
        caution_list.append("장애물 이전 비용과 장비 동선을 별도로 검토해야 합니다.")

    # 6. 인접 건물 이격거리
    if adjacent_building_gap < 2:
        osc_score += 9
        rc_reasons.append("인접 건물 이격거리가 매우 좁아 현장 작업 제약이 큽니다.")
        osc_reasons.append("인접 건물 이격거리가 2m 미만으로 좁아 현장 작업을 줄이는 OSC가 유리할 수 있습니다.")
        caution_list.append("협소 대지에서는 크레인 설치 위치와 양중 반경 검토가 필요합니다.")
    elif 2 <= adjacent_building_gap < 4:
        rc_score += 2
        osc_score += 3
    else:
        rc_score += 6
        rc_reasons.append("인접 건물 이격거리가 4m 이상으로 일반 현장 시공의 제약이 상대적으로 적습니다.")

    # 7. 목표 공사기간
    if target_duration <= 10:
        osc_score += 15
        osc_reasons.append("목표 공사기간이 10개월 이하로 짧아 공기 단축형 공법의 장점이 큽니다.")
    elif 11 <= target_duration <= 15:
        osc_score += 6
        osc_reasons.append("공기 단축 효과를 고려할 수 있는 기간 조건입니다.")
    else:
        rc_score += 6
        rc_reasons.append("목표 공사기간이 16개월 이상으로 공기 제약이 상대적으로 작습니다.")

    # 8. 토지가격 수준
    if official_land_price < 300:
        rc_score += 5
        rc_reasons.append("토지가격 수준이 낮아 공기 단축에 따른 금융비용 절감 효과가 상대적으로 작을 수 있습니다.")
    elif 300 <= official_land_price < 500:
        osc_score += 5
        osc_reasons.append("토지가격이 일정 수준 이상이어서 조기 준공의 가치가 커질 수 있습니다.")
    else:
        osc_score += 10
        osc_reasons.append("토지가격 수준이 높아 공기 단축에 따른 금융비용 절감 효과가 커질 수 있습니다.")

    # 9. 허용 가능한 공사비 할증 한도
    if cost_premium_limit < 5:
        rc_score += 14
        rc_reasons.append("허용 가능한 공사비 할증 한도가 5% 미만으로 낮아 RC가 상대적으로 유리합니다.")
    elif 5 <= cost_premium_limit < 10:
        rc_score += 5
        osc_score += 2
    elif 10 <= cost_premium_limit < 15:
        osc_score += 5
        osc_reasons.append("공사비 할증을 일정 수준 허용할 수 있어 OSC 검토 여지가 있습니다.")
    else:
        osc_score += 10
        osc_reasons.append("허용 가능한 공사비 할증 한도가 15% 이상으로 공기 단축형 공법 검토가 유리합니다.")

    # 10. 평면 반복성
    if plan_repeatability <= 2:
        rc_score += 10
        rc_reasons.append("평면 반복성이 낮아 모듈러 표준화 효과가 제한될 수 있습니다.")
    elif plan_repeatability == 3:
        rc_score += 2
        osc_score += 4
    else:
        osc_score += 12
        osc_reasons.append("평면 반복성이 높아 모듈러 표준화 및 반복 생산에 유리합니다.")

    # 추천 공법
    recommended_method = "RC" if rc_score >= osc_score else "OSC(모듈러)"

    # 추천 이유
    reason_list = rc_reasons if recommended_method == "RC" else osc_reasons

    # 추천 모듈러 타입
    modular_type = "해당 없음"
    if recommended_method == "OSC(모듈러)":
        if road_width >= 8 and gross_area >= 1200 and floors <= 6:
            modular_type = "표준형 모듈러 타입 (기준형)"
        elif road_width >= 6 and site_area < 500:
            modular_type = "협소부지 대응 소형 모듈러 타입"
        else:
            modular_type = "일반형 모듈러 타입"

    # 임계점 해석
    diff = abs(rc_score - osc_score)
    threshold_comment = []

    if recommended_method == "RC":
        if diff >= 10:
            threshold_comment.append("현재 조건에서는 RC가 OSC보다 상대적으로 뚜렷하게 우세합니다.")
        else:
            threshold_comment.append("현재 조건에서는 RC가 소폭 우세하며, 세부 운송·공사비 검토에 따라 결과가 달라질 수 있습니다.")
    else:
        if diff >= 10:
            threshold_comment.append("현재 조건에서는 OSC가 RC보다 상대적으로 뚜렷하게 우세합니다.")
        else:
            threshold_comment.append("현재 조건에서는 OSC가 소폭 우세하며, 실제 공사비와 운송 조건 검토가 필요합니다.")

    return {
        "rc_score": rc_score,
        "osc_score": osc_score,
        "recommended_method": recommended_method,
        "reason_list": reason_list,
        "modular_type": modular_type,
        "caution_list": caution_list,
        "threshold_comment": threshold_comment
    }

# -----------------------------
# 실행
# -----------------------------
st.markdown('<div class="block-card">', unsafe_allow_html=True)
st.subheader("분석 실행")

run_clicked = st.button("STEP 1 분석 실행")

st.markdown('</div>', unsafe_allow_html=True)

if run_clicked:
    result = evaluate_rc_vs_osc(
        site_area=site_area,
        gross_area=gross_area,
        floors=floors,
        road_width=road_width,
        corner_site=corner_site,
        obstacle_count=obstacle_count,
        adjacent_building_gap=adjacent_building_gap,
        target_duration=target_duration,
        official_land_price=official_land_price,
        cost_premium_limit=cost_premium_limit,
        plan_repeatability=plan_repeatability
    )

    rc_score = result["rc_score"]
    osc_score = result["osc_score"]
    recommended_method = result["recommended_method"]
    reason_list = result["reason_list"]
    modular_type = result["modular_type"]
    caution_list = result["caution_list"]
    threshold_comment = result["threshold_comment"]

    st.subheader("분석 결과")

    # 기본 정보 표시
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    info_a, info_b = st.columns(2)
    with info_a:
        st.markdown('<div class="small-label">사업명</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="big-value">{project_name if project_name else "-"}</div>', unsafe_allow_html=True)
    with info_b:
        st.markdown('<div class="small-label">부지 도로명주소</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="big-value">{site_address if site_address else "-"}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 결과 지도
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.subheader("분석 대상 부지 위치")
    if site_address.strip():
        render_kakao_map(site_address.strip(), height=460)
    else:
        st.write("주소가 입력되지 않아 지도를 표시할 수 없습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

    # 점수 카드
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-label">RC 점수</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="big-value">{rc_score}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-label">OSC 점수</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="big-value">{osc_score}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 추천 공법
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.subheader("추천 공법")
    if recommended_method == "RC":
        st.warning(f"추천 공법: **{recommended_method}**")
    else:
        st.success(f"추천 공법: **{recommended_method}**")
    st.markdown('</div>', unsafe_allow_html=True)

    # 점수표
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.subheader("공법별 점수 비교")
    score_df = pd.DataFrame({
        "공법": ["RC", "OSC(모듈러)"],
        "점수": [rc_score, osc_score]
    })
    st.dataframe(score_df, use_container_width=True, hide_index=True)
    st.bar_chart(score_df.set_index("공법"))
    st.markdown('</div>', unsafe_allow_html=True)

    # 추천 사유
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.subheader("추천 사유")
    if reason_list:
        for idx, reason in enumerate(reason_list, start=1):
            st.write(f"{idx}. {reason}")
    else:
        st.write("뚜렷한 우세 요인이 적어 추가 검토가 필요합니다.")
    st.markdown('</div>', unsafe_allow_html=True)

    # 추천 모듈러 타입
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.subheader("추천 모듈러 기본 모델")
    st.write(modular_type)
    st.markdown('</div>', unsafe_allow_html=True)

    # 임계점 해석
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.subheader("임계점 해석")
    for comment in threshold_comment:
        st.write(f"- {comment}")
    st.markdown('</div>', unsafe_allow_html=True)

    # 추가 검토사항
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.subheader("추가 검토 필요 사항")
    if caution_list:
        for caution in caution_list:
            st.write(f"- {caution}")
    else:
        st.write("- 현재 입력 조건에서는 특이 주의사항이 상대적으로 적습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.write("위 조건을 입력한 뒤 **STEP 1 분석 실행** 버튼을 눌러주세요.")
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 헤더
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="centered"
)

st.title("👨‍👩‍👧‍👦 우리 동네 인구 피라미드")
st.caption("전국 읍·면·동의 나이별/성별 인구 구조를 따뜻한 시선으로 살펴봅니다.")
st.markdown("---")

# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 (캐싱 적용으로 속도 향상)
# -----------------------------------------------------------------------------
DATA_URL = "https://raw.githubusercontent.com/first2022-cyber/contents/main/population_ts_yearly_gender.zip"

@st.cache_data
def load_data(url):
    # pandas는 zip 파일 내의 csv를 자동으로 읽어옵니다.
    df = pd.read_csv(url, encoding='utf-8')
    
    # '연도' 열이 존재할 경우 가장 최신 연도 데이터만 추출합니다.
    if '연도' in df.columns:
        latest_year = df['연도'].max()
        df = df[df['연도'] == latest_year].copy()
    else:
        latest_year = "최신"
        
    return df, latest_year

# 데이터 로딩 상태 표시
with st.spinner("인구 데이터를 불러오는 중입니다. 잠시만 기다려주세요..."):
    df, latest_year = load_data(DATA_URL)

st.info(f"💡 현재 **{latest_year}년** 기준 인구 데이터를 바탕으로 조회합니다.")

# -----------------------------------------------------------------------------
# 3. 나이 라벨 순서 정의 (0세 ~ 100세 이상)
# -----------------------------------------------------------------------------
# 나이 컬럼을 0세부터 100세 이상까지 순서대로 리스트화합니다.
age_labels = [f"{i}세" for i in range(101)]
age_labels[-1] = "100세 이상"  # 마지막 100세는 '100세 이상' 라벨명으로 변경

male_cols = [f"남_{age}" for age in age_labels]
female_cols = [f"여_{age}" for age in age_labels]

# -----------------------------------------------------------------------------
# 4. 지역 선택 드롭다운 (시도 -> 시군구 -> 동)
# -----------------------------------------------------------------------------
st.subheader("📍 지역 선택")

# 1) 시도 선택
sido_list = sorted(df['시도'].dropna().unique())
selected_sido = st.selectbox("1. 시·도를 선택하세요", sido_list)

# 2) 시군구 선택 (선택된 시도 필터링)
sigungu_df = df[df['시도'] == selected_sido]
sigungu_list = sorted(sigungu_df['시군구'].dropna().unique())
selected_sigungu = st.selectbox("2. 시·군·구를 선택하세요", sigungu_list)

# 3) 동/읍/면 선택 (선택된 시군구 필터링)
dong_df = sigungu_df[sigungu_df['시군구'] == selected_sigungu]
dong_list = sorted(dong_df['동'].dropna().unique())
selected_dong = st.selectbox("3. 읍·면·동을 선택하세요", dong_list)

# 최종 선택된 지역의 데이터 1개 행 가져오기
target_data = dong_df[dong_df['동'] == selected_dong].iloc[0]

# -----------------------------------------------------------------------------
# 5. 인구 피라미드 Plotly 시각화
# -----------------------------------------------------------------------------
# 남성 인구는 피라미드 왼쪽에 배치하기 위해 음수(-) 값으로 변환합니다.
male_pop = [-float(target_data[col]) for col in male_cols]
female_pop = [float(target_data[col]) for col in female_cols]

# 차트 객체 생성
fig = go.Figure()

# 남성 막대 그래프 (왼쪽)
fig.add_trace(go.Bar(
    y=age_labels,
    x=male_pop,
    name='남성',
    orientation='h',
    marker=dict(color='#5B8FF9'),  # 따뜻하고 신뢰감 주는 파란색
    hoverinfo='text',
    text=[f"남성 {age}: {abs(val):,.0f}명" for age, val in zip(age_labels, male_pop)]
))

# 여성 막대 그래프 (오른쪽)
fig.add_trace(go.Bar(
    y=age_labels,
    x=female_pop,
    name='여성',
    orientation='h',
    marker=dict(color='#F68484'),  # 따뜻한 분홍/코랄색
    hoverinfo='text',
    text=[f"여성 {age}: {val:,.0f}명" for age, val in zip(age_labels, female_pop)]
))

# x축에 표시될 눈금값 계산 (음수 표시 제거 및 보기 좋은 포맷)
max_val = max(max(abs(val) for val in male_pop), max(female_pop))
if max_val == 0:
    max_val = 10  # 데이터가 0일 경우 대비

# x축 레이블에 음수 대신 양수로 보이도록 설정
tick_vals = np.linspace(-max_val, max_val, 7)
tick_text = [f"{abs(int(v)):,}명" for v in tick_vals]

# 레이아웃 설정
fig.update_layout(
    title=dict(
        text=f"<b>{selected_sido} {selected_sigungu} {selected_dong}</b> 인구 피라미드",
        font=dict(size=18, color='#2C3E50'),
        x=0.5,
        xanchor='center'
    ),
    barmode='overlay',      # 막대 중첩 레이아웃
    bargap=0.1,             # 막대 간격
    height=800,             # 피라미드가 잘 보이도록 충분한 높이 지정
    xaxis=dict(
        tickvals=tick_vals,
        ticktext=tick_text,
        title='인구수',
        zeroline=True,
        zerolinecolor='#A0A0A0',
        zerolinewidth=1
    ),
    yaxis=dict(
        title='연령 (세)',
        type='category',                  # 범주형 축 지정
        categoryorder='array',           # 정렬 방식을 사용자 지정 배열로 고정
        categoryarray=age_labels,        # 0세가 맨 아래, 100세 이상이 맨 위로 위치하도록 배열 전달
        autorange=True                   # 순서를 반전시키지 않음 (순방향 유지)
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    template="plotly_white",
    margin=dict(l=60, r=40, t=80, b=60)
)

# 차트 출력
st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# 6. 하단 요약 정보
# -----------------------------------------------------------------------------
total_male = sum(abs(v) for v in male_pop)
total_female = sum(female_pop)
total_pop = total_male + total_female

st.markdown("### 📊 지역 인구 요약")
col1, col2, col3 = st.columns(3)
col1.metric("총인구수", f"{int(total_pop):,} 명")
col2.metric("남성 인구", f"{int(total_male):,} 명")
col3.metric("여성 인구", f"{int(total_female):,} 명")

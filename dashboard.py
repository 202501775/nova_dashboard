"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOVA시 스마트시티 자원 배분 시뮬레이터
dashboard.py  ·  Streamlit 대시보드

실행: streamlit run dashboard.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import math
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from classes import (
    Worker, Student, Caregiver, Unemployed, Elder,
    SolarPanel, HydrogenCell, ESS, ExternalGrid,
    Resource, EnergyGrid, District, City, PolicySimulator,
    budget_to_fulfillment, energy_to_bonus,
    BudgetAllocationError, LowSatisfactionWarning, EnergyAllocationError
)

# ──────────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────────
st.set_page_config(
    page_title="NOVA시 스마트시티 시뮬레이터",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────
# 커스텀 CSS
# ──────────────────────────────────────────────────
st.markdown("""
<style>
/* 전체 배경 */
.stApp { background-color: #ffffff; color: #1f2328; }

/* 사이드바 */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f6f8fa 0%, #ffffff 100%);
    border-right: 1px solid #d0d7de;
}
[data-testid="stSidebar"] .stSlider > div { color: #1f2328; }

/* 메트릭 카드 */
.metric-card {
    background: #f6f8fa;
    border: 1px solid #d0d7de;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #0969da; }
.metric-card .label {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #656d76;
    margin-bottom: 8px;
}
.metric-card .value {
    font-size: 32px;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 4px;
}
.metric-card .sub {
    font-size: 12px;
    color: #656d76;
}
.metric-good  { color: #1a7f37; }
.metric-warn  { color: #9a6700; }
.metric-danger{ color: #cf222e; }
.metric-blue  { color: #0969da; }
.metric-purple{ color: #8250df; }

/* 섹션 헤더 */
.section-header {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #656d76;
    padding: 8px 0 4px;
    border-bottom: 1px solid #d0d7de;
    margin-bottom: 12px;
}

/* 경보 배너 */
.alert-danger {
    background: rgba(207, 34, 46, 0.08);
    border: 1px solid rgba(207, 34, 46, 0.3);
    border-left: 4px solid #cf222e;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
    color: #82071e;
    font-size: 14px;
}
.alert-success {
    background: rgba(26, 127, 55, 0.08);
    border: 1px solid rgba(26, 127, 55, 0.3);
    border-left: 4px solid #1a7f37;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
    color: #0f5323;
    font-size: 14px;
}
.alert-info {
    background: rgba(9, 105, 218, 0.08);
    border: 1px solid rgba(9, 105, 218, 0.3);
    border-left: 4px solid #0969da;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
    color: #0550ae;
    font-size: 14px;
}

/* 탭 스타일 */
.stTabs [data-baseweb="tab-list"] {
    background: #f6f8fa;
    border-bottom: 1px solid #d0d7de;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #656d76;
    font-weight: 600;
    font-size: 13px;
    padding: 8px 16px;
}
.stTabs [aria-selected="true"] {
    color: #1f2328 !important;
    border-bottom: 2px solid #0969da;
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────
# 색상 팔레트
# ──────────────────────────────────────────────────
COLORS = {
    'bg':       '#ffffff',   # 흰 배경
    'surface':  '#f6f8fa',   # 카드/패널 (살짝 회색)
    'border':   '#d0d7de',   # 테두리 (밝은 회색)
    'text':     '#1f2328',   # 본문 텍스트 (거의 검정)
    'muted':    '#656d76',   # 보조 텍스트 (중간 회색)
    'blue':     '#0969da',   # 라이트 모드용 진한 파랑
    'green':    '#1a7f37',
    'yellow':   '#9a6700',
    'red':      '#cf222e',
    'purple':   '#8250df',
    'cyan':     '#1f883d',
    'districts': ['#0969da','#1a7f37','#9a6700','#8250df','#cf222e'],
    'scenarios': ['#0969da','#1a7f37','#9a6700','#8250df','#0550ae'],
}

PLOT_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color=COLORS['text'], family='Inter, sans-serif', size=12),
    margin=dict(l=16, r=16, t=36, b=16),
    legend=dict(
        bgcolor='rgba(246,248,250,0.9)',
        bordercolor=COLORS['border'],
        borderwidth=1,
        font=dict(size=11),
    ),
)

DISTRICT_NAMES = [
    'A구역\n(산업단지)',
    'B구역\n(대학가)',
    'C구역\n(복지타운)',
    'D구역\n(신도시)',
    'E구역\n(구도심)',
]
DISTRICT_KEYS = ['A구역(산업단지)','B구역(대학가)','C구역(복지타운)','D구역(신도시)','E구역(구도심)']
NEED_LABELS = ['건강·안전', '모빌리티', '활동·문화', '기회·교육', '거버넌스']
NEED_KEYS   = ['health_safety','mobility','activities','opportunities','governance']

# ──────────────────────────────────────────────────
# 도시 초기화 (캐시)
# ──────────────────────────────────────────────────
@st.cache_resource
def get_city():
    worker     = Worker()
    student    = Student()
    caregiver  = Caregiver()
    unemployed = Unemployed()
    elder      = Elder()

    districts = [
        District('A구역(산업단지)',
            {worker:0.75, student:0.05, caregiver:0.08, unemployed:0.07, elder:0.05},
            0.45),
        District('B구역(대학가)',
            {worker:0.10, student:0.70, caregiver:0.08, unemployed:0.07, elder:0.05},
            0.42),
        District('C구역(복지타운)',
            {worker:0.05, student:0.03, caregiver:0.10, unemployed:0.07, elder:0.75},
            0.55),
        District('D구역(신도시)',
            {worker:0.35, student:0.25, caregiver:0.20, unemployed:0.10, elder:0.10},
            0.40),
        District('E구역(구도심)',
            {worker:0.30, student:0.05, caregiver:0.20, unemployed:0.18, elder:0.27},
            0.30),
    ]
    return City('NOVA시', districts)

# ──────────────────────────────────────────────────
# 시뮬레이션 실행
# ──────────────────────────────────────────────────
def run_simulation(welfare, education, energy_infra, general_infra, safety,
                   solar, hydrogen, ess, external):
    try:
        resource = Resource(
            welfare=welfare/100,
            education=education/100,
            energy_infra=energy_infra/100,
            general_infra=general_infra/100,
            safety=safety/100,
        )
    except BudgetAllocationError as e:
        return None, str(e)

    try:
        grid = EnergyGrid([
            SolarPanel(solar/100),
            HydrogenCell(hydrogen/100),
            ESS(ess/100),
            ExternalGrid(external/100),
        ])
    except EnergyAllocationError as e:
        return None, str(e)

    city = get_city()
    result = city.apply_policy(resource, grid)
    return result, None

# ──────────────────────────────────────────────────
# 프리셋 시나리오
# ──────────────────────────────────────────────────
PRESETS = {
    '직접 입력': None,
    '초기 상태 (인프라 편중)':  dict(welfare=15, education=15, energy_infra=10, general_infra=45, safety=15,
                                      solar=10, hydrogen=5,  ess=5,  external=80),
    '복지 집중':                dict(welfare=40, education=15, energy_infra=15, general_infra=20, safety=10,
                                      solar=25, hydrogen=15, ess=15, external=45),
    '에너지 자립 집중':         dict(welfare=12, education=10, energy_infra=45, general_infra=23, safety=10,
                                      solar=45, hydrogen=30, ess=20, external=5),
    '균형 배분':                dict(welfare=22, education=20, energy_infra=20, general_infra=23, safety=15,
                                      solar=35, hydrogen=25, ess=20, external=20),
    '선순환 최적 ⭐':           dict(welfare=20, education=18, energy_infra=30, general_infra=22, safety=10,
                                      solar=40, hydrogen=35, ess=20, external=5),
}

# ──────────────────────────────────────────────────
# 차트 함수들
# ──────────────────────────────────────────────────
def score_color(score):
    if score < 50:  return COLORS['red']
    if score < 60:  return COLORS['yellow']
    if score < 75:  return COLORS['blue']
    return COLORS['green']

def score_label(score):
    if score < 50:  return '⚠ 위험'
    if score < 60:  return '주의'
    if score < 75:  return '양호'
    return '✅ 우수'


def chart_district_bar(result):
    scores = [result['districts'][k] for k in DISTRICT_KEYS]
    colors = [score_color(s) for s in scores]
    labels = [f"{s:.1f}" for s in scores]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=DISTRICT_NAMES, y=scores,
        marker_color=colors,
        marker_line_width=0,
        text=labels, textposition='outside',
        textfont=dict(size=13, color=COLORS['text']),
        hovertemplate='<b>%{x}</b><br>만족도: %{y:.1f}점<extra></extra>',
    ))
    fig.add_hline(y=50, line_dash='dot', line_color=COLORS['red'],
                  line_width=1.5, annotation_text='위험 임계치 (50점)',
                  annotation_font_color=COLORS['red'],
                  annotation_font_size=11)
    fig.add_hline(y=75, line_dash='dot', line_color=COLORS['green'],
                  line_width=1, annotation_text='우수 기준 (75점)',
                  annotation_font_color=COLORS['green'],
                  annotation_font_size=11)

    avg = result['city_average']
    fig.add_hline(y=avg, line_dash='dash', line_color=COLORS['purple'],
                  line_width=2, annotation_text=f'도시 평균 {avg:.1f}점',
                  annotation_font_color=COLORS['purple'],
                  annotation_font_size=12, annotation_position='bottom right')

    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text='구역별 시민 만족도', font=dict(size=14, color=COLORS['text'])),
        yaxis=dict(range=[30, 100], gridcolor=COLORS['border'],
                   gridwidth=0.5, tickfont=dict(color=COLORS['muted'])),
        xaxis=dict(tickfont=dict(size=12, color=COLORS['text'])),
        height=340,
    )
    return fig


def chart_need_radar(result, resource):
    need_ratios = resource.get_need_ratios()
    need_scores = [budget_to_fulfillment(need_ratios[k]) for k in NEED_KEYS]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=need_scores + [need_scores[0]],
        theta=NEED_LABELS + [NEED_LABELS[0]],
        fill='toself',
        fillcolor='rgba(56,139,253,0.15)',
        line=dict(color=COLORS['blue'], width=2),
        marker=dict(size=6, color=COLORS['blue']),
        name='니즈 충족도',
        hovertemplate='<b>%{theta}</b><br>%{r:.1f}점<extra></extra>',
    ))
    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text='5개 니즈 충족도', font=dict(size=14, color=COLORS['text'])),
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(range=[0,100], gridcolor=COLORS['border'],
                            tickfont=dict(color=COLORS['muted'], size=10)),
            angularaxis=dict(gridcolor=COLORS['border'],
                             tickfont=dict(color=COLORS['text'], size=12)),
        ),
        height=340,
        showlegend=False,
    )
    return fig


def chart_energy_gauge(rate):
    color = COLORS['red'] if rate < 0.40 else COLORS['yellow'] if rate < 0.60 \
            else COLORS['blue'] if rate < 0.80 else COLORS['green']
    fig = go.Figure(go.Indicator(
        mode='gauge+number+delta',
        value=rate * 100,
        number=dict(suffix='%', font=dict(size=36, color=color)),
        delta=dict(reference=40, valueformat='.1f',
                   increasing=dict(color=COLORS['green']),
                   decreasing=dict(color=COLORS['red'])),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1,
                      tickcolor=COLORS['muted'],
                      tickfont=dict(color=COLORS['muted'], size=10)),
            bar=dict(color=color, thickness=0.25),
            bgcolor='rgba(0,0,0,0)',
            borderwidth=0,
            steps=[
                dict(range=[0,40],  color='rgba(248,81,73,0.15)'),
                dict(range=[40,60], color='rgba(210,153,34,0.15)'),
                dict(range=[60,80], color='rgba(56,139,253,0.15)'),
                dict(range=[80,100],color='rgba(63,185,80,0.15)'),
            ],
            threshold=dict(
                line=dict(color=COLORS['text'], width=2),
                thickness=0.75,
                value=83.13,
            ),
        ),
        title=dict(text='에너지 자립률<br><span style="font-size:11px;color:#7d8590">목표: 83.13% (세종시)</span>',
                   font=dict(size=14, color=COLORS['text'])),
    ))
    fig.update_layout(**PLOT_LAYOUT, height=280)
    return fig


def chart_budget_pie(welfare, education, energy_infra, general_infra, safety):
    labels = ['복지', '교육', '에너지\n인프라', '일반\n인프라', '안전']
    values = [welfare, education, energy_infra, general_infra, safety]
    colors_pie = [COLORS['green'], COLORS['blue'], COLORS['yellow'],
                  COLORS['purple'], COLORS['red']]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker=dict(colors=colors_pie,
                    line=dict(color=COLORS['bg'], width=2)),
        textfont=dict(size=12, color='white'),
        hovertemplate='<b>%{label}</b><br>%{value}%<extra></extra>',
        hole=0.45,
        pull=[0.03]*5,
    ))
    fig.update_layout(
    **{**PLOT_LAYOUT,
       'title': dict(text='예산 배분 현황', font=dict(size=14, color=COLORS['text'])),
       'height': 280,
       'showlegend': True,
       'legend': dict(orientation='v', x=1.0, y=0.5,
                      font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
       'annotations': [dict(text=f'{sum(values)}%', x=0.5, y=0.5, showarrow=False,
                            font=dict(size=16, color=COLORS['text'], family='Inter'))]}
)
    return fig


def chart_energy_pie(solar, hydrogen, ess, external):
    labels = ['태양광', '수소\n연료전지', 'ESS', '외부\n전력망']
    values = [solar, hydrogen, ess, external]
    colors_e = [COLORS['yellow'], COLORS['blue'], COLORS['cyan'], COLORS['muted']]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker=dict(colors=colors_e,
                    line=dict(color=COLORS['bg'], width=2)),
        textfont=dict(size=12, color='white'),
        hovertemplate='<b>%{label}</b><br>%{value}%<extra></extra>',
        hole=0.45,
        pull=[0.03]*4,
    ))
    self_rate = round((solar*0.7 + hydrogen*0.9 + ess*0.6) / 100, 3) * 100
    fig.update_layout(
    **{**PLOT_LAYOUT,
       'title': dict(text='에너지원 구성', font=dict(size=14, color=COLORS['text'])),
       'height': 280,
       'showlegend': True,
       'legend': dict(orientation='v', x=1.0, y=0.5,
                      font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
       'annotations': [dict(text=f'자립<br>{self_rate:.0f}%', x=0.5, y=0.5,
                            showarrow=False,
                            font=dict(size=14, color=COLORS['text'], family='Inter'))]}
)
    return fig


def chart_nonlinear_curve():
    import numpy as np
    x = np.linspace(0, 0.55, 300)
    y = [budget_to_fulfillment(xi) for xi in x]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[xi*100 for xi in x], y=y,
        mode='lines', line=dict(color=COLORS['blue'], width=2.5),
        fill='tozeroy', fillcolor='rgba(56,139,253,0.08)',
        name='충족도 곡선',
        hovertemplate='예산 %{x:.1f}% → 충족도 %{y:.1f}점<extra></extra>',
    ))
    for rx, label in [(0.10,'40pt'),(0.20,'60pt★'),(0.30,'75pt'),(0.40,'96pt')]:
        ry = budget_to_fulfillment(rx)
        fig.add_trace(go.Scatter(
            x=[rx*100], y=[ry], mode='markers+text',
            marker=dict(size=8, color=COLORS['text'], symbol='circle'),
            text=[f'  {rx*100:.0f}%→{ry:.0f}pt'], textposition='middle right',
            textfont=dict(size=10, color=COLORS['muted']),
            showlegend=False,
            hoverinfo='skip',
        ))
    fig.add_vline(x=20, line_dash='dot', line_color=COLORS['red'],
                  line_width=1.5, annotation_text='임계점(20%)',
                  annotation_font_color=COLORS['red'],
                  annotation_font_size=10)
    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text='비선형 변환 함수 — 임계점 효과', font=dict(size=14)),
        xaxis=dict(title='예산 비율 (%)', gridcolor=COLORS['border'],
                   tickfont=dict(color=COLORS['muted'])),
        yaxis=dict(title='니즈 충족도 점수', range=[0,105],
                   gridcolor=COLORS['border'], tickfont=dict(color=COLORS['muted'])),
        height=280, showlegend=False,
    )
    return fig


def chart_scenario_compare(results_dict):
    scenarios = list(results_dict.keys())
    avgs = [results_dict[s]['city_average'] for s in scenarios]
    rates = [results_dict[s]['independence_rate']*100 for s in scenarios]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=scenarios, y=avgs,
        name='도시 평균 만족도',
        marker_color=[COLORS['blue']]*5,
        marker_line_width=0,
        text=[f'{v:.1f}' for v in avgs],
        textposition='outside',
        textfont=dict(size=11, color=COLORS['text']),
        hovertemplate='<b>%{x}</b><br>평균: %{y:.1f}점<extra></extra>',
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=scenarios, y=rates,
        name='에너지 자립률',
        mode='lines+markers',
        line=dict(color=COLORS['yellow'], width=2.5),
        marker=dict(size=8, color=COLORS['yellow']),
        hovertemplate='<b>%{x}</b><br>자립률: %{y:.1f}%<extra></extra>',
    ), secondary_y=True)

    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text='시나리오별 비교 — 만족도 & 에너지 자립률',
                   font=dict(size=14)),
        height=320,
        xaxis=dict(tickfont=dict(size=11, color=COLORS['text']),
                   gridcolor=COLORS['border']),
    )
    fig.update_yaxes(title_text='도시 평균 만족도', range=[40,85],
                     gridcolor=COLORS['border'],
                     tickfont=dict(color=COLORS['muted']),
                     secondary_y=False)
    fig.update_yaxes(title_text='에너지 자립률 (%)', range=[0,100],
                     tickfont=dict(color=COLORS['muted']),
                     secondary_y=True)
    return fig


def chart_district_heatmap(results_dict):
    scenarios = list(results_dict.keys())
    z = [[results_dict[s]['districts'][k] for k in DISTRICT_KEYS]
         for s in scenarios]
    d_labels = ['A (산업단지)','B (대학가)','C (복지타운)','D (신도시)','E (구도심)']

    fig = go.Figure(go.Heatmap(
        z=z, x=d_labels, y=scenarios,
        colorscale='Blues', zmin=40, zmax=80,
        text=[[f'{v:.1f}' for v in row] for row in z],
        texttemplate='%{text}',
        textfont=dict(size=11),
        hovertemplate='시나리오: %{y}<br>구역: %{x}<br>만족도: %{z:.1f}점<extra></extra>',
        colorbar=dict(title='점수', tickfont=dict(color=COLORS['muted'])),
    ))
    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text='구역별 만족도 히트맵 (시나리오 전체)', font=dict(size=14)),
        height=320,
        xaxis=dict(tickfont=dict(size=11, color=COLORS['text'])),
        yaxis=dict(tickfont=dict(size=11, color=COLORS['text'])),
    )
    return fig


# ──────────────────────────────────────────────────
# 사이드바 — 입력 패널
# ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="text-align:center;padding:16px 0 8px">'
                '<span style="font-size:28px">🏙️</span><br>'
                '<span style="font-size:16px;font-weight:800;color:#1f2328">'
                'NOVA시 시뮬레이터</span><br>'
                '<span style="font-size:11px;color:#656d76">'
                'Smart City Resource Allocator</span></div>',
                unsafe_allow_html=True)
    st.markdown('---')

    # 프리셋 선택
    # 프리셋 선택
    st.markdown('<div class="section-header">프리셋 시나리오</div>',
                unsafe_allow_html=True)

    # 프리셋이 바뀌면 슬라이더 값을 자동으로 덮어쓰는 콜백
    def apply_preset():
        p = PRESETS[st.session_state.preset_choice]
        if p is None:
            return
        st.session_state.w   = p['welfare']
        st.session_state.e   = p['education']
        st.session_state.ei  = p['energy_infra']
        st.session_state.gi  = p['general_infra']
        st.session_state.s   = p['safety']
        st.session_state.sol = p['solar']
        st.session_state.hyd = p['hydrogen']
        st.session_state.ess = p['ess']
        st.session_state.ext = p['external']

    preset_choice = st.selectbox(
        '', list(PRESETS.keys()),
        label_visibility='collapsed',
        key='preset_choice',
        on_change=apply_preset,
    )
    preset = PRESETS[preset_choice]

    def pv(key, default):
        return preset[key] if preset else default

    st.markdown('---')

    # ── 예산 배분 ──
    st.markdown('<div class="section-header">💰 예산 배분 (%)</div>',
                unsafe_allow_html=True)

    welfare      = st.slider('복지',        0, 100, pv('welfare', 20),      1, key='w')
    education    = st.slider('교육',        0, 100, pv('education', 18),    1, key='e')
    energy_infra = st.slider('에너지 인프라', 0, 100, pv('energy_infra', 30), 1, key='ei')
    general_infra= st.slider('일반 인프라',  0, 100, pv('general_infra', 22),1, key='gi')
    safety       = st.slider('안전',        0, 100, pv('safety', 10),       1, key='s')

    budget_total = welfare + education + energy_infra + general_infra + safety
    budget_ok = abs(budget_total - 100) <= 1

    if budget_ok:
        st.markdown(f'<div class="alert-success">합계: {budget_total}% ✓</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert-danger">합계: {budget_total}% ← 100%여야 합니다</div>',
                    unsafe_allow_html=True)

    st.markdown('---')

    # ── 에너지 배분 ──
    st.markdown('<div class="section-header">⚡ 에너지 배분 (%)</div>',
                unsafe_allow_html=True)

    solar    = st.slider('태양광',      0, 100, pv('solar', 40),    1, key='sol')
    hydrogen = st.slider('수소연료전지', 0, 100, pv('hydrogen', 35), 1, key='hyd')
    ess      = st.slider('ESS',        0, 100, pv('ess', 20),       1, key='ess')
    external = st.slider('외부전력망',  0, 100, pv('external', 5),  1, key='ext')

    energy_total = solar + hydrogen + ess + external
    energy_ok = abs(energy_total - 100) <= 1

    if energy_ok:
        st.markdown(f'<div class="alert-success">합계: {energy_total}% ✓</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert-danger">합계: {energy_total}% ← 100%여야 합니다</div>',
                    unsafe_allow_html=True)

    st.markdown('---')
    run_btn = st.button('▶ 시뮬레이션 실행', type='primary', use_container_width=True)

# ──────────────────────────────────────────────────
# 세션 스테이트 초기화
# ──────────────────────────────────────────────────
if 'result' not in st.session_state:
    st.session_state.result = None
if 'resource_obj' not in st.session_state:
    st.session_state.resource_obj = None
if 'history' not in st.session_state:
    st.session_state.history = {}

# ──────────────────────────────────────────────────
# 실행 버튼 처리
# ──────────────────────────────────────────────────
if run_btn:
    if not budget_ok:
        st.error(f'예산 합계가 {budget_total}%입니다. 100%로 맞춰주세요.')
    elif not energy_ok:
        st.error(f'에너지 합계가 {energy_total}%입니다. 100%로 맞춰주세요.')
    else:
        with st.spinner('시뮬레이션 실행 중...'):
            result, err = run_simulation(
                welfare, education, energy_infra, general_infra, safety,
                solar, hydrogen, ess, external
            )
            if err:
                st.error(err)
            else:
                try:
                    r_obj = Resource(
                        welfare/100, education/100, energy_infra/100,
                        general_infra/100, safety/100
                    )
                    st.session_state.resource_obj = r_obj
                except:
                    pass
                st.session_state.result = result
                label = preset_choice if preset_choice != '직접 입력' \
                    else f'사용자 입력 #{len(st.session_state.history)+1}'
                st.session_state.history[label] = result

# ──────────────────────────────────────────────────
# 메인 헤더
# ──────────────────────────────────────────────────
st.markdown(
    '<h1 style="font-size:28px;font-weight:800;margin-bottom:4px">'
    '🏙️ NOVA시 스마트시티 자원 배분 시뮬레이터</h1>'
    '<p style="color:#7d8590;font-size:14px;margin-top:0">'
    '"기술이 아니라 배분이 도시의 수준을 결정한다"  ·  '
    'Social Science & AI 융합학부 OOP 프로젝트</p>',
    unsafe_allow_html=True
)
st.markdown('---')

# ──────────────────────────────────────────────────
# 결과 없을 때 — 안내 화면
# ──────────────────────────────────────────────────
if st.session_state.result is None:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("""
<div style="text-align:center;padding:60px 0">
    <div style="font-size:64px;margin-bottom:24px">🏙️</div>
    <div style="font-size:20px;font-weight:700;color:#1f2328;margin-bottom:12px">
        시뮬레이션을 시작하세요
    </div>
    <div style="font-size:14px;color:#656d76;line-height:1.8">
        왼쪽 패널에서 예산과 에너지 배분 비율을 설정하고<br>
        <b style="color:#0969da">▶ 시뮬레이션 실행</b> 버튼을 누르면<br>
        NOVA시 5개 구역의 시민 만족도가 실시간으로 산출됩니다.
    </div>
    <div style="margin-top:32px;display:flex;justify-content:center;gap:16px;flex-wrap:wrap">
        <div style="background:#f6f8fa;border:1px solid #d0d7de;border-radius:8px;padding:12px 20px;font-size:13px;color:#656d76">
            💰 예산: 복지·교육·에너지·인프라·안전
        </div>
        <div style="background:#f6f8fa;border:1px solid #d0d7de;border-radius:8px;padding:12px 20px;font-size:13px;color:#656d76">
            ⚡ 에너지: 태양광·수소·ESS·외부전력망
        </div>
        <div style="background:#f6f8fa;border:1px solid #d0d7de;border-radius:8px;padding:12px 20px;font-size:13px;color:#656d76">
            📊 출력: 5개 구역 만족도 + 자립률
        </div>
    </div>
</div>
        """, unsafe_allow_html=True)
    st.stop()

# ──────────────────────────────────────────────────
# 결과 있을 때 — 대시보드 본문
# ──────────────────────────────────────────────────
result = st.session_state.result
resource_obj = st.session_state.resource_obj

tab1, tab2, tab3, tab4 = st.tabs([
    '📊 현황 대시보드',
    '🔬 시나리오 비교',
    '⚙️ 시스템 분석',
    '📖 프로젝트 소개',
])

# ════════════════════════════════════════════════
# TAB 1: 현황 대시보드
# ════════════════════════════════════════════════
with tab1:

    # KPI 카드 행
    rate = result['independence_rate']
    avg  = result['city_average']
    savings = result['savings']
    warnings = result['warnings']

    r_color = 'metric-good'  if rate >= 0.80 else \
              'metric-blue'  if rate >= 0.60 else \
              'metric-warn'  if rate >= 0.40 else 'metric-danger'
    a_color = 'metric-good'  if avg >= 75 else \
              'metric-blue'  if avg >= 60 else \
              'metric-warn'  if avg >= 50 else 'metric-danger'

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
<div class="metric-card">
    <div class="label">도시 평균 만족도</div>
    <div class="value {a_color}">{avg:.1f}점</div>
    <div class="sub">{score_label(avg)}</div>
</div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
<div class="metric-card">
    <div class="label">에너지 자립률</div>
    <div class="value {r_color}">{rate*100:.1f}%</div>
    <div class="sub">목표: 83.13%</div>
</div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
<div class="metric-card">
    <div class="label">절감액 환원</div>
    <div class="value metric-purple">{savings*100:.2f}%</div>
    <div class="sub">복지·교육 재배분</div>
</div>""", unsafe_allow_html=True)
    with c4:
        bonus = energy_to_bonus(rate)
        b_color = 'metric-good' if bonus > 0 else 'metric-danger'
        st.markdown(f"""
<div class="metric-card">
    <div class="label">에너지 만족도 보정</div>
    <div class="value {b_color}">{bonus:+.1f}점</div>
    <div class="sub">자립률 기반 보정값</div>
</div>""", unsafe_allow_html=True)
    with c5:
        n_warn = len(warnings)
        w_color = 'metric-danger' if n_warn > 0 else 'metric-good'
        st.markdown(f"""
<div class="metric-card">
    <div class="label">위험 구역 수</div>
    <div class="value {w_color}">{n_warn}개</div>
    <div class="sub">만족도 50점 미만</div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)

    # 경보 출력
    if warnings:
        for w in warnings:
            st.markdown(f'<div class="alert-danger">🚨 {w}</div>',
                        unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-success">✅ 모든 구역 안전 구간 — 위험 경보 없음</div>',
                    unsafe_allow_html=True)

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    # 차트 행 1
    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.plotly_chart(chart_district_bar(result),
                        use_container_width=True, config={'displayModeBar': False})
    with col_r:
        st.plotly_chart(chart_energy_gauge(rate),
                        use_container_width=True, config={'displayModeBar': False})
        adj = result['adjusted_budget']
        st.markdown(
            f'<div class="alert-info" style="font-size:12px">'
            f'절감액 반영 후 조정 예산<br>'
            f'복지 {adj.welfare*100:.1f}% / 교육 {adj.education*100:.1f}% / '
            f'에너지 {adj.energy_infra*100:.1f}% / 인프라 {adj.general_infra*100:.1f}%</div>',
            unsafe_allow_html=True)

    # 차트 행 2
    col_a, col_b, col_c = st.columns([2, 2, 2])
    with col_a:
        if resource_obj:
            st.plotly_chart(chart_need_radar(result, resource_obj),
                            use_container_width=True, config={'displayModeBar': False})
    with col_b:
        st.plotly_chart(
            chart_budget_pie(welfare, education, energy_infra, general_infra, safety),
            use_container_width=True, config={'displayModeBar': False})
    with col_c:
        st.plotly_chart(chart_energy_pie(solar, hydrogen, ess, external),
                        use_container_width=True, config={'displayModeBar': False})

    # 구역별 상세 테이블
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">구역별 상세 현황</div>',
                unsafe_allow_html=True)

    rows = []
    for k, name in zip(DISTRICT_KEYS, ['A구역 (산업단지)','B구역 (대학가)',
                                        'C구역 (복지타운)','D구역 (신도시)','E구역 (구도심)']):
        s = result['districts'][k]
        rows.append({
            '구역': name,
            '만족도': f'{s:.1f}점',
            '평가': score_label(s),
            '게이지': int(s),
        })
    df = pd.DataFrame(rows)

    def color_row(row):
        s = float(row['만족도'].replace('점',''))
        c = '#ffebe9' if s < 50 else '#dafbe1' if s >= 75 else '#ddf4ff'
        return [f'background-color:{c};color:#1f2328']*len(row)

    st.dataframe(
        df.style.apply(color_row, axis=1),
        use_container_width=True,
        hide_index=True,
    )


# ════════════════════════════════════════════════
# TAB 2: 시나리오 비교
# ════════════════════════════════════════════════
with tab2:
    # 전체 프리셋 자동 계산
    all_results = {}
    preset_labels = ['초기 상태 (인프라 편중)', '복지 집중', '에너지 자립 집중', '균형 배분', '선순환 최적 ⭐']
    for label in preset_labels:
        p = PRESETS[label]
        r, _ = run_simulation(
            p['welfare'], p['education'], p['energy_infra'],
            p['general_infra'], p['safety'],
            p['solar'], p['hydrogen'], p['ess'], p['external']
        )
        if r:
            all_results[label.replace(' ⭐','')] = r

    # 사용자 결과도 추가
    if result:
        all_results['현재 입력'] = result

    st.plotly_chart(chart_scenario_compare(all_results),
                    use_container_width=True, config={'displayModeBar': False})
    st.plotly_chart(chart_district_heatmap(all_results),
                    use_container_width=True, config={'displayModeBar': False})

    # 비교 테이블
    st.markdown('<div class="section-header">시나리오별 수치 비교</div>',
                unsafe_allow_html=True)
    compare_rows = []
    for name, res in all_results.items():
        compare_rows.append({
            '시나리오': name,
            '도시 평균': f"{res['city_average']:.1f}점",
            '자립률': f"{res['independence_rate']*100:.1f}%",
            '절감액': f"{res['savings']*100:.2f}%",
            'A구역': f"{res['districts']['A구역(산업단지)']:.1f}",
            'B구역': f"{res['districts']['B구역(대학가)']:.1f}",
            'C구역': f"{res['districts']['C구역(복지타운)']:.1f}",
            'D구역': f"{res['districts']['D구역(신도시)']:.1f}",
            'E구역': f"{res['districts']['E구역(구도심)']:.1f}",
        })
    st.dataframe(pd.DataFrame(compare_rows), use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════
# TAB 3: 시스템 분석
# ════════════════════════════════════════════════
with tab3:
    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(chart_nonlinear_curve(),
                        use_container_width=True, config={'displayModeBar': False})
        st.markdown("""
<div class="alert-info">
<b>비선형 변환 함수 설명</b><br>
예산 비율이 임계점(20%) 미만이면 서비스가 붕괴 수준으로 하락합니다.
임계점을 넘는 순간 40점 → 60점으로 급상승 (임계점 효과).
초과 투자 구간에서는 한계효용 체감 법칙에 따라 로그함수로 완만하게 증가합니다.
</div>
        """, unsafe_allow_html=True)
    with col_r:
        # 에너지 보정 곡선
        import numpy as np
        rates_x = np.linspace(0, 1, 200)
        bonuses  = [energy_to_bonus(r) for r in rates_x]
        fig_e = go.Figure()
        fig_e.add_trace(go.Scatter(
            x=[r*100 for r in rates_x], y=bonuses,
            mode='lines', line=dict(color=COLORS['yellow'], width=2.5),
            fill='tozeroy', fillcolor='rgba(210,153,34,0.08)',
            hovertemplate='자립률 %{x:.1f}% → 보정 %{y:+.1f}점<extra></extra>',
        ))
        fig_e.add_hline(y=0, line_dash='dash', line_color=COLORS['muted'],
                        line_width=1)
        for rx, label in [(0.40,'40%\n불안정 구간'),(0.60,'60%\n안정 구간'),
                          (0.80,'80%\n자립 달성'),(0.8313,'83.13%\n세종시 목표')]:
            fig_e.add_vline(x=rx*100, line_dash='dot',
                            line_color=COLORS['muted'], line_width=1,
                            annotation_text=label,
                            annotation_font_color=COLORS['muted'],
                            annotation_font_size=9)
        fig_e.update_layout(
            **PLOT_LAYOUT,
            title=dict(text='에너지 자립률 → 만족도 보정 함수', font=dict(size=14)),
            xaxis=dict(title='에너지 자립률 (%)', gridcolor=COLORS['border'],
                       tickfont=dict(color=COLORS['muted'])),
            yaxis=dict(title='보정값 (점)', gridcolor=COLORS['border'],
                       tickfont=dict(color=COLORS['muted'])),
            height=280, showlegend=False,
        )
        st.plotly_chart(fig_e, use_container_width=True,
                        config={'displayModeBar': False})
        st.markdown("""
<div class="alert-info">
<b>에너지 보정 함수 설명</b><br>
자립률 40% 미만: 정전 위험 → 최대 -12점 페널티.
40~60%: 불안정 구간. 60~80%: 안정 구간 (+5~+13점).
80% 이상: 자립 달성 (+13~+20점). 목표: 세종시 83.13%.
</div>
        """, unsafe_allow_html=True)

    st.markdown('---')
    st.markdown('<div class="section-header">OOP 클래스 구조</div>',
                unsafe_allow_html=True)
    st.markdown("""
<div style="background:#161b22;border:1px solid #21262d;border-radius:10px;padding:20px 24px;font-family:monospace;font-size:13px;color:#e6edf3;line-height:1.8">
<span style="color:#bc8cff">Citizen</span> (부모 클래스) — IMD 5개 니즈 벡터 기반<br>
<span style="color:#7d8590">├──</span> <span style="color:#3fb950">Worker</span>      모빌리티(0.38) + 기회(0.27) 중시<br>
<span style="color:#7d8590">├──</span> <span style="color:#3fb950">Student</span>     교육(0.37) + 활동(0.28) 중시<br>
<span style="color:#7d8590">├──</span> <span style="color:#3fb950">Caregiver</span>   건강·안전(0.38) + 거버넌스(0.22) 중시<br>
<span style="color:#7d8590">├──</span> <span style="color:#3fb950">Unemployed</span>  기회(0.42) + 거버넌스(0.25) 중시<br>
<span style="color:#7d8590">└──</span> <span style="color:#3fb950">Elder</span>       건강·안전(0.42) + 모빌리티(0.25) 중시<br>
<br>
<span style="color:#bc8cff">EnergySource</span> (부모 클래스) — generate() 다형성<br>
<span style="color:#7d8590">├──</span> <span style="color:#388bfd">SolarPanel</span>    실효율 70% · 저비용<br>
<span style="color:#7d8590">├──</span> <span style="color:#388bfd">HydrogenCell</span>  실효율 90% · 24시간 안정<br>
<span style="color:#7d8590">├──</span> <span style="color:#388bfd">ESS</span>           충방전 효율 60% · 태양광 보완<br>
<span style="color:#7d8590">└──</span> <span style="color:#388bfd">ExternalGrid</span>  자립률 기여 0%<br>
<br>
<span style="color:#d29922">District</span>         구역 단위 만족도 계산 (4단계 파이프라인)<br>
<span style="color:#d29922">Resource</span>         예산 배분 + <span style="color:#58a6ff">__add__</span> 절감액 재배분<br>
<span style="color:#d29922">EnergyGrid</span>       자립률 계산 + 선순환 절감액 산출<br>
<span style="color:#d29922">City</span>             5개 구역 통합 정책 적용<br>
<span style="color:#d29922">PolicySimulator</span>  시나리오 실행 및 비교
</div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════
# TAB 4: 프로젝트 소개
# ════════════════════════════════════════════════
with tab4:
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("""
### 프로젝트 배경

한국 정부는 제4차 스마트도시 종합계획(2024-2028)을 추진 중이며, 세종시와 부산은
국가시범도시로 지정되어 막대한 기술 인프라에 투자하고 있습니다. 그러나 IMD Smart City
Index 2026 보고서는 기술보다 거버넌스와 배분이 도시 수준을 결정하는 더 강력한
예측 변수임을 보여줍니다.

### 이 프로젝트의 답

> **"예산과 에너지 배분의 방향이 시민의 삶을 결정한다"**

복지를 늘리면 노인은 행복해지지만 근로자는 상대적으로 소외됩니다.
에너지에 투자하면 자립률이 오르고 절감액이 복지로 환원됩니다.
정답은 없습니다. 누구를 위한 도시인가 — 이것이 정책입니다.

### 데이터 출처
- **IMD Smart City Index 2024/2026** — 시민 만족도 5개 니즈 벡터 구조
- **세종시 로렌하우스** — 에너지 자립률 목표값 83.13%
- **부산 에코델타 스마트빌리지** — 에너지원 조합 사례
- **Shin et al. (2025), J.Policy Stud.** — 공급자 중심 정책 비판 근거
        """)
    with col2:
        st.markdown("""
### 시나리오 가이드

| 프리셋 | 특징 |
|--------|------|
| 초기 상태 | 인프라 45% 편중, B구역 위험 |
| 복지 집중 | C구역↑ A구역 상대적↓ |
| 에너지 집중 | 자립률 70%+ 선순환 작동 |
| 균형 배분 | 전 구역 양호, 극적 변화 없음 |
| 선순환 최적 ⭐ | 전체 최고 만족도 달성 |

### 평가 기준 (검증 완료)
- ✅ 시나리오 변화폭 ≥ 5점
- ✅ 에너지-예산 선순환 작동
- ✅ 트레이드오프 방향 현실 반영
- ✅ 선순환 최적이 최고 평균

### 팀 정보
- **한국외국어대학교** Social Science & AI 융합학부
- **과목** 객체지향형 프로그래밍
        """)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
from pathlib import Path

# ─── Page Config ───
st.set_page_config(
    page_title="연희점 2026 시뮬레이터",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS (clean, non-AI look) ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 { font-weight: 700; color: #2C3E50; font-size: 1.8rem !important; }
    h2 { font-weight: 500; color: #34495E; font-size: 1.3rem !important; border-bottom: 2px solid #E8E8E8; padding-bottom: 0.3rem; }
    h3 { font-weight: 500; color: #5D6D7E; font-size: 1.1rem !important; }

    .metric-card {
        background: white;
        border: 1px solid #E8E8E8;
        border-radius: 8px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-label { font-size: 0.8rem; color: #7F8C8D; margin-bottom: 0.3rem; }
    .metric-value { font-size: 1.6rem; font-weight: 700; color: #2C3E50; }
    .metric-delta { font-size: 0.85rem; margin-top: 0.2rem; }
    .positive { color: #27AE60; }
    .negative { color: #E74C3C; }
    .warning { color: #F39C12; }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #E8E8E8;
        border-radius: 6px;
    }

    .sidebar .sidebar-content { background-color: #F8F9FA; }

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #E8E8E8;
        border-radius: 8px;
        padding: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Authentication ───
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown("### 🔐 로그인")
    pw = st.text_input("비밀번호를 입력하세요", type="password", key="pw_input")
    if st.button("로그인", type="primary"):
        try:
            correct = st.secrets["passwords"]["team_password"]
        except:
            correct = "hkd2026"
        if pw == correct:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다.")
    return False

if not check_password():
    st.stop()

# ─── Data ───
MONTHS = ['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월']
CHANNELS = ['소매(일반)', '소매특판', '도매(일반)', '도매(특판)', '인터넷', '아뜰리에힌트']

REVENUE_2024 = {
    '소매(일반)': [67248430,69867140,58631420,44576872,84125007,66044353,51079900,64934646,56693310,46839062,93710642,67907800],
    '소매특판': [5460100,4680750,7682250,9498600,28990300,27291000,18900,11750200,29693100,6474000,7900800,21681900],
    '도매(일반)': [12783300,21530900,40093450,15668980,52124130,20614930,6476370,26362200,16296030,17831880,23740460,29300100],
    '도매(특판)': [122399137,253762908,136009680,49770963,70174595,66299050,60068376,7668597,53291450,27373430,67671132,30149382],
    '인터넷': [46136800,32447650,27366430,23878580,40044650,34947795,32213100,26448554,18425994,62745206,25089168,84404878],
    '아뜰리에힌트': [0]*12,
}
REVENUE_2025 = {
    '소매(일반)': [69744630,70621300,52747150,52859660,51385790,88302500,43938320,50188010,54016370,50133510,55242920,49067240],
    '소매특판': [25101100,16233100,25991400,16619250,41820840,41564100,28638900,6565050,17901830,8633950,20333130,54817000],
    '도매(일반)': [13853410,16426820,26240020,20751270,25168120,73986210,10186630,10529490,13914470,6917020,16732990,11166980],
    '도매(특판)': [44864856,33465477,56603019,21065688,41954124,93218131,11036782,32071814,151012170,126264563,7808339,29191800],
    '인터넷': [37556946,32131780,31441630,29851950,24416640,23476720,25959050,26694640,39186610,37005960,32617250,44137978],
    '아뜰리에힌트': [0]*12,
}

EXPENSES_2025 = {
    '직원급여': 574322700, '퇴직급여': 45140623, '보험료': 6416050,
    '복리후생비': 41901500, '여비교통비': 8059378, '접대비': 6532164,
    '통신비': 8850907, '수도광열비': 3554920, '전력비': 16683208,
    '세금과공과금': 53624450, '지급임차료': 43500000, '수선비': 16169000,
    '차량유지비': 5304854, '교육훈련비': 3659273, '소모품비': 15478149,
    '도서인쇄비': 5413760, '잡비': 88000,
    '운반비': 38687576, '포장비': 29071088, '지급수수료': 62204119,
    '광고선전비': 34552421,
}

LOANS = [
    {'name': '대출1 (변동1년)', 'limit': 300e6, 'balance': 0, 'maturity': '2026-06-19', 'rate': 4.606, 'monthly_interest': 0},
    {'name': '대출2 (변동3월)', 'limit': 350e6, 'balance': 350e6, 'maturity': '2026-04-22', 'rate': 4.390, 'monthly_interest': 1280417},
    {'name': '대출3 (변동3월)', 'limit': 100e6, 'balance': 100e6, 'maturity': '2026-07-01', 'rate': 5.163, 'monthly_interest': 430250},
    {'name': '대출4 (변동3월)', 'limit': 200e6, 'balance': 200e6, 'maturity': '2026-07-30', 'rate': 5.022, 'monthly_interest': 837000},
    {'name': '대출5 (변동3월)', 'limit': 200e6, 'balance': 50e6, 'maturity': '2026-12-09', 'rate': 4.927, 'monthly_interest': 205292},
    {'name': '대출6 (변동3월)', 'limit': 120e6, 'balance': 120e6, 'maturity': '2026-12-15', 'rate': 4.818, 'monthly_interest': 481800},
]

# ─── Session State Init ───
if 'forecast_2026' not in st.session_state:
    st.session_state.forecast_2026 = {ch: list(REVENUE_2025[ch]) for ch in CHANNELS}
if 'actual_2026' not in st.session_state:
    st.session_state.actual_2026 = {ch: [None]*12 for ch in CHANNELS}
if 'cogs_rate' not in st.session_state:
    st.session_state.cogs_rate = 0.63
if 'expense_adj' not in st.session_state:
    st.session_state.expense_adj = {k: 0.0 for k in EXPENSES_2025}

# ─── Helper Functions ───
def fmt(v):
    if v is None or v == 0: return "-"
    if abs(v) >= 1e8: return f"{v/1e8:.1f}억"
    if abs(v) >= 1e4: return f"{v/1e4:.0f}만"
    return f"{v:,.0f}"

def fmt_full(v):
    if v is None: return "-"
    return f"{v:,.0f}"

def calc_channel_pl(channel, forecast):
    revenue = forecast[channel]
    cogs = [r * st.session_state.cogs_rate for r in revenue]
    gross = [r - c for r, c in zip(revenue, cogs)]
    return revenue, cogs, gross

# ─── Sidebar ───
with st.sidebar:
    st.markdown("## ⚙️ 시뮬레이션 설정")
    st.divider()

    st.session_state.cogs_rate = st.slider(
        "매출원가율", 0.50, 0.80, st.session_state.cogs_rate, 0.01, format="%.0f%%",
        help="매출 대비 매출원가 비율"
    )

    st.divider()
    st.markdown("##### 비용 증감률 조정")
    major_expenses = ['직원급여', '지급임차료', '광고선전비', '지급수수료']
    for exp in major_expenses:
        st.session_state.expense_adj[exp] = st.slider(
            exp, -30, 30, int(st.session_state.expense_adj[exp]), 1,
            format="%d%%", key=f"adj_{exp}"
        )

    st.divider()
    st.caption("한국도자기특판(주) 연희점")
    st.caption("2026 재무 시뮬레이터 v1.0")

# ─── Main Content ───
st.markdown("# 연희점 2026 재무 시뮬레이터")

tab_dash, tab_rev, tab_pl, tab_cf, tab_debt = st.tabs([
    "📊 대시보드", "💰 매출 예측", "📋 손익계산서", "💵 현금흐름", "🏦 차입금"
])

# ═══════════════════════════════════════
# TAB 1: 대시보드
# ═══════════════════════════════════════
with tab_dash:
    forecast = st.session_state.forecast_2026

    total_2025 = sum(sum(REVENUE_2025[ch]) for ch in CHANNELS)
    total_2026f = sum(sum(forecast[ch]) for ch in CHANNELS)
    total_cogs = total_2026f * st.session_state.cogs_rate
    total_gross = total_2026f - total_cogs
    total_expense = sum(v * (1 + st.session_state.expense_adj.get(k, 0)/100) for k, v in EXPENSES_2025.items())
    total_op_income = total_gross - total_expense

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("2026 예상 매출", fmt(total_2026f), f"{(total_2026f/total_2025-1)*100:+.1f}% vs 2025")
    with col2:
        st.metric("매출총이익", fmt(total_gross), f"마진 {total_gross/total_2026f*100:.1f}%")
    with col3:
        delta_color = "normal" if total_op_income >= 0 else "inverse"
        st.metric("영업이익", fmt(total_op_income), f"{'흑자' if total_op_income>=0 else '적자'}", delta_color=delta_color)
    with col4:
        monthly_interest = sum(l['monthly_interest'] for l in LOANS)
        st.metric("월 이자비용", fmt(monthly_interest * 12), f"월 {fmt(monthly_interest)}")

    st.divider()

    # Channel breakdown chart
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("## 채널별 매출 비교")
        ch_data = []
        for ch in CHANNELS:
            ch_data.append({'채널': ch, '2024': sum(REVENUE_2024[ch]), '2025': sum(REVENUE_2025[ch]), '2026(예상)': sum(forecast[ch])})
        df_ch = pd.DataFrame(ch_data)

        fig = go.Figure()
        for year, color in [('2024', '#BDC3C7'), ('2025', '#7FB3D8'), ('2026(예상)', '#2C3E50')]:
            fig.add_trace(go.Bar(name=year, x=df_ch['채널'], y=df_ch[year],
                                marker_color=color, text=[fmt(v) for v in df_ch[year]], textposition='outside'))
        fig.update_layout(barmode='group', height=400, margin=dict(t=30,b=30),
                         font=dict(family="Noto Sans KR"), plot_bgcolor='white',
                         yaxis=dict(gridcolor='#F0F0F0'))
        st.plotly_chart(fig, use_container_width=True)

    with col_chart2:
        st.markdown("## 월별 매출 추이")
        monthly_totals = {
            '2024': [sum(REVENUE_2024[ch][m] for ch in CHANNELS) for m in range(12)],
            '2025': [sum(REVENUE_2025[ch][m] for ch in CHANNELS) for m in range(12)],
            '2026(예상)': [sum(forecast[ch][m] for ch in CHANNELS) for m in range(12)],
        }

        fig2 = go.Figure()
        for year, color, dash in [('2024', '#BDC3C7', 'dot'), ('2025', '#7FB3D8', 'dash'), ('2026(예상)', '#2C3E50', 'solid')]:
            fig2.add_trace(go.Scatter(x=MONTHS, y=monthly_totals[year], name=year,
                                     line=dict(color=color, width=2.5, dash=dash), mode='lines+markers'))
        fig2.update_layout(height=400, margin=dict(t=30,b=30), font=dict(family="Noto Sans KR"),
                          plot_bgcolor='white', yaxis=dict(gridcolor='#F0F0F0'))
        st.plotly_chart(fig2, use_container_width=True)

    # Alert section
    st.markdown("## 경보 시그널")
    loan_balance = sum(l['balance'] for l in LOANS)
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        if total_op_income < 0:
            st.error(f"⚠️ 영업적자 예상: {fmt(total_op_income)}")
        else:
            st.success(f"✅ 영업흑자: {fmt(total_op_income)}")
    with col_a2:
        st.warning(f"🏦 차입금 잔액: {fmt(loan_balance)} (월이자 {fmt(monthly_interest)})")
    with col_a3:
        upcoming = [l for l in LOANS if l['balance'] > 0 and '2026-0' in l['maturity'][:7]]
        if upcoming:
            st.error(f"📅 상반기 만기 도래: {len(upcoming)}건")
        else:
            st.info("📅 상반기 만기 없음")

# ═══════════════════════════════════════
# TAB 2: 매출 예측
# ═══════════════════════════════════════
with tab_rev:
    st.markdown("## 채널별 매출 예측")
    st.caption("2026년 예상 금액을 수정하면 전체 시뮬레이션이 자동 업데이트됩니다.")

    selected_ch = st.selectbox("채널 선택", CHANNELS, key="rev_channel")

    df_rev = pd.DataFrame({
        '월': MONTHS,
        '2024 실적': REVENUE_2024[selected_ch],
        '2025 실적': REVENUE_2025[selected_ch],
        '2026 예상': st.session_state.forecast_2026[selected_ch],
    })
    df_rev['YoY (25→26)'] = [(f-p)/p*100 if p > 0 else 0 for f, p in zip(df_rev['2026 예상'], df_rev['2025 실적'])]

    edited = st.data_editor(
        df_rev,
        column_config={
            '월': st.column_config.TextColumn(disabled=True),
            '2024 실적': st.column_config.NumberColumn(format="%d", disabled=True),
            '2025 실적': st.column_config.NumberColumn(format="%d", disabled=True),
            '2026 예상': st.column_config.NumberColumn(format="%d"),
            'YoY (25→26)': st.column_config.NumberColumn(format="%.1f%%", disabled=True),
        },
        hide_index=True,
        use_container_width=True,
        key=f"editor_{selected_ch}"
    )

    st.session_state.forecast_2026[selected_ch] = edited['2026 예상'].tolist()

    # Summary
    st.divider()
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("2024 합계", fmt(sum(REVENUE_2024[selected_ch])))
    with col_s2:
        st.metric("2025 합계", fmt(sum(REVENUE_2025[selected_ch])))
    with col_s3:
        f26 = sum(st.session_state.forecast_2026[selected_ch])
        f25 = sum(REVENUE_2025[selected_ch])
        st.metric("2026 예상", fmt(f26), f"{(f26/f25-1)*100:+.1f}%" if f25 > 0 else "N/A")

# ═══════════════════════════════════════
# TAB 3: 손익계산서
# ═══════════════════════════════════════
with tab_pl:
    st.markdown("## 채널별 손익계산서")

    view_mode = st.radio("보기", ["합산", "채널별"], horizontal=True, key="pl_view")

    if view_mode == "합산":
        channels_to_show = ['합산']
    else:
        channels_to_show = CHANNELS

    for ch_name in channels_to_show:
        if ch_name == '합산':
            rev = [sum(st.session_state.forecast_2026[c][m] for c in CHANNELS) for m in range(12)]
        else:
            rev = st.session_state.forecast_2026[ch_name]

        cogs = [r * st.session_state.cogs_rate for r in rev]
        gross = [r - c for r, c in zip(rev, cogs)]

        # Simplified expense allocation (proportional)
        total_rev_all = sum(sum(st.session_state.forecast_2026[c]) for c in CHANNELS)
        ch_share = sum(rev) / total_rev_all if total_rev_all > 0 else 1/6
        if ch_name == '합산':
            ch_share = 1.0

        monthly_expense = sum(v * (1 + st.session_state.expense_adj.get(k, 0)/100) for k, v in EXPENSES_2025.items()) / 12 * ch_share
        expenses = [monthly_expense] * 12
        op_income = [g - e for g, e in zip(gross, expenses)]

        with st.expander(f"**{ch_name}**  |  매출 {fmt(sum(rev))}  |  영업이익 {fmt(sum(op_income))}", expanded=(ch_name=='합산')):
            df_pl = pd.DataFrame({
                '항목': ['매출액', '매출원가', '매출총이익', '판관비', '영업이익'],
                **{MONTHS[m]: [rev[m], cogs[m], gross[m], expenses[m], op_income[m]] for m in range(12)},
                '합계': [sum(rev), sum(cogs), sum(gross), sum(expenses), sum(op_income)],
            })

            st.dataframe(
                df_pl.style.format({col: '{:,.0f}' for col in df_pl.columns if col != '항목'})
                    .apply(lambda x: ['font-weight: bold' if x['항목'] in ['매출총이익','영업이익'] else '' for _ in x], axis=1),
                use_container_width=True,
                hide_index=True
            )

# ═══════════════════════════════════════
# TAB 4: 현금흐름
# ═══════════════════════════════════════
with tab_cf:
    st.markdown("## 월별 현금흐름 예측")

    initial_cash = st.number_input("기초 현금잔고 (원)", value=0, step=10000000, format="%d", key="init_cash")

    forecast = st.session_state.forecast_2026
    monthly_interest = sum(l['monthly_interest'] for l in LOANS)
    total_expense_annual = sum(v * (1 + st.session_state.expense_adj.get(k, 0)/100) for k, v in EXPENSES_2025.items())

    cf_data = []
    running_cash = initial_cash
    for m in range(12):
        rev_m = sum(forecast[ch][m] for ch in CHANNELS)
        cogs_m = rev_m * st.session_state.cogs_rate
        expense_m = total_expense_annual / 12

        inflow = rev_m
        outflow = cogs_m + expense_m + monthly_interest
        net = inflow - outflow
        running_cash += net

        status = "양호" if running_cash > 50e6 else ("주의" if running_cash > 0 else "위험")

        cf_data.append({
            '월': MONTHS[m],
            '매출유입': rev_m,
            '매입+비용': cogs_m + expense_m,
            '이자비용': monthly_interest,
            '순현금': net,
            '누적잔고': running_cash,
            '상태': status,
        })

    df_cf = pd.DataFrame(cf_data)

    # Chart
    fig_cf = go.Figure()
    fig_cf.add_trace(go.Bar(name='순현금', x=MONTHS, y=df_cf['순현금'],
                           marker_color=['#27AE60' if v >= 0 else '#E74C3C' for v in df_cf['순현금']]))
    fig_cf.add_trace(go.Scatter(name='누적잔고', x=MONTHS, y=df_cf['누적잔고'],
                               line=dict(color='#2C3E50', width=3), mode='lines+markers'))
    fig_cf.update_layout(height=350, margin=dict(t=30,b=30), font=dict(family="Noto Sans KR"),
                        plot_bgcolor='white', yaxis=dict(gridcolor='#F0F0F0'))
    st.plotly_chart(fig_cf, use_container_width=True)

    st.dataframe(
        df_cf.style.format({
            '매출유입': '{:,.0f}', '매입+비용': '{:,.0f}', '이자비용': '{:,.0f}',
            '순현금': '{:,.0f}', '누적잔고': '{:,.0f}'
        }).apply(lambda x: ['background-color: #FADBD8' if x['상태'] == '위험'
                            else 'background-color: #FCF3CF' if x['상태'] == '주의'
                            else '' for _ in x], axis=1),
        use_container_width=True, hide_index=True
    )

# ═══════════════════════════════════════
# TAB 5: 차입금
# ═══════════════════════════════════════
with tab_debt:
    st.markdown("## 기업은행 차입금 현황")
    st.caption("2026.03.03 기준")

    df_loans = pd.DataFrame(LOANS)
    df_loans.columns = ['대출명', '한도', '잔액', '만기일', '이율(%)', '금리종류', '월이자']

    st.dataframe(
        df_loans.style.format({
            '한도': '{:,.0f}', '잔액': '{:,.0f}', '월이자': '{:,.0f}', '이율(%)': '{:.3f}'
        }),
        use_container_width=True, hide_index=True
    )

    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        st.metric("총 잔액", fmt(sum(l['balance'] for l in LOANS)))
    with col_d2:
        st.metric("월 이자 합계", fmt(sum(l['monthly_interest'] for l in LOANS)))
    with col_d3:
        st.metric("연 이자 추정", fmt(sum(l['monthly_interest'] for l in LOANS) * 12))

    # Maturity timeline
    st.markdown("### 만기 일정")
    for loan in sorted(LOANS, key=lambda x: x['maturity']):
        if loan['balance'] > 0:
            st.markdown(f"- **{loan['maturity']}** | {loan['name']} | 잔액 {fmt(loan['balance'])}")

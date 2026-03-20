import streamlit as st
import pandas as pd
 
st.set_page_config(page_title="연희점 2026", page_icon="📊", layout="wide")
 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
h1 { font-weight: 700; color: #2C3E50; }
h2 { font-weight: 500; color: #34495E; border-bottom: 2px solid #eee; padding-bottom: 4px; }
</style>
""", unsafe_allow_html=True)
 
# Auth
if "auth" not in st.session_state:
    st.session_state.auth = False
if not st.session_state.auth:
    st.markdown("### 로그인")
    pw = st.text_input("비밀번호", type="password")
    if st.button("로그인", type="primary"):
        if pw == "hkd2026":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("비밀번호 오류")
    st.stop()
 
# Data
MONTHS = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
CHANNELS = ["소매(일반)","소매특판","도매(일반)","도매(특판)","인터넷","아뜰리에힌트"]
 
R24 = {
    "소매(일반)":[67248430,69867140,58631420,44576872,84125007,66044353,51079900,64934646,56693310,46839062,93710642,67907800],
    "소매특판":[5460100,4680750,7682250,9498600,28990300,27291000,18900,11750200,29693100,6474000,7900800,21681900],
    "도매(일반)":[12783300,21530900,40093450,15668980,52124130,20614930,6476370,26362200,16296030,17831880,23740460,29300100],
    "도매(특판)":[122399137,253762908,136009680,49770963,70174595,66299050,60068376,7668597,53291450,27373430,67671132,30149382],
    "인터넷":[46136800,32447650,27366430,23878580,40044650,34947795,32213100,26448554,18425994,62745206,25089168,84404878],
    "아뜰리에힌트":[0]*12,
}
R25 = {
    "소매(일반)":[69744630,70621300,52747150,52859660,51385790,88302500,43938320,50188010,54016370,50133510,55242920,49067240],
    "소매특판":[25101100,16233100,25991400,16619250,41820840,41564100,28638900,6565050,17901830,8633950,20333130,54817000],
    "도매(일반)":[13853410,16426820,26240020,20751270,25168120,73986210,10186630,10529490,13914470,6917020,16732990,11166980],
    "도매(특판)":[44864856,33465477,56603019,21065688,41954124,93218131,11036782,32071814,151012170,126264563,7808339,29191800],
    "인터넷":[37556946,32131780,31441630,29851950,24416640,23476720,25959050,26694640,39186610,37005960,32617250,44137978],
    "아뜰리에힌트":[0]*12,
}
 
EXP = {"직원급여":574322700,"퇴직급여":45140623,"복리후생비":41901500,"운반비":38687576,
    "포장비":29071088,"지급수수료":62204119,"광고선전비":34552421,"세금과공과금":53624450,
    "지급임차료":43500000,"전력비":16683208,"수선비":16169000,"소모품비":15478149,
    "통신비":8850907,"여비교통비":8059378,"접대비":6532164,"보험료":6416050,
    "차량유지비":5304854,"교육훈련비":3659273,"도서인쇄비":5413760,"잡비":88000}
 
LOANS = [
    {"name":"대출1(변동1년)","balance":0,"maturity":"2026-06-19","rate":4.606,"interest":0},
    {"name":"대출2(변동3월)","balance":350000000,"maturity":"2026-04-22","rate":4.390,"interest":1280417},
    {"name":"대출3(변동3월)","balance":100000000,"maturity":"2026-07-01","rate":5.163,"interest":430250},
    {"name":"대출4(변동3월)","balance":200000000,"maturity":"2026-07-30","rate":5.022,"interest":837000},
    {"name":"대출5(변동3월)","balance":50000000,"maturity":"2026-12-09","rate":4.927,"interest":205292},
    {"name":"대출6(변동3월)","balance":120000000,"maturity":"2026-12-15","rate":4.818,"interest":481800},
]
 
def fmt(v):
    if v is None or v == 0: return "-"
    if abs(v) >= 1e8: return f"{v/1e8:.1f}억"
    if abs(v) >= 1e4: return f"{v/1e4:,.0f}만"
    return f"{v:,.0f}"
 
# Session state
if "fc" not in st.session_state:
    st.session_state.fc = {ch: list(R25[ch]) for ch in CHANNELS}
if "cogs" not in st.session_state:
    st.session_state.cogs = 0.63
 
# Sidebar
with st.sidebar:
    st.markdown("## 설정")
    st.session_state.cogs = st.slider("매출원가율", 0.50, 0.80, 0.63, 0.01)
    st.divider()
    exp_adj = st.slider("판관비 증감률(%)", -30, 30, 0, 1)
    st.divider()
    st.caption("한국도자기특판(주) 연희점")
 
# Main
st.markdown("# 연희점 2026 재무 시뮬레이터")
 
tab1, tab2, tab3, tab4 = st.tabs(["📊 대시보드", "💰 매출", "📋 손익", "🏦 차입금"])
 
# ── 대시보드 ──
with tab1:
    fc = st.session_state.fc
    t25 = sum(sum(R25[c]) for c in CHANNELS)
    t26 = sum(sum(fc[c]) for c in CHANNELS)
    cogs_total = t26 * st.session_state.cogs
    gross = t26 - cogs_total
    exp_total = sum(EXP.values()) * (1 + exp_adj/100)
    op = gross - exp_total
    mi = sum(l["interest"] for l in LOANS)
 
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("2026 매출", fmt(t26), f"{(t26/t25-1)*100:+.1f}% vs 25")
    c2.metric("매출총이익", fmt(gross), f"마진 {gross/t26*100:.1f}%")
    c3.metric("영업이익", fmt(op), "흑자" if op>=0 else "적자")
    c4.metric("월 이자", fmt(mi), f"연 {fmt(mi*12)}")
 
    st.divider()
    st.markdown("## 채널별 연간 매출")
    rows = []
    for ch in CHANNELS:
        rows.append({"채널":ch, "2024":sum(R24[ch]), "2025":sum(R25[ch]), "2026(예상)":sum(fc[ch])})
    df = pd.DataFrame(rows)
    df["증감(25→26)"] = df.apply(lambda r: f"{(r['2026(예상)']/r['2025']-1)*100:+.1f}%" if r['2025']>0 else "-", axis=1)
    st.dataframe(df.style.format({"2024":"{:,.0f}","2025":"{:,.0f}","2026(예상)":"{:,.0f}"}), hide_index=True, use_container_width=True)
 
    st.divider()
    st.markdown("## 경보")
    loan_bal = sum(l["balance"] for l in LOANS)
    ec1,ec2,ec3 = st.columns(3)
    if op < 0:
        ec1.error(f"영업적자 {fmt(op)}")
    else:
        ec1.success(f"영업흑자 {fmt(op)}")
    ec2.warning(f"차입금 {fmt(loan_bal)} (월이자 {fmt(mi)})")
    soon = [l for l in LOANS if l["balance"]>0 and l["maturity"]<"2026-07"]
    if soon:
        ec3.error(f"상반기 만기 {len(soon)}건")
    else:
        ec3.info("상반기 만기 없음")
 
# ── 매출 ──
with tab2:
    st.markdown("## 채널별 매출 예측 (수정 가능)")
    sel = st.selectbox("채널", CHANNELS)
    df_r = pd.DataFrame({"월":MONTHS, "2024":R24[sel], "2025":R25[sel], "2026예상":st.session_state.fc[sel]})
    df_r["증감(%)"] = df_r.apply(lambda r: round((r["2026예상"]/r["2025"]-1)*100,1) if r["2025"]>0 else 0, axis=1)
 
    edited = st.data_editor(df_r, column_config={
        "월": st.column_config.TextColumn(disabled=True),
        "2024": st.column_config.NumberColumn(format="%d", disabled=True),
        "2025": st.column_config.NumberColumn(format="%d", disabled=True),
        "2026예상": st.column_config.NumberColumn(format="%d"),
        "증감(%)": st.column_config.NumberColumn(format="%.1f", disabled=True),
    }, hide_index=True, use_container_width=True)
 
    st.session_state.fc[sel] = edited["2026예상"].tolist()
 
    sc1,sc2,sc3 = st.columns(3)
    sc1.metric("2024", fmt(sum(R24[sel])))
    sc2.metric("2025", fmt(sum(R25[sel])))
    v26 = sum(st.session_state.fc[sel])
    v25 = sum(R25[sel])
    sc3.metric("2026", fmt(v26), f"{(v26/v25-1)*100:+.1f}%" if v25>0 else "")
 
# ── 손익 ──
with tab3:
    st.markdown("## 손익계산서")
    mode = st.radio("보기", ["합산","채널별"], horizontal=True)
 
    targets = ["합산"] if mode=="합산" else CHANNELS
    for ch in targets:
        if ch == "합산":
            rev = [sum(st.session_state.fc[c][m] for c in CHANNELS) for m in range(12)]
        else:
            rev = st.session_state.fc[ch]
 
        cogs_m = [r * st.session_state.cogs for r in rev]
        gross_m = [r-c for r,c in zip(rev, cogs_m)]
        total_rev = sum(sum(st.session_state.fc[c]) for c in CHANNELS)
        share = sum(rev)/total_rev if total_rev>0 else 1/6
        if ch == "합산": share = 1.0
        exp_m = [sum(EXP.values())*(1+exp_adj/100)/12*share]*12
        op_m = [g-e for g,e in zip(gross_m, exp_m)]
 
        with st.expander(f"**{ch}** | 매출 {fmt(sum(rev))} | 영업이익 {fmt(sum(op_m))}", expanded=(ch=="합산")):
            data = {"항목":["매출","매출원가","매출총이익","판관비","영업이익"]}
            for i,m in enumerate(MONTHS):
                data[m] = [rev[i], cogs_m[i], gross_m[i], exp_m[i], op_m[i]]
            data["합계"] = [sum(rev),sum(cogs_m),sum(gross_m),sum(exp_m),sum(op_m)]
            df_pl = pd.DataFrame(data)
            fmt_cols = {c:"{:,.0f}" for c in df_pl.columns if c != "항목"}
            st.dataframe(df_pl.style.format(fmt_cols), hide_index=True, use_container_width=True)
 
# ── 차입금 ──
with tab4:
    st.markdown("## 기업은행 차입금 (2026.03 기준)")
    rows_l = []
    for l in LOANS:
        rows_l.append({"대출명":l["name"],"잔액":l["balance"],"만기일":l["maturity"],"이율":f'{l["rate"]:.3f}%',"월이자":l["interest"]})
    df_l = pd.DataFrame(rows_l)
    st.dataframe(df_l.style.format({"잔액":"{:,.0f}","월이자":"{:,.0f}"}), hide_index=True, use_container_width=True)
 
    lc1,lc2,lc3 = st.columns(3)
    lc1.metric("총 잔액", fmt(sum(l["balance"] for l in LOANS)))
    lc2.metric("월 이자", fmt(sum(l["interest"] for l in LOANS)))
    lc3.metric("연 이자", fmt(sum(l["interest"] for l in LOANS)*12))
 
    st.markdown("### 만기 일정")
    for l in sorted(LOANS, key=lambda x:x["maturity"]):
        if l["balance"]>0:
            st.markdown(f"- **{l['maturity']}** | {l['name']} | 잔액 {fmt(l['balance'])}")
 

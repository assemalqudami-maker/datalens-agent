import asyncio
import hmac
import os
import secrets
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from datalens.agent import Agent
from datalens.config import Settings
from datalens.data import load_csv, upload
from datalens.provider import ConfigurationError, Gemini
from datalens.results_view import (
    chart_for_evidence,
    evidence_preview,
    key_facts,
    metric_card_html,
    render_answer_html,
)
from datalens.storage import Store, scope_id

load_dotenv()
st.set_page_config(page_title="DataLens Agent | محلّل البيانات", page_icon="◈", layout="wide")
st.markdown("""<style>
:root {--ink:#202542;--muted:#737b95;--line:#e8e9f3;--purple:#6458e8;--purple-light:#efedff;--green:#238b79}
html,body,[class*="css"],.stApp {font-family:Inter,"Segoe UI",Tahoma,Arial,sans-serif}
.stApp {background:radial-gradient(ellipse at 70% -14%,#edebff 0%,transparent 34%),linear-gradient(180deg,#fafbff 0%,#f6f8fd 100%);color:var(--ink)}
[data-testid="stHeader"] {background:transparent}
.block-container {max-width:1310px;padding-top:1.45rem;padding-bottom:5rem}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#ffffff 0%,#f8f8ff 100%);border-right:1px solid #e9eaf2}
[data-testid="stSidebar"] .block-container {padding-top:1.6rem}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {line-height:1.65}
.brand {display:flex;align-items:center;gap:11px;margin:0 0 8px}
.brand-mark {display:grid;place-items:center;width:43px;height:43px;background:linear-gradient(145deg,#7f70ff,#5045c8);border-radius:14px;color:white;font-size:25px;font-weight:700;box-shadow:0 7px 20px #6558df35}
.brand strong {display:block;font-size:1.2rem;line-height:1.2;letter-spacing:-.5px;color:#252341}
.brand small {display:block;font-size:.7rem;letter-spacing:2px;color:#8587aa;font-weight:700}
.sidebar-caption {color:#8187a0;font-size:.79rem;line-height:1.7}
.side-section {font-size:.72rem;font-weight:800;letter-spacing:1.3px;color:#979ab0;text-transform:uppercase;margin:8px 0 1px}
.status-pill {display:inline-flex;align-items:center;gap:7px;padding:8px 12px;border-radius:30px;font-size:.8rem;font-weight:700}
.status-pill.good {background:#e8f7f0;color:#18816d}
.status-pill.warn {background:#fff1e9;color:#ae6237}
.status-dot {width:7px;height:7px;background:currentColor;border-radius:50%}
.hero {position:relative;overflow:hidden;display:flex;align-items:center;min-height:262px;border-radius:26px;background:radial-gradient(circle at 85% 30%,#50429d 0%,transparent 37%),linear-gradient(110deg,#26214d 0%,#36306f 64%,#5b4ed2 100%);color:#fff;padding:40px 46px;margin:8px 0 26px;box-shadow:0 18px 38px #322a712c;animation:riseIn .65s ease both}
.hero::after {content:"";position:absolute;right:-45px;top:-90px;width:380px;height:380px;border:1px solid #ffffff2a;border-radius:40%;transform:rotate(30deg);animation:orbit 24s linear infinite;pointer-events:none}
.hero::before {content:"";position:absolute;right:110px;bottom:-155px;width:350px;height:350px;background:radial-gradient(circle,#968af965,transparent 65%);animation:floatGlow 8s ease-in-out infinite;pointer-events:none}
.hero-copy {position:relative;z-index:2;max-width:780px}
.hero .eyebrow {color:#c9c2ff;font-size:11px;letter-spacing:2.2px;font-weight:800;text-transform:uppercase}
.hero h1 {font-size:clamp(1.95rem,3.35vw,3.25rem);font-weight:800;color:#fff;letter-spacing:-1.25px;line-height:1.3;margin:11px 0}
.hero p {color:#e2dfff;font-size:1rem;max-width:665px;line-height:1.9;margin:0 0 18px}
.hero-badges {display:flex;flex-wrap:wrap;gap:10px}
.hero-badge {display:inline-flex;gap:7px;align-items:center;padding:6px 12px;background:#ffffff1d;color:#fff;border:1px solid #ffffff30;border-radius:50px;font-size:.78rem;font-weight:600;backdrop-filter:blur(7px)}
.hero-orb {position:absolute;right:11%;top:15%;width:135px;height:135px;border-radius:35px;transform:rotate(-19deg);border:1px solid #ffffff45;background:linear-gradient(145deg,#ffffff28,#ffffff05);box-shadow:0 30px 60px #18133566,inset 0 1px 2px #ffffff50;animation:orbFloat 7s ease-in-out infinite}
.hero-orb::after {content:"✦";position:absolute;top:34px;left:44px;font-size:54px;color:#c2baff;text-shadow:0 0 32px #cfc8ff}
.section-intro {display:flex;justify-content:space-between;align-items:center;gap:16px;margin:0 0 15px}
.section-heading {font-size:1.16rem;font-weight:800;color:#252341;margin:0}
.section-subtitle {font-size:.79rem;color:#80849e;margin-top:4px}
.step-ribbon {display:flex;flex-wrap:wrap;gap:10px;margin:0 0 17px}
.step-chip {padding:8px 12px;background:#fff;border:1px solid #ececf5;border-radius:12px;font-size:.76rem;color:#6a6f8c;font-weight:650;box-shadow:0 4px 14px #1f28540a}
.step-chip b {color:#6458e8;margin-inline-end:6px}
.st-key-upload_panel [data-testid="stVerticalBlockBorderWrapper"],
.st-key-query_panel [data-testid="stVerticalBlockBorderWrapper"] {border:1px solid #e8e9f4;border-radius:22px;background:#fff;box-shadow:0 11px 27px #2627540c}
.st-key-upload_panel [data-testid="stVerticalBlockBorderWrapper"] > div,
.st-key-query_panel [data-testid="stVerticalBlockBorderWrapper"] > div {padding:10px 8px}
.st-key-upload_panel,.st-key-query_panel {animation:riseIn .65s ease both}
.st-key-query_panel {animation-delay:.09s}
.st-key-upload_panel h3,.st-key-query_panel h3 {font-size:1.08rem;color:#292748;font-weight:800}
[data-testid="stFileUploader"] {border-radius:16px}
[data-testid="stFileUploaderDropzone"] {border:1.5px dashed #c8c2fa;border-radius:15px;background:#fbfaff;transition:border-color .2s,background .2s}
[data-testid="stFileUploaderDropzone"]:hover {border-color:#8174ea;background:#f4f1ff}
[data-testid="stDataFrame"] {border:1px solid #eef0f6;border-radius:12px;overflow:hidden}
.stButton>button {border-radius:12px;border:1px solid #e5e4f2;font-weight:750;min-height:43px;transition:transform .2s,box-shadow .2s,border-color .2s}
.stButton>button:hover {transform:translateY(-2px);box-shadow:0 7px 17px #40368817;border-color:#8176e6}
.stButton>button[kind="primary"] {border:0;color:#fff;background:linear-gradient(100deg,#6458e8,#7b68ee);box-shadow:0 7px 19px #6558de32}
.stTextArea textarea,.stTextInput input {border-radius:13px!important;border-color:#e6e6f0!important;background:#fdfdff!important;transition:box-shadow .2s,border-color .2s}
.stTextArea textarea:focus,.stTextInput input:focus {box-shadow:0 0 0 3px #6458e822!important;border-color:#8175e7!important}
div[data-testid="stMetric"] {background:#fff;border:1px solid #e8e9f3;border-radius:17px;padding:17px;box-shadow:0 7px 18px #2627540a}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {color:#41378f;font-size:1.35rem}
[data-testid="stTabs"] [data-baseweb="tab-list"] {gap:8px;border-bottom:1px solid #e8e9f1}
[data-testid="stTabs"] button[data-baseweb="tab"] {border-radius:11px 11px 0 0;color:#8587a0;font-weight:700}
[data-testid="stTabs"] button[aria-selected="true"] {color:#6659e8;background:#f1efff}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {background:#6659e8}
[data-testid="stExpander"] {background:#fff;border:1px solid #e9eaf3;border-radius:14px;overflow:hidden}
[data-testid="stAlert"] {border-radius:13px}
.stDownloadButton>button {border-radius:11px}
@keyframes riseIn {from {opacity:0;transform:translateY(13px)}to {opacity:1;transform:translateY(0)}}
@keyframes floatGlow {50% {transform:translate(13px,-20px);opacity:.7}}
@keyframes orbFloat {50% {transform:translateY(-14px) rotate(-9deg)}}
@keyframes orbit {to {transform:rotate(390deg)}}
@media (max-width:1000px) {.hero-orb {opacity:.25;right:5%}.hero {padding:32px 28px;min-height:230px}.block-container {padding-inline:1rem}}
@media (max-width:650px) {.hero {padding:26px 22px;border-radius:19px}.hero h1 {font-size:1.9rem}.hero-orb {display:none}.hero-badge {font-size:.67rem}.step-ribbon {gap:6px}.step-chip {font-size:.7rem}.block-container {padding-top:.75rem}}
@media (prefers-reduced-motion:reduce) {.hero,.hero::before,.hero::after,.hero-orb,.st-key-upload_panel,.st-key-query_panel {animation:none!important}.stButton>button,.stTextArea textarea,.stTextInput input {transition:none!important}.stButton>button:hover {transform:none}}

/* DataLens result system */
.results-heading {margin:28px 0 16px}
.results-overline {color:#7364d8;font-size:.73rem;letter-spacing:1.5px;font-weight:850}
.results-heading h2 {margin:5px 0 5px;font-size:1.4rem;font-weight:850;color:#272449}
.results-heading p {margin:0;color:#83869e;font-size:.85rem;line-height:1.7}
.kpi-card {min-height:134px;position:relative;overflow:hidden;padding:18px;border-radius:20px;background:linear-gradient(145deg,#f4f0ff,#fff);color:#574c9c;border:1px solid #e7e2fc;box-shadow:0 10px 24px #4b408418;transition:transform .22s ease,box-shadow .22s ease;animation:riseIn .55s ease both}
.kpi-card:hover {transform:translateY(-5px);box-shadow:0 16px 30px #6255b329}
.kpi-card:after {content:"";position:absolute;inset:auto -40px -85px auto;width:160px;height:160px;border-radius:50%;border:28px solid #998cff12}
.kpi-main {background:linear-gradient(125deg,#685be8,#8173f6);border-color:transparent;color:#fff}
.kpi-soft {background:linear-gradient(145deg,#f1edff,#fbfaff);color:#51459a}
.kpi-deep {background:linear-gradient(125deg,#433581,#6e60cf);border-color:transparent;color:#fff}
.kpi-neutral {background:linear-gradient(145deg,#fff,#f2efff);color:#5b4ba5}
.kpi-top {display:flex;justify-content:space-between;gap:8px;align-items:start}
.kpi-label {font-size:.76rem;font-weight:750;line-height:1.6;opacity:.86}
.kpi-icon {width:30px;height:30px;display:grid;place-items:center;border-radius:10px;background:#ffffff24;font-size:16px;flex-shrink:0}
.kpi-soft .kpi-icon,.kpi-neutral .kpi-icon {background:#ddd7ff}
.kpi-value {margin-top:18px;font-size:clamp(1.1rem,2vw,1.65rem);font-weight:850;line-height:1.3;letter-spacing:-.3px;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.quick-facts {display:flex;gap:9px;flex-wrap:wrap;margin:14px 0 18px}
.fact-chip {display:inline-flex;gap:8px;align-items:center;background:#fff;border:1px solid #e4e2f6;border-radius:13px;padding:10px 13px;color:#55527d;font-size:.81rem;box-shadow:0 5px 13px #4b40840b}
.fact-chip strong {color:#5d4bd4;font-variant-numeric:tabular-nums}
.answer-header {display:flex;align-items:center;justify-content:space-between;gap:9px;margin:25px 0 11px}
.answer-title {display:flex;align-items:center;gap:9px;color:#302858;font-size:1.08rem;font-weight:850}
.answer-title-icon {display:grid;place-items:center;width:32px;height:32px;border-radius:10px;background:#ece8ff;color:#6555d6}
.answer-label {padding:6px 10px;border-radius:30px;background:#f0edff;color:#7467bd;font-size:.73rem;font-weight:740}
.answer-card {position:relative;overflow:hidden;background:#fff;border:1px solid #e7e6f2;border-radius:21px;padding:26px 28px 24px;box-shadow:0 12px 30px #3f367313;line-height:1.93;color:#353453;overflow-wrap:anywhere;animation:riseIn .5s ease both}
.answer-card-accent {position:absolute;top:0;inset-inline-start:0;height:100%;width:5px;background:linear-gradient(#8376f0,#6552d9)}
.answer-card p {margin:0 0 13px;color:#50516d;font-size:.96rem}
.answer-card p:last-child {margin-bottom:0}
.answer-card h3 {font-size:1.04rem;font-weight:830;color:#3a316f;margin:18px 0 10px}
.answer-card h3:first-of-type {margin-top:0}
.answer-card strong {color:#4734a8;font-weight:850}
.answer-card ul,.answer-card ol {padding-inline-start:1.5rem;margin:9px 0 16px}
.answer-card li {padding:3px 0;line-height:1.8}
.answer-card li::marker {color:#695ce6;font-weight:800}
.answer-card code {font-size:.88em;background:#f1efff;padding:2px 5px;border-radius:5px;color:#5d4caa}
.answer-table-scroll {max-width:100%;overflow-x:auto;margin:15px 0;border:1px solid #e9e7f8;border-radius:13px}
.answer-table {width:100%;border-collapse:collapse;font-size:.88rem}
.answer-table th {background:#f3f0ff;color:#4f418d;text-align:start;font-weight:800}
.answer-table th,.answer-table td {padding:9px 13px;border-bottom:1px solid #eeedf5}
.answer-table tr:last-child td {border-bottom:0}
.answer-table tbody tr:nth-child(even) {background:#fcfbff}
.evidence-intro {margin:22px 0 8px;font-size:.84rem;color:#777995}
.evidence-tool {display:inline-block;background:#f3f0ff;color:#5e4bd1;padding:7px 12px;border-radius:11px;font-size:.82rem;font-weight:750;margin:13px 0 7px}
@media(max-width:790px){.kpi-card{min-height:124px;padding:14px}.kpi-value{font-size:1.16rem}.answer-card{padding:20px 18px}}
@media(max-width:550px){.kpi-card{min-height:105px;padding:11px}.kpi-label{font-size:.68rem}.kpi-value{font-size:1rem}.kpi-icon{width:25px;height:25px}.answer-card{padding:18px 14px}}
@media(prefers-reduced-motion:reduce){.kpi-card,.answer-card{animation:none!important;transition:none!important}.kpi-card:hover{transform:none}}
</style>""", unsafe_allow_html=True)

if "workspace_token" not in st.session_state:
    st.session_state.workspace_token = secrets.token_hex(32)

with st.sidebar:
    st.markdown("""<div class="brand"><span class="brand-mark">◈</span>
    <span><strong>DataLens</strong><small>AGENT STUDIO</small></span></div>""", unsafe_allow_html=True)
    st.markdown('<div class="sidebar-caption">AI-powered CSV intelligence · بيانات تتحول إلى معرفة</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-section">LANGUAGE / اللغة</div>', unsafe_allow_html=True)
    lang = st.radio("اللغة / Language", ["العربية", "English"], horizontal=True, label_visibility="collapsed")
ar = lang == "العربية"


def tr(a, b):
    return a if ar else b


if ar:
    st.markdown("<style>.stTextArea textarea,[data-testid='stText'],[data-testid='stMarkdownContainer'] p {direction:rtl;text-align:right}.hero-copy {text-align:right}.hero-badges {justify-content:flex-start}</style>", unsafe_allow_html=True)

try:
    settings = Settings.from_env()
    store = Store(settings.data_dir)
except (ValueError, OSError) as exc:
    st.error(f"Configuration error: {exc}")
    st.stop()

with st.sidebar:
    st.caption(tr("مساعدك لتحليل البيانات، مع أدلة واضحة لكل نتيجة.", "Your data copilot, with evidence behind every result."))
    st.divider()
    st.markdown('<div class="side-section">CONNECTION / الاتصال</div>', unsafe_allow_html=True)
    server_key = os.getenv("GEMINI_API_KEY", "")
    access_code = os.getenv("DATALENS_ACCESS_CODE", "")
    entered_code = st.text_input(tr("رمز الوصول", "Access code"), type="password") if access_code else ""
    server_allowed = not access_code or hmac.compare_digest(entered_code, access_code)
    api_key = server_key if server_allowed else ""
    if access_code and not server_allowed:
        st.warning(tr("أدخل رمز الوصول للمتابعة.", "Enter the access code to continue."))
    elif server_key:
        st.markdown('<span class="status-pill good"><span class="status-dot"></span>' +
                    tr("إعدادات Gemini متوفرة", "Gemini is configured") + '</span>', unsafe_allow_html=True)
    else:
        st.error(tr("خدمة الذكاء الاصطناعي غير مهيأة. يرجى التواصل مع المسؤول.", "AI service is not configured. Please contact the administrator."))
    st.caption(tr("مفتاح الخدمة محفوظ بأمان على الخادم ولا يحتاج المستخدم إلى إدخاله.", "The service key is stored securely on the server; users do not need to enter it."))
    st.divider()
    st.markdown('<div class="side-section">GUARDRAILS / حدود المهمة</div>', unsafe_allow_html=True)
    st.write(f"{settings.max_turns} " + tr("خطوات كحد أقصى", "maximum turns"))
    st.write(f"${settings.task_budget:.2f} " + tr("سقف تكلفة تقديري", "estimated cost cap"))
    st.caption(tr("حفظ التقرير يحتاج موافقتك.", "Saving a report requires your approval."))
    with st.expander(tr("استعادة مساحة العمل", "Restore workspace")):
        st.caption(tr("احفظ هذا المفتاح سرًا لاسترجاع ذاكرتك بعد إعادة التشغيل. من يملكه يمكنه الوصول إلى سجل هذه المساحة.", "Keep this key private to restore memory after a restart. Anyone holding it can access this workspace's history."))
        st.code(st.session_state.workspace_token, language=None)
        restore = st.text_input(tr("مفتاح مساحة محفوظ", "Saved workspace key"), type="password")
        if st.button(tr("استعادة", "Restore")):
            try:
                scope_id(restore)
                st.session_state.workspace_token = restore
                for k in ("run", "run_settings"):
                    st.session_state.pop(k, None)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

scope = scope_id(st.session_state.workspace_token)
workspace = store.workspace(scope)
st.markdown('<section class="hero"><div class="hero-orb" aria-hidden="true"></div><div class="hero-copy">'
            '<div class="eyebrow">DATALENS / INTELLIGENT DATA WORKSPACE</div><h1>' +
            tr("كل سؤال عن بياناتك، له إجابة أوضح.", "Ask your data. Discover what matters.") +
            '</h1><p>' +
            tr("من ملف CSV إلى رؤى قابلة للفهم. ارفع بياناتك، اطرح سؤالك، وتابع الأدلة والخطوات والتكلفة بوضوح.",
               "From raw CSV to meaningful answers. Explore, question and verify insights in one beautiful workspace.") +
            '</p><div class="hero-badges"><span class="hero-badge">✦ ' +
            tr("تحليل ذكي", "AI-assisted analysis") + '</span><span class="hero-badge">◉ ' +
            tr("نتائج موثّقة", "Traceable insights") + '</span><span class="hero-badge">↗ ' +
            tr("عربي · English", "Arabic · English") +
            '</span></div></div></section>', unsafe_allow_html=True)

analysis_tab, memory_tab, about_tab = st.tabs([
    tr("◈ مساحة التحليل", "◈ Workspace"), tr("◷ سجل المهام", "◷ History"),
    tr("✧ كيف يعمل؟", "✧ How it works")])

with analysis_tab:
    st.markdown('<div class="section-intro"><div><div class="section-heading">' +
                tr("استكشف بياناتك بثقة", "Your analysis workspace") +
                '</div><div class="section-subtitle">' +
                tr("ثلاث خطوات بسيطة من الملف إلى النتيجة", "Three simple steps from upload to insight") +
                '</div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="step-ribbon"><span class="step-chip"><b>01</b>' +
                tr("ارفع البيانات", "Upload data") + '</span><span class="step-chip"><b>02</b>' +
                tr("اسأل الوكيل", "Ask the agent") + '</span><span class="step-chip"><b>03</b>' +
                tr("راجع الأدلة", "Review evidence") + '</span></div>', unsafe_allow_html=True)
    left, right = st.columns([1, 1.12], gap="large")
    with left:
        with st.container(border=True, key="upload_panel"):
            st.subheader(tr("١. بياناتك تبدأ هنا", "1. Start with your data"))
            file = st.file_uploader(tr("ملف CSV بترميز UTF-8، حتى 5 MB", "UTF-8 CSV, up to 5 MB"), type=["csv"])
            raw = file.getvalue() if file else Path("sample_data/sales.csv").read_bytes()
            st.caption(tr("البيانات الافتراضية تجريبية لمتجر، وليست مبيعات حقيقية.", "Default data is a synthetic shop example, not real sales."))
            try:
                frame = load_csv(raw)
                dataset_id = upload(workspace, raw)
                st.dataframe(frame.head(10), hide_index=True, width="stretch")
                st.caption(f"{len(frame):,} " + tr("صفوف", "rows") + f" · {len(frame.columns)} " + tr("أعمدة", "columns"))
            except ValueError as exc:
                st.error(str(exc))
                dataset_id = None
    with right:
        with st.container(border=True, key="query_panel"):
            st.subheader(tr("٢. اسأل واترك التحليل للوكيل", "2. Ask your data anything"))
            examples = [tr("رتّب المنتجات حسب إجمالي الإيرادات واشرح النتيجة.", "Rank products by total revenue and explain the result."),
                        tr("افحص القيم الناقصة والصفوف المكررة.", "Check missing values and duplicate rows."),
                        tr("قارن إيرادات الفروع وجهّز تقريرًا لحفظه.", "Compare branch revenues and prepare a report to save.")]
            if "draft_question" not in st.session_state:
                st.session_state.draft_question = examples[0]

            def select_example():
                selected = st.session_state.get("selected_example")
                if selected in examples:
                    st.session_state.draft_question = selected

            st.selectbox(tr("جرّب سؤالًا مقترحًا", "Try a suggested question"), examples,
                         index=None, placeholder=tr("اختر أحد الأسئلة الجاهزة…", "Choose an example…"),
                         key="selected_example", on_change=select_example)
            question = st.text_area(tr("سؤالك للوكيل", "Your question"), height=160, max_chars=5000,
                                    key="draft_question")
            st.caption(tr("عند التحليل تُرسل إلى Gemini مقتطفات من الملف ونتائج الأدوات وملخص الذاكرة. استخدم بيانات مسموحًا بمشاركتها.", "Analysis sends dataset excerpts, tool results and memory summaries to Gemini. Use data you are allowed to share."))
            waiting = bool(st.session_state.get("run") and st.session_state.run.status == "awaiting_approval")
            start = st.button(tr("حلّل البيانات ←", "Analyze data →"), type="primary", disabled=not dataset_id or waiting, width="stretch")

    async def execute(previous=None, approved=None):
        current_settings = st.session_state.get("run_settings", settings) if previous else settings
        provider = Gemini(current_settings, api_key)
        try:
            agent = Agent(current_settings, store, provider,
                          secret_values=[api_key, st.session_state.workspace_token, access_code])
            return await (agent.resume(previous, approved) if previous else agent.start(scope, dataset_id, question))
        finally:
            await provider.close()

    if start:
        try:
            st.session_state.run_settings = settings
            with st.spinner(tr("الوكيل يفحص البيانات ويستخدم الأدوات…", "The agent is inspecting data and calling tools…")):
                st.session_state.run = asyncio.run(execute())
        except (ConfigurationError, ValueError) as exc:
            st.error(str(exc))

    run = st.session_state.get("run")
    if run:
        st.divider()
        st.markdown(
            '<div class="results-heading"><div class="results-overline">DATALENS · INSIGHTS</div>'
            '<h2>' + tr("نتائج التحليل", "Analysis results") + '</h2><p>' +
            tr("إجابتك، المؤشرات الفعلية، والأدلة المستخدمة للوصول إلى النتيجة.",
               "Your answer, measured facts and the evidence behind every finding.") +
            '</p></div>', unsafe_allow_html=True,
        )
        status_text = {
            "completed": tr("مكتمل", "Completed"),
            "failed": tr("تعذر إكمال الطلب", "Explicit failure"),
            "awaiting_approval": tr("بانتظار الموافقة", "Awaiting approval"),
            "budget_limit": tr("انتهت الميزانية", "Budget limit"),
            "max_turns": tr("حد الخطوات", "Turn limit"),
            "provider_error": tr("خطأ اتصال", "Provider error"),
        }.get(run.status, run.status)
        metrics = [
            (tr("الحالة", "Status"), status_text, "✓", "main"),
            (tr("خطوات النموذج", "Model turns"), f"{run.turns:,}", "↻", "soft"),
            (tr("الرموز المستخدمة", "Tokens used"),
             f"{run.input_tokens + run.output_tokens:,}", "◈", "deep"),
            (tr("التكلفة المقدّرة", "Estimated USD cost"),
             "$" + f"{run.cost:.6f}", "$", "neutral"),
        ]
        for column, (label, value, icon, tone) in zip(st.columns(4, gap="small"), metrics, strict=True):
            with column:
                st.markdown(metric_card_html(label, value, icon, tone), unsafe_allow_html=True)
        st.caption(tr(
            "التكلفة تقديرية وفق أسعار الاستخدام المدفوع؛ قد تختلف الفاتورة أو الحصة المجانية.",
            "Estimated at paid rates; actual billing or free-tier charges may differ.",
        ))
        facts = key_facts(run.evidence, arabic=ar)
        if facts:
            from html import escape

            chips = "".join(
                '<span class="fact-chip"><span>' + escape(label) +
                '</span><strong>' + f"{value:,}" + '</strong></span>'
                for label, value in facts
            )
            st.markdown('<div class="quick-facts">' + chips + '</div>',
                        unsafe_allow_html=True)
        if run.uncertain_cost:
            st.warning(tr(
                "تشمل التكلفة حجزًا لاستدعاء لم تتوفر بيانات استهلاكه.",
                "Cost includes a reservation for a call whose usage is unknown.",
            ))

        if run.status == "awaiting_approval":
            st.warning(tr(
                "الوكيل يريد حفظ التقرير التالي. راجعه قبل الموافقة.",
                "The agent wants to save this report. Review it before approving.",
            ))
            st.text(run.pending["content"])
            approve_col, reject_col = st.columns(2)
            approve = approve_col.button(tr("موافقة وحفظ", "Approve and save"), type="primary")
            reject = reject_col.button(tr("رفض الحفظ", "Decline"))
            if approve or reject:
                try:
                    with st.spinner(tr("جارٍ إكمال المهمة…", "Resuming task…")):
                        st.session_state.run = asyncio.run(execute(run, approve))
                    st.rerun()
                except ConfigurationError as exc:
                    st.error(str(exc))
        elif run.answer:
            st.markdown(
                '<div class="answer-header"><div class="answer-title">'
                '<span class="answer-title-icon" aria-hidden="true">✦</span>' +
                tr("إجابة الوكيل", "Agent answer") +
                '</div><span class="answer-label">' +
                tr("نص الإجابة الأصلي", "Original answer") +
                '</span></div>', unsafe_allow_html=True,
            )
            st.markdown(render_answer_html(run.answer, arabic=ar), unsafe_allow_html=True)
            st.download_button(
                tr("تنزيل الإجابة النصية", "Download answer as text"),
                str(run.answer).encode("utf-8"), "datalens-answer.txt", "text/plain",
            )

        st.markdown(
            '<div class="evidence-intro">' +
            tr("التفاصيل التالية من نتائج أدوات MCP الفعلية، دون إضافة أرقام مُولّدة.",
               "Evidence below comes from actual MCP tool results, with no generated numbers.") +
            '</div>', unsafe_allow_html=True,
        )
        with st.expander(tr("◈ الأدلة والبيانات المصدرية", "◈ Evidence and source data")):
            if not run.evidence:
                st.info(tr("لا توجد أدلة مسجلة لهذه المهمة.", "No tool evidence recorded."))
            for ident, evidence in run.evidence.items():
                name = evidence.get("tool", "")
                known_tools = {
                    "inspect_dataset", "check_data_quality", "summarize_numeric",
                    "aggregate_data", "filter_rows", "compare_groups", "save_report",
                }
                safe_name = name if name in known_tools else "MCP tool"
                st.markdown('<span class="evidence-tool">' + ident + " · " + safe_name +
                            '</span>', unsafe_allow_html=True)
                result = evidence.get("result", {})
                if isinstance(result, dict):
                    preview = evidence_preview(result)
                    if preview:
                        _, data = preview
                        st.dataframe(data, hide_index=True, width="stretch")
                    chart = chart_for_evidence(result)
                    if chart is not None:
                        st.caption(tr(
                            "رسم من بيانات التجميع الفعلية (قد تُعرض مجموعات جزئية).",
                            "Chart of returned groups (results may be truncated).",
                        ))
                        st.bar_chart(chart, width="stretch", color="#7568e8")
                    st.json(result, expanded=False)
                    report = result.get("report_id", "")
                    if (safe_name == "save_report" and isinstance(report, str)
                            and report and Path(report).name == report):
                        path = workspace / "reports" / report
                        if path.is_file():
                            st.download_button(
                                tr("تنزيل التقرير", "Download report"),
                                path.read_bytes(), "datalens-report.md", key=ident,
                            )
                else:
                    st.json(result, expanded=False)

        with st.expander(tr("◷ سجل الخطوات والتكلفة", "◷ Execution trace and cost")):
            if not run.events:
                st.info(tr("لا توجد خطوات مسجلة.", "No recorded steps."))
            for index, event in enumerate(run.events, 1):
                name = str(event.get("event", "event")) if isinstance(event, dict) else "event"
                st.caption(f"{index:02d} · {name}")
                st.json(event, expanded=False)
        st.download_button(
            tr("تنزيل سجل JSONL", "Download JSONL trace"),
            Path(run.trace_path).read_bytes(), f"{run.task_id}.jsonl", "application/x-ndjson",
        )

with memory_tab:
    st.subheader(tr("مهامك السابقة", "Your previous tasks"))
    st.caption(tr("تُحفظ في SQLite. استعد مفتاح مساحة العمل نفسه بعد إعادة التشغيل.", "Stored in SQLite. Restore the same workspace key after restarting."))
    history = store.recall(scope, 20)
    if not history:
        st.info(tr("ستظهر هنا المهام بعد اكتمالها أو توقفها.", "Completed or stopped tasks will appear here."))
    for item in history:
        with st.expander(item["question"][:100]):
            st.text(item["answer"])
            st.caption(f"{item['status']} · ${item['cost']:.6f} · {item['created']}")

with about_tab:
    st.markdown(tr("**وكيل واحد، سبع أدوات، وقرار يمكن تتبعه.**", "**One agent, seven tools, traceable decisions.**"))
    st.write(tr("يقرر Gemini الخطوة التالية، وتنفّذ أدوات MCP الحسابات باستخدام pandas. يتوقف الوكيل عند الإجابة النهائية أو حد الخطوات أو الميزانية.", "Gemini chooses the next step; MCP tools calculate with pandas. The agent stops at a final answer, turn limit or budget limit."))
    st.write(tr("يمكنه تلخيص الأعمدة والتجميع والتصفية ومقارنة المجموعات وفحص الجودة. لا يعدّل ملفك الأصلي، ولا ينفّذ أكوادًا حرة.", "Summarize, aggregate, filter, compare groups and check data quality. The source CSV is unchanged; arbitrary code execution is unavailable."))
    st.caption(tr("إثبات الفشل جزء من المشروع: عند غياب بيانات لازمة، يجب أن يشرح سبب العجز.", "Explicit failure is part of the project: missing required data must lead to an honest explanation."))
    st.link_button("GitHub · source & documentation", "https://github.com/assemalqudami-maker/datalens-agent")

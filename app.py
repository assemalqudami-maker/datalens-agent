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
from datalens.storage import Store, scope_id

load_dotenv()
st.set_page_config(page_title="DataLens Agent | محلّل البيانات", page_icon="◈", layout="wide")
st.markdown("""<style>
.stApp {background:#f6f8fc; color:#18233b}
.block-container {max-width:1200px;padding-top:2rem;padding-bottom:3rem}
[data-testid="stSidebar"] {background:#edf1f8}
.hero {padding:26px 30px;border-radius:20px;background:#152c45;color:white;margin-bottom:22px}
.hero .eyebrow {color:#7fdec6;font-size:12px;letter-spacing:3px;font-weight:700}
.hero h1 {font-size:38px;color:white;letter-spacing:-1.5px;margin:8px 0}
.hero p {color:#cad6e7;max-width:750px;line-height:1.8;margin:0}
div[data-testid="stMetric"] {background:white;border:1px solid #e0e6f0;border-radius:14px;padding:16px}
.stButton>button[kind="primary"] {background:#127d72;border:0;border-radius:9px}
.stTextArea textarea {border-radius:12px}
</style>""", unsafe_allow_html=True)

if "workspace_token" not in st.session_state:
    st.session_state.workspace_token = secrets.token_hex(32)

with st.sidebar:
    st.markdown("### ◈ DataLens")
    lang = st.radio("اللغة / Language", ["العربية", "English"], horizontal=True)
ar = lang == "العربية"


def tr(a, b):
    return a if ar else b


if ar:
    st.markdown("<style>.stTextArea textarea,[data-testid='stText'],[data-testid='stMarkdownContainer'] p {direction:rtl;text-align:right}</style>", unsafe_allow_html=True)

try:
    settings = Settings.from_env()
    store = Store(settings.data_dir)
except (ValueError, OSError) as exc:
    st.error(f"Configuration error: {exc}")
    st.stop()

with st.sidebar:
    st.caption(tr("تحليل قابل للتتبع، خطوة بخطوة", "Analysis you can trace, step by step"))
    st.divider()
    st.markdown(tr("**اتصال النموذج**", "**Model connection**"))
    server_key = os.getenv("GEMINI_API_KEY", "")
    access_code = os.getenv("DATALENS_ACCESS_CODE", "")
    entered_code = st.text_input(tr("رمز الوصول", "Access code"), type="password") if access_code else ""
    server_allowed = not access_code or hmac.compare_digest(entered_code, access_code)
    api_key = server_key if server_allowed else ""
    if access_code and not server_allowed:
        st.warning(tr("أدخل رمز الوصول للمتابعة.", "Enter the access code to continue."))
    elif server_key:
        st.success(tr("خدمة الذكاء الاصطناعي جاهزة.", "AI service is configured and ready."))
    else:
        st.error(tr("خدمة الذكاء الاصطناعي غير مهيأة. يرجى التواصل مع المسؤول.", "AI service is not configured. Please contact the administrator."))
    st.caption(tr("مفتاح الخدمة محفوظ بأمان على الخادم ولا يحتاج المستخدم إلى إدخاله.", "The service key is stored securely on the server; users do not need to enter it."))
    st.divider()
    st.markdown(tr("**حدود المهمة**", "**Task limits**"))
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
st.markdown('<div class="hero"><div class="eyebrow">DATALENS / AI ANALYSIS WORKSPACE</div>'
            '<h1>' + tr("من ملف بيانات إلى إجابة واضحة", "Your data. A clearer answer.") + '</h1><p>' +
            tr("ارفع ملف CSV، اسأل بلغتك، وتابع الأدوات والنتائج والتكلفة في مكان واحد.",
               "Upload a CSV, ask a question, and follow every tool, finding and cost in one place.") + '</p></div>', unsafe_allow_html=True)

analysis_tab, memory_tab, about_tab = st.tabs([
    tr("مساحة التحليل", "Analysis"), tr("الذاكرة", "Memory"), tr("كيف يعمل؟", "How it works")])

with analysis_tab:
    left, right = st.columns([1, 1.25], gap="large")
    with left:
        st.subheader(tr("١. اختر البيانات", "1. Choose your data"))
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
        st.subheader(tr("٢. ما الذي تريد معرفته؟", "2. What would you like to know?"))
        examples = [tr("رتّب المنتجات حسب إجمالي الإيرادات واشرح النتيجة.", "Rank products by total revenue and explain the result."),
                    tr("افحص القيم الناقصة والصفوف المكررة.", "Check missing values and duplicate rows."),
                    tr("قارن إيرادات الفروع وجهّز تقريرًا لحفظه.", "Compare branch revenues and prepare a report to save.")]
        example = st.selectbox(tr("أمثلة للبدء", "Start with an example"), examples)
        question = st.text_area(tr("طلبك", "Your request"), value=example, height=150, max_chars=5000, key=f"q_{examples.index(example)}_{ar}")
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
        status_text = {"completed": tr("مكتمل", "Completed"), "failed": tr("تعذر إكمال الطلب", "Explicit failure"),
                       "awaiting_approval": tr("بانتظار الموافقة", "Awaiting approval")}.get(run.status, run.status)
        a, b, c, d = st.columns(4)
        a.metric(tr("الحالة", "Status"), status_text)
        b.metric(tr("خطوات النموذج", "Model turns"), run.turns)
        c.metric(tr("الرموز المستخدمة", "Tokens"), run.input_tokens + run.output_tokens)
        d.metric(tr("التكلفة المقدّرة بالدولار", "Estimated USD cost"), f"${run.cost:.6f}")
        st.caption(tr("التكلفة محسوبة بأسعار الاستخدام المدفوع؛ قد تختلف الفاتورة الفعلية أو الحصة المجانية.", "Cost uses standard paid rates; actual billing or free-tier charges may differ."))
        if run.uncertain_cost:
            st.warning(tr("تشمل التكلفة حجزًا لاستدعاء لم تتوفر بيانات استهلاكه.", "Cost includes a reservation for a call whose usage is unknown."))
        if run.status == "awaiting_approval":
            st.warning(tr("الوكيل يريد حفظ التقرير التالي. راجعه قبل الموافقة.", "The agent wants to save this report. Review it before approving."))
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
            st.subheader(tr("النتيجة", "Answer"))
            st.text(run.answer)  # Plain text prevents model-generated HTML or remote image requests.
        with st.expander(tr("النتائج التي استند إليها الوكيل", "Tool evidence")):
            for ident, evidence in run.evidence.items():
                st.markdown(f"**{ident} · {evidence['tool']}**")
                st.json(evidence["result"], expanded=False)
                report = evidence["result"].get("report_id", "")
                if evidence["tool"] == "save_report" and Path(report).name == report:
                    path = workspace / "reports" / report
                    if path.is_file():
                        st.download_button(tr("تنزيل التقرير", "Download report"), path.read_bytes(), "datalens-report.md", key=ident)
        with st.expander(tr("سجل الخطوات والتكلفة", "Execution and cost trace")):
            for event in run.events:
                st.json(event, expanded=False)
        st.download_button(tr("تنزيل سجل JSONL", "Download JSONL trace"),
                           Path(run.trace_path).read_bytes(), f"{run.task_id}.jsonl", "application/x-ndjson")

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
    st.markdown(tr("**وكيل واحد، ثماني أدوات، وقرار يمكن تتبعه.**", "**One agent, eight tools, traceable decisions.**"))
    st.write(tr("يقرر Gemini الخطوة التالية، وتنفّذ أدوات MCP الحسابات باستخدام pandas. يتوقف الوكيل عند الإجابة النهائية أو حد الخطوات أو الميزانية.", "Gemini chooses the next step; MCP tools calculate with pandas. The agent stops at a final answer, turn limit or budget limit."))
    st.write(tr("يمكنه تلخيص الأعمدة والتجميع والتصفية ومقارنة المجموعات وفحص الجودة. لا يعدّل ملفك الأصلي، ولا ينفّذ أكوادًا حرة.", "Summarize, aggregate, filter, compare groups and check data quality. The source CSV is unchanged; arbitrary code execution is unavailable."))
    st.caption(tr("إثبات الفشل جزء من المشروع: عند غياب بيانات لازمة، يجب أن يشرح سبب العجز.", "Explicit failure is part of the project: missing required data must lead to an honest explanation."))
    st.link_button("GitHub · source & documentation", "https://github.com/assemalqudami-maker/datalens-agent")

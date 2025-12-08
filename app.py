# app.py — FULL paste-ready
# Collapsible Loaded Data (summary table only) + Agent selector + Ask Question
# Heavy grammar/spell/intent repair + optional light autocorrect + Quarterly Margin + SQL + Data Overview

import os, sys, json, re, difflib
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from data_loader import get_data_loader
from agno_runner import run_agent_task
from llm_client import get_default_client  # used by heavy grammar/intent repair

st.set_page_config(page_title="CFO FP&A Crew AI", page_icon="📊", layout="wide")

# ───────────────────────────────────────────────
# Global CSS (cards + chips)
# ───────────────────────────────────────────────
st.markdown("""
<style>
.card { border-radius: 12px; padding: 12px 14px; margin-bottom: 10px; background: #111418; border: 1px solid #262b31; }
.card h4 { margin: 0 0 6px 0; font-size: 15px; }
.card p  { margin: 0; font-size: 12px; color: #aab; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.badge { display: inline-block; padding: 2px 8px; margin: 2px 6px 2px 0; border-radius: 999px; font-size: 11px; border: 1px solid #2a3138; color: #cfd6e4; }
.badge.date   { background:#0c2236; }
.badge.num    { background:#1c2a14; }
.badge.cardi  { background:#3a1d1d; }
.signal { font-size:12px; margin-right:10px; white-space:nowrap; }
</style>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# Chart helpers
# ───────────────────────────────────────────────
def render_chart(df: pd.DataFrame, chart_type="bar", x=None, y=None, title="Chart"):
    if df is None or df.empty:
        st.info("No data to chart."); return
    if not x or not y or x not in df.columns or y not in df.columns:
        cols = list(df.columns)
        if len(cols) >= 2: x, y = cols[0], cols[1]
        else: st.info("Need at least two columns for chart."); return
    fig, ax = plt.subplots(figsize=(8, 4))
    try:
        if chart_type == "bar": ax.bar(df[x], df[y])
        elif chart_type == "line": ax.plot(df[x], df[y])
        elif chart_type == "pie": ax.pie(df[y], labels=df[x], autopct="%1.1f%%")
        elif chart_type == "area": ax.fill_between(df[x], df[y], alpha=0.4)
        else: ax.plot(df[x], df[y])
    except Exception as e:
        st.warning(f"Chart rendering error: {e}"); return
    ax.set_title(title or "Chart"); ax.set_xlabel(x or ""); ax.set_ylabel(y or "")
    plt.tight_layout(); st.pyplot(fig)

def try_render_chart_from_answer(answer: str) -> bool:
    marker = "##CHART-DATA##"
    if marker not in answer: return False
    try:
        payload = answer.split(marker, 1)[1].strip()
        if payload.startswith("```"):
            payload = payload.strip("` \n"); parts = payload.split("\n", 1)
            payload = parts[1] if len(parts) > 1 else ""
        spec = json.loads(payload)
        if isinstance(spec, list):
            df = pd.DataFrame(spec)
            x = df.columns[0] if len(df.columns)>0 else None
            y = df.columns[1] if len(df.columns)>1 else None
            render_chart(df, "bar", x, y, "Chart"); st.dataframe(df, use_container_width=True); return True
        df_data = spec.get("df")
        df = pd.DataFrame(df_data if isinstance(df_data, list) else df_data)
        render_chart(df, spec.get("chart_type","bar"), spec.get("x"), spec.get("y"), spec.get("title","Chart"))
        st.dataframe(df, use_container_width=True); return True
    except Exception as e:
        st.warning(f"Chart payload parse error: {e}"); return False

# ───────────────────────────────────────────────
# Prompt guidance added to agent tasks
# ───────────────────────────────────────────────
CHART_INSTRUCTIONS = """
Charts Allowed: {charts_allowed}

If charts are allowed AND a chart materially clarifies a trend/comparison/outlier,
append ONE chart payload after your executive summary:

##CHART-DATA##
{
  "chart_type": "bar" | "line" | "pie" | "area",
  "x": "<column>",
  "y": "<column>",
  "title": "<chart title>",
  "df": [ { row objects } ]     // or a columnar dict {col:[...]}
}

Do NOT wrap the payload in markdown code fences.
"""
def chart_instructions_text(allow: bool) -> str:
    return CHART_INSTRUCTIONS.replace("{charts_allowed}", "YES" if allow else "NO")

KAGGLE_JOIN_RULES = """
For US region analysis:
- Prefer loan_with_region (already has Region) when available.
- Otherwise JOIN loan ↔ state_region using a case-insensitive state key.
  Candidate columns:
    loan: addr_state, state, State, STATE, state_code, state_abbr
    state_region: state_abbr, state, State, STATE, state_code
- Group by Region and return numeric results (counts/sums) sorted desc.
If a target column is missing, try the next candidate automatically.
"""

EXEC_SUMMARY_TEMPLATE = """
Adopt the voice of a seasoned CFO/FP&A leader: decisive, concise, quantified.
Return an EXECUTIVE SUMMARY using EXACTLY this structure:

1) Snapshot KPIs — bullet list with exact figures.
2) Highlights — 3–5 bullets (what moved and why).
3) Risks / Watchouts — 2–4 bullets.
4) Drivers — brief attribution (e.g., segment/region/deal).
5) Recommendations — 2–4 concrete next steps (owner + timeline).

Keep it tight. Use numbers. Only add a chart if allowed and genuinely helpful.
"""

# ───────────────────────────────────────────────
# Autocorrect helpers (light)
# ───────────────────────────────────────────────
FINANCE_TERMS = {
    "revenue","margin","profit","cost","costs","sap","salesforce","deal","deals",
    "quarter","quarterly","month","monthly","year","yoy","qoq","pipeline",
    "region","regions","state","states","loan","loans","amount","value","values",
    "customer","customers","purpose","purposes","count","counts","avg","average",
    "sum","total","expense","expenses"
}
ALIAS_MAP = {
    "loaed": "loan",
    "loaned": "loan",
    "salesforce deal": "salesforce_deals",
    "sap cost": "sap_costs",
    "sap costs": "sap_costs",
    "financials": "financial_summary",
    "unified": "unified_financials",
    "loan with region": "loan_with_region",
    "state regions": "state_region",
}
def build_vocab_from_loader(dl):
    vocab = set(FINANCE_TERMS)
    for name, df in dl.data.items():
        vocab.add(name); vocab.update(name.split("_"))
        for c in df.columns:
            cstr = str(c); vocab.add(cstr); vocab.update(re.split(r"[_\s/]+", cstr))
    return {t.lower() for t in vocab if t}
def _tokenize(q: str): return re.findall(r"[A-Za-z_]+", q)
def autocorrect_light(q: str, vocab: set[str], alias_map: dict[str,str]):
    low = q.lower(); applied = {}
    for k in sorted(alias_map.keys(), key=len, reverse=True):
        if k in low: low = low.replace(k, alias_map[k]); applied[k] = alias_map[k]
    for t in set(_tokenize(low)):
        if t in vocab: continue
        cand = difflib.get_close_matches(t, vocab, n=1, cutoff=0.8)
        if cand:
            best = cand[0]
            low = re.sub(rf"\b{re.escape(t)}\b", best, low); applied[t] = best
    return low, applied

# ───────────────────────────────────────────────
# HEAVY NATURAL LANGUAGE CORRECTION ENGINE (grammar + intent)
# Requires: pip install textblob && python -m textblob.download_corpora
# ───────────────────────────────────────────────
def heavy_repair_query(user_query: str) -> str:
    """
    LEVEL-3 NLP FIXER:
    ✔ Spell + Grammar fix (TextBlob)
    ✔ Domain term normalization
    ✔ LLM rewrite to clean English instruction
    """
    try:
        from textblob import TextBlob
    except Exception:
        return user_query.strip() if user_query else ""

    original = (user_query or "").strip()
    basic = re.sub(r"\s+", " ", original)
    # Step 1: TextBlob correction (spelling + simple grammar)
    try:
        blob = TextBlob(basic)
        step2 = str(blob.correct())
    except Exception:
        step2 = basic
    # Step 2: domain replacements
    replacements = {
        r"\bloaed\b": "loan",
        r"\bloaned\b": "loan",
        r"\bloansed\b": "loan",
        r"\bregien\b": "region",
        r"\bregin\b": "region",
        r"\bregiom\b": "region",
        r"\bsalesfroce\b": "salesforce",
        r"\bsaleforce\b": "salesforce",
        r"\bsap cots\b": "sap costs",
        r"\bsapcots\b": "sap costs",
        r"\bquater\b": "quarter",
        r"\bquaterly\b": "quarterly",
        r"\bfinancal\b": "financial",
        r"\bunfied\b": "unified",
        r"\bmnth\b": "month",
        r"\bmohtly\b": "monthly",
    }
    step3 = step2
    for bad, good in replacements.items():
        step3 = re.sub(bad, good, step3, flags=re.IGNORECASE)

    # Step 3: LLM rewrite (clean, correct English instruction)
    try:
        llm = get_default_client().get_client()
        model = get_default_client().model
        prompt = f"""
You are QueryFixerGPT.

Rewrite the following user query into clean, correct English.
Fix grammar, spelling, word order, tense, and missing words.
Do NOT change meaning. Do NOT add facts.

Return ONLY the corrected query, no extra text.

User query:
\"\"\"{step3}\"\"\" 
"""
        llm_fixed = llm.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        ).choices[0].message.content.strip()
    except Exception:
        llm_fixed = step3

    final = llm_fixed
    if not any(w in final.lower() for w in ["show","list","compare","analyze","select","summarize"]):
        final = "Analyze: " + final
    return final

# ───────────────────────────────────────────────
# Data Overview helpers (visuals)
# ───────────────────────────────────────────────
def build_summary_from_loader(dl):
    return (pd.DataFrame([{"Dataset": k, "Rows": len(df), "Cols": len(df.columns)} for k, df in dl.data.items()])
            .sort_values("Dataset").reset_index(drop=True))
def schema_chips(df: pd.DataFrame):
    date_cols = [c for c in df.columns if "date" in c.lower() or "time" in c.lower()]
    num_cols  = list(df.select_dtypes(include="number").columns)
    high_card = [c for c in df.columns if df[c].nunique(dropna=True) >= 0.6 * len(df)]
    return date_cols, num_cols, high_card
def dataset_health(df: pd.DataFrame):
    total_vals = df.shape[0] * max(1, df.shape[1])
    null_pct = float(df.isnull().sum().sum()) / total_vals * 100.0 if total_vals else 0.0
    dup_pct  = float(df.duplicated().sum()) / max(1, len(df)) * 100.0 if len(df) else 0.0
    has_dt = len(df.select_dtypes(include=["datetime", "datetimetz"]).columns) > 0
    return null_pct, dup_pct, has_dt
def signal_badge(null_pct, dup_pct, has_dt):
    null_icon = "✅" if null_pct <= 5 else ("🟡" if null_pct <= 15 else "🚩")
    dup_icon  = "✅" if dup_pct  <= 1 else ("🟡" if dup_pct  <= 5 else "🚩")
    date_icon = "✅" if has_dt else "⚠️"
    return null_icon, dup_icon, date_icon

# ───────────────────────────────────────────────
# Load data once
# ───────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_data(): return get_data_loader()
dl = load_data()

# ───────────────────────────────────────────────
# SIDEBAR
# ───────────────────────────────────────────────
with st.sidebar:
    st.header("🎯 Analysis Mode")
    mode = st.radio("Choose mode:",
        ["❓ Ask Question", "📈 Full Analysis", "📊 View Data", "💰 Quarterly Margin", "🧪 SQL", "🧭 Data Overview"])

    st.divider()
    # ---------------------------
    # 📂 Loaded Data (collapsible) — summary only (no preview, no chart)
    # ---------------------------
    with st.expander("📂 Loaded Data", expanded=False):

        # Shrink fonts inside expander
        st.markdown("""
        <style>
          div[data-testid="stSidebar"] div[data-testid="stExpander"] * {
              font-size: 12px !important;
          }
          div[data-testid="stSidebar"] details summary p {
              font-size: 13px !important;
              font-weight: 600 !important;
          }
          div[data-testid="stSidebar"] .stDataFrame, 
          div[data-testid="stSidebar"] .stDataFrame * {
              font-size: 11px !important;
          }
        </style>
        """, unsafe_allow_html=True)

        if dl.data:
            summary = build_summary_from_loader(dl)
            total_rows = int(summary["Rows"].sum())
            total_tables = len(summary)
            total_cols = int(summary["Cols"].sum())

            st.markdown(
                f"**Total:** {total_rows:,} rows across {total_tables} tables "
                f"({total_cols} columns combined)"
            )

            table_height = min(340, 36 + 24 * len(summary))
            st.dataframe(
                summary[["Dataset", "Rows", "Cols"]],
                use_container_width=True,
                height=table_height
            )
        else:
            st.warning("No data loaded", icon="⚠️")

    st.divider()
    # Agents
    st.header("🤖 AI Agents")
    agent_options = {
        "Data Connector": "data_connector",
        "FP&A Analyst": "fpna_analyst",
        "Profit Twin": "profit_twin",
        "CFO Copilot": "cfo_copilot",
    }
    selected_agent_label = st.radio("Choose an Agent:", list(agent_options.keys()), index=1)
    selected_agent = agent_options[selected_agent_label]
    st.success(f"🧠 Active Agent: {selected_agent_label}")

    st.divider()
    allow_charts = st.checkbox("📊 Allow charts", value=False)
    auto_correct_light_on = st.checkbox("📝 Light autocorrect (typos)", value=True)
    auto_correct_heavy_on = st.checkbox("🧠 Heavy grammar/intent repair", value=True,
                                        help="Requires TextBlob corpora; also leverages your LLM for rewrite.")

# ───────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────
st.write("**Python:**", sys.executable)
st.write("**CWD:**", os.getcwd())
st.write("**Loaded tables:**", ", ".join(sorted(dl.data.keys())))
st.title("📊 CFO FP&A Crew AI Dashboard")
st.markdown("AI-powered financial analysis with real data")

# ❓ ASK
if mode == "❓ Ask Question":
    st.header("❓ Ask Your Financial Question")
    with st.expander("📊 Available Data Context", expanded=False):
        st.text(dl.describe_all())

    AGENT_PLACEHOLDERS = {
        "data_connector": "Summarize datasets and suggest useful joins between Kaggle and FP&A tables.",
        "fpna_analyst": "Executive brief: quarterly Salesforce revenue, QoQ change, and top 5 deals.",
        "profit_twin": "Executive brief: monthly SAP cost trend and top categories.",
        "cfo_copilot": "Executive brief: join loan with state_region, region-wise loan totals + drivers.",
    }
    placeholder = AGENT_PLACEHOLDERS.get(selected_agent, "Ask a financial question. Charts optional.")
    q = st.text_area("Your Question:", placeholder=placeholder, height=110)

    if st.button("🔍 Analyze", type="primary"):
        if not q.strip(): st.warning("⚠️ Please enter a question first.")
        else:
            with st.spinner(f"🤖 {selected_agent_label} is analyzing..."):
                try:
                    final_q = q.strip()
                    fixes_all = {}

                    # Heavy grammar/intent repair first (if ON)
                    if auto_correct_heavy_on:
                        repaired = heavy_repair_query(final_q)
                        if repaired and repaired.lower() != final_q.lower():
                            fixes_all["heavy_repair"] = repaired
                            final_q = repaired

                    # Light typo autocorrect next (if ON)
                    if auto_correct_light_on:
                        vocab = build_vocab_from_loader(dl)
                        corrected, fixes = autocorrect_light(final_q, vocab, ALIAS_MAP)
                        if fixes:
                            fixes_all.update(fixes)
                            final_q = corrected

                    if fixes_all:
                        if "heavy_repair" in fixes_all:
                            st.caption("🧠 Grammar/intent repair applied.")
                            del fixes_all["heavy_repair"]
                        if fixes_all:
                            st.caption("✍️ Autocorrected: " + ", ".join([f"{k}→{v}" for k,v in fixes_all.items()]))

                    task = (
                        "User Question (original):\n"
                        f"{q}\n\n"
                        "Interpreted as:\n"
                        f"{final_q}\n\n"
                        "Treat minor typos and pluralization flexibly. Use available tables directly.\n"
                        f"Available Tables: {', '.join(sorted(dl.data.keys()))}\n\n"
                        f"{KAGGLE_JOIN_RULES}\n\n"
                        f"{EXEC_SUMMARY_TEMPLATE}\n\n"
                        + chart_instructions_text(allow_charts)
                    )

                    answer = run_agent_task(
                        selected_agent,
                        task,
                        context={"tables": dl.data, "data_context": dl.describe_all()},
                    )

                    st.success("✅ Analysis Complete!")
                    st.markdown("### 💡 Answer")
                    if allow_charts and try_render_chart_from_answer(answer): pass
                    else: st.markdown(answer)

                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    import traceback; st.code(traceback.format_exc())

# 💰 MARGIN
elif mode == "💰 Quarterly Margin":
    st.header("💰 Quarterly Margin Analysis"); st.markdown("Salesforce Revenue vs SAP Costs by Quarter")
    if st.button("🔄 Compute Quarterly Margins", type="primary"):
        with st.spinner("Computing..."):
            try:
                result = dl.compute_quarterly_margin(); df = result["df"]
                if not df.empty:
                    st.success("✅ Analysis Complete!")
                    c1,c2,c3 = st.columns(3)
                    with c1: st.metric("🏆 Best Quarter", result["best_quarter"])
                    with c2: st.metric("💰 Best Margin", f"${result['best_margin']:,.2f}")
                    with c3: st.metric("📊 Average Margin", f"${df['Margin'].mean():,.2f}")
                    st.subheader("📊 Quarterly Breakdown")
                    show = df.copy()
                    show["Salesforce_Revenue"] = show["Salesforce_Revenue"].map(lambda x: f"${x:,.2f}")
                    show["SAP_Costs"] = (show["SAP_CostS"].map(lambda x: f"${x:,.2f}") if "SAP_CostS" in show.columns
                                         else show["SAP_Costs"].map(lambda x: f"${x:,.2f}"))
                    show["Margin"] = show["Margin"].map(lambda x: f"${x:,.2f}")
                    show["Margin_Percent"] = show["Margin_Percent"].map(lambda x: f"{x:.2f}%")
                    st.dataframe(show, use_container_width=True)
                    st.subheader("📈 Margin Trend"); st.line_chart(df.set_index("Quarter")["Margin"])
                else: st.warning("⚠️ Could not compute margins. Check data/date columns.")
            except Exception as e:
                st.error(f"❌ Error: {e}"); import traceback; st.code(traceback.format_exc())

# 📈 FULL
elif mode == "📈 Full Analysis":
    st.header("📈 Full Financial Analysis")
    st.info("Run your full multi-agent workflow here.")
    if st.button("🚀 Run Full Analysis", type="primary", use_container_width=True):
        st.warning("Hook this up to agno_runner.run_agno_workflow() if needed.")

# 📊 VIEW
elif mode == "📊 View Data":
    st.header("📊 Financial Data Explorer")
    if not dl.data: st.warning("⚠️ No data loaded.")
    else:
        name = st.selectbox("Select Dataset:", options=list(dl.data.keys()))
        dfv = dl.data[name]
        c1,c2,c3 = st.columns(3)
        with c1: st.metric("Rows", f"{len(dfv):,}")
        with c2: st.metric("Columns", len(dfv.columns))
        with c3: st.metric("Memory", f"{dfv.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        st.subheader("📋 Data Preview"); st.dataframe(dfv.head(100), use_container_width=True)
        with st.expander("📊 Column Info"):
            info = pd.DataFrame({ "Column": dfv.columns, "Type": dfv.dtypes.values,
                                  "Non-Null": dfv.count().values, "Null": dfv.isnull().sum().values,
                                  "Unique": [dfv[col].nunique() for col in dfv.columns] })
            st.dataframe(info, use_container_width=True)
        with st.expander("📈 Statistics"): st.dataframe(dfv.describe(), use_container_width=True)

# 🧪 SQL
elif mode == "🧪 SQL":
    st.header("🧪 Run SQL on Loaded Tables (DuckDB)")
    st.caption("📋 Available Tables:"); st.code(", ".join(sorted(dl.data.keys())))
    default_sql = """SELECT r.Region, COUNT(*) AS loans
FROM loan l
LEFT JOIN state_region r
  ON upper(cast(l.state AS varchar)) = upper(cast(r.state AS varchar))
GROUP BY 1
ORDER BY loans DESC;"""
    sql = st.text_area("Write SQL:", value=default_sql, height=200)
    if st.button("▶️ Run SQL", type="primary"):
        try:
            df = dl.sql(sql); st.success(f"Rows returned: {len(df)}"); st.dataframe(df, use_container_width=True)
            if len(df):
                st.download_button("📥 Download CSV", df.to_csv(index=False).encode("utf-8"),
                                   "query_results.csv", "text/csv")
        except Exception as e: st.error(f"❌ SQL Error: {e}")

# 🧭 OVERVIEW
elif mode == "🧭 Data Overview":
    st.header("🧭 Data Overview")
    if not dl.data: st.warning("No data loaded.")
    else:
        st.subheader("Row Distribution (sparkline)")
        s = build_summary_from_loader(dl).sort_values("Rows")
        spark = pd.DataFrame({"Rows": s["Rows"].values}, index=s["Dataset"]); st.line_chart(spark)
        st.divider(); st.subheader("Metric Cards by Dataset")
        summary = build_summary_from_loader(dl); st.markdown('<div class="grid2">', unsafe_allow_html=True)
        for _, r in summary.iterrows():
            name, rows, cols = r["Dataset"], int(r["Rows"]), int(r["Cols"])
            st.markdown(f'<div class="card"><h4>{name}</h4><p>Rows: <b>{rows:,}</b> &nbsp;•&nbsp; Cols: <b>{cols}</b></p></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.divider(); st.subheader("Schema & Health — Quick Peek")
        ds = st.selectbox("Choose a dataset", options=list(dl.data.keys())); dfx = dl.data[ds]
        date_cols, num_cols, high_card = schema_chips(dfx)
        null_pct, dup_pct, has_dt = dataset_health(dfx); null_icon, dup_icon, date_icon = signal_badge(null_pct, dup_pct, has_dt)
        c1,c2 = st.columns([2,1.2], gap="large")
        with c1:
            st.markdown("**Schema badges**")
            if date_cols: st.markdown("Dates:"); st.markdown(" ".join([f'<span class="badge date">{c}</span>' for c in date_cols]), unsafe_allow_html=True)
            else: st.caption("No obvious date/time columns detected.")
            if num_cols:
                st.markdown("Numeric:"); st.markdown(" ".join([f'<span class="badge num">{c}</span>' for c in num_cols[:30]]), unsafe_allow_html=True)
                if len(num_cols)>30: st.caption(f"... and {len(num_cols)-30} more")
            else: st.caption("No numeric columns detected.")
            if high_card:
                st.markdown("High-cardinality (≥60% unique):")
                st.markdown(" ".join([f'<span class="badge cardi">{c}</span>' for c in high_card[:30]]), unsafe_allow_html=True)
                if len(high_card)>30: st.caption(f"... and {len(high_card)-30} more")
            else: st.caption("No high-cardinality columns flagged.")
        with c2:
            st.markdown("**Health signals**")
            st.markdown(f'<span class="signal">{null_icon} Nulls: {null_pct:.1f}%</span><br/>'
                        f'<span class="signal">{dup_icon} Duplicate rows: {dup_pct:.1f}%</span><br/>'
                        f'<span class="signal">{date_icon} Date parse present</span>', unsafe_allow_html=True)
        st.divider(); st.markdown("**Sample rows**"); st.dataframe(dfx.head(12), use_container_width=True)

# Footer
st.divider(); st.caption("🤖 Powered by Vertex AI & NVIDIA NGC | Built with agnoAGI")

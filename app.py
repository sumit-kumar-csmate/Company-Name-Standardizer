"""
Company Name Normalization Tool v2.0
Streamlit Web Application

VLOOKUP-Friendly Design:
  • Original column NEVER modified
  • "Standardised Name" column added right next to the original
  • Use Standardised Name as the VLOOKUP key in any other Excel file
"""

import streamlit as st
import pandas as pd
import os
import sys
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from company_normalizer.processors.text_cleaner           import clean_text
from company_normalizer.processors.address_remover         import remove_address_details
from company_normalizer.processors.prefix_remover          import remove_prefixes
from company_normalizer.processors.legal_suffix_normalizer import extract_and_normalize_suffix
from company_normalizer.processors.descriptor_checker      import extract_descriptors
from company_normalizer.processors.geographic_matcher      import extract_geography
from company_normalizer.core.merge_engine                  import build_merge_groups
from company_normalizer.core.canonical_generator           import (
    generate_canonical, generate_canonical_for_group, format_canonical_name,
)
from company_normalizer.core.confidence_scorer             import calculate_confidence, get_decision_source
from company_normalizer.processors.ai_refiner              import refine_company_names


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def process_single_name(raw_name: str) -> dict:
    cleaned_display, cleaned_upper = clean_text(raw_name)
    no_address,  removed_address   = remove_address_details(cleaned_upper)
    no_prefix,   removed_prefixes  = remove_prefixes(no_address)
    base_name, legal_suffix, legal_family = extract_and_normalize_suffix(no_prefix)
    return {
        'original':         raw_name,
        'cleaned':          cleaned_display,
        'cleaned_upper':    cleaned_upper,
        'removed_address':  removed_address,
        'removed_prefixes': removed_prefixes,
        'base_name':        base_name,
        'legal_suffix':     legal_suffix,
        'legal_family':     legal_family,
        'descriptors':      extract_descriptors(base_name),
        'geography':        extract_geography(base_name),
    }


def process_dataframe(df: pd.DataFrame, company_col: str, api_key: str = None):
    # Stage 1 — per-name processing
    name_data = [process_single_name(str(row[company_col])) for _, row in df.iterrows()]

    # Stage 2 — merge groups
    # Each group is now a dict: {'indices': [...], 'merge_reason': '...'}
    groups = build_merge_groups(name_data)

    # Stage 3 — assign canonical names & identify AI candidates
    idx_to_canon: dict  = {}
    idx_to_reason: dict = {}   # index → merge_reason for that group
    ai_candidates: set  = set()

    for group in groups:
        indices      = group['indices']
        merge_reason = group['merge_reason']
        canon_raw = generate_canonical_for_group(name_data, indices, merge_reason)
        canon     = format_canonical_name(canon_raw)
        for i in indices:
            idx_to_canon[i]  = canon
            idx_to_reason[i] = merge_reason
            conf, _ = calculate_confidence(name_data[i], merge_reason)
            if conf in ("Medium", "Low"):
                ai_candidates.add(canon)

    # Stage 4 — optional AI refinement
    ai_map: dict = {}
    ai_status: str = "Skipped (AI Disabled)"
    if api_key and ai_candidates:
        with st.spinner(f"🤖 AI verifying {len(ai_candidates)} flagged names …"):
            ai_map, ai_status = refine_company_names(list(ai_candidates), api_key)
    elif api_key and not ai_candidates:
        ai_status = "Skipped (No flags found)"
        st.info("ℹ️ AI enabled, but no Medium/Low confidence names found.")

    # Stage 5 — build output columns
    std_names, conf_scores, flags, ai_names, sources = [], [], [], [], []

    for i, nd in enumerate(name_data):
        canon        = idx_to_canon.get(i, format_canonical_name(generate_canonical(nd)))
        merge_reason = idx_to_reason.get(i, "All rules align")
        ai_can       = ai_map.get(canon, canon)
        conf, flag   = calculate_confidence(nd, merge_reason)

        std_names.append(ai_can)
        conf_scores.append(conf)
        flags.append(flag)
        ai_names.append(ai_can if ai_can != canon else "")
        sources.append("AI + RULE" if ai_can != canon else get_decision_source())

    # Stage 6 — assemble result df (original column untouched)
    result = df.copy()
    col_pos = result.columns.get_loc(company_col) + 1
    result.insert(col_pos, "Standardised Name", std_names)
    result["Confidence Score"] = conf_scores
    result["Review Flag"]      = flags
    if api_key:
        result["AI Verified Name"] = ai_names

    return result, len(name_data), len(groups), ai_status


def to_excel(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Normalised")
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Company Name Normalizer v2.0",
        page_icon="🏢",
        layout="wide",
    )

    # ── CSS ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Compress blank space at the top while keeping header visible */
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }
    [data-testid="stSidebar"] * { margin-top: 0px !important; }
    [data-testid="stSidebar"] > div:first-child { padding-top: 0rem !important; }
    [data-testid="stSidebarUserContent"] { padding-top: 0rem !important; }

    .hero {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        padding: 2.2rem 2.5rem; border-radius: 14px;
        margin-bottom: 1.8rem; border: 1px solid #553c9a;
    }
    .hero h1  { color: #fff; margin: 0; font-size: 2rem; font-weight: 700; }
    .hero p   { color: #b0b8d4; margin: .5rem 0 0; font-size: .95rem; }
    .hero span{ color: #a78bfa; }

    .kpi {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #2d2d6b; border-radius: 10px;
        padding: 1.2rem; text-align: center; color: #fff;
    }
    .kpi .num { font-size: 2.4rem; font-weight: 700; color: #a78bfa; }
    .kpi .lbl { font-size: .8rem; color: #8892b0; margin-top: .3rem; }

    .tip {
        background: #0d1117; border-left: 4px solid #a78bfa;
        border-radius: 8px; padding: .9rem 1.3rem;
        color: #cdd5e0; font-size: .9rem; margin: 1rem 0;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
        color: #fff !important; font-weight: 600 !important;
        border: none !important; border-radius: 9px !important;
        padding: .65rem 2rem !important; font-size: 1rem !important;
        transition: opacity .2s !important;
    }
    div.stButton > button:hover { opacity: .85 !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero">
      <h1>🏢 Company Name Normalizer <span>v2.0</span></h1>
      <p>International Trade Data · Rule-Based Standardisation · VLOOKUP-Ready Output</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        st.markdown("### 🤖 AI Verification")
        st.caption("Model: **gemini-2.5-flash** (via Custom Proxy)")
        api_key = os.environ.get("OPENAI_API_KEY", "")
        
        if api_key:
            enable_ai = st.checkbox("Enable AI Refinement", value=True)
        else:
            enable_ai = st.checkbox("Enable AI Refinement", value=False, disabled=True)
            st.warning("No API key found. Add OPENAI_API_KEY to your .env file to enable AI.")

        st.divider()
        st.markdown("### 📋 Normalisation Rules")
        st.markdown("""
1. Replace special chars with spaces  
   `/  ,  .  '  ;  :  "  (  )  !  …`
2. `&` → `And`  ·  `Pvt` → `Private`  ·  `Ltd` → `Limited`
3. Clean / Trim / Proper (Excel equivalent)
4. Strip trailing address words (Building, Floor, Block …)
5. Remove prefixes (M/S, Messrs, To Order Of …)
6. Normalise legal suffix (Pvt Ltd → Private Limited …)
7. **Word-order normalisation** (jumbled names merged)
8. Singular ↔ Plural (Chemical ↔ Chemicals …)
9. Merge identical base names → one canonical name
10. Confidence scoring + Review flags
11. *(optional)* AI spell-check on flagged names
        """)

        st.divider()
        st.markdown("### 💡 Output Columns")
        st.markdown("""
| Column | Description |
|---|---|
| **Standardised Name** | Use for VLOOKUP |
| Confidence Score | High / Medium / Low |
| Review Flag | YES = needs check |
| AI Verified Name | AI-corrected (if enabled) |
        """)

    # ── File Upload ───────────────────────────────────────────────────────────
    st.markdown("## 📁 Upload File")
    st.markdown(
        '<div class="tip">Upload a CSV or Excel file. The original column is '
        'never modified — standardised names are added in the next column so '
        'you can use VLOOKUP immediately.</div>',
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader("", type=["csv", "xlsx", "xls"],
                                label_visibility="collapsed")

    if uploaded is None:
        st.info("👆 Upload a file to get started.")
        st.markdown("#### Example Input")
        st.dataframe(pd.DataFrame({"Company Name": [
            "M/S Tata Chemical Magadhi Ltd.",
            "Tata Magadhi Chemical Limited",
            "Samsung Electronics Pvt Ltd",
            "Samsung Electronics Private Limited",
            'ABC Corp. Building 5, Floor 3',
        ]}), use_container_width=True)
        return

    # ── Read ──────────────────────────────────────────────────────────────────
    ext = os.path.splitext(uploaded.name)[1].lower()
    try:
        df = pd.read_csv(uploaded) if ext == ".csv" else pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"Could not read file: {e}"); return

    # ── Column selector ───────────────────────────────────────────────────────
    st.markdown("## 🗂️ Select Company Name Column")
    default = next(
        (c for c in df.columns if any(k in c.lower() for k in ["company", "name", "party", "consignee", "shipper"])),
        df.columns[0],
    )
    company_col = st.selectbox("Column", df.columns.tolist(),
                               index=df.columns.tolist().index(default))

    st.markdown("#### Preview (first 10 rows)")
    st.dataframe(df.head(10), use_container_width=True)
    st.caption(f"Total rows: **{len(df):,}**   ·   Selected column: **{company_col}**")

    # ── Process ───────────────────────────────────────────────────────────────
    if st.button("🚀 Standardise Names", use_container_width=True):
        key_to_use = api_key if (enable_ai and api_key) else None
        with st.spinner("Processing …"):
            try:
                result_df, total, n_groups, ai_status = process_dataframe(df, company_col, api_key=key_to_use)
            except Exception as e:
                st.error(f"Processing error: {e}"); st.exception(e); return

        st.success("✅ Output Generated Successfully!")
        
        if enable_ai and api_key:
            if ai_status == "OK":
                st.success(f"🤖 **AI Status:** OK (Model: gemini-2.5-flash)")
            elif ai_status.startswith("Skipped"):
                st.info(f"🤖 **AI Status:** {ai_status}")
            else:
                st.error(f"🤖 **AI Status (Error):** {ai_status}")

        # KPI row
        high   = (result_df["Confidence Score"] == "High").sum()
        medium = (result_df["Confidence Score"] == "Medium").sum()
        low    = (result_df["Confidence Score"] == "Low").sum()
        review = (result_df["Review Flag"] == "YES").sum()

        cols = st.columns(5)
        for col, num, lbl in zip(cols, [total, n_groups, total-n_groups, review, high],
                                  ["Total Names","Canonical Groups","Merged","Needs Review","High Confidence"]):
            col.markdown(
                f'<div class="kpi"><div class="num">{num}</div>'
                f'<div class="lbl">{lbl}</div></div>',
                unsafe_allow_html=True,
            )

        # Confidence
        st.markdown("#### 📈 Confidence Breakdown")
        c1, c2, c3 = st.columns(3)
        c1.metric("🟢 High",   high)
        c2.metric("🟡 Medium", medium)
        c3.metric("🔴 Low",    low)

        # Results table
        st.markdown("#### 📋 Results")
        f1, f2 = st.columns(2)
        only_review  = f1.checkbox("Only rows needing review")
        only_changed = f2.checkbox("Only changed / merged rows")

        disp = result_df.copy()
        if only_review:
            disp = disp[disp["Review Flag"] == "YES"]
        if only_changed:
            disp = disp[disp["Standardised Name"].str.lower() != disp[company_col].str.lower()]

        st.dataframe(disp, use_container_width=True, height=380)

        # Sample transformations
        st.markdown("#### ✨ Sample Transformations")
        show_cols = [c for c in [company_col, "Standardised Name", "Confidence Score", "Review Flag"]
                     if c in result_df.columns]
        changed = result_df[
            result_df["Standardised Name"].str.lower() != result_df[company_col].str.lower()
        ][show_cols].head(10)
        if changed.empty:
            st.info("No changes — all names were already standardised.")
        else:
            st.dataframe(changed, use_container_width=True)

        # Downloads
        st.markdown("#### 💾 Download")
        d1, d2 = st.columns(2)
        stem = uploaded.name.rsplit(".", 1)[0]
        d1.download_button("📥 CSV",
            result_df.to_csv(index=False).encode("utf-8"),
            f"normalised_{stem}.csv", "text/csv",
            use_container_width=True)
        d2.download_button("📥 Excel",
            to_excel(result_df),
            f"normalised_{stem}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)

        st.markdown(
            '<div class="tip">💡 <strong>VLOOKUP Tip:</strong> The '
            '<em>Standardised Name</em> column sits right next to your original '
            'column. All name variations that refer to the same company share '
            'one Standardised Name — making VLOOKUP work across all variations.'
            '</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()

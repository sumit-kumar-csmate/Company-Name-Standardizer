"""
Company Name Normalization Tool v2.1
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
api_key = os.getenv("OPENAI_API_KEY")

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
from company_normalizer.processors.manual_corrector        import apply_manual_corrections


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def process_single_name(raw_name: str) -> dict:
    raw_name = apply_manual_corrections(str(raw_name))   # Step 0: manual corrections
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


def process_dataframe(df: pd.DataFrame, company_col: str, api_key: str = None, model_name: str = "gemini-2.5-flash"):
    # Stage 1 — per-name processing
    name_data = [process_single_name(str(row[company_col])) for _, row in df.iterrows()]

    # Stage 2 — merge groups
    # Each group is now a dict: {'indices': [...], 'merge_reason': '...'}
    groups, base_to_families = build_merge_groups(name_data)

    # Stage 3 — assign canonical names & identify AI candidates
    idx_to_canon: dict  = {}
    idx_to_reason: dict = {}   # index → merge_reason for that group
    ai_candidates: set  = set()

    for group in groups:
        indices      = group['indices']
        merge_reason = group['merge_reason']
        canon_raw = generate_canonical_for_group(name_data, indices, merge_reason, base_to_families)
        canon     = format_canonical_name(canon_raw)
        for i in indices:
            idx_to_canon[i]  = canon
            idx_to_reason[i] = merge_reason
            conf, _ = calculate_confidence(name_data[i], merge_reason)
    # --- STAGE 4: AI REFINEMENT (Intelligent Grouping) ---
    # Prepare confidence scores for all rows
    confidence_scores = []
    for i in range(len(name_data)):
        merge_reason = idx_to_reason.get(i, "None")
        conf, _ = calculate_confidence(name_data[i], merge_reason)
        confidence_scores.append(conf)

    # Group ALL unique canonicals by similarity first
    unique_canons = sorted(list(set(idx_to_canon.values())))
    from company_normalizer.processors.ai_refiner import group_similar_names
    all_groups = group_similar_names(unique_canons)
    
    # Determine which groups need AI (at least one member is Med/Low confidence)
    ai_candidates = set()
    for group in all_groups:
        needs_ai = False
        for canon_name in group:
            # Find any row that matches this canonical name and check its confidence
            for i, c in idx_to_canon.items():
                if c == canon_name and confidence_scores[i] in ["Medium", "Low"]:
                    needs_ai = True
                    break
            if needs_ai: break
        
        if needs_ai:
            for canon_name in group:
                ai_candidates.add(canon_name)

    # Populate near_dup_canons for visual highlighting in the UI (Tiffany Blue)
    near_dup_canons = set()
    for group in all_groups:
        if len(group) > 1:
            for name in group:
                near_dup_canons.add(name)

    # Stage 4 — ask AI to refine
    idx_to_final_canon = idx_to_canon.copy()
    ai_status = "Skipped (No API Key)"
    
    if api_key and ai_candidates:
        st.info(f"🤖 Flagged {len(ai_candidates)} unique groups for AI verification...")
        progress_bar = st.progress(0)
        
        def progress_callback(current, total, eta_seconds):
            pct = int((current / total) * 100) if total > 0 else 0
            eta_str = f"{int(eta_seconds)}s" if eta_seconds > 0 else "Calc..."
            text = f"🤖 AI verifying {current} of {total} flagged names ({pct}%) | ETA: {eta_str}"
            progress_bar.progress(current / total if total > 0 else 0, text=text)

        raw_ai_map, ai_status = refine_company_names(
            list(ai_candidates), 
            api_key, 
            model_name=model_name,
            progress_callback=progress_callback
        )
        progress_bar.empty()
            
        # --- RE-GROUPING POST-AI ---
        # 1. Apply AI fixes to their respective groups
        post_ai_name_data = []
        for i, nd in enumerate(name_data):
            old_canon = idx_to_canon.get(i, "")
            
            # If the original canonical name was refined by AI, use it.
            # If it wasn't returned by AI, or failed, fallback to old_canon.
            ai_refined = raw_ai_map.get(old_canon, old_canon)
            if not ai_refined:
                ai_refined = old_canon
                
            post_ai_name_data.append(process_single_name(ai_refined))

        # 2. Re-build merge partitions from scratch on the cleaned text
        post_groups, post_base_to_families = build_merge_groups(post_ai_name_data)
        
        # 3. Determine final legal suffix & formatting
        for group in post_groups:
            indices = group['indices']
            reason  = group['merge_reason']
            final_canon = format_canonical_name(generate_canonical_for_group(post_ai_name_data, indices, reason, post_base_to_families))
            for i in indices:
                idx_to_final_canon[i] = final_canon

    elif api_key and not ai_candidates:
        ai_status = "Skipped (No flags found)"
        st.info("ℹ️ AI enabled, but no Medium/Low confidence names found.")

    # Stage 5 — build output columns
    std_names, conf_scores, flags, ai_names, sources = [], [], [], [], []

    for i, nd in enumerate(name_data):
        raw_canon    = idx_to_canon.get(i, format_canonical_name(generate_canonical(nd)))
        final_canon  = idx_to_final_canon.get(i, raw_canon)
        merge_reason = idx_to_reason.get(i, "All rules align")
        
        # The confidence was generated purely off the ORIGINAL input vs original reason
        conf, flag   = calculate_confidence(nd, merge_reason)

        std_names.append(final_canon)
        conf_scores.append(conf)
        flags.append(flag)
        ai_names.append(final_canon if final_canon != raw_canon else "")
        sources.append("AI + RULE" if final_canon != raw_canon else get_decision_source())

    # --- NEW SUBSET DETECTION LOGIC ---
    unique_std = list(set(std_names))
    subset_involved = set()
    
    # Pad with spaces for exact word boundary match
    padded = {n: f" {str(n).lower()} " for n in unique_std if isinstance(n, str)}
    for i in range(len(unique_std)):
        for j in range(i+1, len(unique_std)):
            n1 = unique_std[i]
            n2 = unique_std[j]
            if not isinstance(n1, str) or not isinstance(n2, str):
                continue
            
            p1 = padded[n1]
            p2 = padded[n2]
            
            w1 = len(n1.split())
            w2 = len(n2.split())
            if w1 == 0 or w2 == 0:
                continue

            # Check for contiguous word subsets
            if len(p1) > len(p2):
                if p2 in p1:
                    subset_involved.add(n1)
                    subset_involved.add(n2)
            elif len(p2) > len(p1):
                if p1 in p2:
                    subset_involved.add(n1)
                    subset_involved.add(n2)

    subset_highlights = []
    for i in range(len(std_names)):
        n = std_names[i]
        if n in subset_involved:
            flags[i] = "YES"
            # Ensure it is flagged for review by keeping confidence <= Medium
            if conf_scores[i] == "High":
                conf_scores[i] = "Medium"
            subset_highlights.append(True)
        else:
            subset_highlights.append(False)
    # --------------------------------

    # Near-dup flag mutation — must run BEFORE Stage 6 writes lists into the df.
    # IMPORTANT: use idx_to_canon (pre-AI canonical) not std_names (post-AI),
    # because the AI may have corrected a name (e.g. COFOC→COFCO) which would
    # change the string and break the near_dup_canons lookup.
    near_dup_highlights = []
    for i in range(len(std_names)):
        original_canon = idx_to_canon.get(i, std_names[i])
        if original_canon in near_dup_canons:
            flags[i] = "YES"
            if conf_scores[i] == "High":
                conf_scores[i] = "Medium"
            near_dup_highlights.append(True)
        else:
            near_dup_highlights.append(False)
    # --------------------------------


    # Stage 6 — assemble result df (original column untouched)
    result = df.copy()
    
    # Remove existing generated columns to avoid insertion errors if re-processing an output file
    cols_to_remove = ["Standardised Name", "Confidence Score", "Review Flag", "AI Verified Name", "Subset Highlight", "Near Dup Highlight"]
    for col in cols_to_remove:
        if col in result.columns:
            result.drop(columns=[col], inplace=True)
            
    col_pos = result.columns.get_loc(company_col) + 1
    result.insert(col_pos, "Standardised Name", std_names)
    result["Confidence Score"] = conf_scores
    result["Review Flag"]      = flags
    if api_key:
        result["AI Verified Name"] = ai_names
    result["Subset Highlight"]   = subset_highlights
    result["Near Dup Highlight"] = near_dup_highlights

    return result, len(name_data), len(groups), ai_status, near_dup_canons


def to_excel(styled_obj) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        styled_obj.to_excel(w, index=False, sheet_name="Normalised")
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Company Name Normalizer v2.1",
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
      <h1>🏢 Company Name Normalizer <span>v2.1</span></h1>
      <p>International Trade Data · Rule-Based Standardisation · VLOOKUP-Ready Output</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        if api_key:
            enable_ai = st.checkbox("Enable AI Refinement", value=True)
            model_to_use = st.selectbox(
                "Select Model",
                ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
                index=0,
                help="Choose the model for name verification. 2.5/2.0 are recommended for speed."
            )
        else:
            enable_ai = st.checkbox("Enable AI Refinement", value=False, disabled=True)
            model_to_use = "gemini-2.5-flash"
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
10. **Intelligent AI Grouping** (15-char / 70% similarity transitive clusters)
11. **Firm Unification** (Unified output for similar groups)
12. **Aggressive Noise Removal** (Strip NTNs, Bank Details, Branches)
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

    # ── Data Preview ──────────────────────────────────────────────────────────
    company_col = df.columns[0]
    st.markdown("#### Preview (first 10 rows)")
    st.dataframe(df.head(10), use_container_width=True)
    st.caption(f"Total rows: **{len(df):,}**   ·   Column processed: **{company_col}**")

    # ── Process ───────────────────────────────────────────────────────────────
    if st.button("🚀 Standardise Names", use_container_width=True):
        key_to_use = api_key if (enable_ai and api_key) else None
        with st.spinner("Processing …"):
            try:
                result_df, total, n_groups, ai_status, near_dup_canons = process_dataframe(df, company_col, api_key=key_to_use, model_name=model_to_use)
            except Exception as e:
                st.error(f"Processing error: {e}"); st.exception(e); return

        st.success("✅ Output Generated Successfully!")
        
        if enable_ai and api_key:
            if ai_status == "OK":
                st.success(f"🤖 **AI Status:** OK — names refined successfully.")
            elif ai_status.startswith("Skipped"):
                st.info(f"🤖 **AI Status:** {ai_status}")
            elif "Proxy Error" in ai_status or "proxy" in ai_status.lower():
                st.warning(
                    f"⚠️ **AI Proxy Unavailable** — The proxy server (`proxy.abhibots.com`) "
                    f"is currently down. Rule-based results are still complete and accurate. "
                    f"Try again later to apply AI refinement."
                )
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

        # Prepare row highlighting:
        #   Yellow  = subset name pair
        #   Orange  = near-duplicate pair (≥90% similar, sent to AI)
        subset_indices   = result_df.index[result_df["Subset Highlight"] == True].tolist()
        near_dup_indices = result_df.index[result_df["Near Dup Highlight"] == True].tolist()

        def highlight_rows(x):
            df_styles = pd.DataFrame('', index=x.index, columns=x.columns)
            # Near-dup first (orange), then subset (yellow) — subset takes precedence
            mask_nd = df_styles.index.isin(near_dup_indices)
            df_styles.loc[mask_nd, :] = 'background-color: #B5ECEA; color: #000000;'
            mask_ss = df_styles.index.isin(subset_indices)
            df_styles.loc[mask_ss, :] = 'background-color: #FFFF00; color: #000000;'
            return df_styles

        disp_to_show = disp.drop(columns=["Subset Highlight", "Near Dup Highlight"])

        st.dataframe(disp_to_show.style.apply(highlight_rows, axis=None), use_container_width=True, height=380)

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
        
        # Prepare components for download
        export_df = result_df.drop(columns=["Subset Highlight", "Near Dup Highlight"])
        export_styled = export_df.style.apply(highlight_rows, axis=None)

        d1.download_button(
            label="📥 CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name=f"normalised_{stem}.csv",
            mime="text/csv",
            use_container_width=True
        )
        d2.download_button(
            label="📥 Excel",
            data=to_excel(export_styled),
            file_name=f"normalised_{stem}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        st.markdown(
            '<div class="tip">💡 <strong>VLOOKUP Tip:</strong> The '
            '<em>Standardised Name</em> column sits right next to your original '
            'column. All name variations that refer to the same company share '
            'one Standardised Name — making VLOOKUP work across all variations.'
            '</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()

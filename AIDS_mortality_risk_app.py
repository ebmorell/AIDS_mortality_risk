"""
============================================================
HIV MORTALITY RISK ESTIMATOR — Cox Proportional Hazards Model
============================================================
Author: [Your name / Institution]
Last updated: 2026

IMPORTANT — BASELINE SURVIVAL PLACEHOLDER
------------------------------------------
The constant BASELINE_SURVIVAL_5Y below is a PLACEHOLDER value (0.85).
It MUST be replaced with the true baseline survival at 5 years obtained
from your fitted Cox model in R BEFORE using this app clinically.

HOW TO REPLACE IT IN R:
    fit <- coxph(Surv(time, status) ~ ..., data = your_data)
    bh  <- basehaz(fit, centered = FALSE)
    # Extract cumulative baseline hazard at t = 5 years (or closest timepoint)
    H0_5  <- bh$hazard[which.min(abs(bh$time - 5))]
    S0_5  <- exp(-H0_5)          # <-- This is the value you need
    cat("BASELINE_SURVIVAL_5Y =", S0_5)

Then paste the printed value below, replacing 0.85.
============================================================
"""

import math
import streamlit as st

# ============================================================
# BASELINE SURVIVAL — REPLACE THIS VALUE (see header above)
# ============================================================
BASELINE_SURVIVAL_5Y = 0.85   # PLACEHOLDER — replace with S0(5) from R


# ============================================================
# COEFFICIENT DICTIONARIES
# All beta values come from the Cox model output.
# Reference categories have coefficient 0 and are listed first.
# ============================================================

COEFFS_SUBGROUP = {
    "Reference subgroup":                        0.00000,
    "Cervical cancer":                           0.81531,
    "HIV encephalopathy":                       -0.09520,
    "Fungal infections":                        -0.07313,
    "Non-Hodgkin lymphoma":                      0.82300,
    "Mycobacterial infections":                 -0.27919,
    "Other opportunistic infections":           -0.51912,
    "Pneumocystis pneumonia":                   -0.73950,
    "Kaposi sarcoma":                           -0.19511,
    "Viral infections":                         -0.06626,
    "Wasting syndrome":                          0.07644,
    "Progressive multifocal leukoencephalopathy": 0.57226,
    "Toxoplasmosis":                             0.30942,
}

COEFFS_SEX = {
    "Female (reference)":   0.00000,
    "Male":                -0.24394,
}

COEFFS_ART = {
    "Reference regimen":    0.00000,
    "2NRTI + 1PI":          0.22584,
    "2NRTI + 1II":          0.15257,
    "Other / Unknown":     -0.10772,
}

COEFFS_HCV = {
    "Negative (reference)": 0.00000,
    "Positive":             0.53394,
    "Unknown":              1.20466,
}

COEFFS_HBV = {
    "Negative (reference)": 0.00000,
    "Positive":             0.39141,
    "Unknown":              0.19793,
}

COEFFS_AGE = {
    "< 50 years (reference)": 0.00000,
    "≥ 50 years":             0.55588,
}

COEFFS_TRANSMISSION = {
    "Reference transmission category": 0.00000,
    "UDI":                             0.19497,
    "Heterosexual":                    0.20830,
    "Other / Unknown":                 0.23573,
}

COEFFS_EDUCATION = {
    "Reference education category":         0.00000,
    "Upper secondary or university":       -0.37606,
    "Unknown":                              0.23687,
}

COEFFS_YEAR = {
    "Reference period":   0.00000,
    "2008–2011":          0.07516,
    "2012–2015":         -0.23015,
    "2016–2019":         -0.39495,
    "2020–2024":         -0.34554,
}

COEFFS_ORIGIN = {
    "Non-Spanish (reference)": 0.00000,
    "Spanish":                 0.35238,
}

COEFFS_VL = {
    "Reference viral load category":   0.00000,
    "≥ 100,000 copies/mL":             0.18665,
    "Unknown":                        -0.22933,
}

COEFFS_CD4 = {
    "Reference CD4 category":   0.00000,
    "≥ 200 cells/μL":          -0.23757,
    "Unknown":                  1.95215,
}


# ============================================================
# MODEL CALCULATION FUNCTIONS
# ============================================================

def calculate_linear_predictor(
    subgroup, sex, art, hcv, hbv, age, transmission,
    education, year, origin, vl, cd4
):
    """
    Calculate the linear predictor (LP) as the sum of all
    beta_i * X_i terms.  Reference categories contribute 0.
    """
    lp = (
        COEFFS_SUBGROUP[subgroup]
        + COEFFS_SEX[sex]
        + COEFFS_ART[art]
        + COEFFS_HCV[hcv]
        + COEFFS_HBV[hbv]
        + COEFFS_AGE[age]
        + COEFFS_TRANSMISSION[transmission]
        + COEFFS_EDUCATION[education]
        + COEFFS_YEAR[year]
        + COEFFS_ORIGIN[origin]
        + COEFFS_VL[vl]
        + COEFFS_CD4[cd4]
    )
    return lp


def calculate_survival_5y(lp):
    """
    Predicted survival at 5 years using the Cox formula:
        S(5 | X) = S0(5) ^ exp(LP)
    where S0(5) is the baseline survival at t = 5 years.
    """
    return BASELINE_SURVIVAL_5Y ** math.exp(lp)


def calculate_mortality_5y(survival_5y):
    """5-year mortality risk = 1 - S(5 | X)."""
    return 1.0 - survival_5y


def get_risk_category(mortality_risk):
    """Classify the patient into a risk tier."""
    if mortality_risk < 0.10:
        return "Low risk", "#2ecc71"
    elif mortality_risk <= 0.20:
        return "Intermediate risk", "#f39c12"
    else:
        return "High risk", "#e74c3c"


# ============================================================
# STREAMLIT PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="HIV Mortality Risk Estimator",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---- Custom CSS for a clean clinical look ----
st.markdown("""
<style>
    /* Global font and background */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* Header */
    .main-title {
        font-family: 'DM Serif Display', serif;
        font-size: 2.1rem;
        color: #1a2e44;
        margin-bottom: 0;
        line-height: 1.2;
    }
    .main-subtitle {
        font-size: 0.95rem;
        color: #5a7184;
        margin-top: 0.2rem;
        margin-bottom: 1.5rem;
    }

    /* Section headers */
    .section-header {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #8099af;
        margin-top: 1.4rem;
        margin-bottom: 0.4rem;
        border-bottom: 1px solid #e4eaf0;
        padding-bottom: 0.3rem;
    }

    /* Result cards */
    .result-card {
        background: #f5f8fc;
        border-radius: 10px;
        padding: 1rem 1.3rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid #2c7be5;
    }
    .result-label {
        font-size: 0.78rem;
        color: #5a7184;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.15rem;
    }
    .result-value {
        font-size: 1.85rem;
        font-weight: 500;
        color: #1a2e44;
        line-height: 1.1;
    }
    .result-sub {
        font-size: 0.8rem;
        color: #8099af;
        margin-top: 0.1rem;
    }

    /* Risk badge */
    .risk-badge {
        display: inline-block;
        padding: 0.25rem 0.9rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        color: white;
        margin-top: 0.3rem;
    }

    /* Disclaimer box */
    .disclaimer-box {
        background: #fffbe6;
        border: 1px solid #ffe082;
        border-radius: 8px;
        padding: 0.9rem 1.1rem;
        font-size: 0.85rem;
        color: #5d4e00;
        margin-top: 1rem;
    }
    .disclaimer-box strong {
        color: #3d3300;
    }

    /* Interpretation box */
    .interp-box {
        background: #eef4fb;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        font-size: 0.93rem;
        color: #1a2e44;
        line-height: 1.6;
        margin-bottom: 0.8rem;
    }

    /* Gauge bar container */
    .gauge-track {
        background: #e4eaf0;
        border-radius: 8px;
        height: 18px;
        width: 100%;
        overflow: hidden;
        margin: 0.5rem 0 0.3rem;
    }
    .gauge-fill {
        height: 100%;
        border-radius: 8px;
        transition: width 0.5s ease;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ============================================================
# PAGE HEADER
# ============================================================

st.markdown('<p class="main-title">🩺 HIV Mortality Risk Estimator</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="main-subtitle">Cox proportional hazards model · '
    'Predicts 5-year all-cause mortality in people living with HIV initiating ART</p>',
    unsafe_allow_html=True,
)

# Baseline survival warning ribbon
st.info(
    "⚠️ **Placeholder baseline survival in use.** "
    "The value `BASELINE_SURVIVAL_5Y = 0.85` is a placeholder. "
    "Replace it at the top of the script with the true S₀(5) from your fitted R model "
    "before clinical use. Absolute risk estimates are not valid until this is done."
)

st.markdown("---")

# ============================================================
# TWO-COLUMN LAYOUT — Inputs (left) | Results (right)
# ============================================================
col_input, col_result = st.columns([1.1, 1], gap="large")

# ─────────────────────────────────────────
# LEFT COLUMN — PATIENT CHARACTERISTICS
# ─────────────────────────────────────────
with col_input:
    st.markdown('<p class="section-header">Patient Characteristics</p>', unsafe_allow_html=True)

    # 1. AIDS-defining subgroup
    st.markdown("**1. AIDS-defining condition subgroup**")
    subgroup = st.selectbox(
        "Subgroup",
        options=list(COEFFS_SUBGROUP.keys()),
        label_visibility="collapsed",
    )

    # 2. Sex
    st.markdown("**2. Sex**")
    sex = st.selectbox("Sex", options=list(COEFFS_SEX.keys()), label_visibility="collapsed")

    # 3. Initial ART regimen
    st.markdown("**3. Initial ART regimen**")
    art = st.selectbox("ART", options=list(COEFFS_ART.keys()), label_visibility="collapsed")

    # 4. HCV status
    st.markdown("**4. Hepatitis C (HCV) status**")
    hcv = st.selectbox("HCV", options=list(COEFFS_HCV.keys()), label_visibility="collapsed")

    # 5. HBV status
    st.markdown("**5. Hepatitis B (HBV) status**")
    hbv = st.selectbox("HBV", options=list(COEFFS_HBV.keys()), label_visibility="collapsed")

    # 6. Age category
    st.markdown("**6. Age category**")
    age = st.selectbox("Age", options=list(COEFFS_AGE.keys()), label_visibility="collapsed")

    # 7. HIV transmission category
    st.markdown("**7. HIV transmission category**")
    transmission = st.selectbox(
        "Transmission",
        options=list(COEFFS_TRANSMISSION.keys()),
        label_visibility="collapsed",
    )

    # 8. Education level
    st.markdown("**8. Educational level**")
    education = st.selectbox(
        "Education",
        options=list(COEFFS_EDUCATION.keys()),
        label_visibility="collapsed",
    )

    # 9. Year of ART initiation
    st.markdown("**9. Year of ART initiation**")
    year = st.selectbox(
        "Year of ART initiation",
        options=list(COEFFS_YEAR.keys()),
        label_visibility="collapsed",
    )

    # 10. Country of origin
    st.markdown("**10. Country of origin**")
    origin = st.selectbox(
        "Origin",
        options=list(COEFFS_ORIGIN.keys()),
        label_visibility="collapsed",
    )

    # 11. Baseline viral load
    st.markdown("**11. Baseline viral load**")
    vl = st.selectbox(
        "Viral load",
        options=list(COEFFS_VL.keys()),
        label_visibility="collapsed",
    )

    # 12. Baseline CD4 count
    st.markdown("**12. Baseline CD4 cell count**")
    cd4 = st.selectbox("CD4", options=list(COEFFS_CD4.keys()), label_visibility="collapsed")

    st.markdown("")
    run = st.button("⚡  Calculate Risk", type="primary", use_container_width=True)


# ─────────────────────────────────────────
# RIGHT COLUMN — RESULTS
# ─────────────────────────────────────────
with col_result:
    st.markdown('<p class="section-header">Prediction Results</p>', unsafe_allow_html=True)

    # Calculate on every interaction (Streamlit re-runs on any widget change)
    # or explicitly on button click — here we always show results live.
    lp = calculate_linear_predictor(
        subgroup, sex, art, hcv, hbv, age,
        transmission, education, year, origin, vl, cd4,
    )
    rel_hazard = math.exp(lp)
    surv_5y    = calculate_survival_5y(lp)
    mort_5y    = calculate_mortality_5y(surv_5y)
    risk_label, risk_color = get_risk_category(mort_5y)

    # ---- Summary card: selected subgroup ----
    st.markdown(
        f"""
        <div class="result-card" style="border-left-color: #6c8ebf;">
            <div class="result-label">AIDS-defining condition</div>
            <div style="font-size:1.05rem; font-weight:500; color:#1a2e44;">{subgroup}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Linear predictor ----
    st.markdown(
        f"""
        <div class="result-card">
            <div class="result-label">Linear Predictor (LP)</div>
            <div class="result-value">{lp:+.4f}</div>
            <div class="result-sub">Sum of β·X across all covariates</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Relative hazard ----
    st.markdown(
        f"""
        <div class="result-card">
            <div class="result-label">Relative Hazard · exp(LP)</div>
            <div class="result-value">{rel_hazard:.3f}</div>
            <div class="result-sub">Hazard ratio relative to reference patient (all covariates at reference)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- 5-year survival ----
    st.markdown(
        f"""
        <div class="result-card" style="border-left-color: #2ecc71;">
            <div class="result-label">Estimated 5-Year Survival</div>
            <div class="result-value" style="color:#27ae60;">{surv_5y * 100:.1f}%</div>
            <div class="result-sub">S(5 | X) = S₀(5) ^ exp(LP)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- 5-year mortality risk + gauge ----
    gauge_pct = min(mort_5y * 100, 100)
    st.markdown(
        f"""
        <div class="result-card" style="border-left-color: {risk_color};">
            <div class="result-label">Estimated 5-Year Mortality Risk</div>
            <div class="result-value" style="color:{risk_color};">{mort_5y * 100:.1f}%</div>
            <div class="gauge-track">
                <div class="gauge-fill"
                     style="width:{gauge_pct:.1f}%; background:{risk_color};"></div>
            </div>
            <span class="risk-badge" style="background:{risk_color};">{risk_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Risk thresholds legend
    st.markdown(
        "<small style='color:#8099af;'>Risk tiers: "
        "<b style='color:#2ecc71;'>Low</b> &lt;10% · "
        "<b style='color:#f39c12;'>Intermediate</b> 10–20% · "
        "<b style='color:#e74c3c;'>High</b> &gt;20%</small>",
        unsafe_allow_html=True,
    )

    # ============================================================
    # CLINICAL INTERPRETATION
    # ============================================================
    st.markdown('<p class="section-header" style="margin-top:1.6rem;">Clinical Interpretation</p>',
                unsafe_allow_html=True)

    tier_text = risk_label.lower()
    st.markdown(
        f"""
        <div class="interp-box">
            <b>Summary:</b> This patient has an estimated 5-year mortality risk of
            <b>{mort_5y * 100:.1f}%</b>, corresponding to a <b>{tier_text}</b> profile
            (relative hazard {rel_hazard:.2f}× vs. the reference patient).<br><br>
            <b>Key prognostic drivers in this model</b> include the type of AIDS-defining
            condition (particularly Non-Hodgkin lymphoma and cervical cancer confer higher risk;
            Pneumocystis pneumonia and other opportunistic infections confer lower risk),
            baseline CD4 count (unknown CD4 carries substantially elevated risk),
            HCV and HBV co-infection status, age ≥ 50 years, and educational level.<br><br>
            <b>ART era effect:</b> patients initiating ART in 2016–2024 show meaningfully
            lower predicted risk compared with earlier cohorts, consistent with improvements
            in antiretroviral therapy and care.<br><br>
            <i>This tool is based on a Cox proportional hazards model and should be
            interpreted within the full clinical context of the individual patient.</i>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ============================================================
    # METHODOLOGICAL NOTE / DISCLAIMER
    # ============================================================
    st.markdown('<p class="section-header">Methodological Note &amp; Disclaimer</p>',
                unsafe_allow_html=True)

    st.markdown(
        """
        <div class="disclaimer-box">
            <strong>⚕ This is a prediction support tool — not a substitute for clinical judgment.</strong><br><br>
            • Estimates are derived from a <b>Cox proportional hazards model</b> fitted on a
              specific HIV cohort. Performance may differ in other populations.<br>
            • Absolute risk figures depend critically on <b>S₀(5)</b>, the baseline
              survival at 5 years. The current value (<code>BASELINE_SURVIVAL_5Y</code>)
              is a placeholder and <b>must be replaced</b> before clinical use.<br>
            • The model assumes proportional hazards over time and does not account for
              time-varying covariates or treatment changes after ART initiation.<br>
            • Individual predictions carry uncertainty. No threshold should be used
              mechanically to make treatment or management decisions.<br>
            • Always integrate this estimate with the patient's full clinical picture,
              comorbidities, treatment history, and preferences.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Compact model specification expander
    with st.expander("Model specification & coefficients"):
        st.markdown("""
**Model type:** Cox proportional hazards · **Outcome:** All-cause mortality  
**Prediction formula:**
```
LP  = Σ βᵢ · Xᵢ
S(5 | X) = BASELINE_SURVIVAL_5Y ^ exp(LP)
Risk(5)  = 1 − S(5 | X)
```
**BASELINE_SURVIVAL_5Y** = current placeholder value shown below:
""")
        st.code(f"BASELINE_SURVIVAL_5Y = {BASELINE_SURVIVAL_5Y}  # PLACEHOLDER — replace with true S₀(5) from R")

        st.markdown("**Coefficients used:**")
        all_coeffs = {
            "AIDS-defining subgroup": COEFFS_SUBGROUP,
            "Sex": COEFFS_SEX,
            "Initial ART regimen": COEFFS_ART,
            "HCV status": COEFFS_HCV,
            "HBV status": COEFFS_HBV,
            "Age category": COEFFS_AGE,
            "HIV transmission": COEFFS_TRANSMISSION,
            "Education": COEFFS_EDUCATION,
            "Year of ART initiation": COEFFS_YEAR,
            "Country of origin": COEFFS_ORIGIN,
            "Baseline viral load": COEFFS_VL,
            "Baseline CD4": COEFFS_CD4,
        }
        for var_name, coeff_dict in all_coeffs.items():
            st.markdown(f"*{var_name}*")
            for cat, beta in coeff_dict.items():
                st.markdown(f"  &nbsp;&nbsp;`{beta:+.5f}` — {cat}")

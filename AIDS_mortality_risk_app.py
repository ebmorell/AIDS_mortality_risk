"""
============================================================
HIV MORTALITY RISK ESTIMATOR — Cox Proportional Hazards Model
============================================================
Author: [Your name / Institution]
Last updated: 2026

BASELINE SURVIVAL — HOW TO UPDATE FROM R
------------------------------------------
To recalculate if the model changes:
    bh   <- basehaz(modelo_cox_ajustado_subgrupos_refinado, centered = FALSE)
    H0_5 <- bh$hazard[which.min(abs(bh$time - 5))]
    S0_5 <- exp(-H0_5)
    cat("BASELINE_SURVIVAL_5Y =", round(S0_5, 6))

Reference categories used in this model:
    - AIDS-defining subgroup : Pneumocystis pneumonia
    - Sex                    : Female
    - ART regimen            : 2NRTI+1NNRTI
    - HCV                    : Negative
    - HBV                    : Negative
    - Age                    : < 50 years
    - HIV transmission       : MSM/Bisexual
    - Education              : No or compulsory education
    - Year of ART initiation : 2004–2007
    - Country of origin      : Non-Spanish
    - Baseline viral load    : < 100,000 copies/mL
    - Baseline CD4           : < 200 cells/μL
============================================================
"""

import math
import streamlit as st

# ============================================================
# BASELINE SURVIVAL AT 5 YEARS — from fitted R Cox model
# S0(5) = exp(-H0(5)), centered = FALSE
# ============================================================
BASELINE_SURVIVAL_5Y = 0.989024


# ============================================================
# COEFFICIENT DICTIONARIES
# Reference categories have coefficient 0 and are listed first.
# ============================================================

COEFFS_SUBGROUP = {
    "Pneumocystis pneumonia":                     0.00000,  # reference
    "Bacterial infections":                       0.73950,
    "Cervical cancer":                            1.55481,
    "HIV encephalopathy":                         0.64430,
    "Fungal infections":                          0.66637,
    "Non-Hodgkin lymphoma":                       1.56251,
    "Mycobacterial infections":                   0.46031,
    "Other opportunistic infections":             0.22038,
    "Kaposi sarcoma":                             0.54439,
    "Viral infections":                           0.67324,
    "Wasting syndrome":                           0.81594,
    "Progressive multifocal leukoencephalopathy": 1.31177,
    "Toxoplasmosis":                              1.04892,
}

COEFFS_SEX = {
    "Female":   0.00000,  # reference
    "Male":    -0.24394,
}

COEFFS_ART = {
    "2NRTI + 1NNRTI":   0.00000,  # reference
    "2NRTI + 1PI":      0.22584,
    "2NRTI + 1II":      0.15257,
    "Other / Unknown": -0.10772,
}

COEFFS_HCV = {
    "Negative":  0.00000,  # reference
    "Positive":  0.53394,
    "Unknown":   1.20466,
}

COEFFS_HBV = {
    "Negative":  0.00000,  # reference
    "Positive":  0.39141,
    "Unknown":   0.19793,
}

COEFFS_AGE = {
    "< 50 years":  0.00000,  # reference
    "≥ 50 years":  0.55588,
}

COEFFS_TRANSMISSION = {
    "MSM / Bisexual":   0.00000,  # reference
    "UDI":              0.19497,
    "Heterosexual":     0.20830,
    "Other / Unknown":  0.23573,
}

COEFFS_EDUCATION = {
    "No or compulsory education":      0.00000,  # reference
    "Upper secondary or university":  -0.37606,
    "Unknown":                         0.23687,
}

COEFFS_YEAR = {
    "2004–2007":  0.00000,  # reference
    "2008–2011":  0.07516,
    "2012–2015": -0.23015,
    "2016–2019": -0.39495,
    "2020–2024": -0.34554,
}

COEFFS_ORIGIN = {
    "Non-Spanish":  0.00000,  # reference
    "Spanish":      0.35238,
}

COEFFS_VL = {
    "< 100,000 copies/mL":   0.00000,  # reference
    "≥ 100,000 copies/mL":   0.18665,
    "Unknown":               -0.22933,
}

COEFFS_CD4 = {
    "< 200 cells/μL":   0.00000,  # reference
    "≥ 200 cells/μL":  -0.23757,
    "Unknown":           1.95215,
}


# ============================================================
# MODEL CALCULATION FUNCTIONS
# ============================================================

def calculate_linear_predictor(
    subgroup, sex, art, hcv, hbv, age, transmission,
    education, year, origin, vl, cd4
):
    """LP = Σ βᵢ · Xᵢ. Reference categories contribute 0."""
    return (
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


def calculate_survival_5y(lp):
    """S(5 | X) = S₀(5) ^ exp(LP)"""
    return BASELINE_SURVIVAL_5Y ** math.exp(lp)


def calculate_mortality_5y(survival_5y):
    """5-year mortality risk = 1 − S(5 | X)"""
    return 1.0 - survival_5y


def get_risk_category(mortality_risk):
    """Classify patient into a risk tier with associated colour."""
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

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .main-title {
        font-family: 'DM Serif Display', serif;
        font-size: 2.1rem; color: #1a2e44;
        margin-bottom: 0; line-height: 1.2;
    }
    .main-subtitle {
        font-size: 0.95rem; color: #5a7184;
        margin-top: 0.2rem; margin-bottom: 1.5rem;
    }
    .section-header {
        font-size: 0.78rem; font-weight: 600;
        letter-spacing: 0.12em; text-transform: uppercase;
        color: #8099af; margin-top: 1.4rem; margin-bottom: 0.4rem;
        border-bottom: 1px solid #e4eaf0; padding-bottom: 0.3rem;
    }
    .result-card {
        background: #f5f8fc; border-radius: 10px;
        padding: 1rem 1.3rem; margin-bottom: 0.8rem;
        border-left: 4px solid #2c7be5;
    }
    .result-label {
        font-size: 0.78rem; color: #5a7184; font-weight: 600;
        letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 0.15rem;
    }
    .result-value { font-size: 1.85rem; font-weight: 500; color: #1a2e44; line-height: 1.1; }
    .result-sub   { font-size: 0.8rem; color: #8099af; margin-top: 0.1rem; }
    .risk-badge {
        display: inline-block; padding: 0.25rem 0.9rem; border-radius: 20px;
        font-size: 0.85rem; font-weight: 600; color: white; margin-top: 0.3rem;
    }
    .disclaimer-box {
        background: #fffbe6; border: 1px solid #ffe082; border-radius: 8px;
        padding: 0.9rem 1.1rem; font-size: 0.85rem; color: #5d4e00; margin-top: 1rem;
    }
    .disclaimer-box strong { color: #3d3300; }
    .interp-box {
        background: #eef4fb; border-radius: 8px; padding: 1rem 1.2rem;
        font-size: 0.93rem; color: #1a2e44; line-height: 1.6; margin-bottom: 0.8rem;
    }
    .gauge-track {
        background: #e4eaf0; border-radius: 8px; height: 18px;
        width: 100%; overflow: hidden; margin: 0.5rem 0 0.3rem;
    }
    .gauge-fill { height: 100%; border-radius: 8px; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
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
st.markdown("---")

# ============================================================
# TWO-COLUMN LAYOUT
# ============================================================
col_input, col_result = st.columns([1.1, 1], gap="large")

# ─────────────────────────────────────────
# LEFT COLUMN — PATIENT CHARACTERISTICS
# ─────────────────────────────────────────
with col_input:
    st.markdown('<p class="section-header">Patient Characteristics</p>', unsafe_allow_html=True)

    st.markdown("**1. AIDS-defining condition subgroup**")
    subgroup = st.selectbox("Subgroup", list(COEFFS_SUBGROUP.keys()), label_visibility="collapsed")

    st.markdown("**2. Sex**")
    sex = st.selectbox("Sex", list(COEFFS_SEX.keys()), label_visibility="collapsed")

    st.markdown("**3. Initial ART regimen**")
    art = st.selectbox("ART", list(COEFFS_ART.keys()), label_visibility="collapsed")

    st.markdown("**4. Hepatitis C (HCV) status**")
    hcv = st.selectbox("HCV", list(COEFFS_HCV.keys()), label_visibility="collapsed")

    st.markdown("**5. Hepatitis B (HBV) status**")
    hbv = st.selectbox("HBV", list(COEFFS_HBV.keys()), label_visibility="collapsed")

    st.markdown("**6. Age category**")
    age = st.selectbox("Age", list(COEFFS_AGE.keys()), label_visibility="collapsed")

    st.markdown("**7. HIV transmission category**")
    transmission = st.selectbox("Transmission", list(COEFFS_TRANSMISSION.keys()),
                                label_visibility="collapsed")

    st.markdown("**8. Educational level**")
    education = st.selectbox("Education", list(COEFFS_EDUCATION.keys()),
                             label_visibility="collapsed")

    st.markdown("**9. Year of ART initiation**")
    year = st.selectbox("Year", list(COEFFS_YEAR.keys()), label_visibility="collapsed")

    st.markdown("**10. Country of origin**")
    origin = st.selectbox("Origin", list(COEFFS_ORIGIN.keys()), label_visibility="collapsed")

    st.markdown("**11. Baseline viral load**")
    vl = st.selectbox("Viral load", list(COEFFS_VL.keys()), label_visibility="collapsed")

    st.markdown("**12. Baseline CD4 cell count**")
    cd4 = st.selectbox("CD4", list(COEFFS_CD4.keys()), label_visibility="collapsed")


# ─────────────────────────────────────────
# RIGHT COLUMN — RESULTS
# ─────────────────────────────────────────
with col_result:
    st.markdown('<p class="section-header">Prediction Results</p>', unsafe_allow_html=True)

    lp         = calculate_linear_predictor(
                     subgroup, sex, art, hcv, hbv, age,
                     transmission, education, year, origin, vl, cd4)
    rel_hazard = math.exp(lp)
    surv_5y    = calculate_survival_5y(lp)
    mort_5y    = calculate_mortality_5y(surv_5y)
    risk_label, risk_color = get_risk_category(mort_5y)

    # Selected subgroup
    st.markdown(
        f"""<div class="result-card" style="border-left-color:#6c8ebf;">
            <div class="result-label">AIDS-defining condition</div>
            <div style="font-size:1.05rem;font-weight:500;color:#1a2e44;">{subgroup}</div>
        </div>""", unsafe_allow_html=True)

    # Linear predictor
    st.markdown(
        f"""<div class="result-card">
            <div class="result-label">Linear Predictor (LP)</div>
            <div class="result-value">{lp:+.4f}</div>
            <div class="result-sub">Sum of β·X across all covariates</div>
        </div>""", unsafe_allow_html=True)

    # Relative hazard
    st.markdown(
        f"""<div class="result-card">
            <div class="result-label">Relative Hazard · exp(LP)</div>
            <div class="result-value">{rel_hazard:.3f}</div>
            <div class="result-sub">Hazard ratio vs. reference patient (all covariates at reference)</div>
        </div>""", unsafe_allow_html=True)

    # 5-year survival
    st.markdown(
        f"""<div class="result-card" style="border-left-color:#2ecc71;">
            <div class="result-label">Estimated 5-Year Survival</div>
            <div class="result-value" style="color:#27ae60;">{surv_5y * 100:.1f}%</div>
            <div class="result-sub">S(5 | X) = S₀(5) ^ exp(LP)</div>
        </div>""", unsafe_allow_html=True)

    # 5-year mortality + gauge
    gauge_pct = min(mort_5y * 100, 100)
    st.markdown(
        f"""<div class="result-card" style="border-left-color:{risk_color};">
            <div class="result-label">Estimated 5-Year Mortality Risk</div>
            <div class="result-value" style="color:{risk_color};">{mort_5y * 100:.1f}%</div>
            <div class="gauge-track">
                <div class="gauge-fill" style="width:{gauge_pct:.1f}%;background:{risk_color};"></div>
            </div>
            <span class="risk-badge" style="background:{risk_color};">{risk_label}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown(
        "<small style='color:#8099af;'>Risk tiers: "
        "<b style='color:#2ecc71;'>Low</b> &lt;10% · "
        "<b style='color:#f39c12;'>Intermediate</b> 10–20% · "
        "<b style='color:#e74c3c;'>High</b> &gt;20%</small>",
        unsafe_allow_html=True)

    # ---- Clinical interpretation ----
    st.markdown('<p class="section-header" style="margin-top:1.6rem;">Clinical Interpretation</p>',
                unsafe_allow_html=True)

    st.markdown(
        f"""<div class="interp-box">
            <b>Summary:</b> This patient has an estimated 5-year mortality risk of
            <b>{mort_5y * 100:.1f}%</b>, corresponding to a <b>{risk_label.lower()}</b> profile
            (relative hazard {rel_hazard:.2f}× vs. the reference patient).<br><br>
            <b>Key prognostic drivers</b> include the AIDS-defining condition (Non-Hodgkin lymphoma
            and cervical cancer confer the highest risk relative to Pneumocystis pneumonia),
            unknown baseline CD4 count (markedly elevated risk), HCV and HBV co-infection,
            age ≥ 50 years, and educational attainment.<br><br>
            <b>ART era:</b> patients initiating ART in 2016–2024 show meaningfully lower predicted
            risk compared with the 2004–2007 reference period.<br><br>
            <i>This tool is based on a Cox proportional hazards model and should be interpreted
            within the full clinical context of the individual patient.</i>
        </div>""", unsafe_allow_html=True)

    # ---- Disclaimer ----
    st.markdown('<p class="section-header">Methodological Note &amp; Disclaimer</p>',
                unsafe_allow_html=True)

    st.markdown(
        """<div class="disclaimer-box">
            <strong>⚕ Prediction support tool — not a substitute for clinical judgment.</strong><br><br>
            • Derived from a <b>Cox proportional hazards model</b> (n = 2,666; 403 events;
              C-statistic = 0.727) fitted on a specific HIV cohort. Performance may differ in
              other populations.<br>
            • Assumes proportional hazards; does not account for time-varying covariates or
              treatment changes after ART initiation.<br>
            • Individual predictions carry uncertainty. No threshold should be used mechanically
              to drive treatment decisions.<br>
            • Always integrate with the patient's full clinical picture, comorbidities,
              treatment history, and preferences.
        </div>""", unsafe_allow_html=True)

    # ---- Coefficient reference expander ----
    with st.expander("Model specification & reference categories"):
        st.markdown(f"""
**Model:** Cox proportional hazards · **Outcome:** All-cause mortality  
**N =** 2,666 · **Events =** 403 · **C-statistic =** 0.727  
**S₀(5) =** `{BASELINE_SURVIVAL_5Y}` (baseline survival at 5 years, centered = FALSE)

**Prediction formula:**
```
LP       = Σ βᵢ · Xᵢ
S(5 | X) = {BASELINE_SURVIVAL_5Y} ^ exp(LP)
Risk(5)  = 1 − S(5 | X)
```

**Reference patient** (LP = 0):  
Pneumocystis pneumonia · Female · 2NRTI+1NNRTI · HCV negative · HBV negative ·  
Age < 50 y · MSM/Bisexual · No or compulsory education · ART 2004–2007 ·  
Non-Spanish · Viral load < 100,000 copies/mL · CD4 < 200 cells/μL  
→ Predicted 5-year mortality: {(1 - BASELINE_SURVIVAL_5Y)*100:.2f}%
""")

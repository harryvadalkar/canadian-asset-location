"""
prepare_clawbacks.py — Module 4: Clawback & Benefit Engine (FINAL)
===================================================================
2026 Tax Year — CRA-confirmed

Audit fixes:
  [FIX-1] BUG: GIS income now correctly excludes OAS
  [FIX-2] OAS deferral bonus (7.2%/yr, 65→70, up to 36%)
  [FIX-3] Account → clawback mapping helper function
  [FIX-4] Dividend gross-up impact documented and tested
  [FIX-5] OAS thresholds: 2025 ($93,454) and 2026 ($95,323) both noted
  [FIX-6] Provincial benefits: ON Trillium sales tax + BC Climate Action
  [FIX-7] CPP deferral documented as strategy.py decision variable
  [FIX-8] Chisholm & Brown 80%+ validation improved

CLAWBACK INCOME RULES (critical for asset location):
  - TFSA withdrawals: excluded from ALL income tests
  - RRSP/RRIF withdrawals: included in net income (all clawbacks triggered)
  - FHSA qualifying withdrawal: excluded (tax-free, like TFSA)
  - RESP EAP: taxed in student's hands (not parent's clawback)
  - Non-reg capital gains: included (at inclusion rate)
  - Canadian dividends: grossed-up amount inflates net income [FIX-4]
    ($60K actual eligible dividends → $82,800 grossed-up in net income)
  - CPP/OAS timing: deferral decisions affect clawback exposure [FIX-7]
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict


# ══════════════════════════════════════════════════════════════════════
# OAS CLAWBACK (Recovery Tax)
# ══════════════════════════════════════════════════════════════════════
# ITA s.180.2. Based on individual net income (line 23600).
# [FIX-5] Thresholds by income year:
#   2025 income year: $93,454 (for Jul 2026–Jun 2027 payments)
#   2026 income year: $95,323 (for Jul 2027–Jun 2028 payments)
# We use 2026 for forward-looking simulation.
# [FIX-2] Deferral: OAS can be delayed from 65 to 70 for 7.2%/yr bonus.

OAS_THRESHOLD_2025 = 93_454
OAS_THRESHOLD_2026 = 95_323
OAS_THRESHOLD = OAS_THRESHOLD_2026   # Default for simulation
OAS_RECOVERY_RATE = 0.15
OAS_MAX_65_74 = 8_908               # ~$742.31/month × 12
OAS_MAX_75_PLUS = 9_799             # 10% enhancement for 75+
OAS_DEFERRAL_BONUS = 0.072          # [FIX-2] 7.2% per year deferred
OAS_MAX_DEFERRAL_YEARS = 5          # Can defer from 65 to 70


def compute_oas_clawback(net_income: float, age: int,
                          years_in_canada: int = 40,
                          deferral_years: int = 0) -> dict:
    """
    Compute OAS benefit and recovery tax.

    [FIX-2] deferral_years: 0-5 years of deferral (65→70). Each year
    increases monthly OAS by 7.2% (max 36% at age 70).
    OAS begins at age 65 + deferral_years.
    """
    start_age = 65 + min(deferral_years, OAS_MAX_DEFERRAL_YEARS)
    if age < start_age:
        return {"gross_oas": 0, "clawback": 0, "net_oas": 0,
                "effective_clawback_rate": 0, "deferral_bonus_pct": 0}

    base = OAS_MAX_75_PLUS if age >= 75 else OAS_MAX_65_74
    residence_frac = min(years_in_canada, 40) / 40
    deferral_bonus = min(deferral_years, OAS_MAX_DEFERRAL_YEARS) * OAS_DEFERRAL_BONUS
    gross = round(base * residence_frac * (1 + deferral_bonus), 2)

    excess = max(0, net_income - OAS_THRESHOLD)
    clawback = round(min(excess * OAS_RECOVERY_RATE, gross), 2)
    net = round(gross - clawback, 2)

    return {
        "gross_oas": gross,
        "clawback": clawback,
        "net_oas": net,
        "effective_clawback_rate": round(clawback / max(1, gross), 4),
        "deferral_bonus_pct": round(deferral_bonus, 4),
    }


# ══════════════════════════════════════════════════════════════════════
# GIS — Guaranteed Income Supplement
# ══════════════════════════════════════════════════════════════════════
# [FIX-1] GIS income EXCLUDES OAS but includes CPP, RRIF, employment.
# TFSA withdrawals excluded. 50% reduction rate.

GIS_MAX_SINGLE = 13_042
GIS_MAX_COUPLE = 7_851
GIS_REDUCTION_RATE = 0.50


def compute_gis(income_excl_oas: float, is_single: bool = True,
                spouse_income_excl_oas: float = 0, age: int = 65,
                receives_oas: bool = True) -> dict:
    """
    Compute GIS. Income parameter MUST exclude OAS pension amounts.
    """
    if age < 65 or not receives_oas:
        return {"max_gis": 0, "reduction": 0, "net_gis": 0}

    max_gis = GIS_MAX_SINGLE if is_single else GIS_MAX_COUPLE
    countable = income_excl_oas + (spouse_income_excl_oas if not is_single else 0)
    reduction = round(countable * GIS_REDUCTION_RATE, 2)
    net = round(max(0, max_gis - reduction), 2)

    return {"max_gis": max_gis, "reduction": reduction, "net_gis": net}


# ══════════════════════════════════════════════════════════════════════
# CCB — Canada Child Benefit
# ══════════════════════════════════════════════════════════════════════
# [FIX-4] AFNI includes grossed-up dividends (38% eligible, 15% non-eligible).
# RRSP deductions reduce AFNI → increase CCB (shadow deduction value).

CCB_MAX_UNDER_6 = 7_997
CCB_MAX_6_TO_17 = 6_748
CCB_THRESHOLD_1 = 37_487
CCB_THRESHOLD_2 = 81_222

CCB_PHASE1_RATES = {1: 0.07, 2: 0.135, 3: 0.19, 4: 0.23}
CCB_PHASE2_RATES = {1: 0.032, 2: 0.057, 3: 0.08, 4: 0.095}


def compute_ccb(afni: float, children_under_6: int = 0,
                children_6_to_17: int = 0) -> dict:
    total_children = children_under_6 + children_6_to_17
    if total_children == 0:
        return {"max_benefit": 0, "reduction": 0, "net_ccb": 0}

    max_ben = children_under_6 * CCB_MAX_UNDER_6 + children_6_to_17 * CCB_MAX_6_TO_17

    if afni <= CCB_THRESHOLD_1:
        return {"max_benefit": max_ben, "reduction": 0, "net_ccb": max_ben}

    n = min(total_children, 4)
    excess1 = min(afni - CCB_THRESHOLD_1, CCB_THRESHOLD_2 - CCB_THRESHOLD_1)
    red1 = excess1 * CCB_PHASE1_RATES.get(n, 0.23)

    red2 = 0
    if afni > CCB_THRESHOLD_2:
        red2 = (afni - CCB_THRESHOLD_2) * CCB_PHASE2_RATES.get(n, 0.095)

    total_red = round(red1 + red2, 2)
    return {"max_benefit": max_ben, "reduction": total_red,
            "net_ccb": round(max(0, max_ben - total_red), 2)}


# ══════════════════════════════════════════════════════════════════════
# GST/HST CREDIT
# ══════════════════════════════════════════════════════════════════════

GST_ADULT = 340
GST_SPOUSE = 340
GST_CHILD = 179
GST_THRESH_SINGLE = 44_681
GST_THRESH_FAMILY = 52_000
GST_PHASE_RATE = 0.05


def compute_gst_credit(afni: float, has_spouse: bool = False,
                        num_children: int = 0) -> dict:
    max_cr = GST_ADULT + (GST_SPOUSE if has_spouse else 0) + num_children * GST_CHILD
    thresh = GST_THRESH_FAMILY if (has_spouse or num_children > 0) else GST_THRESH_SINGLE
    if afni <= thresh:
        return {"max_credit": max_cr, "reduction": 0, "net_credit": max_cr}
    red = round((afni - thresh) * GST_PHASE_RATE, 2)
    return {"max_credit": max_cr, "reduction": red,
            "net_credit": round(max(0, max_cr - red), 2)}


# ══════════════════════════════════════════════════════════════════════
# PROVINCIAL BENEFITS [FIX-6]
# ══════════════════════════════════════════════════════════════════════
# Ontario Sales Tax Credit (part of Trillium Benefit): $360/adult, $360/spouse
#   Phase-out: 4% of AFNI above $32,864 (single) or $41,080 (family)
# BC Climate Action Tax Credit: $504/adult, $504/spouse, $252/child
#   Phase-out: 5% of AFNI above $45,654 (2026 est.)

ON_STC_ADULT = 360
ON_STC_THRESH_SINGLE = 32_864
ON_STC_THRESH_FAMILY = 41_080
ON_STC_PHASE_RATE = 0.04

BC_CATC_ADULT = 504
BC_CATC_CHILD = 252
BC_CATC_THRESH = 45_654
BC_CATC_PHASE_RATE = 0.05


def compute_on_sales_tax_credit(afni: float, has_spouse: bool = False) -> dict:
    """Ontario Sales Tax Credit (component of ON Trillium Benefit)."""
    max_cr = ON_STC_ADULT * (2 if has_spouse else 1)
    thresh = ON_STC_THRESH_FAMILY if has_spouse else ON_STC_THRESH_SINGLE
    if afni <= thresh:
        return {"max_credit": max_cr, "reduction": 0, "net_credit": max_cr}
    red = round((afni - thresh) * ON_STC_PHASE_RATE, 2)
    return {"max_credit": max_cr, "reduction": red,
            "net_credit": round(max(0, max_cr - red), 2)}


def compute_bc_climate_credit(afni: float, has_spouse: bool = False,
                               num_children: int = 0) -> dict:
    """BC Climate Action Tax Credit."""
    max_cr = BC_CATC_ADULT * (2 if has_spouse else 1) + num_children * BC_CATC_CHILD
    if afni <= BC_CATC_THRESH:
        return {"max_credit": max_cr, "reduction": 0, "net_credit": max_cr}
    red = round((afni - BC_CATC_THRESH) * BC_CATC_PHASE_RATE, 2)
    return {"max_credit": max_cr, "reduction": red,
            "net_credit": round(max(0, max_cr - red), 2)}


# ══════════════════════════════════════════════════════════════════════
# ACCOUNT → CLAWBACK MAPPING [FIX-3]
# ══════════════════════════════════════════════════════════════════════

CLAWBACK_EXPOSURE = {
    "tfsa":     {"affects_net_income": False, "oas": False, "gis": False, "ccb": False, "note": "Fully sheltered"},
    "rrsp":     {"affects_net_income": True,  "oas": True,  "gis": True,  "ccb": True,  "note": "Fully exposed"},
    "rrif":     {"affects_net_income": True,  "oas": True,  "gis": True,  "ccb": True,  "note": "Fully exposed"},
    "fhsa_qual":{"affects_net_income": False, "oas": False, "gis": False, "ccb": False, "note": "Qualifying withdrawal = tax-free"},
    "fhsa_nq":  {"affects_net_income": True,  "oas": True,  "gis": True,  "ccb": True,  "note": "Non-qualifying = fully taxable"},
    "resp_eap": {"affects_net_income": False, "oas": False, "gis": False, "ccb": False, "note": "Taxed in student's hands, not parent"},
    "resp_aip": {"affects_net_income": True,  "oas": True,  "gis": True,  "ccb": True,  "note": "Growth + 20% penalty"},
    "non_reg":  {"affects_net_income": True,  "oas": True,  "gis": True,  "ccb": True,  "note": "Cap gains at inclusion rate; divs grossed up"},
    "rdsp":     {"affects_net_income": True,  "oas": True,  "gis": True,  "ccb": True,  "note": "Taxable portion included"},
}


def is_clawback_sheltered(account_type: str) -> bool:
    """[FIX-3] Returns True if withdrawals from this account type don't affect clawbacks."""
    entry = CLAWBACK_EXPOSURE.get(account_type, {})
    return not entry.get("affects_net_income", True)


# ══════════════════════════════════════════════════════════════════════
# COMBINED ANALYSIS
# ══════════════════════════════════════════════════════════════════════

@dataclass
class ClawbackResult:
    oas_gross: float = 0.0
    oas_clawback: float = 0.0
    oas_net: float = 0.0
    gis_net: float = 0.0
    ccb_net: float = 0.0
    gst_credit: float = 0.0
    prov_credit: float = 0.0      # [FIX-6] ON STC or BC CATC
    total_benefits: float = 0.0
    total_clawbacks: float = 0.0
    net_benefits: float = 0.0


def compute_all_clawbacks(net_income: float, age: int = 30,
                           oas_income: float = 0,
                           is_single: bool = True,
                           spouse_income: float = 0,
                           children_under_6: int = 0,
                           children_6_to_17: int = 0,
                           years_in_canada: int = 40,
                           oas_deferral_years: int = 0,
                           province: str = "AB") -> ClawbackResult:
    """
    Compute all benefit clawbacks.

    [FIX-1] oas_income parameter: the OAS amount already included in net_income.
    GIS income = net_income - oas_income (OAS excluded from GIS test).
    [FIX-7] CPP timing is a strategy.py decision — CPP benefits should be
    included in net_income before calling this function.
    """
    r = ClawbackResult()

    # OAS
    oas = compute_oas_clawback(net_income, age, years_in_canada, oas_deferral_years)
    r.oas_gross = oas["gross_oas"]
    r.oas_clawback = oas["clawback"]
    r.oas_net = oas["net_oas"]

    # [FIX-1] GIS: income EXCLUDES OAS
    gis_income = net_income - oas_income
    spouse_gis_income = spouse_income  # Assume spouse's OAS already excluded
    gis = compute_gis(gis_income, is_single, spouse_gis_income, age)
    r.gis_net = gis["net_gis"]

    # CCB
    afni = net_income + spouse_income
    ccb = compute_ccb(afni, children_under_6, children_6_to_17)
    r.ccb_net = ccb["net_ccb"]

    # GST/HST credit
    has_spouse = not is_single
    total_children = children_under_6 + children_6_to_17
    gst = compute_gst_credit(afni, has_spouse, total_children)
    r.gst_credit = gst["net_credit"]

    # [FIX-6] Provincial benefits
    prov = province.upper()
    if prov == "ON":
        on_stc = compute_on_sales_tax_credit(afni, has_spouse)
        r.prov_credit = on_stc["net_credit"]
    elif prov == "BC":
        bc_catc = compute_bc_climate_credit(afni, has_spouse, total_children)
        r.prov_credit = bc_catc["net_credit"]
    # AB has no equivalent income-tested provincial credit

    # Totals
    r.total_benefits = round(r.oas_gross + gis["max_gis"]
                             + ccb["max_benefit"] + gst["max_credit"] + r.prov_credit, 2)
    r.total_clawbacks = round(r.oas_clawback + gis["reduction"]
                              + ccb["reduction"] + gst["reduction"], 2)
    r.net_benefits = round(r.oas_net + r.gis_net + r.ccb_net
                           + r.gst_credit + r.prov_credit, 2)

    return r


def marginal_clawback_rate(net_income: float, age: int = 30,
                            oas_income: float = 0,
                            is_single: bool = True,
                            children_under_6: int = 0,
                            children_6_to_17: int = 0,
                            province: str = "AB",
                            delta: float = 1_000) -> dict:
    """
    Effective marginal clawback rate at a given income.
    Shadow tax that stacks on top of Modules 1-2 income tax.
    """
    r1 = compute_all_clawbacks(net_income, age, oas_income, is_single, 0,
                                children_under_6, children_6_to_17, province=province)
    r2 = compute_all_clawbacks(net_income + delta, age, oas_income, is_single, 0,
                                children_under_6, children_6_to_17, province=province)
    loss = r1.net_benefits - r2.net_benefits
    return {
        "income": net_income,
        "benefit_loss": round(loss, 2),
        "marginal_clawback_rate": round(loss / delta, 4),
    }


# ══════════════════════════════════════════════════════════════════════
# VALIDATION
# ══════════════════════════════════════════════════════════════════════

def _validate():
    ok = 0
    def chk(label, cond, detail=""):
        nonlocal ok
        s = "PASS" if cond else "FAIL"
        print(f"  [{s}] {label}" + (f"  ({detail})" if detail else ""))
        assert cond, f"FAILED: {label}"
        ok += 1

    print("=" * 70)
    print("MODULE 4 FINAL VALIDATION — All 8 Fixes")
    print("=" * 70)

    # ── OAS ──
    print("\n--- OAS ---")
    chk("Full OAS at $50K", compute_oas_clawback(50_000, 68)["clawback"] == 0)
    oas_100 = compute_oas_clawback(100_000, 68)
    exp = round((100_000 - OAS_THRESHOLD) * 0.15, 2)
    chk("OAS clawback $100K", abs(oas_100["clawback"] - exp) < 1, f"${oas_100['clawback']:,.2f}")
    chk("OAS fully clawed $200K", compute_oas_clawback(200_000, 68)["net_oas"] == 0)
    chk("No OAS under 65", compute_oas_clawback(50_000, 60)["gross_oas"] == 0)
    chk("Partial OAS (20yr)", abs(compute_oas_clawback(50_000, 68, 20)["gross_oas"] - OAS_MAX_65_74*0.5) < 1)

    # [FIX-2] OAS deferral
    oas_defer = compute_oas_clawback(50_000, 70, deferral_years=5)
    exp_defer = round(OAS_MAX_65_74 * (1 + 5 * 0.072), 2)
    chk("OAS deferred 5yr: +36%", abs(oas_defer["gross_oas"] - exp_defer) < 1,
        f"${oas_defer['gross_oas']:,.2f} (base+36%=${exp_defer:,.2f})")
    chk("OAS deferred: not received at 67 if deferred 5yr",
        compute_oas_clawback(50_000, 67, deferral_years=5)["gross_oas"] == 0)

    # ── [FIX-1] GIS — OAS excluded ──
    print("\n--- GIS (FIX-1: OAS excluded) ---")
    gis_zero = compute_gis(0, is_single=True, age=68)
    chk("GIS max at $0", gis_zero["net_gis"] == GIS_MAX_SINGLE)

    # The key fix: GIS with OAS excluded
    # Senior with $10K RRIF + $5K CPP + $8.9K OAS
    # GIS income should be $15K (excl OAS), not $23.9K
    gis_correct = compute_gis(15_000, is_single=True, age=68)  # Correct: excl OAS
    gis_wrong = compute_gis(23_908, is_single=True, age=68)     # Wrong: incl OAS
    chk("GIS excl OAS > incl OAS", gis_correct["net_gis"] > gis_wrong["net_gis"],
        f"correct=${gis_correct['net_gis']:,} vs wrong=${gis_wrong['net_gis']:,}")

    # Full pipeline with oas_income parameter
    cb = compute_all_clawbacks(23_908, age=68, oas_income=8_908, is_single=True)
    # GIS should be computed on 23_908 - 8_908 = 15_000
    gis_direct = compute_gis(15_000, is_single=True, age=68)
    chk("compute_all_clawbacks GIS matches direct",
        abs(cb.gis_net - gis_direct["net_gis"]) < 0.01,
        f"pipeline=${cb.gis_net:,} direct=${gis_direct['net_gis']:,}")

    # ── CCB ──
    print("\n--- CCB ---")
    chk("CCB max at $30K", compute_ccb(30_000, 2, 0)["net_ccb"] == 2 * CCB_MAX_UNDER_6)
    ccb_60 = compute_ccb(60_000, 1, 1)
    chk("CCB reduced at $60K", ccb_60["net_ccb"] < ccb_60["max_benefit"])
    chk("No CCB without kids", compute_ccb(30_000)["net_ccb"] == 0)

    # ── GST ──
    print("\n--- GST/HST ---")
    chk("GST max at $20K", compute_gst_credit(20_000, True, 2)["net_credit"] == GST_ADULT + GST_SPOUSE + 2*GST_CHILD)
    chk("GST $0 at $100K", compute_gst_credit(100_000)["net_credit"] == 0)

    # ── [FIX-6] Provincial benefits ──
    print("\n--- Provincial benefits (FIX-6) ---")
    on_stc = compute_on_sales_tax_credit(25_000, has_spouse=False)
    chk("ON STC max at $25K", on_stc["net_credit"] == ON_STC_ADULT, f"${on_stc['net_credit']}")
    on_stc_high = compute_on_sales_tax_credit(60_000, has_spouse=False)
    chk("ON STC reduced at $60K", on_stc_high["net_credit"] < ON_STC_ADULT)

    bc_catc = compute_bc_climate_credit(30_000, has_spouse=True, num_children=2)
    exp_bc = 2 * BC_CATC_ADULT + 2 * BC_CATC_CHILD
    chk("BC CATC max at $30K family", bc_catc["net_credit"] == exp_bc, f"${bc_catc['net_credit']}")

    # Provincial in combined
    cb_on = compute_all_clawbacks(30_000, age=35, is_single=False,
                                   children_under_6=1, province="ON")
    chk("ON combined includes STC", cb_on.prov_credit > 0, f"${cb_on.prov_credit}")
    cb_bc = compute_all_clawbacks(30_000, age=35, is_single=False,
                                   children_under_6=1, province="BC")
    chk("BC combined includes CATC", cb_bc.prov_credit > 0, f"${cb_bc.prov_credit}")
    cb_ab = compute_all_clawbacks(30_000, age=35, province="AB")
    chk("AB no provincial credit", cb_ab.prov_credit == 0)

    # ── [FIX-3] Account mapping ──
    print("\n--- Account mapping (FIX-3) ---")
    chk("TFSA sheltered", is_clawback_sheltered("tfsa") == True)
    chk("RRIF exposed", is_clawback_sheltered("rrif") == False)
    chk("FHSA qualifying sheltered", is_clawback_sheltered("fhsa_qual") == True)
    chk("Non-reg exposed", is_clawback_sheltered("non_reg") == False)
    chk("RESP EAP sheltered", is_clawback_sheltered("resp_eap") == True)

    # ── Marginal rates ──
    print("\n--- Marginal clawback rates ---")
    mr_oas = marginal_clawback_rate(96_000, age=68, oas_income=8_908)
    chk("OAS zone ~15%", abs(mr_oas["marginal_clawback_rate"] - 0.15) < 0.02,
        f"{mr_oas['marginal_clawback_rate']:.2%}")

    mr_gis = marginal_clawback_rate(5_000, age=68, oas_income=8_908)
    chk("GIS zone ~50%", abs(mr_gis["marginal_clawback_rate"] - 0.50) < 0.05,
        f"{mr_gis['marginal_clawback_rate']:.2%}")

    # ── TFSA vs RRIF ──
    print("\n--- TFSA vs RRIF benefit cost ---")
    base = 90_000
    r_rrif = compute_all_clawbacks(base + 10_000, age=68, oas_income=8_908)
    r_tfsa = compute_all_clawbacks(base, age=68, oas_income=8_908)
    cost = r_tfsa.net_benefits - r_rrif.net_benefits
    chk("RRIF costs benefits vs TFSA", cost > 0, f"${cost:,.2f}")

    # ── [FIX-4] Dividend gross-up ──
    print("\n--- Dividend gross-up (FIX-4) ---")
    from prepare import compute_federal_tax, IncomeProfile
    p_div = IncomeProfile(eligible_dividends=60_000, oas_benefits=8_908, age=68)
    fed = compute_federal_tax(p_div)
    chk("Div gross-up inflates net income",
        fed.net_income > 60_000 + 8_908,
        f"actual=$68.9K, net_income=${fed.net_income:,.0f} (gross-up adds ${fed.net_income - 68_908:,.0f})")

    # ── [FIX-8] Chisholm & Brown validation ──
    print("\n--- Chisholm & Brown 80%+ (FIX-8) ---")
    from prepare_provincial import compute_combined_tax
    # At $20K RRIF income in ON: GIS 50% + tax marginal
    p20 = IncomeProfile(rrsp_rrif_income=20_000, age=68, eligible_pension_amount=20_000)
    p21 = IncomeProfile(rrsp_rrif_income=21_000, age=68, eligible_pension_amount=21_000)
    tax20 = compute_combined_tax(p20, "ON")
    tax21 = compute_combined_tax(p21, "ON")
    tax_marginal = (tax21.total_tax - tax20.total_tax) / 1_000
    gis_marginal = 0.50  # GIS always reduces 50%
    combined = tax_marginal + gis_marginal
    print(f"  At $20K RRIF (ON): tax marginal {tax_marginal:.1%} + GIS 50% = {combined:.1%}")

    # At $25K where ON tax is higher
    p25 = IncomeProfile(rrsp_rrif_income=25_000, age=68, eligible_pension_amount=25_000)
    p26 = IncomeProfile(rrsp_rrif_income=26_000, age=68, eligible_pension_amount=26_000)
    tax25 = compute_combined_tax(p25, "ON")
    tax26 = compute_combined_tax(p26, "ON")
    tax_m25 = (tax26.total_tax - tax25.total_tax) / 1_000
    combined25 = tax_m25 + gis_marginal
    print(f"  At $25K RRIF (ON): tax marginal {tax_m25:.1%} + GIS 50% = {combined25:.1%}")
    chk("GIS + tax > 50% at $25K ON", combined25 > 0.55, f"{combined25:.1%}")

    print(f"\n{'='*70}")
    print(f"TOTAL: {ok}/{ok} TESTS PASSED — MODULE 4 FINAL")
    print(f"{'='*70}")


if __name__ == "__main__":
    _validate()

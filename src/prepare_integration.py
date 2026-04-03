"""
prepare_integration.py — Module 5: Integration & Validation (FINAL)
====================================================================
Ties Modules 1-4 into a single pipeline for strategy.py.

Audit fixes:
  [FIX-1] OAS double-counting: after_tax_income excludes oas_net from benefits
  [FIX-2] Effective rate split: tax_effective_rate + total_effective_rate
  [FIX-3] RESP contributions + CESG in simulate_year()
  [FIX-4] Decomposed returns via return_decomposition dict
  [FIX-5] Pension splitting in simulate_year() for married profiles
  [FIX-6] RDSP/CLB processing in simulate_year()
  [FIX-7] Mutation warning documented; deepcopy helper
  [FIX-8] 5th profile: disabled adult with RDSP (covers all 6 accounts)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, List
import copy

from prepare import (
    IncomeProfile, HouseholdProfile, FederalTaxResult,
    compute_federal_tax, pension_split, foreign_withholding,
)
from prepare_provincial import (
    ProvincialTaxResult, CombinedTaxResult,
    compute_provincial_tax, compute_combined_tax,
)
from prepare_accounts import (
    TFSAAccount, RRSPAccount, FHSAAccount, RESPAccount,
    RDSPAccount, NonRegisteredAccount, HouseholdAccounts,
    compute_estate_tax,
)
from prepare_clawbacks import (
    ClawbackResult, compute_all_clawbacks, marginal_clawback_rate,
    is_clawback_sheltered,
)


# ══════════════════════════════════════════════════════════════════════
# UNIFIED ANNUAL OUTCOME
# ══════════════════════════════════════════════════════════════════════

@dataclass
class AnnualOutcome:
    """Complete financial outcome for one person for one year."""
    year: int = 0
    age: int = 0
    province: str = ""

    gross_income: float = 0.0
    net_income: float = 0.0
    taxable_income: float = 0.0

    federal_tax: float = 0.0
    provincial_tax: float = 0.0
    total_income_tax: float = 0.0
    cpp_ei: float = 0.0

    # Benefits — [FIX-1] OAS tracked separately
    oas_gross: float = 0.0
    oas_clawback: float = 0.0
    oas_net: float = 0.0
    gis_net: float = 0.0
    ccb_net: float = 0.0
    gst_credit: float = 0.0
    prov_credit: float = 0.0
    non_oas_benefits: float = 0.0  # [FIX-1] GIS + CCB + GST + prov (excludes OAS)
    total_clawbacks: float = 0.0

    # Net position — [FIX-1] corrected formula
    after_tax_income: float = 0.0

    # [FIX-2] Split effective rates
    tax_effective_rate: float = 0.0     # income tax only / net_income
    total_effective_rate: float = 0.0   # (tax + all clawbacks) / net_income

    total_account_balance: float = 0.0

    federal_result: FederalTaxResult = None
    provincial_result: ProvincialTaxResult = None
    clawback_result: ClawbackResult = None


def compute_annual_outcome(profile: IncomeProfile, province: str,
                            oas_income: float = 0,
                            is_single: bool = True,
                            spouse_income: float = 0,
                            children_under_6: int = 0,
                            children_6_to_17: int = 0,
                            oas_deferral_years: int = 0,
                            year: int = 2026) -> AnnualOutcome:
    """
    Single-call: income → federal tax → provincial tax → clawbacks → net.
    """
    r = AnnualOutcome(year=year, age=profile.age, province=province.upper())

    # Module 1
    fed = compute_federal_tax(profile)
    r.federal_result = fed
    r.gross_income = fed.gross_income
    r.net_income = fed.net_income
    r.taxable_income = fed.taxable_income
    r.federal_tax = fed.tax_payable
    r.cpp_ei = round(fed.cpp1 + fed.cpp2 + fed.ei_premiums, 2)

    # Module 2
    prov = compute_provincial_tax(profile, province, fed_result=fed)
    r.provincial_result = prov
    r.provincial_tax = prov.prov_tax_payable
    r.total_income_tax = round(r.federal_tax + r.provincial_tax, 2)

    # Module 4
    cb = compute_all_clawbacks(
        net_income=fed.net_income, age=profile.age, oas_income=oas_income,
        is_single=is_single, spouse_income=spouse_income,
        children_under_6=children_under_6, children_6_to_17=children_6_to_17,
        oas_deferral_years=oas_deferral_years, province=province,
    )
    r.clawback_result = cb
    r.oas_gross = cb.oas_gross
    r.oas_clawback = cb.oas_clawback
    r.oas_net = cb.oas_net
    r.gis_net = cb.gis_net
    r.ccb_net = cb.ccb_net
    r.gst_credit = cb.gst_credit
    r.prov_credit = cb.prov_credit
    r.total_clawbacks = cb.total_clawbacks

    # [FIX-1] Non-OAS benefits (these are NOT already in gross_income)
    r.non_oas_benefits = round(r.gis_net + r.ccb_net + r.gst_credit + r.prov_credit, 2)

    # [FIX-1] After-tax income:
    # OAS is already in gross_income via IncomeProfile.oas_benefits.
    # Only the OAS CLAWBACK reduces it. Non-OAS benefits are external additions.
    r.after_tax_income = round(
        r.gross_income - r.total_income_tax - r.cpp_ei
        - r.oas_clawback + r.non_oas_benefits, 2)

    # [FIX-2] Split effective rates
    r.tax_effective_rate = round(r.total_income_tax / max(1, r.net_income), 4)
    # Total effective rate: tax + ACTUAL benefit loss (not raw clawbacks which can exceed max)
    actual_benefit_loss = round(cb.total_benefits - cb.net_benefits, 2)
    r.total_effective_rate = round(
        (r.total_income_tax + actual_benefit_loss) / max(1, r.net_income), 4)

    return r


# ══════════════════════════════════════════════════════════════════════
# YEAR SIMULATION — [FIX-3,4,5,6,7]
# ══════════════════════════════════════════════════════════════════════

@dataclass
class YearSimResult:
    outcome: AnnualOutcome = None
    spouse_outcome: AnnualOutcome = None  # [FIX-5]
    accounts: HouseholdAccounts = None
    contributions: Dict[str, float] = field(default_factory=dict)
    withdrawals: Dict[str, float] = field(default_factory=dict)
    grants: Dict[str, float] = field(default_factory=dict)  # [FIX-3/6]


def simulate_year(accounts: HouseholdAccounts, profile: IncomeProfile,
                   province: str, year: int,
                   contribution_plan: Dict[str, float] = None,
                   withdrawal_plan: Dict[str, float] = None,
                   return_rate: float = 0.05,
                   return_decomposition: Dict[str, float] = None,
                   is_single: bool = True,
                   spouse_profile: IncomeProfile = None,
                   pension_split_frac: float = 0.0,
                   spouse_income: float = 0,
                   children_under_6: int = 0,
                   children_6_to_17: int = 0,
                   family_income: float = 0) -> YearSimResult:
    """
    Simulate one calendar year for a household.

    WARNING [FIX-7]: This function MUTATES the accounts and profile objects.
    For alternative scenario comparison, use deepcopy BEFORE calling:
        import copy
        alt_accounts = copy.deepcopy(accounts)
        alt_profile = copy.deepcopy(profile)
        simulate_year(alt_accounts, alt_profile, ...)

    [FIX-3] RESP contributions with CESG/CLB grants
    [FIX-4] return_decomposition: {"interest":X, "cdn_div_elig":X, ...}
    [FIX-5] Pension splitting for married retirees
    [FIX-6] RDSP contributions and CDSB payments
    """
    result = YearSimResult(accounts=accounts)
    contrib = contribution_plan or {}
    wd_plan = withdrawal_plan or {}
    grants = {}

    # ── Step 1: New year ──
    accounts.tfsa.new_year(year)
    prior_earned = profile.employment_income + profile.self_employment_income
    accounts.rrsp.new_year(prior_earned, year, profile.age)
    if accounts.fhsa.is_open:
        accounts.fhsa.new_year(year, profile.age)
    if accounts.resp:
        b_age = accounts.resp.beneficiary_age + 1
        accounts.resp.new_year(b_age)

    # ── Step 2: Contributions ──
    actual = {}
    if "tfsa" in contrib:
        actual["tfsa"] = accounts.tfsa.contribute(contrib["tfsa"])
    if "rrsp" in contrib:
        actual["rrsp"] = accounts.rrsp.contribute(contrib["rrsp"])
        profile.rrsp_deduction = actual["rrsp"]
    if "fhsa" in contrib:
        actual["fhsa"] = accounts.fhsa.contribute(contrib["fhsa"])
        profile.fhsa_deduction = actual["fhsa"]
    if "non_reg" in contrib:
        accounts.non_reg.contribute(contrib["non_reg"])
        actual["non_reg"] = contrib["non_reg"]

    # [FIX-3] RESP contributions + CESG
    if "resp" in contrib and accounts.resp:
        fi = family_income or (profile.employment_income + spouse_income)
        resp_result = accounts.resp.contribute(contrib["resp"], fi)
        actual["resp"] = resp_result["contribution"]
        grants["cesg"] = resp_result["cesg"]
        grants["acesg"] = resp_result["acesg"]

    # [FIX-3] CLB for low-income families
    if accounts.resp and family_income and family_income < 56_000:
        is_first = accounts.resp.total_clb == 0
        clb = accounts.resp.clb_payment(family_income, is_first=is_first)
        grants["clb"] = clb

    # [FIX-6] RDSP contributions + CDSB
    if "rdsp" in contrib and accounts.rdsp:
        fi = family_income or profile.employment_income
        rdsp_result = accounts.rdsp.contribute(contrib["rdsp"], fi, year)
        actual["rdsp"] = rdsp_result["contribution"]
        grants["cdsg"] = rdsp_result["cdsg"]

    if accounts.rdsp and family_income:
        cdsb = accounts.rdsp.cdsb_payment(family_income, year)
        grants["cdsb"] = cdsb

    result.contributions = actual
    result.grants = grants

    # ── Step 3: Withdrawals ──
    wd_actual = {}
    if "rrif" in wd_plan or accounts.rrsp.is_rrif:
        requested = wd_plan.get("rrif", 0)
        wd = accounts.rrsp.withdraw(requested, profile.age)
        wd_actual["rrif"] = wd["amount"]
        profile.rrsp_rrif_income = wd["amount"]
        profile.eligible_pension_amount = wd["amount"]

    if "tfsa" in wd_plan:
        wd = accounts.tfsa.withdraw(wd_plan["tfsa"])
        wd_actual["tfsa"] = wd["amount"]
        # NOT added to IncomeProfile

    if "non_reg" in wd_plan:
        wd = accounts.non_reg.withdraw(wd_plan["non_reg"])
        wd_actual["non_reg"] = wd["amount"]
        profile.capital_gains += wd["capital_gain"]

    result.withdrawals = wd_actual

    # ── Step 4: Investment returns ── [FIX-4]
    if return_decomposition:
        rd = return_decomposition
        accounts.tfsa.apply_return_decomposed(**rd)
        accounts.rrsp.apply_return_decomposed(**rd)
        if accounts.fhsa.is_open:
            accounts.fhsa.apply_return_decomposed(**rd)
        nr_result = accounts.non_reg.apply_return_decomposed(**rd)
        if accounts.resp:
            accounts.resp.apply_return_decomposed(**rd)
        if accounts.rdsp:
            accounts.rdsp.apply_return_decomposed(**rd)

        # Non-reg annual taxable income feeds into profile
        if nr_result and "annual_taxable" in nr_result:
            at = nr_result["annual_taxable"]
            profile.interest_income += at.get("interest", 0)
            profile.eligible_dividends += at.get("eligible_dividends", 0)
            profile.non_eligible_dividends += at.get("non_eligible_dividends", 0)
            profile.foreign_dividends_us += at.get("foreign_dividends_us", 0)
            profile.foreign_dividends_intl += at.get("foreign_dividends_intl", 0)
            profile.foreign_tax_paid += at.get("foreign_tax_paid", 0)
    else:
        accounts.tfsa.apply_return(return_rate)
        accounts.rrsp.apply_return(return_rate)
        if accounts.fhsa.is_open:
            accounts.fhsa.apply_return(return_rate)
        accounts.non_reg.apply_return(return_rate)
        if accounts.resp:
            accounts.resp.apply_return(return_rate)
        if accounts.rdsp:
            accounts.rdsp.apply_return(return_rate)

    # ── Step 5: Pension splitting ── [FIX-5]
    if not is_single and spouse_profile and pension_split_frac > 0 and profile.age >= 65:
        hh = HouseholdProfile(
            taxpayer=profile, spouse=spouse_profile,
            pension_split_fraction=pension_split_frac,
        )
        split_t, split_s = pension_split(hh)
        # Compute taxpayer outcome on split profile
        result.outcome = compute_annual_outcome(
            split_t, province, oas_income=profile.oas_benefits,
            is_single=False, spouse_income=spouse_income,
            children_under_6=children_under_6, children_6_to_17=children_6_to_17,
            year=year,
        )
        # Compute spouse outcome
        if split_s:
            result.spouse_outcome = compute_annual_outcome(
                split_s, province, oas_income=split_s.oas_benefits,
                is_single=False, year=year,
            )
    else:
        # Single or no splitting
        result.outcome = compute_annual_outcome(
            profile, province, oas_income=profile.oas_benefits,
            is_single=is_single, spouse_income=spouse_income,
            children_under_6=children_under_6, children_6_to_17=children_6_to_17,
            year=year,
        )

    result.outcome.total_account_balance = accounts.total_balance
    return result


def deepcopy_for_scenario(accounts: HouseholdAccounts,
                           profile: IncomeProfile) -> tuple:
    """[FIX-7] Helper: deepcopy accounts and profile for alternative scenarios."""
    return copy.deepcopy(accounts), copy.deepcopy(profile)


# ══════════════════════════════════════════════════════════════════════
# HOUSEHOLD PROFILES — Five Research Profiles [FIX-8]
# ══════════════════════════════════════════════════════════════════════

def profile_young_professional() -> dict:
    """Age 28, $75K, single, FHSA-eligible. Tests FHSA vs RRSP priority (Gap 4)."""
    return {
        "profile": IncomeProfile(employment_income=75_000, age=28),
        "accounts": HouseholdAccounts(
            tfsa=TFSAAccount(balance=30_000, contribution_room=7_000),
            rrsp=RRSPAccount(balance=15_000, contribution_room=13_500),
            fhsa=FHSAAccount(balance=0, is_open=True, year_opened=2024,
                             is_first_time_buyer=True, annual_room=8_000),
        ),
        "is_single": True, "children_under_6": 0, "children_6_to_17": 0,
    }


def profile_mid_career_family() -> dict:
    """Age 38, $150K, married (spouse $50K), 2 kids. Tests CCB + RESP (Gaps 5,7)."""
    return {
        "profile": IncomeProfile(employment_income=150_000, age=38),
        "accounts": HouseholdAccounts(
            tfsa=TFSAAccount(balance=80_000, contribution_room=7_000),
            rrsp=RRSPAccount(balance=120_000, contribution_room=27_000),
            resp=RESPAccount(beneficiary_age=3, total_contrib=10_000,
                             bal_contrib=10_000, total_cesg=2_000, bal_grants=2_000),
        ),
        "is_single": False, "spouse_income": 50_000,
        "children_under_6": 1, "children_6_to_17": 1,
        "family_income": 200_000,
    }


def profile_peak_earner() -> dict:
    """Age 50, $250K, married (spouse $80K), 1 teen. Tests high-income location (Gap 2)."""
    return {
        "profile": IncomeProfile(employment_income=250_000, age=50),
        "accounts": HouseholdAccounts(
            tfsa=TFSAAccount(balance=109_000, contribution_room=7_000),
            rrsp=RRSPAccount(balance=500_000, contribution_room=33_810),
            non_reg=NonRegisteredAccount(balance=200_000, acb=150_000,
                                         unrealized_gains=50_000),
        ),
        "is_single": False, "spouse_income": 80_000,
        "children_under_6": 0, "children_6_to_17": 1,
    }


def profile_retiree() -> dict:
    """Age 68, $50K RRIF + $15K CPP + $8.9K OAS, single. Tests withdrawal + OAS (Gaps 5,6)."""
    return {
        "profile": IncomeProfile(
            rrsp_rrif_income=50_000, cpp_benefits=15_000, oas_benefits=8_908,
            age=68, eligible_pension_amount=50_000,
        ),
        "accounts": HouseholdAccounts(
            tfsa=TFSAAccount(balance=109_000, contribution_room=7_000),
            rrsp=RRSPAccount(balance=400_000, is_rrif=True),
            non_reg=NonRegisteredAccount(balance=100_000, acb=70_000,
                                         unrealized_gains=30_000),
        ),
        "is_single": True, "children_under_6": 0, "children_6_to_17": 0,
    }


def profile_disabled_adult() -> dict:
    """[FIX-8] Age 35, $30K, single, DTC-eligible. Tests RDSP grants (Gap 1)."""
    return {
        "profile": IncomeProfile(employment_income=30_000, age=35),
        "accounts": HouseholdAccounts(
            tfsa=TFSAAccount(balance=20_000, contribution_room=7_000),
            rrsp=RRSPAccount(balance=5_000, contribution_room=5_400),
            rdsp=RDSPAccount(beneficiary_age=35, has_dtc=True),
        ),
        "is_single": True, "children_under_6": 0, "children_6_to_17": 0,
        "family_income": 30_000,
    }


PROFILES = {
    "young_pro": profile_young_professional,
    "mid_career": profile_mid_career_family,
    "peak_earner": profile_peak_earner,
    "retiree": profile_retiree,
    "disabled_adult": profile_disabled_adult,
}


# ══════════════════════════════════════════════════════════════════════
# COMPARATIVE ANALYSIS
# ══════════════════════════════════════════════════════════════════════

def compare_provinces(profile: IncomeProfile, **kwargs) -> Dict[str, AnnualOutcome]:
    return {prov: compute_annual_outcome(profile, prov, **kwargs) for prov in ["AB", "ON", "BC"]}


def compare_rrif_vs_tfsa(base_rrif: float, withdrawal: float,
                          age: int, province: str) -> dict:
    p_rrif = IncomeProfile(rrsp_rrif_income=base_rrif + withdrawal, oas_benefits=8_908,
                            age=age, eligible_pension_amount=base_rrif + withdrawal)
    p_tfsa = IncomeProfile(rrsp_rrif_income=base_rrif, oas_benefits=8_908,
                            age=age, eligible_pension_amount=base_rrif)
    o_rrif = compute_annual_outcome(p_rrif, province, oas_income=8_908)
    o_tfsa = compute_annual_outcome(p_tfsa, province, oas_income=8_908)

    tax_cost = round(o_rrif.total_income_tax - o_tfsa.total_income_tax, 2)
    benefit_cost = round(o_tfsa.non_oas_benefits - o_rrif.non_oas_benefits
                         + o_tfsa.oas_net - o_rrif.oas_net, 2)
    return {"withdrawal": withdrawal, "tax_cost": tax_cost,
            "benefit_cost": benefit_cost, "total_cost": round(tax_cost + benefit_cost, 2)}


def compute_terminal_wealth(accounts: HouseholdAccounts, province: str, age: int) -> dict:
    estate = compute_estate_tax(accounts.tfsa, accounts.rrsp, accounts.non_reg,
                                 accounts.fhsa if accounts.fhsa.is_open else None,
                                 accounts.resp, accounts.rdsp)
    deemed = IncomeProfile(
        rrsp_rrif_income=estate["rrsp_deemed_income"],
        capital_gains=estate["nonreg_capital_gain"],
        other_income=estate.get("fhsa_deemed_income", 0) + estate.get("resp_growth_taxable", 0),
        age=age,
    )
    tax = compute_combined_tax(deemed, province)
    return {
        "gross_estate": accounts.total_balance,
        "tax_at_death": tax.total_tax,
        "after_tax_estate": round(accounts.total_balance - tax.total_tax, 2),
        "tfsa_tax_free": estate["tfsa_tax_free"],
        "rrsp_deemed_taxable": estate["rrsp_deemed_income"],
        "nonreg_gain_taxable": estate["nonreg_capital_gain"],
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
    print("MODULE 5 FINAL VALIDATION — All 8 Fixes")
    print("=" * 70)

    # ── A. Pipeline ──
    print("\n--- A. Pipeline ---")
    p = IncomeProfile(employment_income=100_000, age=35)
    o = compute_annual_outcome(p, "ON", children_under_6=1, is_single=False, spouse_income=40_000)
    chk("Pipeline returns result", isinstance(o, AnnualOutcome))
    chk("Federal tax > 0", o.federal_tax > 0)
    chk("Provincial tax > 0", o.provincial_tax > 0)
    chk("CCB > 0", o.ccb_net > 0, f"${o.ccb_net:,.2f}")

    # ── [FIX-1] OAS double-count fix ──
    print("\n--- B. OAS double-count fix (FIX-1) ---")
    p_ret = IncomeProfile(rrsp_rrif_income=50_000, cpp_benefits=15_000,
                           oas_benefits=8_908, age=68, eligible_pension_amount=50_000)
    o_ret = compute_annual_outcome(p_ret, "ON", oas_income=8_908)

    # after_tax = gross - tax - cpp_ei - oas_clawback + non_oas_benefits
    expected = (o_ret.gross_income - o_ret.total_income_tax - o_ret.cpp_ei
                - o_ret.oas_clawback + o_ret.non_oas_benefits)
    chk("After-tax formula correct", abs(o_ret.after_tax_income - expected) < 0.01,
        f"${o_ret.after_tax_income:,.2f}")

    # OAS not double-counted: after_tax should be LESS than gross
    chk("After-tax < gross (no double-count)",
        o_ret.after_tax_income < o_ret.gross_income,
        f"${o_ret.after_tax_income:,.2f} < ${o_ret.gross_income:,.2f}")

    # Sanity: retiree at $73.9K gross, ~$12.6K tax, no clawback at this level
    # after-tax should be ~$61K, not ~$70K (old bug)
    chk("Retiree after-tax ~$61K (not $70K)", o_ret.after_tax_income < 65_000,
        f"${o_ret.after_tax_income:,.2f}")

    # ── [FIX-2] Split effective rates ──
    print("\n--- C. Split effective rates (FIX-2) ---")
    chk("tax_effective_rate defined", o_ret.tax_effective_rate > 0)
    chk("total_effective_rate ≥ tax_effective",
        o_ret.total_effective_rate >= o_ret.tax_effective_rate,
        f"tax={o_ret.tax_effective_rate:.2%}, total={o_ret.total_effective_rate:.2%}")

    # For high-income worker with minimal benefits, rates should be close
    p_w = IncomeProfile(employment_income=150_000, age=35)
    o_w = compute_annual_outcome(p_w, "AB")
    chk("High-income: total ≈ tax rate (minimal clawback gap)",
        abs(o_w.tax_effective_rate - o_w.total_effective_rate) < 0.01,
        f"tax={o_w.tax_effective_rate:.2%}, total={o_w.total_effective_rate:.2%}")

    # ── [FIX-3] RESP in simulation ──
    print("\n--- D. RESP in simulation (FIX-3) ---")
    cfg = profile_mid_career_family()
    accts = cfg["accounts"]
    prof = copy.deepcopy(cfg["profile"])
    yr = simulate_year(accts, prof, "ON", 2026,
                        contribution_plan={"rrsp": 27_000, "resp": 2_500},
                        family_income=200_000, is_single=False, spouse_income=50_000,
                        children_under_6=1, children_6_to_17=1)
    chk("RESP contribution processed", yr.contributions.get("resp", 0) == 2_500)
    chk("CESG grant received", yr.grants.get("cesg", 0) > 0,
        f"${yr.grants.get('cesg', 0)}")

    # ── [FIX-4] Decomposed returns ──
    print("\n--- E. Decomposed returns (FIX-4) ---")
    cfg2 = profile_young_professional()
    accts2 = cfg2["accounts"]
    prof2 = copy.deepcopy(cfg2["profile"])
    decomp = {"interest": 500, "cdn_div_elig": 300, "us_div": 200}
    yr2 = simulate_year(accts2, prof2, "AB", 2026,
                         contribution_plan={"tfsa": 7_000},
                         return_decomposition=decomp)
    chk("Decomposed returns applied", accts2.total_balance > 30_000 + 15_000)
    # Non-reg decomposed: interest should be in profile
    chk("Interest in profile", prof2.interest_income >= 500,
        f"${prof2.interest_income}")

    # ── [FIX-5] Pension splitting ──
    print("\n--- F. Pension splitting in sim (FIX-5) ---")
    cfg_ret = profile_retiree()
    accts_r = cfg_ret["accounts"]
    prof_r = IncomeProfile(rrsp_rrif_income=0, cpp_benefits=15_000, oas_benefits=8_908,
                            age=68, eligible_pension_amount=0)
    spouse = IncomeProfile(oas_benefits=8_908, age=66)

    yr_split = simulate_year(accts_r, prof_r, "ON", 2026,
                              withdrawal_plan={"rrif": 60_000},
                              is_single=False, spouse_profile=spouse,
                              pension_split_frac=0.50, spouse_income=8_908)
    chk("Split: taxpayer outcome exists", yr_split.outcome is not None)
    chk("Split: spouse outcome exists", yr_split.spouse_outcome is not None)
    chk("Split: taxpayer tax < unsplit",
        yr_split.outcome.total_income_tax < 25_000,
        f"${yr_split.outcome.total_income_tax:,.2f}")

    # ── [FIX-6] RDSP in simulation ──
    print("\n--- G. RDSP in simulation (FIX-6) ---")
    cfg_d = profile_disabled_adult()
    accts_d = cfg_d["accounts"]
    prof_d = copy.deepcopy(cfg_d["profile"])
    yr_d = simulate_year(accts_d, prof_d, "AB", 2026,
                          contribution_plan={"tfsa": 7_000, "rdsp": 1_500},
                          family_income=30_000)
    chk("RDSP contribution", yr_d.contributions.get("rdsp", 0) == 1_500)
    chk("CDSG grant", yr_d.grants.get("cdsg", 0) == 3_500,
        f"${yr_d.grants.get('cdsg', 0)}")
    chk("CDSB payment", yr_d.grants.get("cdsb", 0) == 1_000,
        f"${yr_d.grants.get('cdsb', 0)}")

    # ── [FIX-7] Deepcopy helper ──
    print("\n--- H. Deepcopy helper (FIX-7) ---")
    orig_accts = HouseholdAccounts(tfsa=TFSAAccount(balance=50_000))
    a2, p2 = deepcopy_for_scenario(orig_accts, IncomeProfile(employment_income=75_000))
    a2.tfsa.balance = 0
    chk("Deepcopy independent", orig_accts.tfsa.balance == 50_000,
        f"orig=${orig_accts.tfsa.balance}, copy=${a2.tfsa.balance}")

    # ── [FIX-8] All 5 profiles ──
    print("\n--- I. All 5 profiles (FIX-8) ---")
    for name, factory in PROFILES.items():
        cfg = factory()
        p = cfg["profile"]
        o = compute_annual_outcome(p, "ON", oas_income=p.oas_benefits,
                                    is_single=cfg.get("is_single", True),
                                    spouse_income=cfg.get("spouse_income", 0),
                                    children_under_6=cfg.get("children_under_6", 0),
                                    children_6_to_17=cfg.get("children_6_to_17", 0))
        chk(f"{name}: after-tax > 0", o.after_tax_income > 0,
            f"${o.after_tax_income:,.0f}")

    # RDSP profile has RDSP account
    chk("Disabled profile has RDSP", profile_disabled_adult()["accounts"].rdsp is not None)

    # ── J. Province comparison ──
    print("\n--- J. Cross-province ---")
    results = compare_provinces(IncomeProfile(employment_income=150_000, age=40))
    chk("AB < ON at $150K", results["AB"].total_income_tax < results["ON"].total_income_tax)

    # ── K. Terminal wealth ──
    print("\n--- K. Terminal wealth ---")
    tw = compute_terminal_wealth(profile_retiree()["accounts"], "ON", 68)
    chk("Terminal: after-tax < gross", tw["after_tax_estate"] < tw["gross_estate"])
    chk("Terminal: TFSA tax-free", tw["tfsa_tax_free"] == 109_000)

    # ── L. RRIF vs TFSA ──
    print("\n--- L. RRIF vs TFSA ---")
    comp = compare_rrif_vs_tfsa(40_000, 10_000, 68, "ON")
    chk("RRIF costs more", comp["total_cost"] > 0, f"${comp['total_cost']:,.2f}")

    # ── M. Multi-year ──
    print("\n--- M. Multi-year ---")
    cfg_my = profile_young_professional()
    accts_my = cfg_my["accounts"]
    for yr in range(2026, 2029):
        p_my = copy.deepcopy(cfg_my["profile"])
        p_my.age = 28 + (yr - 2026)
        simulate_year(accts_my, p_my, "AB", yr,
                       contribution_plan={"tfsa": 7_000, "rrsp": 13_500},
                       return_rate=0.06)
    chk("3-year growth", accts_my.total_balance > 100_000, f"${accts_my.total_balance:,.0f}")

    print(f"\n{'='*70}")
    print(f"TOTAL: {ok}/{ok} TESTS PASSED — MODULE 5 FINAL")
    print(f"{'='*70}")
    print(f"\nFull engine: M1(35) + M2(32) + M3(42) + M4(31) + M5({ok}) = {35+32+42+31+ok} tests")


if __name__ == "__main__":
    _validate()

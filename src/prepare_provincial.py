"""
prepare_provincial.py — Module 2: Provincial Tax Engines (FINAL)
================================================================
2026 Tax Year — CRA-confirmed (TaxTips.ca)

Provinces: Alberta, Ontario, British Columbia

Audit fixes applied:
  [FIX-1] DRY: accepts FederalTaxResult for taxable_income instead of re-deriving
  [FIX-2] Provincial age amount credits (AB $6,078, ON $6,192, BC $6,234)
  [FIX-3] Provincial pension income credits (AB $1,583, ON $1,647, BC $1,000)
  [FIX-4] BC low-income tax reduction (income ≤$24,580 = $0 prov tax)
  [FIX-5] ON $300 low-income tax reduction (clawback above $18,930)
  [FIX-6] DOC: Execution strategy says AB has 'flat health premium' — AB has NONE
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from prepare import (
    IncomeProfile, FederalTaxResult, compute_federal_tax,
    div_grossup, cap_gains_taxable, cpp_calc,
    ELIG_DIV_GROSSUP, NELIG_DIV_GROSSUP,
)


# ══════════════════════════════════════════════════════════════════════
# ALBERTA — 2026  (CRA-confirmed, Bill 32 indexation cap 2%)
# No surtax. No health premium. No PST. [FIX-6 noted]
# ══════════════════════════════════════════════════════════════════════

AB_BRACKETS = [
    (61_200,  0.08),   # New 8% bracket (introduced 2025, indexed 2026)
    (154_259, 0.10),
    (185_111, 0.12),
    (246_813, 0.13),
    (370_220, 0.14),
    (None,    0.15),
]
AB_BPA          = 22_769
AB_LOWEST       = 0.08
AB_ELIG_DTC     = 0.0812
AB_NELIG_DTC    = 0.0218
AB_AGE_AMOUNT   = 6_078    # [FIX-2] Provincial age amount
AB_PENSION_AMT  = 1_583    # [FIX-3] Provincial pension income amount


# ══════════════════════════════════════════════════════════════════════
# ONTARIO — 2026  (CRA-confirmed, indexation 1.019)
# $150K/$220K brackets NOT indexed.
# Surtax: 20% on basic tax > $5,818; 36% on basic tax > $7,446
# Health Premium: $0–$900 (NOT indexed)
# Low-income reduction: $300 clawed back above $18,930 [FIX-5]
# ══════════════════════════════════════════════════════════════════════

ON_BRACKETS = [
    (53_891,  0.0505),
    (107_785, 0.0915),
    (150_000, 0.1116),
    (220_000, 0.1216),
    (None,    0.1316),
]
ON_BPA              = 12_989
ON_LOWEST           = 0.0505
ON_ELIG_DTC         = 0.1000
ON_NELIG_DTC        = 0.029863
ON_SURTAX_20_THRESH = 5_818
ON_SURTAX_36_THRESH = 7_446
ON_AGE_AMOUNT       = 6_192    # [FIX-2]
ON_PENSION_AMT      = 1_647    # [FIX-3]
ON_LOW_INC_REDUCE   = 300      # [FIX-5] $300 reduction
ON_LOW_INC_CLAW_START = 18_930 # [FIX-5] Clawback starts here
ON_LOW_INC_CLAW_RATE = 0.0505  # [FIX-5] At lowest ON rate


# ══════════════════════════════════════════════════════════════════════
# BRITISH COLUMBIA — 2026  (CRA-confirmed, indexation 1.022)
# Lowest rate INCREASED to 5.6% from 5.06% (BC 2026 Budget)
# Indexation PAUSED 2027-2030. No surtax. No health premium (MSP eliminated).
# Low-income tax reduction: income ≤$24,580 = $0; clawback $25,570–$41,722 [FIX-4]
# ══════════════════════════════════════════════════════════════════════

BC_BRACKETS = [
    (50_363,  0.056),   # Increased from 5.06%
    (100_728, 0.077),
    (115_648, 0.105),
    (140_430, 0.1229),
    (190_405, 0.147),
    (265_545, 0.168),
    (None,    0.205),
]
BC_BPA              = 12_580
BC_LOWEST           = 0.056
BC_ELIG_DTC         = 0.12
BC_NELIG_DTC        = 0.0196
BC_AGE_AMOUNT       = 6_234    # [FIX-2]
BC_PENSION_AMT      = 1_000    # [FIX-3]
BC_LOW_INC_THRESH   = 24_580   # [FIX-4] No prov tax below this
BC_LOW_INC_CLAW_START = 25_570 # [FIX-4] Clawback begins
BC_LOW_INC_CLAW_END = 41_722   # [FIX-4] Reduction fully eliminated
BC_LOW_INC_CLAW_RATE = 0.0356  # [FIX-4] 3.56% additional rate


# ══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def _bracket_tax(taxable: float, brackets: list) -> float:
    if taxable <= 0: return 0.0
    tax, prev = 0.0, 0.0
    for lim, rate in brackets:
        if lim is None:
            return round(tax + (taxable - prev) * rate, 2)
        if taxable <= lim:
            return round(tax + (taxable - prev) * rate, 2)
        tax += (lim - prev) * rate
        prev = lim
    return round(tax, 2)


def _prov_div_credit(elig: float, nelig: float, er: float, nr: float) -> float:
    return round(
        elig * (1 + ELIG_DIV_GROSSUP) * er
        + nelig * (1 + NELIG_DIV_GROSSUP) * nr, 2)


def _prov_age_credit(net_income: float, age: int, age_amt: float,
                     lowest_rate: float, claw_start: float = 44_325,
                     claw_rate: float = 0.15) -> float:
    """[FIX-2] Provincial age amount credit — same clawback logic as federal."""
    if age < 65: return 0.0
    clawback = max(0, (net_income - claw_start) * claw_rate)
    return round(max(0, age_amt - clawback) * lowest_rate, 2)


def _prov_pension_credit(pension_amt: float, age: int, prov_pension_limit: float,
                         lowest_rate: float) -> float:
    """[FIX-3] Provincial pension income credit."""
    if age < 65: return 0.0
    return round(min(pension_amt, prov_pension_limit) * lowest_rate, 2)


# ── Ontario-specific ──

def on_surtax(basic_after_bpa: float) -> float:
    """Ontario surtax: 20% above $5,818 + 36% above $7,446 (cumulative)."""
    s20 = max(0, (basic_after_bpa - ON_SURTAX_20_THRESH) * 0.20)
    s36 = max(0, (basic_after_bpa - ON_SURTAX_36_THRESH) * 0.36)
    return round(s20 + s36, 2)


def on_health_premium(taxable: float) -> float:
    """Ontario Health Premium — tiered, $0 to $900, NOT indexed."""
    if taxable <= 20_000:  return 0.0
    if taxable <= 25_000:  return round(0.06 * (taxable - 20_000), 2)
    if taxable <= 36_000:  return 300.0
    if taxable <= 38_500:  return round(300 + 0.06 * (taxable - 36_000), 2)
    if taxable <= 48_000:  return 450.0
    if taxable <= 48_600:  return round(450 + 0.25 * (taxable - 48_000), 2)
    if taxable <= 72_000:  return 600.0
    if taxable <= 72_600:  return round(600 + 0.25 * (taxable - 72_000), 2)
    if taxable <= 200_000: return 750.0
    if taxable <= 200_600: return round(750 + 0.25 * (taxable - 200_000), 2)
    return 900.0


def on_low_income_reduction(basic_tax: float, taxable: float) -> float:
    """[FIX-5] Ontario $300 low-income tax reduction, clawed back above $18,930."""
    if taxable <= ON_LOW_INC_CLAW_START:
        return min(ON_LOW_INC_REDUCE, basic_tax)
    clawback = (taxable - ON_LOW_INC_CLAW_START) * ON_LOW_INC_CLAW_RATE
    reduction = max(0, ON_LOW_INC_REDUCE - clawback)
    return round(min(reduction, basic_tax), 2)


# ── BC-specific ──

def bc_low_income_reduction(basic_tax: float, taxable: float) -> float:
    """
    [FIX-4] BC low-income tax reduction.
    Income ≤ $24,580: no provincial tax.
    Clawback at 3.56% between $25,570 and $41,722 (reduction eliminated).
    """
    if taxable <= BC_LOW_INC_THRESH:
        return basic_tax  # Full reduction — no prov tax
    if taxable <= BC_LOW_INC_CLAW_START:
        return basic_tax  # Still in gap before clawback begins
    if taxable >= BC_LOW_INC_CLAW_END:
        return 0.0  # Reduction fully eliminated
    # Partial clawback zone
    max_reduction = basic_tax
    clawback = (taxable - BC_LOW_INC_CLAW_START) * BC_LOW_INC_CLAW_RATE
    # The reduction = credit_amount - clawback
    # credit_amount = basic tax at threshold ≈ $24,580 * 5.6% = $1,376
    # But simplification: reduction = basic_tax minus what's been clawed back
    credit_base = _bracket_tax(BC_LOW_INC_THRESH, BC_BRACKETS)
    reduction = max(0, credit_base - clawback)
    return round(min(reduction, basic_tax), 2)


# ══════════════════════════════════════════════════════════════════════
# RESULT STRUCTURES
# ══════════════════════════════════════════════════════════════════════

@dataclass
class ProvincialTaxResult:
    province: str = ""
    basic_prov_tax: float = 0.0
    bpa_credit: float = 0.0
    age_credit: float = 0.0        # [FIX-2]
    pension_credit: float = 0.0    # [FIX-3]
    div_credit: float = 0.0
    low_income_reduction: float = 0.0  # [FIX-4/5]
    surtax: float = 0.0
    health_premium: float = 0.0
    prov_tax_payable: float = 0.0
    prov_effective_rate: float = 0.0


@dataclass
class CombinedTaxResult:
    federal: FederalTaxResult = None
    provincial: ProvincialTaxResult = None
    total_tax: float = 0.0
    total_with_payroll: float = 0.0
    combined_effective_rate: float = 0.0


# ══════════════════════════════════════════════════════════════════════
# MAIN COMPUTATION — [FIX-1] Accepts FederalTaxResult
# ══════════════════════════════════════════════════════════════════════

def compute_provincial_tax(profile: IncomeProfile, province: str,
                            fed_result: FederalTaxResult = None) -> ProvincialTaxResult:
    """
    Compute provincial tax for AB, ON, or BC.

    [FIX-1] Accepts pre-computed FederalTaxResult to avoid re-deriving
    taxable income. If not provided, computes federal tax internally.
    """
    if fed_result is None:
        fed_result = compute_federal_tax(profile)

    taxable = fed_result.taxable_income
    net_inc = fed_result.net_income
    r = ProvincialTaxResult(province=province.upper())
    prov = province.upper()

    # Determine pension amount for credit calculation
    pen = profile.eligible_pension_amount
    if profile.age >= 65 and profile.rrsp_rrif_income > 0:
        pen = max(pen, profile.rrsp_rrif_income)

    if prov == "AB":
        r.basic_prov_tax = _bracket_tax(taxable, AB_BRACKETS)
        r.bpa_credit = round(AB_BPA * AB_LOWEST, 2)
        r.age_credit = _prov_age_credit(net_inc, profile.age, AB_AGE_AMOUNT, AB_LOWEST)
        r.pension_credit = _prov_pension_credit(pen, profile.age, AB_PENSION_AMT, AB_LOWEST)
        r.div_credit = _prov_div_credit(profile.eligible_dividends,
                                         profile.non_eligible_dividends, AB_ELIG_DTC, AB_NELIG_DTC)
        credits = r.bpa_credit + r.age_credit + r.pension_credit + r.div_credit
        r.prov_tax_payable = round(max(0, r.basic_prov_tax - credits), 2)

    elif prov == "ON":
        r.basic_prov_tax = _bracket_tax(taxable, ON_BRACKETS)
        r.bpa_credit = round(ON_BPA * ON_LOWEST, 2)
        r.age_credit = _prov_age_credit(net_inc, profile.age, ON_AGE_AMOUNT, ON_LOWEST)
        r.pension_credit = _prov_pension_credit(pen, profile.age, ON_PENSION_AMT, ON_LOWEST)
        r.div_credit = _prov_div_credit(profile.eligible_dividends,
                                         profile.non_eligible_dividends, ON_ELIG_DTC, ON_NELIG_DTC)

        # ON surtax: computed on (basic - BPA - age - pension) BEFORE DTC
        base_for_surtax = max(0, r.basic_prov_tax - r.bpa_credit - r.age_credit - r.pension_credit)
        r.surtax = on_surtax(base_for_surtax)

        # ON low-income reduction [FIX-5]
        r.low_income_reduction = on_low_income_reduction(r.basic_prov_tax, taxable)

        credits = r.bpa_credit + r.age_credit + r.pension_credit + r.div_credit + r.low_income_reduction
        prov_tax = max(0, r.basic_prov_tax + r.surtax - credits)
        r.health_premium = on_health_premium(taxable)
        r.prov_tax_payable = round(prov_tax + r.health_premium, 2)

    elif prov == "BC":
        r.basic_prov_tax = _bracket_tax(taxable, BC_BRACKETS)
        r.bpa_credit = round(BC_BPA * BC_LOWEST, 2)
        r.age_credit = _prov_age_credit(net_inc, profile.age, BC_AGE_AMOUNT, BC_LOWEST)
        r.pension_credit = _prov_pension_credit(pen, profile.age, BC_PENSION_AMT, BC_LOWEST)
        r.div_credit = _prov_div_credit(profile.eligible_dividends,
                                         profile.non_eligible_dividends, BC_ELIG_DTC, BC_NELIG_DTC)

        # BC low-income reduction [FIX-4]
        r.low_income_reduction = bc_low_income_reduction(r.basic_prov_tax, taxable)

        credits = r.bpa_credit + r.age_credit + r.pension_credit + r.div_credit + r.low_income_reduction
        r.prov_tax_payable = round(max(0, r.basic_prov_tax - credits), 2)
    else:
        raise ValueError(f"Unsupported province: {province}. Use 'AB', 'ON', or 'BC'.")

    r.prov_effective_rate = round(r.prov_tax_payable / max(1, taxable), 4)
    return r


def compute_combined_tax(profile: IncomeProfile, province: str) -> CombinedTaxResult:
    """Compute combined federal + provincial tax. [FIX-1] Single pass."""
    fed = compute_federal_tax(profile)
    prov = compute_provincial_tax(profile, province, fed_result=fed)  # Reuses fed result

    total = round(fed.tax_payable + prov.prov_tax_payable, 2)
    total_payroll = round(total + fed.cpp1 + fed.cpp2 + fed.ei_premiums, 2)

    return CombinedTaxResult(
        federal=fed, provincial=prov,
        total_tax=total, total_with_payroll=total_payroll,
        combined_effective_rate=round(total / max(1, fed.net_income), 4),
    )


# ══════════════════════════════════════════════════════════════════════
# VALIDATION
# ══════════════════════════════════════════════════════════════════════

def _validate():
    from prepare import IncomeProfile
    ok = 0
    def chk(label, cond, detail=""):
        nonlocal ok
        s = "PASS" if cond else "FAIL"
        print(f"  [{s}] {label}" + (f"  ({detail})" if detail else ""))
        assert cond, f"FAILED: {label} — {detail}"
        ok += 1

    print("=" * 70)
    print("MODULE 2 FINAL VALIDATION — All 6 Fixes Applied")
    print("=" * 70)

    # ── Alberta ──
    print("\n--- Alberta ---")
    chk("AB $50K basic", abs(_bracket_tax(50_000, AB_BRACKETS) - 4_000) < 0.01)
    chk("AB $100K basic", abs(_bracket_tax(100_000, AB_BRACKETS) - (61_200*0.08+(100_000-61_200)*0.10)) < 0.01)
    chk("AB BPA", abs(round(AB_BPA * AB_LOWEST, 2) - round(22_769*0.08, 2)) < 0.01)

    r_ab = compute_combined_tax(IncomeProfile(employment_income=100_000), "AB")
    chk("AB no surtax", r_ab.provincial.surtax == 0)
    chk("AB no health prem", r_ab.provincial.health_premium == 0)
    chk("AB no low-inc reduction", r_ab.provincial.low_income_reduction == 0)

    # [FIX-2/3] Age and pension credits
    ret_ab = compute_combined_tax(
        IncomeProfile(rrsp_rrif_income=50_000, age=68, eligible_pension_amount=50_000), "AB")
    chk("AB retiree age credit > 0", ret_ab.provincial.age_credit > 0,
        f"${ret_ab.provincial.age_credit:,.2f}")
    chk("AB retiree pension credit > 0", ret_ab.provincial.pension_credit > 0,
        f"${ret_ab.provincial.pension_credit:,.2f}")
    exp_ab_pen = round(min(50_000, AB_PENSION_AMT) * AB_LOWEST, 2)
    chk("AB pension credit = $126.64", abs(ret_ab.provincial.pension_credit - exp_ab_pen) < 0.01)

    # ── Ontario ──
    print("\n--- Ontario ---")
    chk("ON $50K basic", abs(_bracket_tax(50_000, ON_BRACKETS) - 2_525) < 0.01)
    chk("ON surtax $6K", on_surtax(6_000) > 0)
    chk("ON HP $50K = $600", abs(on_health_premium(50_000) - 600) < 1)
    chk("ON HP $250K = $900", on_health_premium(250_000) == 900)

    # [FIX-5] Ontario low-income reduction
    chk("ON low-inc $15K = $300", abs(on_low_income_reduction(1_000, 15_000) - 300) < 0.01)
    chk("ON low-inc $19K < $300 (clawed)",
        on_low_income_reduction(1_000, 19_000) < 300,
        f"${on_low_income_reduction(1_000, 19_000):,.2f}")
    chk("ON low-inc $30K = $0",
        on_low_income_reduction(1_000, 30_000) == 0)

    # ON retiree credits
    ret_on = compute_combined_tax(
        IncomeProfile(rrsp_rrif_income=50_000, age=68, eligible_pension_amount=50_000), "ON")
    chk("ON retiree age credit > 0", ret_on.provincial.age_credit > 0,
        f"${ret_on.provincial.age_credit:,.2f}")
    chk("ON retiree pension credit > 0", ret_on.provincial.pension_credit > 0,
        f"${ret_on.provincial.pension_credit:,.2f}")

    # ── BC ──
    print("\n--- British Columbia ---")
    chk("BC $40K basic", abs(_bracket_tax(40_000, BC_BRACKETS) - 40_000*0.056) < 0.01)

    # [FIX-4] BC low-income reduction
    bc_20k = compute_provincial_tax(IncomeProfile(employment_income=20_000), "BC")
    chk("BC $20K prov tax = $0 (low-inc reduction)",
        bc_20k.prov_tax_payable == 0,
        f"${bc_20k.prov_tax_payable:,.2f}")

    bc_24k = compute_provincial_tax(IncomeProfile(employment_income=24_000), "BC")
    chk("BC $24K prov tax = $0 (below threshold)",
        bc_24k.prov_tax_payable == 0,
        f"${bc_24k.prov_tax_payable:,.2f}")

    bc_35k = compute_provincial_tax(IncomeProfile(employment_income=35_000), "BC")
    chk("BC $35K prov tax > $0 (above clawback)",
        bc_35k.prov_tax_payable > 0,
        f"${bc_35k.prov_tax_payable:,.2f}")

    bc_60k = compute_provincial_tax(IncomeProfile(employment_income=60_000), "BC")
    chk("BC $60K: no low-inc reduction",
        bc_60k.low_income_reduction == 0,
        f"reduction=${bc_60k.low_income_reduction:,.2f}")

    ret_bc = compute_combined_tax(
        IncomeProfile(rrsp_rrif_income=50_000, age=68, eligible_pension_amount=50_000), "BC")
    chk("BC retiree age credit > 0", ret_bc.provincial.age_credit > 0,
        f"${ret_bc.provincial.age_credit:,.2f}")
    chk("BC retiree pension credit > 0", ret_bc.provincial.pension_credit > 0,
        f"${ret_bc.provincial.pension_credit:,.2f}")

    # ── [FIX-1] DRY consistency check ──
    print("\n--- DRY consistency (FIX-1) ---")
    p = IncomeProfile(employment_income=100_000, rrsp_deduction=10_000)
    fed = compute_federal_tax(p)
    prov_pass = compute_provincial_tax(p, "ON", fed_result=fed)
    prov_no_pass = compute_provincial_tax(p, "ON")
    chk("Passed vs computed federal: same prov tax",
        abs(prov_pass.prov_tax_payable - prov_no_pass.prov_tax_payable) < 0.01,
        f"${prov_pass.prov_tax_payable:,.2f} vs ${prov_no_pass.prov_tax_payable:,.2f}")

    # ── Cross-province at $250K ──
    print("\n--- Cross-province $250K ---")
    p250 = IncomeProfile(employment_income=250_000)
    ab = compute_combined_tax(p250, "AB")
    on = compute_combined_tax(p250, "ON")
    bc = compute_combined_tax(p250, "BC")
    print(f"  AB: ${ab.total_tax:>10,.2f}  ({ab.combined_effective_rate:.2%})")
    print(f"  ON: ${on.total_tax:>10,.2f}  ({on.combined_effective_rate:.2%})")
    print(f"  BC: ${bc.total_tax:>10,.2f}  ({bc.combined_effective_rate:.2%})")
    chk("AB cheapest at $250K", ab.total_tax < bc.total_tax < on.total_tax)
    chk("ON→AB saves >$5K", on.total_tax - ab.total_tax > 5_000,
        f"${on.total_tax - ab.total_tax:,.2f}")

    # ── Retiree comparison ──
    print("\n--- Retiree cross-province ($50K RRIF + $15K CPP + $8.5K OAS) ---")
    ret_p = IncomeProfile(rrsp_rrif_income=50_000, cpp_benefits=15_000, oas_benefits=8_500,
                          age=68, eligible_pension_amount=50_000)
    for prov_code in ["AB", "ON", "BC"]:
        r = compute_combined_tax(ret_p, prov_code)
        print(f"  {prov_code}: ${r.total_tax:>9,.2f} (eff={r.combined_effective_rate:.2%}) "
              f"age_cr=${r.provincial.age_credit:,.0f} pen_cr=${r.provincial.pension_credit:,.0f}")
    chk("Retiree: all provinces have age+pension credits",
        all(compute_combined_tax(ret_p, p).provincial.age_credit > 0 for p in ["AB","ON","BC"]))

    # ── Dividend test ──
    print("\n--- $50K eligible dividends ---")
    dp = IncomeProfile(eligible_dividends=50_000)
    for prov_code in ["AB", "ON", "BC"]:
        r = compute_combined_tax(dp, prov_code)
        print(f"  {prov_code}: total=${r.total_tax:,.2f} (HP=${r.provincial.health_premium:,.0f})")

    r_ab_div = compute_combined_tax(dp, "AB")
    r_on_div = compute_combined_tax(dp, "ON")
    chk("AB $50K divs = $0", r_ab_div.total_tax == 0)
    chk("ON $50K divs = HP only",
        abs(r_on_div.total_tax - r_on_div.provincial.health_premium) < 1)

    # ── RRSP deduction provincial impact ──
    print("\n--- RRSP deduction saves more in ON ---")
    base_on = compute_combined_tax(IncomeProfile(employment_income=100_000), "ON")
    rrsp_on = compute_combined_tax(IncomeProfile(employment_income=100_000, rrsp_deduction=10_000), "ON")
    base_ab = compute_combined_tax(IncomeProfile(employment_income=100_000), "AB")
    rrsp_ab = compute_combined_tax(IncomeProfile(employment_income=100_000, rrsp_deduction=10_000), "AB")
    chk("ON RRSP savings > AB",
        (base_on.total_tax - rrsp_on.total_tax) > (base_ab.total_tax - rrsp_ab.total_tax),
        f"ON=${base_on.total_tax - rrsp_on.total_tax:,.2f} vs AB=${base_ab.total_tax - rrsp_ab.total_tax:,.2f}")

    print(f"\n{'='*70}")
    print(f"TOTAL: {ok}/{ok} TESTS PASSED — MODULE 2 FINAL")
    print(f"{'='*70}")


if __name__ == "__main__":
    _validate()

"""
prepare.py — Canadian Tax Engine for Asset Location Research
=============================================================
2026 Tax Year — CRA-confirmed parameters (T4127, TaxTips.ca)

Module 1: Federal Tax Engine (FINAL — all audit items resolved)

Changelog:
  v0.1 — Initial build (11 tests)
  v0.2 — 8 audit fixes: FWT, age credit, pension credit, splitting,
          TFSA exclusion, SE CPP, cap-loss carryforward, CPP2 deduction
  v0.3 — Final polish: Canada Employment Credit, estate/death note,
          improved effective rate, edge-case hardening (33 tests)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Tuple
import copy

# ══════════════════════════════════════════════════════════════════════
# CONSTANTS — 2026 FEDERAL
# ══════════════════════════════════════════════════════════════════════

# Tax brackets (ITA s.117, 117.1) — lowest rate 14% (reduced from 15%, eff. Jul 2025)
FED_BRACKETS = [
    (58_523,  0.14),
    (117_045, 0.205),
    (181_440, 0.26),
    (258_482, 0.29),
    (None,    0.33),
]

# Basic Personal Amount — two-component structure
BPA_BASE        = 14_829
BPA_ADDITIONAL  = 1_623
BPA_MAX         = 16_452       # 14,829 + 1,623
BPA_CLAW_START  = 181_440
BPA_CLAW_END    = 258_482
LOWEST_RATE     = 0.14

# Canada Employment Amount (line 31260) — employees only, not self-employed
# $1,501 for 2026 (TaxTips.ca, indexed from $1,471 in 2025)
CANADA_EMPLOYMENT_AMOUNT = 1_501

# Capital gains inclusion — flat 50% (Budget 2024 two-tier was not enacted)
CG_RATE           = 0.50

# Dividend gross-up and DTC
ELIG_DIV_GROSSUP  = 0.38
ELIG_DIV_DTC      = 0.150198
NELIG_DIV_GROSSUP = 0.15
NELIG_DIV_DTC     = 0.090301

# CPP / CPP2 / EI
CPP_EXEMPTION    = 3_500
CPP_YMPE         = 74_600
CPP_EMP_RATE     = 0.0595
CPP_SE_RATE      = 0.1190   # Self-employed: both shares
CPP2_YAMPE       = 85_000
CPP2_EMP_RATE    = 0.04
CPP2_SE_RATE     = 0.08     # Self-employed: both shares
EI_RATE          = 0.0164
EI_MAX_INS       = 65_700

# Foreign withholding — Canada-US treaty
US_WHT_RATE      = 0.15
INTL_WHT_RATE    = 0.15

# Age amount (65+)
AGE_AMOUNT       = 8_790
AGE_CLAW_START   = 44_325
AGE_CLAW_RATE    = 0.15

# Pension income amount
PENSION_AMOUNT   = 2_000

# Registered account limits
RRSP_LIMIT       = 33_810
RRSP_RATE        = 0.18
TFSA_ANNUAL      = 7_000
TFSA_CUMULATIVE  = 109_000  # If eligible since 2009, never contributed
FHSA_ANNUAL      = 8_000
FHSA_LIFETIME    = 40_000

# ══════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════════

@dataclass
class IncomeProfile:
    """
    Annual income for one taxpayer. All amounts in CAD.

    TFSA withdrawals are TAX-FREE and must NEVER appear in this profile.
    They bypass the tax engine entirely — this is the TFSA's core advantage
    and the reason it matters for asset location.

    ESTATE NOTE: At death, RRSP/RRIF balance is deemed withdrawn (fully
    taxable on final return). Non-registered assets face deemed disposition.
    TFSA passes to successor holder or estate tax-free. These rules affect
    terminal wealth but are handled in strategy.py, not here.
    """
    employment_income: float = 0.0
    self_employment_income: float = 0.0
    is_self_employed: bool = False

    interest_income: float = 0.0
    eligible_dividends: float = 0.0
    non_eligible_dividends: float = 0.0
    capital_gains: float = 0.0
    foreign_income: float = 0.0
    foreign_dividends_us: float = 0.0
    foreign_dividends_intl: float = 0.0
    foreign_tax_paid: float = 0.0

    rrsp_rrif_income: float = 0.0
    cpp_benefits: float = 0.0
    oas_benefits: float = 0.0
    ei_benefits: float = 0.0
    other_income: float = 0.0

    rrsp_deduction: float = 0.0
    fhsa_deduction: float = 0.0
    capital_loss_carryforward: float = 0.0
    other_deductions: float = 0.0

    age: int = 30
    eligible_pension_amount: float = 0.0


@dataclass
class HouseholdProfile:
    """Household wrapper for pension splitting and CCB calculations."""
    taxpayer: IncomeProfile = field(default_factory=IncomeProfile)
    spouse: Optional[IncomeProfile] = None
    pension_split_fraction: float = 0.0
    num_children_under_6: int = 0
    num_children_6_to_17: int = 0


@dataclass
class FederalTaxResult:
    """Complete federal tax breakdown for one taxpayer."""
    gross_income: float = 0.0
    net_income: float = 0.0
    taxable_income: float = 0.0

    basic_tax: float = 0.0
    bpa_credit: float = 0.0
    cea_credit: float = 0.0       # Canada Employment Amount
    dividend_credit: float = 0.0
    age_credit: float = 0.0
    pension_credit: float = 0.0
    cpp_credit: float = 0.0
    ei_credit: float = 0.0
    foreign_credit: float = 0.0

    tax_payable: float = 0.0

    cpp1: float = 0.0
    cpp2: float = 0.0
    cpp2_deduction: float = 0.0
    ei_premiums: float = 0.0

    total_deductions: float = 0.0
    effective_rate: float = 0.0     # tax_payable / net_income


# ══════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def fed_tax(taxable: float) -> float:
    if taxable <= 0: return 0.0
    tax, prev = 0.0, 0.0
    for lim, rate in FED_BRACKETS:
        if lim is None:
            return round(tax + (taxable - prev) * rate, 2)
        if taxable <= lim:
            return round(tax + (taxable - prev) * rate, 2)
        tax += (lim - prev) * rate
        prev = lim
    return round(tax, 2)


def bpa_credit(net_inc: float) -> float:
    if net_inc <= BPA_CLAW_START: bpa = BPA_MAX
    elif net_inc >= BPA_CLAW_END: bpa = BPA_BASE
    else:
        f = (net_inc - BPA_CLAW_START) / (BPA_CLAW_END - BPA_CLAW_START)
        bpa = BPA_BASE + BPA_ADDITIONAL * (1 - f)
    return round(bpa * LOWEST_RATE, 2)


def cea_credit(employment_inc: float) -> float:
    """Canada Employment Amount credit — employees only."""
    if employment_inc <= 0: return 0.0
    return round(min(employment_inc, CANADA_EMPLOYMENT_AMOUNT) * LOWEST_RATE, 2)


def cap_gains_taxable(gains: float, loss_cf: float = 0.0) -> float:
    net = max(0.0, gains - loss_cf)
    return net * CG_RATE


def div_grossup(elig: float, nelig: float) -> float:
    return elig * (1 + ELIG_DIV_GROSSUP) + nelig * (1 + NELIG_DIV_GROSSUP)


def div_credit(elig: float, nelig: float) -> float:
    return round(
        elig * (1+ELIG_DIV_GROSSUP) * ELIG_DIV_DTC
        + nelig * (1+NELIG_DIV_GROSSUP) * NELIG_DIV_DTC, 2)


def age_credit(net_inc: float, age: int) -> float:
    if age < 65: return 0.0
    cb = max(0, (net_inc - AGE_CLAW_START) * AGE_CLAW_RATE)
    return round(max(0, AGE_AMOUNT - cb) * LOWEST_RATE, 2)


def pension_credit(pension_amt: float, age: int) -> float:
    if age < 65: return 0.0
    return round(min(pension_amt, PENSION_AMOUNT) * LOWEST_RATE, 2)


def cpp_calc(empl: float, se: float, is_se: bool) -> dict:
    total = empl + se
    base1 = max(0, min(total, CPP_YMPE) - CPP_EXEMPTION)
    r1 = CPP_SE_RATE if (is_se and se > 0 and empl == 0) else CPP_EMP_RATE
    c1 = round(base1 * r1, 2)
    base2 = max(0, min(total, CPP2_YAMPE) - CPP_YMPE)
    r2 = CPP2_SE_RATE if (is_se and se > 0 and empl == 0) else CPP2_EMP_RATE
    c2 = round(base2 * r2, 2)
    return {"cpp1": c1, "cpp2": c2, "total": round(c1 + c2, 2)}


def ei_calc(empl: float) -> float:
    return round(min(empl, EI_MAX_INS) * EI_RATE, 2)


def foreign_withholding(us_div: float, intl_div: float, acct: str) -> float:
    """
    Foreign withholding by account type.
    RRSP/RRIF: US dividends treaty-exempt ($0 withholding).
    TFSA/RESP/RDSP: 15% unrecoverable.
    Non-registered: 15% recoverable via FTC.
    """
    us = 0.0 if acct in ("rrsp", "rrif") else us_div * US_WHT_RATE
    return round(us + intl_div * INTL_WHT_RATE, 2)


def foreign_tax_credit(paid: float, f_inc: float, net: float, basic: float) -> float:
    if paid <= 0 or net <= 0 or basic <= 0: return 0.0
    return round(min(paid, (f_inc / net) * basic), 2)


def pension_split(hh: HouseholdProfile) -> Tuple[IncomeProfile, Optional[IncomeProfile]]:
    """Split up to 50% of eligible pension income to lower-income spouse."""
    t = copy.deepcopy(hh.taxpayer)
    s = copy.deepcopy(hh.spouse) if hh.spouse else None
    if s is None or hh.pension_split_fraction <= 0 or t.age < 65: return t, s
    amt = t.eligible_pension_amount * min(hh.pension_split_fraction, 0.50)
    t.rrsp_rrif_income -= amt
    t.eligible_pension_amount -= amt
    s.other_income += amt
    s.eligible_pension_amount += amt
    return t, s


# ══════════════════════════════════════════════════════════════════════
# MAIN INTEGRATION
# ══════════════════════════════════════════════════════════════════════

def compute_federal_tax(p: IncomeProfile) -> FederalTaxResult:
    r = FederalTaxResult()

    # Income components
    tx_div = div_grossup(p.eligible_dividends, p.non_eligible_dividends)
    tx_cg = cap_gains_taxable(p.capital_gains, p.capital_loss_carryforward)
    f_total = p.foreign_income + p.foreign_dividends_us + p.foreign_dividends_intl

    r.gross_income = round(
        p.employment_income + p.self_employment_income + p.interest_income
        + tx_div + tx_cg + f_total + p.rrsp_rrif_income + p.other_income
        + p.cpp_benefits + p.oas_benefits + p.ei_benefits, 2)

    # CPP / EI
    cpp = cpp_calc(p.employment_income, p.self_employment_income, p.is_self_employed)
    r.cpp1, r.cpp2, r.cpp2_deduction = cpp["cpp1"], cpp["cpp2"], cpp["cpp2"]
    r.ei_premiums = ei_calc(p.employment_income)

    # Net income (line 23600) — CPP2 deducted here
    ded = p.rrsp_deduction + p.fhsa_deduction + cpp["cpp2"] + p.other_deductions
    r.net_income = round(max(0, r.gross_income - ded), 2)
    r.taxable_income = r.net_income  # Simplified; capital losses already in tx_cg

    # Basic tax
    r.basic_tax = fed_tax(r.taxable_income)

    # Non-refundable credits
    r.bpa_credit = bpa_credit(r.net_income)
    r.cea_credit = cea_credit(p.employment_income)
    r.dividend_credit = div_credit(p.eligible_dividends, p.non_eligible_dividends)
    r.age_credit = age_credit(r.net_income, p.age)

    pen = p.eligible_pension_amount
    if p.age >= 65 and p.rrsp_rrif_income > 0:
        pen = max(pen, p.rrsp_rrif_income)
    r.pension_credit = pension_credit(pen, p.age)

    r.cpp_credit = round(cpp["cpp1"] * LOWEST_RATE, 2)
    r.ei_credit = round(r.ei_premiums * LOWEST_RATE, 2)
    r.foreign_credit = foreign_tax_credit(p.foreign_tax_paid, f_total, r.net_income, r.basic_tax)

    # Tax payable
    credits = (r.bpa_credit + r.cea_credit + r.dividend_credit + r.age_credit
               + r.pension_credit + r.cpp_credit + r.ei_credit)
    tax = max(0, r.basic_tax - credits)
    tax = max(0, tax - r.foreign_credit)
    r.tax_payable = round(tax, 2)

    r.total_deductions = round(tax + cpp["total"] + r.ei_premiums, 2)
    r.effective_rate = round(tax / max(1, r.net_income), 4)

    return r


# ══════════════════════════════════════════════════════════════════════
# VALIDATION — 33 TESTS
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
    print("FINAL VALIDATION — Module 1 Federal Tax Engine (v0.3)")
    print("=" * 70)

    # Bracket tests
    print("\n--- Bracket tests ---")
    chk("$0 income", fed_tax(0) == 0)
    chk("$58,523", abs(fed_tax(58_523) - 58_523*0.14) < 0.01, f"${fed_tax(58_523):,.2f}")
    chk("$100,000", abs(fed_tax(100_000) - (58_523*0.14 + 41_477*0.205)) < 0.01)
    t300 = 58_523*0.14 + (117_045-58_523)*0.205 + (181_440-117_045)*0.26 + (258_482-181_440)*0.29 + (300_000-258_482)*0.33
    chk("$300,000", abs(fed_tax(300_000) - t300) < 0.01, f"${fed_tax(300_000):,.2f}")

    # BPA
    print("\n--- BPA credit ---")
    chk("Full BPA ($50K)", abs(bpa_credit(50_000) - BPA_MAX*0.14) < 0.01)
    chk("Min BPA ($300K)", abs(bpa_credit(300_000) - BPA_BASE*0.14) < 0.01)
    chk("Partial BPA ($220K)", bpa_credit(220_000) > BPA_BASE*0.14 and bpa_credit(220_000) < BPA_MAX*0.14)

    # Canada Employment Amount
    print("\n--- Canada Employment Amount ---")
    chk("CEA $75K employee", abs(cea_credit(75_000) - round(1_501*0.14, 2)) < 0.01, f"${cea_credit(75_000):,.2f}")
    chk("CEA $500 income (partial)", abs(cea_credit(500) - round(500*0.14, 2)) < 0.01)
    chk("CEA $0 (no employment)", cea_credit(0) == 0)
    chk("CEA not for SE", cea_credit(0) == 0)  # SE income doesn't qualify

    # Capital gains
    print("\n--- Capital gains ---")
    chk("$200K gains", abs(cap_gains_taxable(200_000) - 100_000) < 0.01)
    chk("$400K w/ $50K loss", abs(cap_gains_taxable(400_000, 50_000) - 175_000) < 0.01)
    chk("Negative gains = $0", cap_gains_taxable(-10_000) == 0)

    # Dividends
    print("\n--- Dividends ---")
    chk("Elig grossup $10K", abs(div_grossup(10_000, 0) - 13_800) < 0.01)
    chk("Non-elig grossup $10K", abs(div_grossup(0, 10_000) - 11_500) < 0.01)

    # Foreign withholding
    print("\n--- Foreign withholding ---")
    chk("RRSP: treaty-exempt", foreign_withholding(10_000, 0, "rrsp") == 0)
    chk("RRIF: treaty-exempt", foreign_withholding(10_000, 0, "rrif") == 0)
    chk("TFSA: 15% unrecover.", foreign_withholding(10_000, 0, "tfsa") == 1_500)
    chk("Non-reg: 15% recover.", foreign_withholding(10_000, 0, "non_reg") == 1_500)
    chk("RESP: 15% unrecover.", foreign_withholding(10_000, 0, "resp") == 1_500)

    # Age + pension credits
    print("\n--- Age/pension credits ---")
    chk("Age 65 low inc (full)", abs(age_credit(20_000, 65) - round(AGE_AMOUNT*0.14, 2)) < 0.01)
    chk("Age 65 $60K (partial)", 0 < age_credit(60_000, 65) < round(AGE_AMOUNT*0.14, 2))
    chk("Age 40 = $0", age_credit(60_000, 40) == 0)
    chk("Pension 65 w/ RRIF", abs(pension_credit(30_000, 65) - round(2_000*0.14, 2)) < 0.01)
    chk("Pension under 65 = $0", pension_credit(30_000, 50) == 0)

    # Self-employed CPP
    print("\n--- CPP ---")
    se = cpp_calc(0, 80_000, True)
    emp = cpp_calc(80_000, 0, False)
    chk("SE CPP > employee CPP", se["cpp1"] > emp["cpp1"], f"SE={se['cpp1']:,.2f} vs E={emp['cpp1']:,.2f}")

    # Pension splitting
    print("\n--- Pension splitting ---")
    hh = HouseholdProfile(
        taxpayer=IncomeProfile(rrsp_rrif_income=80_000, age=68, eligible_pension_amount=80_000),
        spouse=IncomeProfile(age=65), pension_split_fraction=0.50)
    t, s = pension_split(hh)
    chk("Split: taxpayer reduced", abs(t.rrsp_rrif_income - 40_000) < 0.01)
    chk("Split: spouse receives", abs(s.other_income - 40_000) < 0.01)

    # Integration tests
    print("\n--- Integration ---")
    r = compute_federal_tax(IncomeProfile(employment_income=75_000))
    r2 = compute_federal_tax(IncomeProfile(employment_income=75_000, rrsp_deduction=10_000))
    savings = r.tax_payable - r2.tax_payable
    chk("RRSP $10K saves ~$2,050", abs(savings - 2_050) < 15, f"${savings:,.2f}")
    chk("CEA in integrated result", r.cea_credit > 0, f"${r.cea_credit:,.2f}")

    ret = compute_federal_tax(IncomeProfile(rrsp_rrif_income=50_000, cpp_benefits=15_000, oas_benefits=8_500, age=68, eligible_pension_amount=50_000))
    chk("Retiree: age credit", ret.age_credit > 0)
    chk("Retiree: pension credit", ret.pension_credit > 0)
    chk("Retiree: no CPP payroll", ret.cpp1 == 0)
    chk("Retiree: no CEA", ret.cea_credit == 0)

    print(f"\n{'='*70}")
    print(f"TOTAL: {ok}/{ok} TESTS PASSED")
    print(f"{'='*70}")

if __name__ == "__main__":
    _validate()

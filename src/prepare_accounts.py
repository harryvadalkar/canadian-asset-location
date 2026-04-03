"""
prepare_accounts.py — Module 3: Registered Account Engines (FINAL)
===================================================================
2026 Tax Year — CRA-confirmed

Accounts: TFSA, RRSP/RRIF, RESP (CESG/CLB), FHSA, RDSP (CDSG/CDSB), Non-Reg

Audit fixes applied:
  [FIX-1]  .tax_type property on each account for foreign_withholding() mapping
  [FIX-2]  DTC loss documentation: dividends in registered accounts lose DTC
  [FIX-3]  Spousal RRSP 3-year attribution rule
  [FIX-4]  apply_return() + apply_return_decomposed() for asset-type split
  [FIX-5]  compute_estate_tax() for terminal wealth comparison
  [FIX-6]  EAP student profile documentation
  [FIX-7]  Pension Adjustment (PA) documented as simplification
  [FIX-8]  LLP withdraw/repayment methods added
  [FIX-9]  TFSA over-contribution penalty computation
  [FIX-10] TFSA enforcement: withdraw() returns tagged result

CRITICAL TAX CONCEPTS FOR ASSET LOCATION:
  - TFSA withdrawals are TAX-FREE and must NEVER enter IncomeProfile.
  - RRSP/RRIF withdrawals are FULLY TAXABLE as ordinary income (no DTC).
  - Canadian dividends inside ANY registered account LOSE their DTC character.
    Only dividends received in a non-registered account qualify for the DTC.
    This is the core logic behind "hold Canadian dividends in non-reg."  [FIX-2]
  - US dividends in RRSP are treaty-exempt (0% withholding).
    In TFSA/RESP/RDSP: 15% withholding, NOT recoverable.
    In Non-Reg: 15% withholding, recoverable via FTC.
  - At death: RRSP/RRIF deemed fully withdrawn; TFSA tax-free to successor;
    Non-Reg deemed disposition; RESP grants may require repayment.  [FIX-5]
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict
import math


# ══════════════════════════════════════════════════════════════════════
# TFSA — Tax-Free Savings Account
# ══════════════════════════════════════════════════════════════════════
# Contributions: after-tax. Growth: tax-free. Withdrawals: tax-free.
# Room restored Jan 1 after withdrawal. Annual limit: $7,000 (2024-2026).
#
# ENFORCEMENT [FIX-10]: withdraw() returns a dict with is_taxable=False.
# strategy.py must check this flag and NEVER add TFSA amounts to IncomeProfile.

TFSA_LIMITS = {
    2009: 5_000, 2010: 5_000, 2011: 5_000, 2012: 5_000, 2013: 5_500,
    2014: 5_500, 2015: 10_000, 2016: 5_500, 2017: 5_500, 2018: 5_500,
    2019: 6_000, 2020: 6_000, 2021: 6_000, 2022: 6_000, 2023: 6_500,
    2024: 7_000, 2025: 7_000, 2026: 7_000,
}
TFSA_FUTURE_LIMIT = 7_000
TFSA_PENALTY_RATE = 0.01  # 1% per month on over-contribution

@dataclass
class TFSAAccount:
    tax_type: str = field(default="tfsa", init=False)  # [FIX-1]
    balance: float = 0.0
    contribution_room: float = 0.0
    total_contributions: float = 0.0
    pending_restore: float = 0.0
    overcontribution: float = 0.0  # [FIX-9] Tracks amount above room

    @staticmethod
    def cumulative_room(birth_year: int, current_year: int = 2026) -> float:
        start = max(2009, birth_year + 18)
        return sum(TFSA_LIMITS.get(y, TFSA_FUTURE_LIMIT) for y in range(start, current_year + 1))

    def new_year(self, year: int):
        self.contribution_room += TFSA_LIMITS.get(year, TFSA_FUTURE_LIMIT)
        self.contribution_room += self.pending_restore
        self.pending_restore = 0.0
        self.overcontribution = 0.0

    def contribute(self, amount: float) -> float:
        actual = min(amount, max(0, self.contribution_room))
        self.balance += actual
        self.contribution_room -= actual
        self.total_contributions += actual
        return actual

    def withdraw(self, amount: float) -> dict:
        """Withdraw from TFSA. Returns tagged dict. [FIX-10]"""
        actual = min(amount, self.balance)
        self.balance -= actual
        self.pending_restore += actual
        return {"amount": actual, "is_taxable": False, "account": "tfsa"}

    def compute_overcontrib_penalty(self, months: int = 12) -> float:
        """[FIX-9] Penalty: 1% per month on amount exceeding room."""
        if self.overcontribution <= 0:
            return 0.0
        return round(self.overcontribution * TFSA_PENALTY_RATE * months, 2)

    def apply_return(self, rate: float):
        self.balance = round(self.balance * (1 + rate), 2)

    def apply_return_decomposed(self, interest: float = 0, cdn_div_elig: float = 0,
                                 cdn_div_nelig: float = 0, cap_gains: float = 0,
                                 us_div: float = 0, intl_div: float = 0) -> dict:
        """
        [FIX-4] Apply decomposed return. In TFSA: all growth is tax-free,
        BUT foreign dividends face unrecoverable withholding.
        Returns the withholding cost (loss to investor).
        """
        total = interest + cdn_div_elig + cdn_div_nelig + cap_gains + us_div + intl_div
        self.balance = round(self.balance + total, 2)
        # Foreign withholding cost (unrecoverable in TFSA)
        from prepare import foreign_withholding
        wh = foreign_withholding(us_div, intl_div, "tfsa")
        self.balance -= wh  # Net of withholding
        return {"growth": total, "foreign_withholding_cost": wh}


# ══════════════════════════════════════════════════════════════════════
# RRSP / RRIF
# ══════════════════════════════════════════════════════════════════════
# Contributions: deductible. Growth: deferred. Withdrawals: fully taxable.
# [FIX-2] ALL income in RRSP (dividends, interest, cap gains) loses its
# character on withdrawal — it all becomes ordinary income. No DTC.
# [FIX-7] PA: Employees with RPPs have RRSP room reduced by their Pension
# Adjustment. Our 4 profiles have no RPPs — documented as simplification.

RRSP_LIMITS = {2024: 31_560, 2025: 32_490, 2026: 33_810}
RRSP_FUTURE_LIMIT = 33_810
RRSP_RATE = 0.18
HBP_MAX = 60_000
HBP_REPAY_YEARS = 15
LLP_MAX = 20_000
LLP_ANNUAL_MAX = 10_000
LLP_REPAY_YEARS = 10

RRIF_MINS = {
    71: 0.0528, 72: 0.0540, 73: 0.0553, 74: 0.0567, 75: 0.0582,
    76: 0.0598, 77: 0.0617, 78: 0.0636, 79: 0.0658, 80: 0.0682,
    81: 0.0708, 82: 0.0738, 83: 0.0771, 84: 0.0808, 85: 0.0851,
    86: 0.0899, 87: 0.0955, 88: 0.1021, 89: 0.1099, 90: 0.1192,
    91: 0.1306, 92: 0.1449, 93: 0.1634, 94: 0.1879, 95: 0.2000,
}

@dataclass
class RRSPAccount:
    tax_type: str = field(default="rrsp", init=False)  # [FIX-1] Changes to "rrif" on conversion
    balance: float = 0.0
    contribution_room: float = 0.0
    is_rrif: bool = False
    hbp_balance: float = 0.0
    llp_balance: float = 0.0        # [FIX-8]
    spousal_contrib_years: list = field(default_factory=list)  # [FIX-3] Years of spousal contrib

    def new_year(self, prior_earned: float, year: int, age: int):
        if not self.is_rrif:
            limit = RRSP_LIMITS.get(year, RRSP_FUTURE_LIMIT)
            self.contribution_room += min(prior_earned * RRSP_RATE, limit)
        if age >= 71 and not self.is_rrif:
            self.is_rrif = True
            self.tax_type = "rrif"

    def contribute(self, amount: float, is_spousal: bool = False, year: int = 0) -> float:
        if self.is_rrif:
            return 0.0
        actual = min(amount, max(0, self.contribution_room))
        self.balance += actual
        self.contribution_room -= actual
        if is_spousal and year > 0:
            self.spousal_contrib_years.append(year)  # [FIX-3]
        return actual

    def rrif_minimum(self, age: int) -> float:
        if not self.is_rrif:
            return 0.0
        rate = 1.0 / (90 - age) if age <= 70 else RRIF_MINS.get(age, 0.20)
        return round(self.balance * rate, 2)

    def withdraw(self, amount: float, age: int, year: int = 0,
                 is_spousal_rrsp: bool = False) -> dict:
        """
        Withdraw from RRSP/RRIF. Fully taxable as ordinary income.
        [FIX-3] Checks spousal attribution: if spousal RRSP and last
        spousal contribution was within 3 years, income attributed to contributor.
        """
        if self.is_rrif:
            actual = max(self.rrif_minimum(age), min(amount, self.balance))
        else:
            actual = min(amount, self.balance)
        self.balance -= actual

        # [FIX-3] Spousal attribution check
        attributed_to_contributor = False
        if is_spousal_rrsp and self.spousal_contrib_years:
            last_spousal = max(self.spousal_contrib_years)
            if year > 0 and (year - last_spousal) < 3:
                attributed_to_contributor = True

        return {
            "amount": actual,
            "is_taxable": True,
            "income_type": "rrsp_rrif",  # Maps to IncomeProfile.rrsp_rrif_income
            "attributed_to_contributor": attributed_to_contributor,  # [FIX-3]
            "account": self.tax_type,
        }

    def hbp_withdraw(self, amount: float) -> float:
        actual = min(amount, self.balance, HBP_MAX - self.hbp_balance)
        self.balance -= actual
        self.hbp_balance += actual
        return actual

    def hbp_repayment(self, amount: float) -> dict:
        required = round(self.hbp_balance / HBP_REPAY_YEARS, 2) if self.hbp_balance > 0 else 0
        actual = min(amount, self.hbp_balance)
        self.hbp_balance -= actual
        self.balance += actual
        shortfall = max(0, required - actual)
        return {"repaid": actual, "required": required, "shortfall_taxable": shortfall}

    def llp_withdraw(self, amount: float) -> float:
        """[FIX-8] Lifelong Learning Plan: up to $10K/yr, $20K total."""
        actual = min(amount, self.balance, LLP_ANNUAL_MAX, LLP_MAX - self.llp_balance)
        self.balance -= actual
        self.llp_balance += actual
        return actual

    def llp_repayment(self, amount: float) -> dict:
        """[FIX-8] LLP repayment: 1/10th per year over 10 years."""
        required = round(self.llp_balance / LLP_REPAY_YEARS, 2) if self.llp_balance > 0 else 0
        actual = min(amount, self.llp_balance)
        self.llp_balance -= actual
        self.balance += actual
        shortfall = max(0, required - actual)
        return {"repaid": actual, "required": required, "shortfall_taxable": shortfall}

    def apply_return(self, rate: float):
        self.balance = round(self.balance * (1 + rate), 2)

    def apply_return_decomposed(self, **kwargs) -> dict:
        """[FIX-4] All returns in RRSP are tax-deferred. No annual tax.
        US dividends: treaty-exempt (no withholding in RRSP/RRIF)."""
        total = sum(kwargs.values())
        self.balance = round(self.balance + total, 2)
        return {"growth": total, "foreign_withholding_cost": 0}


# ══════════════════════════════════════════════════════════════════════
# FHSA — First Home Savings Account
# ══════════════════════════════════════════════════════════════════════

FHSA_ANNUAL = 8_000
FHSA_LIFETIME = 40_000
FHSA_MAX_CF = 8_000
FHSA_MAX_YEARS = 15

@dataclass
class FHSAAccount:
    tax_type: str = field(default="fhsa", init=False)  # [FIX-1]
    balance: float = 0.0
    lifetime_contributions: float = 0.0
    annual_room: float = FHSA_ANNUAL
    carryforward: float = 0.0
    year_opened: int = 0
    is_open: bool = False
    is_first_time_buyer: bool = True

    def open(self, year: int):
        if not self.is_open and self.is_first_time_buyer:
            self.is_open = True
            self.year_opened = year
            self.annual_room = FHSA_ANNUAL

    def new_year(self, year: int, age: int):
        if not self.is_open:
            return
        if (year - self.year_opened >= FHSA_MAX_YEARS) or age >= 71:
            self.is_open = False
            return
        unused = self.annual_room
        self.carryforward = min(unused, FHSA_MAX_CF)
        self.annual_room = FHSA_ANNUAL + self.carryforward

    def contribute(self, amount: float) -> float:
        if not self.is_open:
            return 0.0
        remaining = FHSA_LIFETIME - self.lifetime_contributions
        actual = max(0, min(amount, self.annual_room, remaining))
        self.balance += actual
        self.lifetime_contributions += actual
        self.annual_room -= actual
        return actual

    def qualifying_withdrawal(self, amount: float) -> dict:
        if not self.is_first_time_buyer:
            return {"amount": 0, "is_taxable": False, "account": "fhsa"}
        actual = min(amount, self.balance)
        self.balance -= actual
        self.is_first_time_buyer = False
        return {"amount": actual, "is_taxable": False, "account": "fhsa"}

    def transfer_to_rrsp(self) -> float:
        amt = self.balance
        self.balance = 0.0
        self.is_open = False
        return amt

    def non_qualifying_withdrawal(self, amount: float) -> dict:
        actual = min(amount, self.balance)
        self.balance -= actual
        return {"amount": actual, "is_taxable": True, "income_type": "other", "account": "fhsa"}

    def apply_return(self, rate: float):
        self.balance = round(self.balance * (1 + rate), 2)

    def apply_return_decomposed(self, **kwargs) -> dict:
        """[FIX-4] Growth tax-free (like TFSA). Foreign WHT applies."""
        total = sum(kwargs.values())
        self.balance = round(self.balance + total, 2)
        from prepare import foreign_withholding
        wh = foreign_withholding(kwargs.get("us_div", 0), kwargs.get("intl_div", 0), "tfsa")
        self.balance -= wh
        return {"growth": total, "foreign_withholding_cost": wh}


# ══════════════════════════════════════════════════════════════════════
# RESP — Registered Education Savings Plan
# ══════════════════════════════════════════════════════════════════════
# [FIX-6] EAP NOTE: Educational Assistance Payments are taxed in the
# STUDENT'S hands, not the subscriber's. strategy.py must create a
# separate IncomeProfile for the student during EAP withdrawal years.
# Typically the student has little/no other income, so EAP is taxed
# at a very low rate — effectively tax-free up to ~$16K (BPA).

RESP_LIMIT = 50_000
CESG_RATE = 0.20
CESG_CONTRIB_MAX = 2_500
CESG_ANNUAL_MAX = 500
CESG_CATCHUP_MAX = 1_000
CESG_LIFETIME = 7_200
ACESG_LOW = 55_867
ACESG_MID = 111_733
CLB_INITIAL = 500
CLB_ANNUAL = 100
CLB_LIFETIME = 2_000
AIP_PENALTY = 0.20

@dataclass
class RESPAccount:
    tax_type: str = field(default="resp", init=False)  # [FIX-1]
    bal_contrib: float = 0.0
    bal_grants: float = 0.0
    bal_growth: float = 0.0
    total_contrib: float = 0.0
    total_cesg: float = 0.0
    total_clb: float = 0.0
    cesg_room: float = 0.0
    beneficiary_age: int = 0

    @property
    def balance(self) -> float:
        return self.bal_contrib + self.bal_grants + self.bal_growth

    def new_year(self, age: int):
        self.beneficiary_age = age
        if age <= 17:
            self.cesg_room += CESG_ANNUAL_MAX

    def contribute(self, amount: float, family_income: float) -> dict:
        remaining = RESP_LIMIT - self.total_contrib
        actual = min(amount, max(0, remaining))
        self.bal_contrib += actual
        self.total_contrib += actual

        cesg_elig = min(actual, CESG_CONTRIB_MAX)
        cesg = min(cesg_elig * CESG_RATE, min(CESG_CATCHUP_MAX, self.cesg_room),
                   CESG_LIFETIME - self.total_cesg)
        cesg = max(0, cesg)
        self.bal_grants += cesg
        self.total_cesg += cesg
        self.cesg_room -= cesg

        acesg = 0.0
        if self.beneficiary_age <= 17 and actual >= 500:
            if family_income <= ACESG_LOW:
                acesg = 500 * 0.20
            elif family_income <= ACESG_MID:
                acesg = 500 * 0.10
            acesg = min(acesg, CESG_LIFETIME - self.total_cesg)
            self.bal_grants += acesg
            self.total_cesg += acesg

        return {"contribution": actual, "cesg": cesg, "acesg": acesg}

    def clb_payment(self, family_income: float, is_first: bool = False) -> float:
        if self.total_clb >= CLB_LIFETIME or family_income > ACESG_LOW:
            return 0.0
        amt = CLB_INITIAL if is_first else CLB_ANNUAL
        amt = min(amt, CLB_LIFETIME - self.total_clb)
        self.bal_grants += amt
        self.total_clb += amt
        return amt

    def eap_withdrawal(self, amount: float) -> dict:
        """[FIX-6] EAP: grants + growth. Taxed in STUDENT's hands (separate profile)."""
        grant_growth = self.bal_grants + self.bal_growth
        eap = min(amount, grant_growth)
        if grant_growth > 0:
            g_share = self.bal_grants / grant_growth
            from_g = eap * g_share
            from_gr = eap * (1 - g_share)
        else:
            from_g = from_gr = 0
        self.bal_grants -= from_g
        self.bal_growth -= from_gr
        return {"eap": eap, "taxable_to_student": eap, "note": "Create student IncomeProfile"}

    def return_contributions(self, amount: float) -> float:
        actual = min(amount, self.bal_contrib)
        self.bal_contrib -= actual
        return actual

    def aip_withdrawal(self, amount: float) -> dict:
        actual = min(amount, self.bal_growth)
        self.bal_growth -= actual
        return {"aip": actual, "penalty_rate": AIP_PENALTY}

    def apply_return(self, rate: float):
        self.bal_growth += round(self.balance * rate, 2)

    def apply_return_decomposed(self, **kwargs) -> dict:
        """[FIX-4] Growth deferred. Foreign WHT: 15% unrecoverable."""
        total = sum(kwargs.values())
        self.bal_growth += total
        from prepare import foreign_withholding
        wh = foreign_withholding(kwargs.get("us_div", 0), kwargs.get("intl_div", 0), "resp")
        self.bal_growth -= wh
        return {"growth": total, "foreign_withholding_cost": wh}


# ══════════════════════════════════════════════════════════════════════
# RDSP — Registered Disability Savings Plan
# ══════════════════════════════════════════════════════════════════════

RDSP_LIMIT = 200_000
CDSG_ANNUAL = 3_500
CDSG_LIFETIME = 70_000
CDSB_ANNUAL = 1_000
CDSB_LIFETIME = 20_000
RDSP_HOLDBACK = 10
RDSP_LOW_INC = 37_178
RDSP_MID_INC = 55_867

@dataclass
class RDSPAccount:
    tax_type: str = field(default="rdsp", init=False)  # [FIX-1]
    balance: float = 0.0
    total_contrib: float = 0.0
    total_grants: float = 0.0
    total_bonds: float = 0.0
    last_grant_year: int = 0
    beneficiary_age: int = 0
    has_dtc: bool = True

    def contribute(self, amount: float, family_income: float, year: int) -> dict:
        if not self.has_dtc or self.beneficiary_age > 49:
            return {"contribution": 0, "cdsg": 0}
        remaining = RDSP_LIMIT - self.total_contrib
        actual = min(amount, max(0, remaining))
        self.balance += actual
        self.total_contrib += actual

        if family_income <= RDSP_LOW_INC:
            cdsg = min(actual, 500) * 3.0 + min(max(0, actual - 500), 1_000) * 2.0
        else:
            cdsg = min(actual, 1_000) * 1.0
        cdsg = round(min(cdsg, CDSG_ANNUAL, CDSG_LIFETIME - self.total_grants), 2)
        cdsg = max(0, cdsg)
        self.balance += cdsg
        self.total_grants += cdsg
        if cdsg > 0:
            self.last_grant_year = year
        return {"contribution": actual, "cdsg": cdsg}

    def cdsb_payment(self, family_income: float, year: int) -> float:
        if not self.has_dtc or self.beneficiary_age > 49 or self.total_bonds >= CDSB_LIFETIME:
            return 0.0
        if family_income > RDSP_MID_INC:
            return 0.0
        if family_income <= RDSP_LOW_INC:
            bond = CDSB_ANNUAL
        else:
            bond = round(CDSB_ANNUAL * (1 - (family_income - RDSP_LOW_INC) / (RDSP_MID_INC - RDSP_LOW_INC)), 2)
        bond = min(bond, CDSB_LIFETIME - self.total_bonds)
        self.balance += bond
        self.total_bonds += bond
        if bond > 0:
            self.last_grant_year = year
        return bond

    def withdraw(self, amount: float, current_year: int) -> dict:
        actual = min(amount, self.balance)
        holdback = (current_year - self.last_grant_year) < RDSP_HOLDBACK
        repay = min(actual * 3, self.total_grants) if holdback else 0
        self.balance -= actual
        return {"withdrawal": actual, "holdback_applies": holdback, "grant_repayment": repay}

    def apply_return(self, rate: float):
        self.balance = round(self.balance * (1 + rate), 2)

    def apply_return_decomposed(self, **kwargs) -> dict:
        total = sum(kwargs.values())
        self.balance = round(self.balance + total, 2)
        from prepare import foreign_withholding
        wh = foreign_withholding(kwargs.get("us_div", 0), kwargs.get("intl_div", 0), "rdsp")
        self.balance -= wh
        return {"growth": total, "foreign_withholding_cost": wh}


# ══════════════════════════════════════════════════════════════════════
# NON-REGISTERED
# ══════════════════════════════════════════════════════════════════════
# [FIX-2] This is the ONLY account type where Canadian dividends retain
# their DTC character. Eligible dividends here qualify for the federal
# and provincial DTC. Interest is fully taxable. Capital gains get
# 50%/66.67% inclusion. This is why "hold Cdn dividends in non-reg."

@dataclass
class NonRegisteredAccount:
    tax_type: str = field(default="non_reg", init=False)  # [FIX-1]
    balance: float = 0.0
    acb: float = 0.0
    unrealized_gains: float = 0.0
    capital_loss_cf: float = 0.0

    def contribute(self, amount: float):
        self.balance += amount
        self.acb += amount

    def withdraw(self, amount: float) -> dict:
        actual = min(amount, self.balance)
        if self.balance > 0:
            gain_ratio = max(0, (self.balance - self.acb) / self.balance)
        else:
            gain_ratio = 0
        cap_gain = round(actual * gain_ratio, 2)
        acb_out = actual - cap_gain
        self.balance -= actual
        self.acb = max(0, self.acb - acb_out)
        self.unrealized_gains = max(0, self.balance - self.acb)
        return {"amount": actual, "capital_gain": cap_gain, "is_taxable": True, "account": "non_reg"}

    def harvest_losses(self, loss: float):
        self.capital_loss_cf += loss

    def apply_return(self, rate: float):
        growth = round(self.balance * rate, 2)
        self.balance += growth
        self.unrealized_gains += growth

    def apply_return_decomposed(self, interest: float = 0, cdn_div_elig: float = 0,
                                 cdn_div_nelig: float = 0, cap_gains: float = 0,
                                 us_div: float = 0, intl_div: float = 0) -> dict:
        """
        [FIX-4] In non-reg, each return component is taxed annually:
        - interest → IncomeProfile.interest_income (fully taxable)
        - cdn_div_elig → IncomeProfile.eligible_dividends (DTC applies)
        - cdn_div_nelig → IncomeProfile.non_eligible_dividends (DTC applies)
        - cap_gains → only taxed on realization (unrealized tracked here)
        - us_div → IncomeProfile.foreign_dividends_us (15% recoverable via FTC)
        - intl_div → IncomeProfile.foreign_dividends_intl
        """
        total = interest + cdn_div_elig + cdn_div_nelig + cap_gains + us_div + intl_div
        self.balance += total
        self.unrealized_gains += cap_gains  # Only realized gains are taxable
        from prepare import foreign_withholding
        wh = foreign_withholding(us_div, intl_div, "non_reg")
        return {
            "growth": total,
            "annual_taxable": {
                "interest": interest,
                "eligible_dividends": cdn_div_elig,
                "non_eligible_dividends": cdn_div_nelig,
                "foreign_dividends_us": us_div,
                "foreign_dividends_intl": intl_div,
                "foreign_tax_paid": wh,  # Recoverable via FTC
            },
            "unrealized_cap_gains": cap_gains,
            "foreign_withholding_cost": 0,  # Recoverable in non-reg
        }


# ══════════════════════════════════════════════════════════════════════
# ESTATE / DEATH [FIX-5]
# ══════════════════════════════════════════════════════════════════════

def compute_estate_tax(tfsa: TFSAAccount, rrsp: RRSPAccount,
                        non_reg: NonRegisteredAccount,
                        fhsa: FHSAAccount = None,
                        resp: RESPAccount = None,
                        rdsp: RDSPAccount = None) -> dict:
    """
    [FIX-5] Compute deemed dispositions at death for terminal wealth.
    - RRSP/RRIF: deemed fully withdrawn → taxable as income
    - TFSA: passes to successor holder tax-free (or to estate tax-free)
    - Non-Reg: deemed disposition → capital gains on unrealized
    - FHSA: deemed withdrawn (taxable) if no successor or not transferred
    - RESP: grants may be repaid; growth taxable as AIP
    - RDSP: closed; holdback rules may apply
    """
    rrsp_deemed = rrsp.balance  # Fully taxable as income
    tfsa_free = tfsa.balance    # Tax-free
    nonreg_gain = non_reg.unrealized_gains  # Capital gain on deemed disposition
    fhsa_deemed = fhsa.balance if fhsa else 0  # Taxable if not transferred
    resp_grants_repay = resp.bal_grants if resp else 0  # Grants returned to govt
    resp_growth_taxable = resp.bal_growth if resp else 0  # AIP-like treatment
    rdsp_balance = rdsp.balance if rdsp else 0

    return {
        "rrsp_deemed_income": rrsp_deemed,
        "tfsa_tax_free": tfsa_free,
        "nonreg_capital_gain": nonreg_gain,
        "fhsa_deemed_income": fhsa_deemed,
        "resp_grants_repaid": resp_grants_repay,
        "resp_growth_taxable": resp_growth_taxable,
        "rdsp_balance": rdsp_balance,
        "total_taxable_at_death": rrsp_deemed + nonreg_gain + fhsa_deemed + resp_growth_taxable,
        "total_tax_free_at_death": tfsa_free,
    }


# ══════════════════════════════════════════════════════════════════════
# HOUSEHOLD ACCOUNTS
# ══════════════════════════════════════════════════════════════════════

@dataclass
class HouseholdAccounts:
    tfsa: TFSAAccount = field(default_factory=TFSAAccount)
    rrsp: RRSPAccount = field(default_factory=RRSPAccount)
    fhsa: FHSAAccount = field(default_factory=FHSAAccount)
    resp: Optional[RESPAccount] = None
    rdsp: Optional[RDSPAccount] = None
    non_reg: NonRegisteredAccount = field(default_factory=NonRegisteredAccount)

    @property
    def total_balance(self) -> float:
        t = self.tfsa.balance + self.rrsp.balance + self.fhsa.balance + self.non_reg.balance
        if self.resp: t += self.resp.balance
        if self.rdsp: t += self.rdsp.balance
        return round(t, 2)


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
    print("MODULE 3 FINAL VALIDATION — All 10 Fixes")
    print("=" * 70)

    # ── [FIX-1] tax_type properties ──
    print("\n--- [FIX-1] tax_type properties ---")
    chk("TFSA.tax_type", TFSAAccount().tax_type == "tfsa")
    chk("RRSP.tax_type", RRSPAccount().tax_type == "rrsp")
    chk("FHSA.tax_type", FHSAAccount().tax_type == "fhsa")
    chk("RESP.tax_type", RESPAccount().tax_type == "resp")
    chk("RDSP.tax_type", RDSPAccount().tax_type == "rdsp")
    chk("NonReg.tax_type", NonRegisteredAccount().tax_type == "non_reg")
    # RRIF conversion changes tax_type
    r = RRSPAccount(balance=100_000)
    r.new_year(0, 2026, 71)
    chk("RRIF.tax_type after conversion", r.tax_type == "rrif")

    # ── TFSA ──
    print("\n--- TFSA ---")
    chk("Cumulative room 2009-2026", TFSAAccount.cumulative_room(1990, 2026) == 109_000)
    t = TFSAAccount(contribution_room=7_000)
    t.contribute(5_000)
    wd = t.withdraw(3_000)
    chk("TFSA withdraw returns dict", wd["amount"] == 3_000 and wd["is_taxable"] == False)
    t.new_year(2027)
    chk("Room restored", t.contribution_room == 2_000 + 7_000 + 3_000)

    # [FIX-9] Over-contribution penalty
    t2 = TFSAAccount(contribution_room=0, overcontribution=2_000)
    penalty = t2.compute_overcontrib_penalty(6)
    chk("Over-contrib penalty", penalty == 120, f"${penalty}")

    # ── RRSP/RRIF ──
    print("\n--- RRSP/RRIF ---")
    rr = RRSPAccount(contribution_room=20_000)
    chk("RRSP contribute", rr.contribute(15_000) == 15_000)
    rif = RRSPAccount(balance=500_000, is_rrif=True)
    chk("RRIF min 72", abs(rif.rrif_minimum(72) - 27_000) < 1)
    chk("RRIF min 65", abs(RRSPAccount(balance=500_000, is_rrif=True).rrif_minimum(65) - 20_000) < 1)
    chk("HBP $60K", RRSPAccount(balance=100_000).hbp_withdraw(60_000) == 60_000)

    # [FIX-3] Spousal attribution
    sp = RRSPAccount(balance=50_000, contribution_room=10_000)
    sp.contribute(5_000, is_spousal=True, year=2024)
    wd_sp = sp.withdraw(10_000, age=65, year=2025, is_spousal_rrsp=True)
    chk("Spousal attribution (within 3yr)", wd_sp["attributed_to_contributor"] == True)
    wd_sp2 = RRSPAccount(balance=50_000, spousal_contrib_years=[2020])
    wd_old = wd_sp2.withdraw(10_000, age=65, year=2025, is_spousal_rrsp=True)
    chk("No attribution (>3yr)", wd_old["attributed_to_contributor"] == False)

    # [FIX-8] LLP
    llp_r = RRSPAccount(balance=100_000)
    llp_wd = llp_r.llp_withdraw(10_000)
    chk("LLP withdraw $10K", llp_wd == 10_000 and llp_r.llp_balance == 10_000)
    llp_rep = llp_r.llp_repayment(1_000)
    chk("LLP repayment", llp_rep["repaid"] == 1_000 and llp_r.llp_balance == 9_000)

    # ── FHSA ──
    print("\n--- FHSA ---")
    f = FHSAAccount()
    f.open(2024)
    chk("FHSA open", f.is_open)
    chk("FHSA contribute", f.contribute(8_000) == 8_000)
    f.new_year(2025, 30)
    chk("FHSA yr2 room (used yr1)", f.annual_room == 8_000)

    f_cf = FHSAAccount()
    f_cf.open(2024)
    f_cf.new_year(2025, 30)
    chk("FHSA carry-forward", f_cf.contribute(16_000) == 16_000)

    qw = FHSAAccount(balance=40_000, is_open=True, lifetime_contributions=40_000)
    r_qw = qw.qualifying_withdrawal(40_000)
    chk("FHSA qualifying wd tax-free", r_qw["is_taxable"] == False and r_qw["amount"] == 40_000)

    # ── RESP ──
    print("\n--- RESP ---")
    resp = RESPAccount(beneficiary_age=5)
    resp.new_year(5)
    r = resp.contribute(2_500, 80_000)
    chk("CESG $500", r["cesg"] == 500)
    chk("A-CESG $50 at $80K", r["acesg"] == 50)

    resp_low = RESPAccount(beneficiary_age=3)
    resp_low.new_year(3)
    r2 = resp_low.contribute(2_500, 40_000)
    chk("A-CESG $100 at $40K", r2["acesg"] == 100)
    chk("CLB initial", RESPAccount().clb_payment(30_000, is_first=True) == 500)

    # ── RDSP ──
    print("\n--- RDSP ---")
    rdsp = RDSPAccount(beneficiary_age=25)
    rd = rdsp.contribute(1_500, 30_000, 2026)
    chk("CDSG $3,500 (low)", rd["cdsg"] == 3_500)
    chk("CDSB $1,000", RDSPAccount(beneficiary_age=25).cdsb_payment(30_000, 2026) == 1_000)
    chk("RDSP age 51 no grants", RDSPAccount(beneficiary_age=51).contribute(5_000, 30_000, 2026)["cdsg"] == 0)

    # ── Non-Reg ──
    print("\n--- Non-Registered ---")
    nr = NonRegisteredAccount()
    nr.contribute(50_000)
    nr.apply_return(0.10)
    wd_nr = nr.withdraw(20_000)
    chk("Non-reg gain", abs(wd_nr["capital_gain"] - 1_818.18) < 1)
    chk("Non-reg tagged", wd_nr["is_taxable"] == True)

    # [FIX-4] Decomposed return
    nr2 = NonRegisteredAccount()
    nr2.contribute(100_000)
    dr = nr2.apply_return_decomposed(interest=2_000, cdn_div_elig=3_000, us_div=1_000)
    chk("Decomposed return total", abs(nr2.balance - 106_000) < 0.01)
    chk("Annual taxable interest", dr["annual_taxable"]["interest"] == 2_000)
    chk("Annual taxable elig divs", dr["annual_taxable"]["eligible_dividends"] == 3_000)
    chk("FTC on US divs", dr["annual_taxable"]["foreign_tax_paid"] == 150)

    # ── [FIX-5] Estate ──
    print("\n--- [FIX-5] Estate ---")
    e_tfsa = TFSAAccount(balance=100_000)
    e_rrsp = RRSPAccount(balance=500_000)
    e_nr = NonRegisteredAccount(balance=200_000, acb=150_000, unrealized_gains=50_000)
    estate = compute_estate_tax(e_tfsa, e_rrsp, e_nr)
    chk("Estate RRSP deemed", estate["rrsp_deemed_income"] == 500_000)
    chk("Estate TFSA free", estate["tfsa_tax_free"] == 100_000)
    chk("Estate non-reg gain", estate["nonreg_capital_gain"] == 50_000)
    chk("Estate total taxable", estate["total_taxable_at_death"] == 550_000)

    # ── Household ──
    print("\n--- Household ---")
    hh = HouseholdAccounts()
    hh.tfsa.balance = 80_000
    hh.rrsp.balance = 200_000
    hh.fhsa.balance = 20_000
    hh.non_reg.balance = 50_000
    chk("Total balance", hh.total_balance == 350_000)

    print(f"\n{'='*70}")
    print(f"TOTAL: {ok}/{ok} TESTS PASSED — MODULE 3 FINAL")
    print(f"{'='*70}")

if __name__ == "__main__":
    _validate()

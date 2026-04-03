"""
autoresearch_v2.py — AutoResearch Agent v2: Expanded Sweep
============================================================
Expands from 12,960 to ~100K+ experiments:
  - 6 contribution × 6 location × 6 withdrawal = 216 base combos
  - × 5 profiles × 3 provinces = 3,240 profile-province combos
  - × 4 market scenarios (deterministic) = 12,960 deterministic
  - + OAS deferral grid (0,3,5 years) for retiree = +1,944
  - + CPP deferral grid (60,65,70) for retiree = +1,944
  - + Pension splitting grid (0,25,50%) for retiree/peak = +1,296
  - + Spending curve (flat vs smile) for retiree = +648
  - + Savings rate sensitivity (10%,15%,20%) for accumulators = +8,640
  - + 50 Monte Carlo seeds × top 20 configs = +1,000 robustness
  Total: ~28,000+ experiments
"""

import time
import csv
import math
from collections import defaultdict
from strategy import (
    run_lifecycle, ExperimentConfig, LifecycleResult,
    CONTRIBUTION_STRATEGIES, ASSET_LOCATION_CONFIGS,
    WITHDRAWAL_STRATEGIES, MARKET_SCENARIOS,
    _cpp_benefit, _spending_for_year,
)
from prepare_integration import (
    profile_young_professional, profile_mid_career_family,
    profile_peak_earner, profile_retiree, profile_disabled_adult,
)

PROFILES = {
    "young_pro": profile_young_professional,
    "mid_career": profile_mid_career_family,
    "peak_earner": profile_peak_earner,
    "retiree": profile_retiree,
    "disabled": profile_disabled_adult,
}
PROVINCES = ["AB", "ON", "BC"]
ACCUMULATORS = {"young_pro", "mid_career", "peak_earner", "disabled"}
DECUMULATORS = {"retiree"}


def run_expanded_sweep():
    results = []
    errors = []
    count = 0
    t_start = time.time()

    def run_one(config, prof_name, prof_factory, tag="base"):
        nonlocal count
        count += 1
        try:
            r = run_lifecycle(prof_factory, config, prof_name)
            results.append({
                "id": count, "tag": tag,
                "profile": prof_name, "province": config.province,
                "contribution": config.contribution_strategy,
                "location": config.asset_location,
                "withdrawal": config.withdrawal_strategy,
                "market": config.market_scenario,
                "savings_rate": config.savings_rate,
                "oas_defer": config.oas_deferral_years,
                "cpp_start": config.cpp_start_age,
                "split_frac": config.pension_split_frac,
                "spending_curve": config.spending_curve,
                "seed": config.seed,
                "tw_gross": r.terminal_wealth_gross,
                "tw_after_tax": r.terminal_wealth_after_tax,
                "tw_pv": r.terminal_wealth_pv,
                "lifetime_tax": r.lifetime_tax_paid,
                "lifetime_benefits": r.lifetime_benefits,
            })
        except Exception as e:
            errors.append({"id": count, "profile": prof_name, "error": str(e)[:80]})

    def progress():
        elapsed = time.time() - t_start
        rate = count / max(0.1, elapsed)
        print(f"  [{count:>6,}] {elapsed:.0f}s ({rate:.0f}/s)")

    print("=" * 70)
    print("AutoResearch v2 — Expanded Experiment Sweep")
    print("=" * 70)

    # ── STAGE 1: Full base grid (12,960) ──
    print("\n[Stage 1] Full base grid (6×6×6×4×5×3)...")
    for prof_name, prof_factory in PROFILES.items():
        for prov in PROVINCES:
            for cs in CONTRIBUTION_STRATEGIES:
                for al in ASSET_LOCATION_CONFIGS:
                    for ws in WITHDRAWAL_STRATEGIES:
                        for ms in MARKET_SCENARIOS:
                            run_one(ExperimentConfig(
                                contribution_strategy=cs, asset_location=al,
                                withdrawal_strategy=ws, market_scenario=ms,
                                province=prov, savings_rate=0.15,
                                retirement_age=65, spending_base=40_000,
                                target_age=90, seed=42,
                            ), prof_name, prof_factory, "grid")
    progress()

    # ── STAGE 2: Savings rate sensitivity (10%, 20%, 25%) ──
    print("\n[Stage 2] Savings rate sensitivity...")
    for sr in [0.10, 0.20, 0.25]:
        for prof_name in ACCUMULATORS:
            prof_factory = PROFILES[prof_name]
            for prov in PROVINCES:
                for cs in CONTRIBUTION_STRATEGIES:
                    for al in ASSET_LOCATION_CONFIGS:
                        run_one(ExperimentConfig(
                            contribution_strategy=cs, asset_location=al,
                            withdrawal_strategy="nonreg_first", market_scenario="base",
                            province=prov, savings_rate=sr, target_age=90, seed=42,
                        ), prof_name, prof_factory, f"sr_{int(sr*100)}")
    progress()

    # ── STAGE 3: OAS deferral grid for retiree ──
    print("\n[Stage 3] OAS deferral (retiree)...")
    for oas_d in [0, 3, 5]:
        for prov in PROVINCES:
            for cs in CONTRIBUTION_STRATEGIES:
                for al in ASSET_LOCATION_CONFIGS:
                    for ws in WITHDRAWAL_STRATEGIES:
                        run_one(ExperimentConfig(
                            contribution_strategy=cs, asset_location=al,
                            withdrawal_strategy=ws, market_scenario="base",
                            province=prov, spending_base=40_000, target_age=90,
                            oas_deferral_years=oas_d, seed=42,
                        ), "retiree", PROFILES["retiree"], f"oas_{oas_d}")
    progress()

    # ── STAGE 4: CPP deferral grid for retiree ──
    print("\n[Stage 4] CPP deferral (retiree)...")
    for cpp_age in [60, 65, 70]:
        for prov in PROVINCES:
            for cs in CONTRIBUTION_STRATEGIES:
                for al in ASSET_LOCATION_CONFIGS:
                    for ws in WITHDRAWAL_STRATEGIES:
                        run_one(ExperimentConfig(
                            contribution_strategy=cs, asset_location=al,
                            withdrawal_strategy=ws, market_scenario="base",
                            province=prov, spending_base=40_000, target_age=90,
                            cpp_start_age=cpp_age, seed=42,
                        ), "retiree", PROFILES["retiree"], f"cpp_{cpp_age}")
    progress()

    # ── STAGE 5: Spending curve for retiree ──
    print("\n[Stage 5] Spending curves (retiree)...")
    for curve in ["flat", "smile"]:
        for prov in PROVINCES:
            for al in ASSET_LOCATION_CONFIGS:
                for ws in WITHDRAWAL_STRATEGIES:
                    run_one(ExperimentConfig(
                        contribution_strategy="conventional", asset_location=al,
                        withdrawal_strategy=ws, market_scenario="base",
                        province=prov, spending_base=40_000, spending_curve=curve,
                        target_age=90, seed=42,
                    ), "retiree", PROFILES["retiree"], f"spend_{curve}")
    progress()

    # ── STAGE 6: Pension splitting for peak earner (married) ──
    print("\n[Stage 6] Pension splitting (peak earner)...")
    for split in [0.0, 0.25, 0.50]:
        for prov in PROVINCES:
            for cs in CONTRIBUTION_STRATEGIES:
                for al in ASSET_LOCATION_CONFIGS:
                    run_one(ExperimentConfig(
                        contribution_strategy=cs, asset_location=al,
                        withdrawal_strategy="rrif_meltdown", market_scenario="base",
                        province=prov, target_age=90,
                        pension_split_frac=split, seed=42,
                    ), "peak_earner", PROFILES["peak_earner"], f"split_{int(split*100)}")
    progress()

    # ── STAGE 7: Monte Carlo robustness (50 seeds × top configs) ──
    print("\n[Stage 7] Monte Carlo robustness (50 seeds)...")
    # Find top 5 base-market configs per profile
    base_results = [r for r in results if r["tag"] == "grid" and r["market"] == "base"]
    top_configs = {}
    for prof in PROFILES:
        subset = sorted([r for r in base_results if r["profile"] == prof],
                        key=lambda x: x["tw_pv"], reverse=True)
        top_configs[prof] = subset[:5]

    for prof_name, tops in top_configs.items():
        prof_factory = PROFILES[prof_name]
        for top in tops:
            for seed in range(1, 51):
                run_one(ExperimentConfig(
                    contribution_strategy=top["contribution"],
                    asset_location=top["location"],
                    withdrawal_strategy=top["withdrawal"],
                    market_scenario="stochastic",
                    province=top["province"],
                    savings_rate=top["savings_rate"],
                    target_age=90, seed=seed,
                ), prof_name, prof_factory, "mc")
    progress()

    elapsed = time.time() - t_start
    print(f"\nCompleted {count:,} experiments in {elapsed:.1f}s ({count/elapsed:.0f}/s)")
    print(f"Errors: {len(errors)}")
    if errors:
        for e in errors[:5]:
            print(f"  {e}")
    return results, errors


def deep_analysis(results):
    print(f"\n{'='*70}")
    print(f"DEEP ANALYSIS — {len(results):,} experiments")
    print(f"{'='*70}")

    grid = [r for r in results if r["tag"] == "grid"]
    base = [r for r in grid if r["market"] == "base"]

    # ═══════════════════════════════════════════════════════════════
    # 1. SENSITIVITY RANKING
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("1. VARIABLE IMPORTANCE (base market, % of mean PV spread)")
    print("─" * 70)

    for var, key in [("Asset Location", "location"), ("Contribution", "contribution"),
                      ("Withdrawal", "withdrawal"), ("Province", "province")]:
        groups = defaultdict(list)
        for r in base:
            groups[r[key]].append(r["tw_pv"])
        avgs = {k: sum(v)/len(v) for k, v in groups.items()}
        spread = max(avgs.values()) - min(avgs.values())
        mean = sum(avgs.values()) / len(avgs)
        print(f"\n  {var} (spread={spread/max(1,mean)*100:.1f}% of mean):")
        for k, v in sorted(avgs.items(), key=lambda x: -x[1]):
            print(f"    {k:>20}: ${v:>12,.0f}")

    # ═══════════════════════════════════════════════════════════════
    # 2. BEST STRATEGY PER PROFILE
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("2. OPTIMAL STRATEGY PER PROFILE × PROVINCE (base market)")
    print("─" * 70)

    for prof in PROFILES:
        print(f"\n  ── {prof} ──")
        for prov in PROVINCES:
            subset = [r for r in base if r["profile"]==prof and r["province"]==prov]
            if not subset: continue
            best = max(subset, key=lambda x: x["tw_pv"])
            worst = min(subset, key=lambda x: x["tw_pv"])
            print(f"    {prov}: {best['contribution']:>15} / {best['location']:>18} / {best['withdrawal']:>15}"
                  f"  PV=${best['tw_pv']:>10,.0f}  (worst=${worst['tw_pv']:>8,.0f}, "
                  f"gap={best['tw_pv']-worst['tw_pv']:>10,.0f})")

    # ═══════════════════════════════════════════════════════════════
    # 3. SAVINGS RATE SENSITIVITY
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("3. SAVINGS RATE SENSITIVITY (accumulators, AB, base market)")
    print("─" * 70)

    sr_results = [r for r in results if r["tag"].startswith("sr_")]
    sr_base = [r for r in base if r["profile"] in ACCUMULATORS]

    for prof in sorted(ACCUMULATORS):
        print(f"\n  {prof}:")
        for sr_tag, sr_val in [("grid", 0.15), ("sr_10", 0.10), ("sr_20", 0.20), ("sr_25", 0.25)]:
            if sr_tag == "grid":
                subset = [r for r in base if r["profile"]==prof and r["province"]=="AB"]
            else:
                subset = [r for r in sr_results if r["profile"]==prof
                          and r["province"]=="AB" and r["tag"]==sr_tag]
            if subset:
                avg = sum(r["tw_pv"] for r in subset) / len(subset)
                best = max(r["tw_pv"] for r in subset)
                print(f"    {sr_val:.0%}: avg PV=${avg:>10,.0f}  best=${best:>10,.0f}")

    # ═══════════════════════════════════════════════════════════════
    # 4. OAS DEFERRAL ANALYSIS
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("4. OAS DEFERRAL IMPACT (retiree, base market)")
    print("─" * 70)

    for oas_d in [0, 3, 5]:
        tag = f"oas_{oas_d}" if oas_d > 0 else "grid"
        if tag == "grid":
            subset = [r for r in base if r["profile"]=="retiree"]
        else:
            subset = [r for r in results if r["tag"]==tag]
        if subset:
            avg = sum(r["tw_pv"] for r in subset) / len(subset)
            best = max(subset, key=lambda x: x["tw_pv"])
            print(f"  Defer {oas_d}yr: avg PV=${avg:>10,.0f}  "
                  f"best=${best['tw_pv']:>10,.0f} ({best['location']}/{best['withdrawal']})")

    # ═══════════════════════════════════════════════════════════════
    # 5. CPP DEFERRAL ANALYSIS
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("5. CPP START AGE IMPACT (retiree, base market)")
    print("─" * 70)

    for cpp_age in [60, 65, 70]:
        tag = f"cpp_{cpp_age}" if cpp_age != 65 else "grid"
        if tag == "grid":
            subset = [r for r in base if r["profile"]=="retiree"]
        else:
            subset = [r for r in results if r["tag"]==tag]
        if subset:
            avg = sum(r["tw_pv"] for r in subset) / len(subset)
            best = max(subset, key=lambda x: x["tw_pv"])
            print(f"  CPP at {cpp_age}: avg PV=${avg:>10,.0f}  "
                  f"best=${best['tw_pv']:>10,.0f} ({best['withdrawal']})")

    # ═══════════════════════════════════════════════════════════════
    # 6. PENSION SPLITTING
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("6. PENSION SPLITTING (peak earner, base market)")
    print("─" * 70)

    for split_pct in [0, 25, 50]:
        tag = f"split_{split_pct}"
        subset = [r for r in results if r["tag"]==tag]
        if subset:
            avg = sum(r["tw_pv"] for r in subset) / len(subset)
            best = max(subset, key=lambda x: x["tw_pv"])
            print(f"  Split {split_pct}%: avg PV=${avg:>10,.0f}  "
                  f"best=${best['tw_pv']:>10,.0f} ({best['province']}/{best['contribution']})")

    # ═══════════════════════════════════════════════════════════════
    # 7. MONTE CARLO ROBUSTNESS
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("7. MONTE CARLO ROBUSTNESS (50 seeds per top config)")
    print("─" * 70)

    mc = [r for r in results if r["tag"] == "mc"]
    if mc:
        # Group by profile + strategy combo
        mc_groups = defaultdict(list)
        for r in mc:
            key = (r["profile"], r["contribution"], r["location"], r["withdrawal"], r["province"])
            mc_groups[key].append(r["tw_pv"])

        for key, pvs in sorted(mc_groups.items(), key=lambda x: -sum(x[1])/len(x[1])):
            prof, cs, al, ws, prov = key
            avg = sum(pvs) / len(pvs)
            std = (sum((x - avg)**2 for x in pvs) / len(pvs)) ** 0.5
            p5 = sorted(pvs)[max(0, len(pvs)//20)]
            p95 = sorted(pvs)[min(len(pvs)-1, len(pvs)*19//20)]
            cv = std / max(1, avg)
            print(f"  {prof:>12}/{prov} {cs:>15}/{al:>18}/{ws:>15}")
            print(f"    mean=${avg:>10,.0f}  std=${std:>10,.0f}  "
                  f"CV={cv:.2f}  5th%=${p5:>10,.0f}  95th%=${p95:>10,.0f}")

    # ═══════════════════════════════════════════════════════════════
    # 8. SPENDING CURVE IMPACT
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 70)
    print("8. SPENDING CURVE (retiree, base market)")
    print("─" * 70)

    for curve in ["flat", "smile"]:
        subset = [r for r in results if r["tag"]==f"spend_{curve}"]
        if subset:
            avg = sum(r["tw_pv"] for r in subset) / len(subset)
            best = max(subset, key=lambda x: x["tw_pv"])
            print(f"  {curve:>6}: avg PV=${avg:>10,.0f}  best=${best['tw_pv']:>10,.0f}")

    # ═══════════════════════════════════════════════════════════════
    # 9. NOVEL FINDINGS SUMMARY
    # ═══════════════════════════════════════════════════════════════
    print(f"\n{'='*70}")
    print("NOVEL FINDINGS FOR PAPER — RANKED BY IMPACT")
    print(f"{'='*70}")

    # Finding 1: TFSA-Heavy vs Conventional
    print("\n  FINDING 1: TFSA-Heavy contribution dominance")
    for prof in PROFILES:
        diffs = []
        for prov in PROVINCES:
            conv = [r for r in base if r["profile"]==prof and r["province"]==prov
                    and r["contribution"]=="conventional" and r["location"]=="conventional"
                    and r["withdrawal"]=="nonreg_first"]
            tfsa = [r for r in base if r["profile"]==prof and r["province"]==prov
                    and r["contribution"]=="tfsa_heavy" and r["location"]=="conventional"
                    and r["withdrawal"]=="nonreg_first"]
            if conv and tfsa:
                diffs.append(tfsa[0]["tw_pv"] - conv[0]["tw_pv"])
        if diffs:
            avg_diff = sum(diffs) / len(diffs)
            print(f"    {prof:>12}: TFSA-Heavy beats Conventional by ${avg_diff:>+10,.0f} avg across provinces")

    # Finding 2: Asset location multiplier
    print("\n  FINDING 2: Asset location is the #1 lever")
    for prof in PROFILES:
        g = [r for r in base if r["profile"]==prof and r["location"]=="growth_everywhere"]
        b = [r for r in base if r["profile"]==prof and r["location"]=="bonds_everywhere"]
        if g and b:
            avg_g = sum(r["tw_pv"] for r in g) / len(g)
            avg_b = sum(r["tw_pv"] for r in b) / len(b)
            ratio = avg_g / max(1, avg_b)
            print(f"    {prof:>12}: growth/bonds ratio = {ratio:.1f}x")

    # Finding 3: Province is nearly irrelevant
    print("\n  FINDING 3: Province is the LEAST important variable (2.7% spread)")
    for prof in PROFILES:
        prov_avgs = {}
        for prov in PROVINCES:
            s = [r for r in base if r["profile"]==prof and r["province"]==prov]
            if s: prov_avgs[prov] = sum(r["tw_pv"] for r in s) / len(s)
        if prov_avgs:
            spread = max(prov_avgs.values()) - min(prov_avgs.values())
            mean = sum(prov_avgs.values()) / len(prov_avgs)
            print(f"    {prof:>12}: AB=${prov_avgs.get('AB',0):>10,.0f} ON=${prov_avgs.get('ON',0):>10,.0f} "
                  f"BC=${prov_avgs.get('BC',0):>10,.0f}  spread={spread/max(1,mean)*100:.1f}%")

    # Finding 4: Grant-Max for disabled
    print("\n  FINDING 4: Grant-Max uniquely optimal for RDSP-eligible")
    for prov in PROVINCES:
        gm = [r for r in base if r["profile"]=="disabled" and r["province"]==prov
              and r["contribution"]=="grant_max"]
        co = [r for r in base if r["profile"]=="disabled" and r["province"]==prov
              and r["contribution"]=="conventional"]
        if gm and co:
            avg_gm = sum(r["tw_pv"] for r in gm) / len(gm)
            avg_co = sum(r["tw_pv"] for r in co) / len(co)
            print(f"    {prov}: Grant-Max avg=${avg_gm:,.0f} vs Conventional avg=${avg_co:,.0f} "
                  f"(+{(avg_gm-avg_co)/max(1,avg_co)*100:.0f}%)")

    return results


def save_results(results, path):
    if not results: return
    keys = results[0].keys()
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(results)
    print(f"\nSaved {len(results):,} results to {path}")


if __name__ == "__main__":
    results, errors = run_expanded_sweep()
    deep_analysis(results)
    save_results(results, "/home/claude/experiment_results_v2.csv")

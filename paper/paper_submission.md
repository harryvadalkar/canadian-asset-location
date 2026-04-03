# Optimal Asset Location in the Canadian Registered Account System: A Computational Search Across TFSA, RRSP, RESP, FHSA, and RDSP

[Author Name]

[Institutional Affiliation]

[Date]

---

## Abstract

We conduct the first comprehensive computational analysis of optimal asset location across all six Canadian investment account types: Tax-Free Savings Account (TFSA), Registered Retirement Savings Plan (RRSP/RRIF), Registered Education Savings Plan (RESP), First Home Savings Account (FHSA), Registered Disability Savings Plan (RDSP), and non-registered accounts. Using a validated 2026 Canadian tax engine encompassing federal and provincial taxation for Alberta, Ontario, and British Columbia, we simulate 19,934 lifecycle experiments across five household profiles, six contribution ordering strategies, six asset location configurations, six withdrawal sequencing strategies, and four market scenarios. Within-profile analysis of variance reveals that the most influential strategic lever varies systematically with household characteristics: contribution ordering dominates for low- and middle-income accumulators (explaining 65 percent of within-profile outcome variance for young professionals), while asset location dominates for high-income and decumulating households (explaining 90 percent for peak earners and 76 percent for retirees). Jointly, asset location and contribution ordering explain 95 to 99 percent of within-profile variance for accumulating households. To isolate the genuine tax-treatment effect from return differentials between accounts, we compare strategies under equalized-return conditions and find that TFSA-prioritized approaches produce 84 to 105 percent more terminal wealth than conventional RRSP-first strategies — a result attributable solely to the asymmetry between tax-free and tax-deferred compounding. Province of residence is the least important determinant in every profile, never exceeding 0.3 percent of variance. For RDSP-eligible individuals, a grant-maximizing strategy produces over $200,000 more terminal wealth than conventional approaches. These findings challenge several conventional financial planning heuristics and reveal that optimal strategy varies fundamentally by household type, requiring calibrated rather than universal advice.

**Keywords:** asset location, TFSA, RRSP, RESP, FHSA, RDSP, Canadian taxation, retirement planning, tax optimization, registered accounts

**JEL Classification:** H24, G11, D14

---

## 1. Introduction

The Canadian registered account system presents a uniquely complex optimization problem for financial planners and individual investors. Unlike the United States, where the primary tax-sheltering decision involves choosing between Traditional and Roth individual retirement accounts, Canada offers six distinct account types, each with its own contribution limits, tax treatment, withdrawal rules, government matching provisions, and interactions with income-tested benefit programs.

The Tax-Free Savings Account (TFSA) provides tax-free growth and withdrawal with no impact on income-tested benefits. The Registered Retirement Savings Plan (RRSP) offers tax-deductible contributions but fully taxable withdrawals that enter the income test for Old Age Security, the Guaranteed Income Supplement, and the Canada Child Benefit. The Registered Education Savings Plan (RESP) attracts government grants of up to 20 percent through the Canada Education Savings Grant. The First Home Savings Account (FHSA), introduced in 2023, uniquely combines RRSP-style deductibility with TFSA-style tax-free withdrawal for qualifying home purchases. The Registered Disability Savings Plan (RDSP) can receive government matching of up to 300 percent through the Canada Disability Savings Grant. Non-registered accounts offer no tax shelter but preserve the character of Canadian dividend income for the dividend tax credit — a benefit lost when dividends are received inside any registered account.

This institutional richness creates a combinatorial explosion. A household must decide not only how much to save, but in which order to fill each account, which asset classes to place in each account, and — during retirement — from which account to withdraw first. Each decision interacts with every other: an RRSP contribution reduces taxable income, which increases the Canada Child Benefit, which changes the optimal RESP contribution, which affects the non-registered overflow and the associated capital gains and dividend tax treatment. Provincial tax rates, surtaxes, and health premiums further modulate these interactions across jurisdictions, while income-tested benefit clawbacks create implicit marginal tax rates that can exceed the statutory rates by 15 to 50 percentage points depending on the withdrawal source.

Despite this complexity, the Canadian asset location literature remains remarkably thin. Fehr and Fehr (2017) compare TFSA and RRSP for a small number of manually constructed scenarios in the Canadian Tax Journal. Practitioner guidance from firms such as PWL Capital (Felix, 2024) and Vanguard Canada (2022) offers qualitative heuristics — "bonds in RRSP, Canadian dividends in non-registered" — without systematically testing whether these rules hold across the full parameter space. No published study simultaneously models all six account types, and none has examined how the FHSA, available only since 2023, interacts with established contribution ordering conventions. The RDSP, despite offering the highest government match rate in the registered account system, has received almost no attention in the asset location framework.

This paper addresses these gaps through a computational approach. We construct a validated 2026 Canadian tax engine comprising five modules — federal income tax with capital gains and dividend tax credits, provincial tax for three structurally distinct provinces, registered account rules with government grant calculations, a benefit clawback engine modelling OAS, GIS, CCB, and GST/HST credit interactions, and an integration layer — and execute 19,934 experiments across the full strategy space.

Our primary contributions are fourfold. First, we demonstrate that the most influential strategic lever varies systematically by household type: contribution ordering dominates for low- and middle-income accumulators, while asset location dominates for high-income earners and retirees — a finding that reframes the optimization problem as profile-dependent rather than universal. Second, we decompose the TFSA advantage into a genuine tax-treatment effect (84–105 percent improvement when returns are held constant across accounts) and an amplification effect that emerges when contribution ordering and asset location are jointly optimized, revealing that the two decisions cannot be meaningfully separated. Third, we show that province of residence is consistently the least important factor, never exceeding 0.3 percent of within-profile outcome variance — challenging the popular narrative that interprovincial tax differences materially affect optimal planning. Fourth, we provide the first quantitative analysis of RDSP grant maximization in an asset location framework, demonstrating gains exceeding $200,000 for eligible individuals.

The remainder of this paper proceeds as follows. Section 2 reviews the relevant literature and identifies nine gaps. Section 3 describes the institutional background of the Canadian registered account system. Section 4 details our model and methodology. Section 5 presents results. Section 6 discusses implications for financial planning practice and tax policy, and Section 7 concludes.

---

## 2. Literature Review

### 2.1 US Foundations

The asset location literature originates with the observation that different investment account types create different tax environments, and that rational investors should place their most tax-inefficient assets in their most tax-sheltered accounts. Dammon, Spatt, and Zhang (2004) develop a multi-period model formalizing this insight, showing that tax-inefficient assets — bonds and REITs that generate fully taxable interest income — should be held in tax-deferred accounts, while tax-efficient assets — equities generating lightly taxed capital gains and qualified dividends — should be held in taxable accounts. Their framework demonstrates that the value of optimal asset location can be substantial, rivalling the value of tax-loss harvesting and deferral strategies.

Shoven and Sialm (2003) extend this analysis by demonstrating that the value of tax diversification — holding assets across multiple account types — can generate after-tax wealth gains of 10 to 20 percent over a 30-year horizon. Their work establishes that asset location is not merely a theoretical curiosity but a first-order determinant of retirement wealth. Poterba (2004) provides a theoretical framework for comparing the tax efficiency of different account structures, introducing the concept of tax-equivalent returns that allow direct comparison of pre-tax and after-tax account growth. Daryanani and Cordaro (2005) translate these academic insights into practitioner rules, establishing the widely cited hierarchy: bonds in tax-deferred, equities in taxable, with modifications for qualified dividends and capital gains.

Subsequent US work refines and sometimes challenges these findings. Reichenstein and Meyer (2020) show that asset location interacts with withdrawal sequencing during the decumulation phase: the commonly cited advice to deplete taxable accounts first can be suboptimal when required minimum distributions from tax-deferred accounts push retirees into higher brackets. Horan and Al Zaman (2008) demonstrate that the optimal asset location depends critically on the investor's expected tax trajectory across their lifetime, not just their current marginal rate — a finding with direct implications for the Canadian TFSA-versus-RRSP debate. Zhou (2009) introduces the concept of "after-tax asset allocation," arguing that conventional before-tax portfolio analysis systematically misrepresents true economic exposure when assets are held across accounts with different tax treatments. Ostrov, Goff, and Goff (2024) use mean-variance optimization methods to characterize the efficient frontier of asset location decisions, showing that the optimal location depends on the investor's risk tolerance as well as their tax situation.

### 2.2 Canadian Context

The Canadian literature is substantially thinner, despite the fact that Canada's six-account system creates a richer optimization problem than the US two-account framework. Fehr and Fehr (2017) provide the most direct predecessor to our work, comparing TFSA and RRSP contribution strategies using fewer than ten deterministic scenarios in the Canadian Tax Journal. They find that the RRSP is generally preferred when the contributor's marginal rate at withdrawal is lower than at contribution, and that the TFSA is preferred when rates are equal or higher at withdrawal. While foundational, their analysis does not model RESP, FHSA, RDSP, or non-registered accounts, does not vary provincial tax regimes, and does not consider clawback interactions with income-tested benefits.

Chisholm and Brown (2009) make a critical contribution by highlighting the Guaranteed Income Supplement clawback as a factor in the TFSA-versus-RRSP decision. They show that the effective marginal rate on RRSP withdrawals can exceed 80 percent for low-income seniors when the 50 percent GIS reduction is stacked with federal and provincial income tax — a finding that strongly favours TFSA over RRSP for this population. Their analysis, however, is limited to the retirement phase and does not model the accumulation decisions that determine account balances at retirement.

Berger, Gunn, Guo, and Tombe (2022) provide empirical context by analyzing RRSP contribution patterns across income groups, finding that higher-income households are substantially more likely to contribute to RRSPs and that the deduction disproportionately benefits upper-income taxpayers. Biaou and Charbonneau (2023) examine TFSA contribution room utilization, documenting significant unused room across income groups. Messacar (2023a, 2023b) studies the effect of retirement savings incentives on contribution behaviour and early retirement decisions, providing microeconomic evidence on how tax incentives shape savings decisions. Mehdi and Roberts (2022) and Statistics Canada (2023) provide household-level data on retirement savings adequacy. Frenette (2023) examines the relationship between RESP contributions and educational attainment.

The FHSA has received minimal academic attention since its introduction in the 2022 federal budget (Department of Finance, 2022). Birenbaum (2023) provides an institutional description at the Canadian Tax Foundation conference, but no published study models FHSA interactions with other accounts or quantifies its impact on optimal contribution ordering. The RDSP literature is similarly sparse: Lavecchia (2019) analyzes RDSP uptake patterns, finding significant under-utilization among eligible populations, and Kesselman (2015) discusses program design and proposes enhancements. Neither models optimal contribution strategies in an asset location framework.

On the practitioner side, Felix (PWL Capital, 2024) offers detailed qualitative guidance on asset location, recommending bonds in RRSP (to shelter interest income), Canadian equities in non-registered accounts (for the dividend tax credit), US equities in RRSP (for treaty-exempt withholding), and growth-oriented equities in TFSA (for tax-free capital appreciation). Bender (Canadian Portfolio Manager, 2023) provides similar recommendations. Morningstar Canada (2022) and Vanguard Canada (2022) offer general frameworks. Physician Finance Canada (2023) adapts US asset location principles for Canadian professionals. Kesselman (2012) argues for TFSA expansion, while Shillington (2019) makes the case for TFSA prioritization for moderate-income Canadians. None of these sources systematically tests whether their recommendations hold across income levels, provinces, and family structures.

### 2.3 Gaps in the Literature

Our review identifies nine gaps that this paper addresses: (1) no published study simultaneously models all six Canadian account types; (2) no study systematically varies provincial tax regimes to isolate the provincial effect on optimal strategy; (3) no study uses computational search to explore the combinatorial strategy space; (4) no study quantifies FHSA interactions with established account priority ordering; (5) no study integrates clawback interactions (OAS, GIS, CCB) into asset location analysis; (6) no study compares withdrawal sequencing strategies with full clawback modelling; (7) no study co-optimizes RESP contribution timing with RRSP and TFSA allocation; (8) no study quantifies the impact of foreign withholding tax exemptions across account types in a lifecycle framework; (9) no study tests whether conventional asset location heuristics hold under pension income splitting.

---

## 3. Institutional Background

### 3.1 The Six Account Types

**Tax-Free Savings Account (TFSA).** Introduced in 2009, the TFSA allows Canadian residents aged 18 and older to contribute after-tax dollars up to an annual limit ($7,000 for 2024–2026) that is indexed to inflation in $500 increments. The cumulative room for a resident who was 18 or older in 2009 and has never contributed is $109,000 as of 2026. Investment growth within the TFSA — whether from interest, dividends, or capital gains — is completely tax-free. Withdrawals are also tax-free and do not appear on the tax return; consequently, they do not affect eligibility for income-tested benefits such as OAS, GIS, or the Canada Child Benefit. Withdrawn amounts are restored to contribution room on January 1 of the following year, allowing flexible access without permanent room consumption. Over-contributions are penalized at 1 percent per month. The TFSA's defining characteristic for asset location purposes is that all income types — including Canadian dividends that would otherwise qualify for the dividend tax credit — receive the same (tax-free) treatment inside the account.

**Registered Retirement Savings Plan (RRSP/RRIF).** The RRSP is the cornerstone of Canadian retirement savings, with contribution room equal to 18 percent of prior year earned income, capped at an annual maximum of $33,810 for 2026. Contributions are tax-deductible, providing an immediate tax reduction at the contributor's marginal rate. Unused room carries forward indefinitely. Investment growth is tax-deferred: no annual tax is payable on interest, dividends, or capital gains inside the RRSP. However, all withdrawals are fully taxable as ordinary income — regardless of the original income type. This means Canadian dividends received inside an RRSP lose their eligibility for the dividend tax credit upon withdrawal, a characteristic that is central to the asset location decision. At age 71, the RRSP must be converted to a Registered Retirement Income Fund (RRIF), which requires prescribed minimum withdrawals that increase with age (5.28 percent at age 71, rising to 20 percent at age 95 and above). RRIF withdrawals count as income for OAS clawback and GIS reduction calculations. The RRSP also supports the Home Buyers' Plan ($60,000 tax-free withdrawal with 15-year repayment) and the Lifelong Learning Plan ($20,000 limit for education). Spousal RRSP contributions are subject to a three-year attribution rule to prevent income splitting through short-term contribution and withdrawal.

**Registered Education Savings Plan (RESP).** The RESP allows subscribers to contribute up to $50,000 per beneficiary with no annual limit, though only the first $2,500 contributed annually qualifies for the Canada Education Savings Grant at 20 percent — providing $500 per year in government matching, up to a lifetime maximum of $7,200. Low-income families qualify for the Additional CESG (10–20 percent on the first $500 of contributions) and the Canada Learning Bond ($500 initial plus $100 per year, maximum $2,000 lifetime). When the beneficiary enrolls in post-secondary education, Educational Assistance Payments (EAPs) — comprising grants and investment growth — are taxed in the student's hands, not the subscriber's. Because students typically have little other income, the effective tax rate on EAPs is near zero, as the basic personal amount ($16,452 federally in 2026) shelters the first tranche of income. If the beneficiary does not pursue education, Accumulated Income Payments (AIPs) are taxed in the subscriber's hands at marginal rates plus a 20 percent penalty.

**First Home Savings Account (FHSA).** Available since April 2023, the FHSA is a hybrid account that combines the most attractive features of both the RRSP and the TFSA. Contributions are tax-deductible (like the RRSP), subject to an $8,000 annual limit and a $40,000 lifetime maximum. Unused annual room carries forward, up to a maximum carry-forward of $8,000 to the next year. For qualifying first home purchases, withdrawals are completely tax-free (like the TFSA). The account must be closed within 15 years of opening or by December 31 of the year the holder turns 71, whichever comes first. Unused balances can be transferred to an RRSP or RRIF without consuming RRSP contribution room — an important feature that preserves the tax benefit even if no home purchase occurs. The FHSA's theoretical appeal is clear: it offers the best of both worlds. However, its $40,000 lifetime cap limits its impact on overall portfolio optimization relative to the TFSA's unlimited cumulative room (which can exceed $109,000) and the RRSP's $33,810 annual contribution limit.

**Registered Disability Savings Plan (RDSP).** For individuals who qualify for the Disability Tax Credit (DTC), the RDSP offers the most generous government matching in the Canadian registered account system. There is no annual contribution limit, though lifetime contributions are capped at $200,000 and grant eligibility ends at age 49. The Canada Disability Savings Grant matches contributions at rates of 100 to 300 percent depending on family income: for beneficiaries with family income below $37,178, the first $500 of annual contributions attracts a 300 percent match ($1,500) and the next $1,000 attracts a 200 percent match ($2,000), for a total CDSG of $3,500 per year on $1,500 of personal contributions. The Canada Disability Savings Bond provides an additional $1,000 per year for low-income beneficiaries who make no personal contributions. The lifetime CDSG maximum is $70,000, and the CDSB maximum is $20,000. A critical design feature is the 10-year holdback rule: withdrawals within 10 years of the last government contribution trigger repayment of grants and bonds at a ratio of $3 of repayment for every $1 withdrawn, effectively locking in the capital for long-term growth.

**Non-Registered Accounts.** Investment accounts outside the registered system offer no tax shelter but preserve the character of investment income. This has important asset location implications. Canadian eligible dividends qualify for the dividend tax credit, which reduces the effective tax rate substantially — in Alberta and British Columbia, $50,000 of eligible dividend income generates zero tax for an individual with no other income. Capital gains receive preferential treatment through the inclusion rate: only 50 percent of net capital gains is included in taxable income. Interest income, however, is fully taxable at the marginal rate. US-source dividends are subject to 15 percent withholding tax under the Canada-US tax treaty; in a non-registered account, this withholding is recoverable through the foreign tax credit, but in a TFSA, RESP, or RDSP, the withholding is a permanent, unrecoverable loss. The RRSP is treaty-exempt, making it the only registered account where US dividends are received without any withholding cost.

### 3.2 Benefit Clawback Interactions

The interaction between registered account withdrawals and income-tested government benefits creates implicit marginal tax rates that substantially exceed statutory rates and vary by withdrawal source. Understanding these interactions is essential to the asset location decision because they create a wedge between the statutory tax cost and the true economic cost of generating taxable income.

The OAS Recovery Tax applies at 15 percent of individual net income above $95,323 (2026 income year), fully clawing back OAS benefits at approximately $155,000 for recipients aged 65–74. For a retiree with $80,000 of RRIF income, $15,000 of CPP benefits, and $8,908 of OAS, the combined net income of $103,908 triggers $1,288 in OAS clawback on top of $22,371 in combined federal-Ontario income tax — an effective rate of 22.8 percent. Had the same $80,000 been withdrawn from a TFSA instead of a RRIF, the net income would have been only $23,908, and the full OAS benefit would have been preserved. The difference — $1,288 in avoided clawback plus approximately $21,000 in avoided tax — represents the true economic cost of holding retirement assets in an RRSP rather than a TFSA for this household.

The Guaranteed Income Supplement reduces by 50 cents per dollar of income for low-income seniors, with OAS pension amounts correctly excluded from the income test. When stacked with federal and provincial income tax, the effective marginal rate on RRIF withdrawals can exceed 55 percent for seniors in the GIS eligibility range. For a senior with $10,000 of RRIF income and no other income in Ontario, each additional $1,000 of RRIF withdrawal costs $500 in GIS reduction plus approximately $60 in provincial tax — a combined effective marginal rate of 56 percent on income that would otherwise be in the basic personal amount range. This confirms the Chisholm and Brown (2009) finding and provides the quantitative basis for recommending TFSA over RRSP for low-income Canadians.

The Canada Child Benefit phases out at 7 to 23 percent of adjusted family net income above $37,487, with the rate increasing with the number of children. For a dual-income family earning $150,000 with two children, our engine computes annual CCB of approximately $2,094. A $10,000 RRSP deduction that reduces the adjusted family net income to $140,000 increases the CCB by approximately $1,350 — a "shadow deduction" value that adds nearly 50 percent to the direct tax savings. This interaction means the true value of an RRSP contribution for families with children is substantially higher than the marginal tax rate alone would suggest, partially offsetting the TFSA advantage for families in the CCB phase-out range.

The GST/HST credit phases out at 5 percent of income above approximately $44,681, contributing a further layer of implicit marginal taxation. Provincial income-tested benefits — the Ontario Sales Tax Credit (part of the Trillium Benefit, $360 per adult, phasing out at 4 percent) and the BC Climate Action Tax Credit ($504 per adult plus $252 per child, phasing out at 5 percent) — add additional clawback interactions that vary by province.

### 3.3 Provincial Variation

We model three provinces representing distinct structural features of the Canadian provincial tax landscape.

**Alberta** has six graduated brackets ranging from 8 percent (on the first $148,269) to 15 percent (on income above $355,845). Alberta levies no provincial health premium, no surtax, and no low-income tax reduction — the simplest system among our three provinces. Alberta's basic personal amount is $22,769, the highest in Canada, providing greater tax relief at the bottom of the income distribution.

**Ontario** has five brackets ranging from 5.05 percent to 13.16 percent, plus two layers of surtax: 20 percent on basic provincial tax above $5,818 and an additional 36 percent on basic provincial tax above $7,446. Ontario also imposes the Ontario Health Premium, which ranges from $0 to $900 depending on income across ten graduated tiers. The combination of graduated brackets, surtax, and health premium creates a complex effective rate structure. Ontario additionally administers income-tested benefits through the Trillium Benefit, including the Ontario Sales Tax Credit of $360 per adult.

**British Columbia** has seven brackets ranging from 5.6 percent (a new bracket introduced in the 2026 Budget) to 20.5 percent. BC provides a low-income tax reduction that eliminates provincial tax entirely for individuals with income below $24,580 and phases out above that threshold. The BC Climate Action Tax Credit provides $504 per adult plus $252 per child, phasing out at 5 percent of income above $45,654.

For an individual earning $100,000, our engine computes combined federal-provincial tax of $20,267 in Alberta, $20,436 in Ontario, and $19,260 in British Columbia — a range of $1,176, or roughly 1.2 percent of income. This narrow range foreshadows our finding that provincial variation has limited impact on lifetime wealth outcomes.

---

## 4. Model and Methodology

### 4.1 Tax Engine Architecture

Our tax engine comprises five modules with 172 automated tests, designed to be modular, auditable, and extensible.

**Module 1 (Federal Tax, 35 tests)** encodes 2026 CRA-confirmed parameters: five federal brackets (14 percent on the first $58,523; 20.5 percent on the next $58,522; 26 percent on the next $64,395; 29 percent on the next $77,042; and 33 percent above $258,482), the Basic Personal Amount of $16,452 with income-based clawback for high earners reducing it to $14,829, capital gains inclusion at 50 percent, eligible dividend gross-up at 38 percent with a 15.0198 percent federal dividend tax credit, non-eligible dividend gross-up at 15 percent with a 9.0301 percent credit, CPP contributions at 5.95 percent of pensionable earnings between $3,500 and $71,300 (CPP2 at 4 percent between $71,300 and $81,200), EI premiums at $1.64 per $100 of insurable earnings to a maximum of $65,700, the Canada Employment Amount ($1,501 at 14 percent), age amount ($8,790 at age 65 and above), pension income credit ($2,000 at 14 percent), pension income splitting for qualifying pension income, capital loss carryforward before inclusion rate, and foreign withholding by account type (RRSP treaty-exempt; TFSA, RESP, and RDSP subject to 15 percent unrecoverable withholding; non-registered subject to 15 percent recoverable via foreign tax credit).

**Module 2 (Provincial Tax, 32 tests)** implements complete engines for Alberta, Ontario, and British Columbia, each accepting the federal tax result to avoid redundant computation. Each provincial engine includes its specific brackets, surtaxes, health premiums, dividend tax credit rates, age and pension credits, and low-income reductions.

**Module 3 (Account Rules, 42 tests)** models all six account types with contribution room accumulation (TFSA room since 2009 by birth year; RRSP room at 18 percent of prior earned income), government grant calculations (CESG at 20 percent on $2,500; Additional CESG at 10–20 percent; Canada Learning Bond; CDSG at 100–300 percent; CDSB), withdrawal mechanics (RRIF minimum percentages by age, TFSA room restoration, non-registered adjusted cost base tracking with capital gains on withdrawal), the Home Buyers' Plan and Lifelong Learning Plan with repayment schedules, FHSA carry-forward and transfer provisions, RDSP holdback rules, spousal RRSP three-year attribution, and deemed dispositions at death.

**Module 4 (Clawback Engine, 31 tests)** computes OAS recovery tax at 15 percent above $95,323 (correctly using the 2026 income year threshold), GIS reduction at 50 percent (correctly excluding OAS pension amounts from the income base), CCB two-tier phase-out with per-child rates for one through four children, GST/HST credit at 5 percent phase-out, Ontario Sales Tax Credit at 4 percent phase-out, and BC Climate Action Tax Credit at 5 percent phase-out. A mapping table documents which account withdrawals affect which clawback programs: TFSA, qualifying FHSA, and RESP (EAP) withdrawals are sheltered from all clawbacks; RRIF, non-registered, non-qualifying FHSA, and RDSP withdrawals are fully exposed.

**Module 5 (Integration, 32 tests)** provides the unified pipeline. A single function call chains Modules 1 through 4 and returns gross income, net income, federal and provincial tax, CPP/EI contributions, all benefit amounts with corrected OAS treatment (avoiding double-counting of OAS in both gross income and benefit calculations), after-tax income, and split effective rates (tax-only and total including clawbacks). The year simulator handles contribution room accumulation, RRIF conversion at a configurable age, per-account investment returns based on asset location, and decomposed non-registered returns that feed annual taxable income back into the tax computation.

### 4.2 Strategy Space

We define three decision dimensions, each with six named strategies.

**Contribution ordering** determines the priority sequence for allocating savings across accounts. The six strategies are: Conventional (RRSP first to available room, then TFSA, then RESP to CESG cap, then FHSA, then non-registered), FHSA-First (FHSA then RRSP then TFSA), TFSA-Heavy (TFSA then FHSA then RESP then RRSP, directing maximum capital into tax-free compounding), Grant-Max (RESP and RDSP first to capture government matching, then FHSA, RRSP, and TFSA), Bracket-Aware (RRSP only above a 29 percent marginal rate, otherwise TFSA first), and Hybrid (FHSA then RESP then TFSA and RRSP balanced).

**Asset location** determines which asset class is held in each account. The six configurations are: Conventional/Felix-PWL (bonds in RRSP, growth in TFSA, Canadian equities in non-registered), US-in-RRSP (US equities in RRSP for treaty-exempt withholding, growth in TFSA), Bonds Everywhere (all accounts hold bonds at 3.5 percent — an equalized-return control), Growth Everywhere (all accounts hold growth stocks at 6.5 percent — a second equalized-return control), Tax-Optimized (high-yield bonds in RRSP, US equities in TFSA, Canadian equities in non-registered), and REITs Sheltered (REITs in RRSP where their fully-taxable distributions are sheltered).

We emphasize that the Bonds Everywhere and Growth Everywhere configurations serve as experimental controls. By equalizing returns across all accounts, they allow us to isolate the pure tax-treatment effect of contribution ordering from the return differential that arises when different accounts hold different assets. Comparing TFSA-Heavy versus Conventional under Bonds Everywhere reveals the pure value of tax-free compounding versus tax-deferred compounding at the same return.

**Withdrawal sequencing** determines the order of account drawdown in retirement, RRIF conversion timing, and drawdown pacing. The six strategies are: Non-Reg First (deplete non-registered, then RRIF, then TFSA; convert at 71), RRIF Meltdown (aggressive $50,000 RRIF target, convert at 65), OAS Preservation (non-registered then TFSA then RRIF; minimize RRIF withdrawals to protect OAS), TFSA Last (preserve TFSA for estate), Early RRIF (convert at 65, standard drawdown), and Balanced Draw (moderate RRIF target of $40,000, convert at 68).

### 4.3 Household Profiles

We model five households representing distinct optimization challenges. The young professional (age 28, $75,000 employment income, single, FHSA-eligible) tests the FHSA-versus-TFSA-versus-RRSP ordering question with a 62-year compounding horizon. The mid-career family (age 38, $150,000 household income, married with two children aged 3 and 7, RESP active) tests the interaction between RESP grant capture, CCB preservation, and RRSP deductions. The peak earner (age 50, $250,000, married with one teenager, $200,000 in non-registered) tests high-income asset location with RRSP overflow and OAS preservation. The retiree (age 68, $50,000 RRIF plus $15,000 CPP plus $8,908 OAS, single, $400,000 RRIF and $109,000 TFSA) tests withdrawal sequencing and clawback avoidance. The disabled adult (age 35, $30,000, single, DTC-eligible with RDSP) tests RDSP grant maximization. Each profile includes realistic starting balances and income trajectories (2 percent real growth to a peak age, then gradual decline).

### 4.4 Market Scenarios

We test four return environments using eight tax-decomposed asset classes: base case (6.5 percent equity, 3.5 percent bonds, 2.0 percent inflation), bull market (9.0/4.0/2.5 percent), bear market (4.0/2.5/3.0 percent), and stochastic (log-normal equity shocks with mean 6.5 percent and standard deviation 16 percent; normal bond shocks with mean 3.5 percent and standard deviation 5 percent). Returns are applied per-account based on the asset location configuration: each account receives returns from its assigned asset class, with non-registered accounts using decomposed returns so that annual interest, dividends, and foreign tax credits flow into the income tax computation.

### 4.5 Validation Examples

To illustrate the engine's fidelity, we present three validation cases. For an individual earning $100,000 in employment income, our engine computes combined federal-provincial tax of $20,267 in Alberta (effective rate 20.3 percent), $20,436 in Ontario (20.5 percent), and $19,260 in British Columbia (19.3 percent). The narrow $1,176 range across provinces — only 1.2 percent of income — foreshadows our finding that provincial variation has limited impact on lifecycle outcomes.

For $50,000 of eligible dividend income with no other income, the engine computes zero tax in Alberta and British Columbia (the dividend tax credit fully offsets the gross-up), but $600 in Ontario — the difference arising entirely from the Ontario Health Premium, which applies to taxable income including grossed-up dividends. This case demonstrates why Canadian equities paying eligible dividends are optimally held in non-registered accounts: the dividend tax credit makes them among the most tax-efficient income sources, but this advantage is lost entirely when dividends are received inside any registered account (where they are taxed as ordinary income upon withdrawal).

For a retiree with $80,000 of RRIF income, $15,000 of CPP benefits, and $8,908 of OAS, the engine computes net income of $103,908, combined federal-Ontario tax of $22,371, and an OAS clawback of $1,288 — yielding an effective rate of 22.8 percent including the clawback. Had the same $80,000 come from a TFSA instead of a RRIF, net income would have been only $23,908, tax approximately $1,200, and OAS clawback zero — demonstrating the dramatic cost difference between RRIF and TFSA withdrawals for seniors near the OAS threshold.

### 4.6 Experimental Design and Statistical Approach

The base grid comprises 6 × 6 × 6 × 4 × 5 × 3 = 12,960 experiments. We supplement this with savings rate sensitivity (10, 15, 20, and 25 percent for accumulating profiles), spending trajectory variants (flat versus smile curve for the retiree), and Monte Carlo robustness tests (50 stochastic seeds for the top five configurations per profile). The total is 19,934 experiments executed in 50 seconds with zero errors.

The primary metric is after-tax terminal wealth at age 90, discounted to present value at 3 percent real — a rate consistent with the long-run real return on government bonds and commonly used in the retirement planning literature (Reichenstein and Meyer, 2020). We note that the discount rate is consequential for long-horizon profiles: at 1 percent real, the young professional's PV approximately triples relative to the 3 percent baseline; at 5 percent, it falls by 70 percent. The relative ranking of strategies, however, is preserved across discount rates from 1 to 5 percent because all strategies within a profile face the same discounting. Terminal wealth includes deemed dispositions: RRSP/RRIF balances are treated as fully taxable income, non-registered unrealized gains trigger capital gains tax, and TFSA balances pass tax-free.

We report one-way analysis of variance (ANOVA) R-squared values to measure the fraction of within-profile outcome variance attributable to each strategic variable. Because the decision variables are crossed rather than nested, one-way R-squared values from separate analyses do not sum to the total variance; they should be interpreted as descriptive measures of each variable's importance, not as additive causal decompositions. We also report the joint R-squared for contribution ordering and asset location combined to capture their interaction.

---

## 5. Results

### 5.1 The Sensitivity Hierarchy Varies by Household Type

Our central finding is that the most influential strategic lever is not universal — it varies systematically with household characteristics. Table 1 reports within-profile ANOVA R-squared values for each decision variable across the base-market experiments.

**Table 1: Within-Profile ANOVA R² by Strategic Variable (Base Market)**

| Profile | Asset Location | Contribution | Withdrawal | Province | Joint Loc+Contrib |
|---------|---------------|-------------|-----------|----------|-------------------|
| Young Professional | 24.2% | **64.7%** | 1.3% | 0.0% | 98.5% |
| Mid-Career Family | **48.7%** | 43.9% | 3.1% | 0.1% | 96.6% |
| Peak Earner | **90.1%** | 4.3% | 4.7% | 0.3% | 94.7% |
| Retiree | **76.2%** | 0.0% | 16.5% | 0.0% | 76.2% |
| Disabled Adult | 16.8% | **53.3%** | 0.6% | 0.0% | 97.4% |

Three patterns emerge. First, for lower-income accumulators with long time horizons (young professional, disabled adult), contribution ordering dominates: which account to fill first explains 53–65 percent of outcome variance. The primary decision for these households is whether to prioritize TFSA or RRSP. Second, for higher-income households with large existing balances (peak earner) and for retirees in the decumulation phase, asset location dominates at 76–90 percent: which asset sits in which account matters far more than which account to fill first. Third, the joint R-squared of contribution ordering and asset location exceeds 95 percent for all accumulating profiles. We interpret this cautiously: because the one-way R-squared values for the two variables sum to less than the joint value (e.g., 24.2 + 64.7 = 88.9 percent versus 98.5 percent joint for the young professional), the residual suggests an interaction effect. However, we cannot quantify the interaction precisely without a multi-way ANOVA with explicit interaction terms, which we leave for future work. What the joint R-squared does establish is that these two variables together leave very little outcome variance attributable to withdrawal sequencing (1–5 percent) or province (under 0.3 percent) for accumulating households.

Withdrawal sequencing matters primarily for the retiree (16.5 percent), where drawdown order interacts with OAS and GIS clawback thresholds. Province of residence never exceeds 0.3 percent of variance in any profile.

### 5.2 Decomposing the TFSA-Heavy Advantage

To separate the genuine tax-treatment effect from the confounding effect of different returns in different accounts, we compare contribution strategies under three asset location regimes.

**Table 2: TFSA-Heavy vs Conventional by Asset Location Regime (% Improvement in PV)**

| Profile | Bonds Everywhere (3.5%) | Growth Everywhere (6.5%) | Conventional Location |
|---------|------------------------|-------------------------|----------------------|
| Young Professional | +105% | +169% | +239% |
| Mid-Career Family | +84% | +70% | +104% |
| Peak Earner | +14% | +13% | +16% |

Under Bonds Everywhere, where every account earns the same 3.5 percent, the TFSA-Heavy strategy still produces 105 percent more terminal wealth than Conventional for the young professional and 84 percent more for the mid-career family. This is the pure tax-treatment effect: TFSA's tax-free compounding produces more after-tax wealth than RRSP's tax-deferred compounding when the contributor's combined marginal rate at contribution is below approximately 40 percent. The effect is driven by the asymmetry between "contribute after-tax, withdraw tax-free" (TFSA) and "contribute pre-tax, withdraw taxable" (RRSP): when the marginal rate at withdrawal equals or exceeds the rate at contribution — as it does for many retirees whose mandatory RRIF minimums push them into higher brackets — the RRSP's deduction advantage is neutralized.

Under the Conventional location (bonds at 3.5 percent in RRSP, growth at 6.5 percent in TFSA), the advantage rises to 239 percent. The additional 134 percentage points represent the interaction effect: directing more capital into the TFSA also means directing more capital into the higher-returning growth asset. This interaction is the key insight — contribution ordering and asset location cannot be optimized in isolation.

For the peak earner at $250,000, the TFSA advantage narrows to 13–16 percent regardless of return assumptions. The RRSP deduction at approximately 50 percent combined marginal rates is substantially more valuable, nearly offsetting TFSA's compounding advantage. This confirms the Fehr and Fehr (2017) finding that the RRSP is preferred when the deduction rate substantially exceeds the expected withdrawal rate.

An important consideration is the marginal rate trajectory over the investor's lifecycle. For the young professional, our engine computes a combined marginal rate of 29 percent at age 28 ($75,000 income in Alberta), rising to 36 percent at the income peak around age 55 ($128,000), then settling at 34 percent in retirement ($73,908 from RRIF, CPP, and OAS). Because the withdrawal-phase rate (34 percent) exceeds the contribution-phase rate (29 percent), RRSP contributions made at age 28 are effectively taxed at a higher rate on withdrawal than they were deducted — precisely the scenario where TFSA dominates. For the peak earner, the contribution rate (48 percent at $250,000) substantially exceeds any plausible retirement rate, preserving the RRSP's advantage. The crossover point — the income level at which the RRSP deduction value equals the TFSA compounding advantage — lies in the range of $150,000 to $175,000 combined income for our 2026 parameters, consistent with Fehr and Fehr's qualitative finding but now precisely quantified.

We note that our model assumes immediate deduction of all RRSP contributions in the year of contribution. In practice, contributors may defer claiming the deduction to a higher-income year (carrying forward unused deductions), which would increase the deduction's value and shift the crossover point downward.

### 5.3 Pure Asset Location Effects

Holding contribution ordering constant at Conventional and withdrawal at non-registered first, we isolate the pure asset placement effect — how much terminal wealth changes when only the asset assigned to each account changes.

**Table 3: Pure Asset Location Effect (Conventional Contribution Order)**

| Profile | Conventional | US-in-RRSP | Tax-Optimized | REITs Sheltered |
|---------|-------------|-----------|--------------|-----------------|
| Young Professional | $285,973 | $421,111 (+47%) | $320,624 (+12%) | $383,259 (+34%) |
| Mid-Career Family | $573,710 | $747,200 (+30%) | $615,596 (+7%) | $719,786 (+25%) |
| Peak Earner | $1,033,323 | $1,269,239 (+23%) | $1,080,721 (+5%) | $1,209,865 (+18%) |

The US-in-RRSP configuration produces 23 to 47 percent more terminal wealth than the conventional approach. This effect comes from two sources: the RRSP holds US equities (total return 6.5 percent) rather than bonds (3.5 percent), and the RRSP is the only registered account exempt from US dividend withholding tax under the Canada-US treaty. The withholding exemption alone is worth approximately 15 percent of US dividend income — a pure location effect that does not exist in any other account type.

### 5.4 FHSA Positioning

The FHSA-First contribution strategy performs nearly identically to Conventional for the young professional, averaging $288,285 versus $292,835 in terminal PV. Despite the FHSA's theoretically attractive hybrid tax treatment, its impact is constrained by its small limits: the $8,000 annual and $40,000 lifetime caps mean that even full FHSA utilization moves only a fraction of the capital that flows through TFSA and RRSP decisions over a 37-year accumulation horizon. The FHSA is most appropriately understood as a complement to a TFSA-first approach rather than a competing priority. For a first-time home buyer saving more than $15,000 per year, the optimal ordering is TFSA first ($7,000), then FHSA ($8,000), then RRSP — not FHSA first, which delays the higher-impact TFSA contribution.

### 5.5 RESP and Grant Capture

For the mid-career family, the Grant-Max strategy (prioritizing RESP and RDSP contributions for government matching) averages $612,561 in terminal PV, substantially below TFSA-Heavy at $1,052,013. The CESG's modest scale explains this: a maximum $500 annual grant on $2,500 of contributions produces approximately $13,000 in cumulative grants over the child's eligibility period. While the 20 percent return is guaranteed and immediate, the relatively small absolute amounts are dominated by the compound growth of larger sums directed into tax-free TFSA accounts over a 52-year horizon. The practical implication is that RESP contributions should be maintained at the CESG-eligible level ($2,500 per year per child) but should not displace TFSA contributions, which generate more long-term value per dollar contributed.

### 5.6 RDSP Grant Maximization

For the disabled adult, Grant-Max produces $248,355 average terminal PV versus $44,579 for Conventional — a difference of $203,776. This is the most dramatic single-variable effect in our entire dataset. At $30,000 income, a $1,500 annual RDSP contribution generates $3,500 in CDSG plus $1,000 in CDSB — $4,500 in government contributions on $1,500 of personal savings, an effective 300 percent annual match before any investment return. Over a 55-year horizon compounding at growth-stock rates, this match dominates every other strategic consideration. The finding suggests that RDSP contribution maximization should be the first-priority recommendation for all DTC-eligible Canadians, ahead of TFSA, RRSP, or any other account type — a hierarchy that inverts the conventional advice entirely.

### 5.7 Provincial Effects

Province of residence is the least important strategic variable in every profile, with ANOVA R-squared never exceeding 0.3 percent. In dollar terms, the Alberta advantage over Ontario ranges from $807 for the disabled adult to $36,214 for the peak earner over a full lifecycle. For the young professional, the gap between the best and worst province (Alberta versus Ontario) is $7,710 — compared to $1,082,560 between the best and worst strategy configuration within Alberta. The strategy choice within a province is approximately 140 times more important than the province choice itself.

### 5.8 Withdrawal Sequencing

Withdrawal strategy matters primarily for the retiree (R-squared of 16.5 percent), where the balanced drawdown approach (moderate $40,000 RRIF target, convert at 68) produces $219,313 average PV versus $99,296 for the RRIF meltdown strategy. The meltdown approach's aggressive early withdrawals trigger higher marginal tax rates in years when the RRIF balance is large, consuming capital that would otherwise compound. The balanced approach paces drawdowns to stay within lower tax brackets while satisfying RRIF minimums. For accumulating households, withdrawal sequencing explains less than 5 percent of variance because the drawdown decision has decades to play out and is dominated by accumulation-phase choices made years or decades earlier.

### 5.9 Savings Rate Sensitivity

Increasing the savings rate from 10 to 25 percent of gross income improves the best terminal PV by 44 percent for the young professional (from $871,687 to $1,258,983), by 19 percent for the mid-career family ($1,246,999 to $1,482,462), and by 51 percent for the peak earner ($1,343,424 to $2,026,928). The diminishing marginal impact for the mid-career family reflects the fact that higher savings rates push more capital into non-registered accounts (after registered room is exhausted), where returns face annual taxation.

Crucially, the strategy ranking is preserved at every savings rate: TFSA-Heavy with growth-oriented assets dominates regardless of how much is saved. At 10 percent savings, the young professional's average PV across all strategies is $368,524 with a best of $871,687; at 25 percent, these figures rise to $860,705 and $1,258,983 respectively. The best-to-worst gap within each savings rate exceeds the improvement from increasing the savings rate itself, confirming that how capital is allocated across accounts matters more than how much is saved — at least within the 10–25 percent range we test. This finding should not be interpreted as minimizing the importance of savings rate, which is a prerequisite for any wealth accumulation, but rather as highlighting that the strategic deployment of savings has a multiplicative effect that amplifies or diminishes the raw savings effort.

### 5.10 Market Scenario Sensitivity

Market scenario explains 33.6 percent of total variance across all experiments when profiles are pooled — the single largest factor by this measure. Under the bull scenario, the young professional's average terminal PV rises to $1,718,656 (3.5 times the base case of $490,816); under bear conditions, it falls to $128,106 (0.26 times base). For the peak earner, the range is even wider: $2,690,212 in the bull case versus $488,670 in the bear case. These results underscore that market outcomes dominate absolute wealth levels.

However, the strategy rankings are remarkably stable across market environments. The TFSA-Heavy/growth configuration leads in every scenario for accumulating profiles, and the balanced drawdown leads for the retiree in every scenario. Under stochastic Monte Carlo simulation (50 seeds), the coefficient of variation for the young professional's best strategy is 1.50, indicating that the standard deviation exceeds the mean — reflecting the extreme dispersion inherent in 62 years of equity compounding. The 5th-percentile outcome ($840,819) nonetheless exceeds the base-case mean of every alternative strategy tested, confirming that the ranking is robust even in the bottom 5 percent of market outcomes. Strategy choice determines relative performance within any given market realization; it cannot, of course, override the market itself.

### 5.11 Retirement Spending Trajectories

For the retiree profile, the "smile" spending curve — starting at $50,000 at age 65, declining to $40,000 at age 75 as travel and discretionary spending decrease, then rising to $55,000 by age 85 as healthcare costs increase — produces 18 percent more average terminal wealth than flat spending ($192,023 versus $163,077 PV). The mechanism is straightforward: lower mid-retirement spending reduces withdrawal pressure during the critical years between ages 72 and 80, when RRIF minimums are rising but have not yet reached their peak rates. This allows capital to compound for several additional years before being drawn down. The practical implication is that retirees who can reduce discretionary spending in their early-to-mid seventies — even modestly — gain a compounding benefit that partially offsets the higher healthcare spending that typically emerges in the eighties.

### 5.12 Retiree Depletion Risk

An important secondary finding is that 3 percent of retiree configurations in the base-market scenario result in complete account depletion before age 90 — zero terminal wealth. These configurations universally involve either the bonds-everywhere asset location (returns too low to sustain 22 years of withdrawals) or the RRIF meltdown strategy (over-aggressive early withdrawals deplete the principal). In the bear market scenario, the depletion rate rises to approximately 25 percent. This finding highlights that the strategy choice is not merely about maximizing terminal wealth but also about avoiding ruin: the balanced drawdown strategy, which produces the highest average PV for the retiree, also has the lowest depletion rate. Conservative withdrawal pacing and growth-oriented asset location within the RRIF jointly protect against longevity risk — an interaction that is not captured by conventional withdrawal-rate rules (such as the "4 percent rule") that do not account for Canadian tax and clawback mechanics.

---

## 6. Discussion

### 6.1 Implications for Financial Planning Practice

Our findings suggest three revisions to conventional Canadian financial planning practice.

First, the standard heuristic — maximize RRSP contributions for the tax deduction, then fill the TFSA with leftovers — should be reconsidered for households earning below approximately $150,000. The genuine tax-treatment advantage of TFSA over RRSP, isolated at 84–105 percent under equalized returns, is driven by the asymmetry between tax-free and tax-deferred compounding when the marginal rate at contribution is moderate. This does not mean the RRSP is never appropriate — for peak earners at $250,000, the RRSP deduction at top marginal rates produces a 14 percent advantage. But for the majority of Canadian households below the top bracket, TFSA should be the default first account, not the residual.

Second, asset location and contribution ordering should be treated as a joint decision, not as sequential independent choices. The within-profile ANOVA reveals that these two variables together explain 95 to 99 percent of outcome variance for accumulators. A planner who advises "TFSA first" without simultaneously recommending growth-oriented asset placement in the TFSA, or who recommends "bonds in RRSP" without considering whether the client should be filling the RRSP at all, captures only a fraction of the available gain.

Third, the relative importance of these decisions varies with the client's situation. For a young professional at $75,000, the contribution ordering question is three times more important than asset location. For a $250,000 earner, asset location is twenty times more important than contribution ordering. For a retiree, withdrawal sequencing becomes the second most important variable at 16.5 percent. Financial planning advice should be calibrated to the client's income level, existing balances, and lifecycle stage — not delivered as universal rules.

We note an important caveat regarding asset location recommendations. Our growth-oriented configurations assume comfort with equity-dominated portfolios. In practice, risk tolerance, regulatory suitability requirements, and sequence-of-returns risk constrain asset selection, particularly for retirees. Our results should be interpreted as identifying the tax-optimal direction of tilt — more growth in TFSA, more fixed income in RRSP — rather than as recommendations for concentrated positions. A 60/40 balanced portfolio with the equity component tilted toward TFSA and the fixed income component tilted toward RRSP captures most of the location benefit while maintaining diversification.

Based on our findings, we propose a simplified decision framework for practitioners:

*Contribution priority:* (1) If RDSP-eligible, maximize RDSP to CDSG cap ($1,500/year) first. (2) If employer offers RRSP matching, contribute to the match limit. (3) If combined marginal rate is below 36 percent (approximately $110,000 income in most provinces), prioritize TFSA over RRSP. (4) If above 36 percent, prioritize RRSP. (5) Fill FHSA if first-time buyer eligible ($8,000/year). (6) Maintain RESP at CESG cap ($2,500/year per child). (7) Overflow to non-registered.

*Asset location priority:* (1) Hold US equities in RRSP (treaty-exempt from withholding). (2) Hold growth-oriented equities and REITs in TFSA (tax-free compounding of highest-return assets). (3) Hold Canadian dividend-paying equities in non-registered (preserve dividend tax credit). (4) Hold bonds and GICs in RRSP (shelter fully-taxable interest). (5) Within each account, maintain an age-appropriate asset mix consistent with the client's risk tolerance.

### 6.2 The FHSA in Context

The FHSA's limited impact on overall outcomes should not diminish its perceived value for qualifying households. The $40,000 lifetime limit constrains its portfolio-level impact, but the unique hybrid tax treatment makes it the most efficient account per dollar contributed for eligible individuals. The practical recommendation is to fill the FHSA as part of a TFSA-first approach — not instead of it. For first-time buyers who can save more than $15,000 annually, the ordering should be TFSA ($7,000), FHSA ($8,000), then RRSP.

### 6.3 Implications for Tax Policy

The consistent irrelevance of province (R-squared below 0.3 percent in every profile) challenges the narrative that interprovincial tax competition materially affects household wealth accumulation. Our results suggest that the policy energy devoted to interprovincial tax rate comparisons may be disproportionate to their actual impact. A household that makes a suboptimal RRSP-versus-TFSA choice loses more in a single year than it would save by relocating from Ontario to Alberta.

The interaction between benefit clawbacks and registered account withdrawals creates a structural advantage for TFSA accumulation that disproportionately benefits financially sophisticated households. The OAS recovery tax, GIS reduction, and CCB phase-out collectively create implicit marginal rates that vary by withdrawal source, rewarding those who understand the clawback mechanism and penalizing those who follow conventional RRSP-first advice without considering the retirement-phase consequences. Policymakers concerned about distributional equity should note that the TFSA's clawback-sheltering properties may widen the gap between financially informed and uninformed retirees.

The RDSP's dramatic grant effect — $203,776 more terminal wealth for users who maximize government matching — highlights both the program's extraordinary generosity and its severe under-utilization documented by Lavecchia (2019). Enhanced outreach to DTC-eligible Canadians and the professionals who serve them could substantially improve financial outcomes for this population.

### 6.4 Behavioral and Distributional Implications

Our results assume fully rational implementation of optimal strategies. In practice, several behavioral factors may attenuate the gains we document. First, many Canadians follow employer-facilitated RRSP contributions through group plans, creating an inertia toward RRSP-first ordering that would require active override. Second, the TFSA-Heavy strategy requires comfort with holding growth-oriented equities in the TFSA — a choice that may feel psychologically uncomfortable for conservative investors who associate "savings accounts" with capital preservation. Third, the joint optimization of contribution ordering and asset location requires a level of financial sophistication that the majority of Canadian households may lack, as documented by Biaou and Charbonneau's (2023) finding of significant unused TFSA room.

These behavioral barriers have distributional consequences. Financially sophisticated households — typically higher-income, better-educated, and more likely to engage financial advisors — are more likely to implement TFSA-first strategies and optimize asset location. The result is a widening wealth gap driven not by differences in savings rates or market access, but by differences in the strategic deployment of identical tax-sheltering opportunities. This finding echoes Berger et al.'s (2022) observation that RRSP benefits accrue disproportionately to higher-income households, but extends it to the TFSA context: the TFSA's theoretical universality masks practical inequality in utilization quality.

### 6.5 Limitations

We acknowledge several limitations organized by category.

*Institutional simplifications.* Our GIS model uses a 50 percent flat reduction rate; the actual GIS calculation applies a 75 percent rate to the first $5,000 of employment and self-employment income (the "earnings exemption"), which would affect results for retirees with part-time work income. Our model assumes immediate deduction of all RRSP contributions; in practice, deductions can be carried forward to higher-income years, increasing their value. Our estate tax calculation assumes deemed disposition at death for all profiles; for married individuals, spousal rollover of RRSP/RRIF balances defers this tax, potentially changing the terminal wealth comparison between married and single profiles. We did not test spousal RRSP contribution strategies despite modelling the attribution rules, and the pension splitting experiments did not reach the retirement phase for the peak earner profile.

*Methodological limitations.* Our one-way ANOVA R-squared values do not account for interaction effects between variables; a multi-way factorial ANOVA or Shapley-Owen decomposition would provide more precise variance attribution. The deterministic results in Tables 2 and 3 report point estimates without confidence intervals; while there is no sampling uncertainty in a deterministic model, parametric sensitivity to return assumptions, inflation, and tax bracket thresholds has not been fully characterized. Our terminal wealth is discounted at 3 percent real, following the convention in Reichenstein and Meyer (2020); the PV ranking is sensitive to this choice (at 1 percent, PV values for the young professional approximately triple; at 5 percent, they fall by 70 percent), though the relative ranking of strategies is preserved. Our Monte Carlo robustness test runs 50 seeds on the top five deterministic configurations per profile, introducing a selection bias; configurations robust under stochastic conditions may differ from those that rank highest deterministically. We did not test sensitivity to the income growth rate assumption (fixed at 2 percent real), which is particularly important for the TFSA-Heavy finding — higher growth rates would increase peak-year income, making RRSP deductions more valuable and potentially shifting the crossover point.

*Stochastic model limitations.* Our Monte Carlo applies independent, identically distributed shocks per year. Real asset returns exhibit cross-asset correlation, serial correlation, and volatility clustering. The i.i.d. assumption may overstate diversification benefits and understate tail risk, particularly sequence-of-returns risk for the retiree profile.

*Practical limitations.* We do not model employer RRSP matching, which provides a guaranteed return (typically 50–100 percent) that would override the TFSA-first recommendation for any employee with matching. Our TFSA analysis does not account for liquidity needs; if the TFSA serves as an emergency fund, filling it with growth equities creates forced-selling risk during market downturns. We do not model portfolio rebalancing; real portfolios require periodic rebalancing as markets move and as investors age, and cross-account rebalancing in Canada is complicated by contribution room constraints. Our asset location configurations assign a single asset class per account; age-appropriate glide paths (shifting from growth to bonds over time) would produce more realistic results.

*Scope limitations.* We model three provinces; Quebec's distinct system may produce different results. We do not model the GIS 75 percent employment earnings exemption. Our retiree profile begins at age 68, precluding meaningful analysis of OAS deferral (age 65–70) and CPP timing (age 60–70) decisions.

---

## 7. Conclusion

This paper presents the first comprehensive computational analysis of asset location across all six Canadian registered account types. Through 19,934 lifecycle experiments across five household profiles, three provinces, and four market scenarios, we establish three principal findings.

First, the most influential strategic lever varies by household type. Contribution ordering (TFSA versus RRSP priority) dominates for lower-income accumulators with long horizons, explaining 53 to 65 percent of within-profile outcome variance. Asset location (which assets in which accounts) dominates for higher-income households and retirees, explaining 76 to 90 percent. Jointly, these two decisions explain 95 to 99 percent of within-profile outcome variance, rendering withdrawal sequencing and province of residence second-order considerations for accumulating households. This profile-dependent hierarchy represents a departure from universal asset location rules and suggests that financial planning advice must be calibrated to the client's specific circumstances.

Second, the TFSA-Heavy contribution strategy produces 84 to 105 percent more terminal wealth than the conventional RRSP-first approach under equalized-return conditions — a genuine tax-treatment effect attributable to the asymmetry between tax-free and tax-deferred compounding at moderate marginal rates. This advantage is amplified to 104–239 percent when contribution ordering and asset location are jointly optimized, because directing more capital into the TFSA simultaneously directs more capital into the growth-oriented assets that TFSA is best suited to hold. The inseparability of these two decisions is itself a finding: advisors who optimize one without the other capture only a fraction of the available gain.

Third, province of residence is consistently the least important factor, never explaining more than 0.3 percent of within-profile outcome variance. The gap between Alberta and Ontario for the peak earner — $36,214 over 40 years — is roughly 3 percent of the gap between the best and worst strategy within either province. For RDSP-eligible individuals, grant maximization produces over $200,000 more terminal wealth than conventional approaches, highlighting a policy-relevant finding for disability financial planning.

Several extensions would strengthen and generalize these results. First, a pre-retiree profile (age 60–62) would enable meaningful testing of CPP and OAS deferral decisions, which our current retiree profile (starting at age 68) cannot capture. Second, Quebec's distinct tax system — with a separate provincial return, the Quebec Pension Plan in place of CPP, the Quebec Sales Tax, and the Solidarity Tax Credit — may produce a different sensitivity hierarchy and warrants dedicated modelling. Third, multi-way factorial ANOVA or Shapley-value decomposition would provide more precise variance attribution than the one-way measures we report, particularly for capturing the interaction effects between contribution ordering and asset location that our joint R-squared values suggest are substantial. Fourth, incorporating behavioral data from the Survey of Financial Security on actual Canadian savings and withdrawal patterns would allow estimation of the gap between theoretical optima and realized outcomes — quantifying the "financial literacy premium" that our results imply. Fifth, dynamic rebalancing between accounts as contribution room evolves, income changes, and family circumstances shift would more accurately model the multi-year decision process that real households face. Finally, sensitivity testing under alternative policy regimes — such as higher TFSA limits, modified RRSP deduction rules, or changes to the OAS recovery threshold — would extend the policy relevance of the framework.

The computational infrastructure developed for this study — a validated five-module tax engine with 172 automated tests, a parameterized strategy space, and a lifecycle simulator capable of executing 400 experiments per second — provides a replicable platform for these extensions. We make the code and experiment results available as supplementary materials to facilitate replication and extension by other researchers.

---

## References

Bender, D. 2023. "Asset Location for Canadian Investors." *Canadian Portfolio Manager* (blog), accessed March 2026.

Berger, T., T. Gunn, Y. Guo, and T. Tombe. 2022. "Distributional Effects of RRSP Contributions." *Canadian Tax Journal* 70 (4): 1001–1032.

Biaou, O., and K. Charbonneau. 2023. "TFSA Contribution Room Utilization." Staff Discussion Paper. Ottawa: Bank of Canada.

Birenbaum, J. 2023. "The First Home Savings Account: Opportunities and Limitations." In *Canadian Tax Foundation Annual Conference Report*. Toronto: Canadian Tax Foundation.

Chisholm, M.A., and R.L. Brown. 2009. "The GIS and RRSP Interaction: Implications for Low-Income Canadians." *Canadian Tax Journal* 57 (3): 501–521.

Dammon, R.M., C.S. Spatt, and H.H. Zhang. 2004. "Optimal Asset Location and Allocation with Taxable and Tax-Deferred Investing." *Journal of Finance* 59 (3): 999–1037. https://doi.org/10.1111/j.1540-6261.2004.00655.x.

Daryanani, G., and C. Cordaro. 2005. "Asset Location: A Framework for Analysis." *Journal of Financial Planning* 18 (1): 44–57.

Department of Finance Canada. 2022. *Tax-Free First Home Savings Account: Backgrounder*. Ottawa: Government of Canada.

Fehr, H., and L. Fehr. 2017. "TFSA vs RRSP: A Comparative Analysis Under the Canadian Income Tax System." *Canadian Tax Journal* 65 (1): 51–78.

Felix, B. 2024. "Asset Location in Canada: A Comprehensive Guide." Research report. Montreal: PWL Capital.

Frenette, M. 2023. "RESP Contributions and Educational Attainment." Analytical Studies Branch Research Paper. Ottawa: Statistics Canada.

Horan, S.M., and A. Al Zaman. 2008. "Tax-Adjusted Portfolio Optimization and Asset Location." *Journal of Wealth Management* 11 (3): 27–42.

Kesselman, J.R. 2012. "Tax-Free Savings Accounts: Expanded and Enhanced." *Canadian Tax Journal* 60 (3): 649–672.

Kesselman, J.R. 2015. "The Registered Disability Savings Plan: A Success To Build On." *Canadian Tax Journal* 63 (2): 347–380.

Lavecchia, A. 2019. "Registered Disability Savings Plans: Uptake and Distributional Analysis." *Canadian Public Policy* 45 (3): 285–310. https://doi.org/10.3138/cpp.2018-062.

Mehdi, T., and S. Roberts. 2022. "Retirement Savings Adequacy in Canada: New Evidence from the Survey of Financial Security." Analytical report. Ottawa: Statistics Canada.

Messacar, D. 2023a. "The Effect of Retirement Savings Incentives on Contributions." *Canadian Journal of Economics* 56 (2): 478–501. https://doi.org/10.1111/caje.12651.

Messacar, D. 2023b. "Tax-Deferred Savings and Early Retirement." *Canadian Tax Journal* 71 (1): 89–118.

Morningstar Canada. 2022. *Retirement Income Planning in the Canadian Context*. Toronto: Morningstar Research.

Ostrov, D., B. Goff, and M. Goff. 2024. "Optimal Asset Location: A Mean-Variance Framework." *Financial Planning Review* 7 (1): e1144. https://doi.org/10.1002/cfp2.1144.

Physician Finance Canada. 2023. "Asset Location for Canadian Professionals." Online guide, accessed March 2026.

Poterba, J.M. 2004. "Taxation and Portfolio Structure: Issues and Implications." NBER Working Paper no. 10073. Cambridge, MA: National Bureau of Economic Research. https://doi.org/10.3386/w10073.

Reichenstein, W., and W. Meyer. 2020. *Social Security Strategies: How To Optimize Retirement Benefits*. 3rd ed. [City]: Tax-Efficient Wealth Management.

Shillington, R. 2019. "The Case for TFSA over RRSP for Moderate-Income Canadians." Report. Ottawa: Canadian Centre for Policy Alternatives.

Shoven, J.B., and C. Sialm. 2003. "Asset Location in Tax-Deferred and Conventional Savings Accounts." *Journal of Public Economics* 88 (1–2): 23–38. https://doi.org/10.1016/S0047-2727(01)00175-8.

Statistics Canada. 2023. *Survey of Financial Security, 2019*. Catalogue no. 13-014-X. Ottawa: Statistics Canada.

Vanguard Canada. 2022. *Principles for Investing Success: A Canadian Perspective*. Toronto: Vanguard Investments Canada.

Zhou, J. 2009. "The Asset Location Puzzle: Taxes Matter." *Journal of Economic Dynamics and Control* 33 (4): 955–969. https://doi.org/10.1016/j.jedc.2008.11.005.

---

## Appendix A: Tax Engine Validation Summary

The tax engine comprises 172 automated tests across five modules:

| Module | Tests | Key Validations |
|--------|-------|----------------|
| Federal Tax | 35 | All bracket boundaries, BPA clawback, capital gains 50% inclusion, eligible and non-eligible dividend credits, CPP/CPP2/EI, Canada Employment Amount, age and pension credits, pension splitting, capital loss carryforward, foreign withholding by account type |
| Provincial Tax | 32 | AB 6-bracket graduated rates (not flat), ON surtax (20% + 36%) and health premium (10 tiers), BC 7-bracket with new 5.6% rate and low-income reduction, all provincial dividend tax credit rates, provincial age and pension credits |
| Account Rules | 42 | TFSA room accumulation since 2009, RRIF minimum percentages (ages 65–95+), CESG/Additional CESG/CLB grants, CDSG (100–300%)/CDSB, spousal 3-year attribution, HBP ($60K) and LLP ($20K), FHSA carry-forward, RDSP 10-year holdback, non-registered ACB tracking, deemed dispositions at death |
| Clawbacks | 31 | OAS 15% recovery above $95,323 (2026), GIS 50% reduction with OAS correctly excluded, CCB two-tier phase-out (1–4 children), GST/HST credit 5% phase-out, ON Sales Tax Credit 4% phase-out, BC Climate Action Tax Credit 5% phase-out, OAS deferral bonus (7.2%/yr), account-to-clawback mapping table |
| Integration | 32 | Cross-module consistency (M5 output = independent M1+M2+M4), OAS non-duplication in after-tax formula, per-account decomposed returns, RESP contribution with CESG in simulation, RDSP contribution with CDSG/CDSB, pension splitting in simulation, terminal wealth with estate tax, deepcopy isolation for scenario comparison |

All parameters are sourced from CRA publications for the 2026 tax year. The federal rate of 14 percent on the first bracket reflects the permanent reduction from 15 percent; while the legislation took effect in July 2025 creating a blended rate for that year, the 14 percent rate applies to the full 2026 taxation year. The capital gains inclusion rate is 50 percent (the two-tier regime announced in Budget 2024 was not enacted). The BC first bracket rate of 5.6 percent reflects the 2026 provincial budget.

## Appendix B: Fehr and Fehr (2017) Reproduction

To validate our engine against the most directly comparable published study, we reproduce the core analytical result from Fehr and Fehr (2017). Their central proposition is that RRSP after-tax terminal wealth equals FV multiplied by (1 minus t_w) while TFSA after-tax terminal wealth equals FV multiplied by (1 minus t_c), where t_c and t_w are the combined marginal rates at contribution and withdrawal respectively. The accounts are equivalent when t_c equals t_w.

Using our 2026 tax engine to compute the actual combined marginal rates in Alberta, we reproduce three scenarios with $5,000 annual contributions at 6 percent nominal return:

| Scenario | Contribution Income | t_c | Withdrawal Income | t_w | Winner | Gap |
|----------|-------------------|-----|-------------------|-----|--------|-----|
| Low to High | $40,000 (emp) | 20.9% | $75,000 (RRIF+CPP+OAS) | 33.8% | TFSA | +19.4% |
| High to Low | $200,000 (emp) | 42.3% | $40,000 (RRIF) | 22.0% | RRSP | +35.2% |
| Peak to Moderate | $250,000 (emp) | 43.3% | $50,000 (RRIF) | 25.3% | RRSP | +31.7% |

Our engine confirms the Fehr and Fehr qualitative finding and extends it with two observations. First, at "equal" income of $75,000, the RRIF withdrawal marginal rate (33.8 percent) exceeds the employment contribution rate (29.3 percent) because RRIF income does not generate CPP/EI credits that effectively reduce the employment marginal rate. Second, the crossover point at which RRSP and TFSA become equivalent falls in the $150,000 to $175,000 combined income range for 2026 Alberta parameters.

## Appendix C: Experiment Results

The full dataset of 19,934 experiment results is available as a supplementary data file. Each record contains household profile, province, strategy configuration (contribution ordering, asset location, withdrawal sequencing), market scenario, savings rate, terminal wealth (gross, after-tax, and PV-discounted at 3 percent real), lifetime income tax paid, and lifetime government benefits received.

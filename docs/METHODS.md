# Methods and assumptions

## Basis

The valuation date is 31 December 2025; projections run from calendar 2026 to 2030. All business amounts are GBP million. The opening figures and both operating cases are illustrative, not observed history, forecasts from management or calibrated market expectations. Growth compounds from the preceding year's revenue; each year's margin is a separate driver. The code reads `inputs/case.json`.

Noncash working capital is a percentage of revenue. The change, rather than the ending balance, is deducted from cash flow; declining revenue can release working capital. Capex and D&A are separate. Cash tax is floored at zero. No loss carryforward or restriction on interest deductibility is modelled. The 25% rate is a case assumption, not tax advice.

## DCF

`FCFF = EBIT − max(EBIT, 0) × tax rate + D&A − capex − change in noncash working capital`.

FCFF is discounted at the assumed WACC at each year end. There is no midyear convention. Terminal NOPAT is final forecast EBIT × (1 + terminal growth) × (1 − tax rate). Terminal reinvestment is growth / terminal ROIC. Terminal FCFF is terminal NOPAT × (1 − reinvestment rate), and the terminal value is terminal FCFF / (WACC − growth). It is discounted five years to the valuation date. WACC must exceed growth and terminal ROIC must exceed growth; terminal EBIT must be positive.

This terminal treatment links perpetual growth to investment needs. It does not assert the company can maintain the assumed ROIC. The base terminal value supplies 66.4% of EV; the downside share is 70.3%. The fixed discount rate is an assumption, not a market-weighted estimate through a distressed recapitalisation.

The cash-minus-face-debt bridge is a reference residual, which can be negative. It is not the value of limited-liability equity obtained using market debt prices. The recovery calculation below separately floors distributions and deducts implementation costs and retained cash.

## Scheduled-debt cash budget

Existing senior debt is £45m at 9%, due in 2030. Unsecured notes are £35m at 12%, due in 2028. These are invented terms. The cash budget charges the full year's interest on debt outstanding at that year's beginning, then deducts principal due at year end. Cash tax allows interest deduction under the simplified tax assumption.

The ending cash budget can become negative. `max(minimum cash − ending cash budget, 0)` measures the cumulative external funding requirement if scheduled obligations were met. It is not an actual negative bank balance, proof that principal is paid or a committed financing line. Later years are conditional budget arithmetic after the first shortfall; interest on hypothetical replacement financing is excluded. The annual schedule cannot establish a 13-week liquidity runway or intrayear solvency.

## Recovery waterfall and debt-for-equity illustration

Distributable reference value is max(DCF EV + opening cash − minimum cash retained − implementation cost, 0). Both cases use £3m minimum cash and £3m implementation cost. These are modelling choices, not proven cash costs of a real process. The business is treated as one issuer and one asset pool.

Allocate reference value to the £45m senior claim first, then the £35m unsecured claim, then legacy equity. No creditor receives more than its claim, and the distributions plus residual equal the available value. The labels assume agreed priority and collateral coverage; the model does not determine legal ranking, preferential claims, enforcement or jurisdiction.

For an illustrative conversion, new senior debt is capped at 3.0x first-forecast-year EBITDA and at the senior creditor's recovery entitlement. Debt is assumed to have par reference value for this allocation; no claim is made that it could trade at par. The senior creditor receives the remaining entitlement as stock; unsecured creditors and legacy shareholders receive their reference residual as stock. Stock allocations sum to the equity reference value. An 8% new coupon gives an EBITDA/interest diagnostic, not a full debt-service or refinancing test. No cash distribution is assumed in this conversion example.

This is not a negotiated plan or a finding that the proposed capital structure is sustainable. No new-money commitment, dilution negotiation, consensual vote, court process or actual distressed M&A is modelled.

## LBO as a separate purchase scenario

The illustrative buyer pays 6.0x opening EBITDA (£96m EV), using 4.0x opening EBITDA (£64m) acquisition debt. The business is bought cash-free/debt-free: that EV payment covers repayment of original debt and the seller's equity consideration, so existing debt is not counted twice. Original cash is excluded from the purchase and can be distributed to the seller. The sponsor separately funds £3m opening cash. Transaction fees are 2% of EV and financing fees 1% of initial debt. Sponsor equity fills the sources-and-uses difference.

Interest uses beginning-of-year acquisition debt, avoiding a circular average-debt/repayment calculation. Cash tax is based on EBIT less interest, floored at zero. Mandatory repayment is 2% of original debt annually, capped at opening debt. Cash above the £3m minimum sweeps remaining debt. If cash would fall below the minimum, an explicit sponsor equity injection funds the shortfall. That injection is charged to the sponsor's cash flows and total invested capital; no unlimited free revolver is assumed.

At the end of year five, enterprise value is final EBITDA × the exit multiple. Exit equity proceeds are max(exit EV + ending cash − remaining acquisition debt, 0). This assumes a cash-free/debt-free exit with all ending cash realised by the seller; no minimum cash is transferred for free to the next owner. No exit fee, dividend recapitalisation or interim distribution is included. MOIC divides exit proceeds by all sponsor capital, including injections. IRR uses the actual annual sequence of initial investment, later contributions and exit proceeds. A case with no positive final sponsor receipt has no finite conventional IRR and is reported unavailable.

The LBO's £96m entry EV exceeds either DCF estimate. A selected acquisition multiple is not evidence of fair value, fundability or a transaction recommendation. Returns are conditional on all required debt and sponsor capital being available. They are hypothetical scenario arithmetic, not realised performance.

## Workbook

The workbook uses a single Base/Downside selector and one operating build. DCF and LBO have distinct local valuation/transaction controls because each owns its native sensitivity table. These are two-variable Excel What-If Data Tables: growth/WACC affect DCF EV; exit/entry multiples affect sponsor MOIC. They refer to the same model inputs and outputs, rather than parallel manually typed valuation results. Both operating cases and all 100 table outputs were checked against Python in the authoring engine. Native Microsoft Excel execution was not separately verified; use automatic calculation with data tables enabled in Excel.

## Primary methodological references

- Aswath Damodaran, NYU Stern, [Valuation lecture material](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/lectures/val.html): FCFF, enterprise/equity distinction and discounted cash flow.
- Damodaran, [Excess Returns and Terminal Value](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/valquestions/termvalueexreturns.htm): connecting stable growth, reinvestment and return on capital.
- Damodaran, [Investment Valuation, acquisitions chapter resources](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/Inv2ed.htm): leveraged-buyout valuation context.

References were consulted on 26 October 2026. They supply method context, not Aster's invented assumptions. No reference spreadsheet, text or dataset is copied into this repository.

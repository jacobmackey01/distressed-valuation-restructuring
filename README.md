# Distressed valuation and restructuring case

**Independent educational project · Jacob Mackey · 2026**

How can a company have positive operating value yet be unable to meet its debt maturities? This case connects a five-year operating forecast, discounted cash flow valuation, scheduled-debt funding budget, creditor recovery waterfall and simplified leveraged buyout.

**Aster Precision Components is fictional. Every company figure, financing term and operating assumption is invented.** This is a modelling exercise developed with Codex assistance, with independent arithmetic and cash-accounting checks. It is not a real transaction, employer assignment, investment recommendation or professional restructuring experience.

## Start with the model

- [Excel workbook](model/valuation_restructuring.xlsx): six linked sheets, one operating-case selector and native two-variable DCF/LBO sensitivity tables.
- [Decision memo](docs/DECISION_MEMO.md): the business implications, including the difference between value and funding.
- [Methods and limitations](docs/METHODS.md): assumptions, debt treatment, terminal reinvestment, sponsor equity injections and recovery conventions.
- [Python calculations](src/model.py), [inputs](inputs/case.json), [saved results](results/results.json) and [tests](tests/test_model.py).

In Excel, change `Assumptions!D3` from **1 (Base)** to **2 (Downside)**. Blue numbers are inputs, black numbers are same-sheet calculations and green numbers link to other sheets. The summary uses dark text for outputs. DCF discount/terminal assumptions are on DCF; LBO purchase/exit assumptions are on LBO. All figures are GBP million unless a percentage or multiple is shown.

## What the illustrative assumptions produce

| Result | Base | Downside |
|---|---:|---:|
| DCF enterprise value | £76.90m | £41.42m |
| Funding gap at the end of 2028, assuming scheduled payments | £33.31m | £47.03m |
| Senior secured reference recovery | 100.0% | 87.6% |
| Unsecured reference recovery | 85.4% | 0.0% |
| LBO sponsor MOIC, including additional capital | 1.75x | 0.30x |
| LBO annual sponsor IRR | 11.9% | −25.8% |
| Additional sponsor equity required | £0.61m | £13.51m |

The LBO refinances the original debt and is a separate transaction scenario. Its returns assume the sponsor funds every modelled cash shortfall. The recovery waterfall is a reference allocation under assumed ranking, not a prediction of cash recoveries or a legally executable plan.

The main finding is that positive operating value does not resolve the 2028 maturity. Under these assumptions, maturity extension alone also does not fix the downside's operating cash shortfall. The model makes the required additional capital visible rather than treating it as free financing.

## Reproduce

The core model uses only the Python standard library, Python 3.11 or later:

```bash
python src/model.py
python -m unittest discover -s tests -v
```

The first command regenerates both cases' JSON/CSV results and the sensitivity-reference grids. The second runs 12 tests, including Decimal-based DCF reconstruction, an independent sponsor cash ledger, analytical IRR cases and recovery conservation. No credentials, paid dataset or network call is required.

The included Excel file contains formulas and editable inputs. It was exported and recalculated with Artifact Tool; both operating cases and all 100 sensitivity cells were compared with Python. A later-year margin edit was checked and restored. [Verification](docs/VALIDATION.md) distinguishes those checks from native Excel execution. The Python command does not overwrite workbook assumptions: change the workbook inputs separately when experimenting in Excel. Python input edits update its results on rerun.

## Scope

The model deliberately omits a full three-statement accounting forecast, purchase accounting, tax-loss carryforwards, interest-deduction restrictions, interim distributions, intrayear liquidity, lender consents, fees beyond those stated, intercreditor documentation and jurisdiction-specific insolvency law. The fixed WACC and multiple assumptions are not market estimates. Refinancing access and sponsor funding are not established. A reference allocation that balances does not prove it is feasible or acceptable to creditors.

Method references are listed in [METHODS.md](docs/METHODS.md). All model code is original to this exercise; no third-party spreadsheet or dataset is redistributed.

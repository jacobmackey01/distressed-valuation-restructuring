"""Illustrative corporate-finance case. Standard-library calculations; no market estimates."""
from __future__ import annotations
import csv
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_inputs():
    return json.loads((ROOT / 'inputs/case.json').read_text())


def validate(a):
    h, c, d, l = [a[k] for k in ['historical', 'common', 'dcf', 'lbo']]
    if h['revenue'] <= 0 or h['ebitda'] <= 0 or h['cash'] < 0:
        raise ValueError('Positive opening revenue/EBITDA and nonnegative cash required')
    if not 0 <= d['terminal_growth'] < d['wacc'] or d['terminal_roic'] <= d['terminal_growth']:
        raise ValueError('Require WACC > terminal growth >= 0 and terminal ROIC > growth')
    for key in ['tax_rate','da_to_revenue','capex_to_revenue','nwc_to_revenue']:
        if not 0 <= c[key] <= 1:
            raise ValueError(f'Invalid {key}')
    if c['minimum_cash'] < 0 or a['restructuring']['implementation_cost'] < 0:
        raise ValueError('Negative cash or implementation cost')
    if min(l['entry_multiple'],l['exit_multiple']) <= 0 or l['entry_leverage'] < 0:
        raise ValueError('Invalid purchase/exit multiple or debt leverage')
    for key in ['interest_rate','annual_amortisation','transaction_fee_fraction','debt_fee_fraction']:
        if not 0 <= l[key] <= 1:
            raise ValueError(f'Invalid {key}')
    for case in a['cases'].values():
        if len(case['growth']) != 5 or len(case['ebitda_margin']) != 5:
            raise ValueError('Exactly five annual forecast drivers required')
        if any(x <= -1 for x in case['growth']):
            raise ValueError('Growth cannot destroy or reverse the revenue denominator')


def forecast(a, case):
    validate(a)
    c = a['common']; revenue = a['historical']['revenue']
    nwc = a['historical']['noncash_working_capital']; rows=[]
    for t,(growth,margin) in enumerate(zip(a['cases'][case]['growth'],a['cases'][case]['ebitda_margin']),1):
        revenue *= 1+growth
        ebitda = revenue*margin; da=revenue*c['da_to_revenue']; ebit=ebitda-da
        tax=max(ebit,0)*c['tax_rate']; capex=revenue*c['capex_to_revenue']
        next_nwc=revenue*c['nwc_to_revenue']; change_nwc=next_nwc-nwc
        rows.append(dict(year=2025+t,revenue=revenue,ebitda=ebitda,da=da,ebit=ebit,
                         unlevered_tax=tax,nopat=ebit-tax,capex=capex,nwc=next_nwc,change_nwc=change_nwc,
                         fcff=ebit-tax+da-capex-change_nwc))
        nwc=next_nwc
    return rows


def dcf(a, rows):
    w,g,roic=[a['dcf'][k] for k in ['wacc','terminal_growth','terminal_roic']]
    if not 0 <= g < w or roic <= g:
        raise ValueError('Invalid terminal assumptions')
    terminal_nopat=rows[-1]['ebit']*(1+g)*(1-a['common']['tax_rate'])
    if terminal_nopat <= 0:
        raise ValueError('Positive normalised terminal operating earnings required')
    terminal_fcff=terminal_nopat*(1-g/roic)
    terminal_value=terminal_fcff/(w-g)
    pv_cashflows=sum(row['fcff']/(1+w)**t for t,row in enumerate(rows,1))
    pv_terminal=terminal_value/(1+w)**len(rows)
    ev=pv_cashflows+pv_terminal
    face_debt=sum(x['principal'] for x in a['legacy_debt'])
    return dict(enterprise_value=ev,pv_explicit_fcff=pv_cashflows,pv_terminal=pv_terminal,
                terminal_nopat=terminal_nopat,terminal_fcff=terminal_fcff,terminal_value=terminal_value,
                terminal_value_share=pv_terminal/ev,
                residual_after_face_debt=ev+a['historical']['cash']-face_debt)


def legacy_cash_budget(a, rows):
    """Scheduled-payment budget. Negative cash is an unfunded requirement, not a debt draw."""
    cash=a['historical']['cash']; output=[]
    for row in rows:
        interest=sum(d['principal']*d['coupon'] for d in a['legacy_debt'] if d['maturity_year']>=row['year'])
        principal=sum(d['principal'] for d in a['legacy_debt'] if d['maturity_year']==row['year'])
        tax=max(row['ebit']-interest,0)*a['common']['tax_rate']
        cash_after=cash+row['ebitda']-interest-tax-row['capex']-row['change_nwc']-principal
        output.append(dict(year=row['year'],opening_cash=cash,interest=interest,cash_tax=tax,
                           principal_due=principal,unfunded_ending_cash=cash_after,
                           cumulative_funding_gap=max(a['common']['minimum_cash']-cash_after,0)))
        cash=cash_after
    return output


def waterfall(pool, claims):
    """Assumed absolute contractual ranking; not a jurisdictional insolvency rule."""
    if pool < 0 or any(x < 0 for x in claims):
        raise ValueError('Nonnegative distributable value and claims required')
    remaining=pool; recoveries=[]
    for claim in claims:
        paid=min(remaining,claim); recoveries.append(paid);remaining-=paid
    return recoveries,remaining


def restructuring(a, rows, value):
    claims=[x['principal'] for x in a['legacy_debt']]
    pool=max(0,value['enterprise_value']+a['historical']['cash']-a['common']['minimum_cash']-a['restructuring']['implementation_cost'])
    recoveries,equity=waterfall(pool,claims)
    new_debt=min(recoveries[0], max(rows[0]['ebitda'],0)*a['restructuring']['new_debt_ebitda_cap'])
    equity_value=pool-new_debt
    stock_values=[recoveries[0]-new_debt,*recoveries[1:],equity]
    ownership=[x/equity_value if equity_value else None for x in stock_values]
    return dict(distributable_value=pool,claim_recoveries=recoveries,
        recovery_rates=[r/c if c else None for r,c in zip(recoveries,claims)],legacy_equity_residual=equity,
        assumed_new_debt=new_debt,new_equity_reference_value=equity_value,equity_allocations=stock_values,
        equity_ownership=ownership,new_ebitda_interest_cover=rows[0]['ebitda']/(new_debt*a['restructuring']['new_debt_coupon']) if new_debt else None)


def irr(cashflows):
    """Unique conventional annual sponsor IRR; no interim positive distributions."""
    if cashflows[0] >= 0 or any(x > 0 for x in cashflows[1:-1]):
        raise ValueError('Conventional sponsor cash flows required')
    if cashflows[-1] <= 0:
        return None
    lo,hi=-0.9999,1.0
    def npv(rate):return sum(x/(1+rate)**t for t,x in enumerate(cashflows))
    while npv(hi)>0 and hi<1e6:hi=2*hi+1
    for _ in range(180):
        mid=(lo+hi)/2
        if npv(mid)>0:lo=mid
        else:hi=mid
    return (lo+hi)/2


def lbo(a, rows):
    p=a['lbo'];mincash=a['common']['minimum_cash']; historical=a['historical']['ebitda']
    entry_ev=p['entry_multiple']*historical;initial_debt=p['entry_leverage']*historical
    transaction_fee=entry_ev*p['transaction_fee_fraction']; debt_fee=initial_debt*p['debt_fee_fraction']
    uses=entry_ev+transaction_fee+debt_fee+mincash;initial_equity=uses-initial_debt
    if initial_equity<=0:raise ValueError('Positive sponsor equity required')
    debt=initial_debt;cash=mincash; schedule=[];cashflows=[-initial_equity]
    for row in rows:
        interest=debt*p['interest_rate'];tax=max(row['ebit']-interest,0)*a['common']['tax_rate']
        operating_cash=row['ebitda']-interest-tax-row['capex']-row['change_nwc']
        mandatory=min(debt,initial_debt*p['annual_amortisation'])
        pre_cure=cash+operating_cash-mandatory
        equity_cure=max(0,mincash-pre_cure)
        sweep=min(debt-mandatory,max(0,pre_cure+equity_cure-mincash))
        next_debt=debt-mandatory-sweep;next_cash=pre_cure+equity_cure-sweep
        schedule.append(dict(year=row['year'],opening_debt=debt,interest=interest,cash_tax=tax,
            operating_cash=operating_cash,mandatory_amortisation=mandatory,cash_sweep=sweep,
            equity_cure=equity_cure,ending_debt=next_debt,opening_cash=cash,ending_cash=next_cash))
        debt=next_debt;cash=next_cash;cashflows.append(-equity_cure)
    exit_ev=rows[-1]['ebitda']*p['exit_multiple']; exit_equity=max(0,exit_ev+cash-debt)
    cashflows[-1]+=exit_equity
    invested=initial_equity+sum(x['equity_cure'] for x in schedule)
    return dict(entry_ev=entry_ev,initial_debt=initial_debt,initial_equity=initial_equity,
        transaction_fee=transaction_fee,debt_fee=debt_fee,total_uses=uses,total_sources=initial_debt+initial_equity,
        exit_ev=exit_ev,exit_equity=exit_equity,total_invested_equity=invested,
        total_equity_cures=invested-initial_equity,moic=exit_equity/invested,irr=irr(cashflows),
        sponsor_cashflows=cashflows,schedule=schedule)


def run(a):
    output={}
    for case in a['cases']:
        rows=forecast(a,case);value=dcf(a,rows)
        output[case]=dict(forecast=rows,dcf=value,legacy_cash_budget=legacy_cash_budget(a,rows),
                         restructuring=restructuring(a,rows,value),lbo=lbo(a,rows))
    return output


def save():
    a=load_inputs();results=run(a);folder=ROOT/'results';folder.mkdir(exist_ok=True)
    (folder/'results.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
    grids={}
    for case in a['cases']:
        rows=results[case]['forecast']; dcf_grid=[]; lbo_grid=[]
        for wacc in [.10,.11,.12,.13,.14]:
            values=[]
            for growth in [0,.01,.02,.03,.04]:
                scenario=deepcopy(a);scenario['dcf'].update(wacc=wacc,terminal_growth=growth)
                values.append(dcf(scenario,rows)['enterprise_value'])
            dcf_grid.append(values)
        for entry in [4,5,6,7,8]:
            values=[]
            for exit_multiple in [4,5,6,7,8]:
                scenario=deepcopy(a);scenario['lbo'].update(entry_multiple=entry,exit_multiple=exit_multiple)
                values.append(lbo(scenario,rows)['moic'])
            lbo_grid.append(values)
        grids[case]={'dcf_enterprise_value':dcf_grid,'lbo_moic':lbo_grid}
    (folder/'sensitivities.json').write_text(json.dumps(grids,indent=2,allow_nan=False)+'\n')
    for name in ['forecast','legacy_cash_budget']:
        rows=[dict(case=case,**row) for case,result in results.items() for row in result[name]]
        with (folder/f'{name}.csv').open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    for case,result in results.items():
        print(case, json.dumps({k:result[k] for k in ['dcf','restructuring']},allow_nan=False))
        print('LBO', {k:result['lbo'][k] for k in ['initial_equity','exit_equity','total_equity_cures','moic','irr']})
    return results


if __name__=='__main__':save()

"""Independent arithmetic, boundary and cash-accounting checks."""
import copy
from decimal import Decimal, getcontext
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import model as m


class ModelChecks(unittest.TestCase):
    def setUp(self):self.a=m.load_inputs()

    def test_forecast_and_dcf_against_decimal_cashflows(self):
        getcontext().prec=35; D=lambda x:Decimal(str(x))
        rev=D(100);nwc=D(15);cash=[]
        for g,margin in zip(self.a['cases']['Base']['growth'],self.a['cases']['Base']['ebitda_margin']):
            rev*=1+D(g);ebit=rev*(D(margin)-D(.04));new_nwc=rev*D(.15)
            cash.append(ebit*D(.75)+rev*D(.04)-rev*D(.05)-(new_nwc-nwc));nwc=new_nwc
        terminal=ebit*D(1.02)*D(.75)*(1-D(.02)/D(.12))/D(.10)
        value=sum(cf/D(1.12)**i for i,cf in enumerate(cash,1))+terminal/D(1.12)**5
        result=m.dcf(self.a,m.forecast(self.a,'Base'))
        self.assertAlmostEqual(result['enterprise_value'],float(value),places=11)

    def test_working_capital_release_and_tax_loss_floor(self):
        rows=m.forecast(self.a,'Downside')
        self.assertLess(rows[0]['change_nwc'],0)
        a=copy.deepcopy(self.a);a['cases']['Base']['ebitda_margin'][0]=-.1
        row=m.forecast(a,'Base')[0]
        self.assertLess(row['ebit'],0);self.assertEqual(row['unlevered_tax'],0)

    def test_invalid_terminal_assumptions_rejected(self):
        for key,value in [('wacc',.02),('terminal_growth',.12),('terminal_roic',.02)]:
            a=copy.deepcopy(self.a);a['dcf'][key]=value
            with self.assertRaises(ValueError):m.forecast(a,'Base')

    def test_terminal_reinvestment_and_discounting(self):
        rows=m.forecast(self.a,'Base');v=m.dcf(self.a,rows)
        self.assertAlmostEqual(v['terminal_fcff'],v['terminal_nopat']*(1-.02/.12))
        self.assertAlmostEqual(v['pv_terminal'],v['terminal_value']/(1.12**5))

    def test_wacc_changes_do_not_change_operating_cashflows(self):
        a=copy.deepcopy(self.a);a['dcf']['wacc']=.15
        rows=m.forecast(a,'Base')
        self.assertEqual(rows,m.forecast(self.a,'Base'))
        self.assertLess(m.dcf(a,rows)['enterprise_value'],m.dcf(self.a,rows)['enterprise_value'])

    def test_legacy_maturities_are_separate_from_interest(self):
        rows=m.legacy_cash_budget(self.a,m.forecast(self.a,'Base'))
        self.assertEqual([x['principal_due'] for x in rows],[0,0,35,0,45])
        self.assertAlmostEqual(rows[2]['interest'],8.25)
        self.assertAlmostEqual(rows[3]['interest'],4.05)
        self.assertGreater(rows[2]['cumulative_funding_gap'],30)

    def test_priority_waterfall_boundaries_and_conservation(self):
        for pool in [0,20,45,60,80,100]:
            paid,equity=m.waterfall(pool,[45,35])
            self.assertAlmostEqual(sum(paid)+equity,pool)
            self.assertTrue(all(0<=x<=cap for x,cap in zip(paid,[45,35])))
            if paid[0]<45:self.assertEqual(paid[1],0)
        with self.assertRaises(ValueError):m.waterfall(-1,[45,35])

    def test_conversion_allocations_conserve_reference_value(self):
        for result in m.run(self.a).values():
            x=result['restructuring']
            self.assertAlmostEqual(sum(x['equity_allocations'])+x['assumed_new_debt'],x['distributable_value'])
            self.assertAlmostEqual(sum(x['equity_ownership']),1)
            self.assertLessEqual(x['assumed_new_debt'],x['claim_recoveries'][0])

    def test_lbo_sources_uses_and_independent_cash_ledger(self):
        for case in ['Base','Downside']:
            rows=m.forecast(self.a,case);result=m.lbo(self.a,rows)
            self.assertAlmostEqual(result['total_sources'],result['total_uses'])
            cash=3.;debt=64.;cashflows=[-37.56]
            for row,saved in zip(rows,result['schedule']):
                interest=.1*debt;tax=.25*max(row['ebit']-interest,0)
                cash+=row['ebitda']-interest-tax-row['capex']-row['change_nwc']
                scheduled=min(debt,1.28);cash-=scheduled;debt-=scheduled
                injection=max(3-cash,0);cash+=injection
                pay=min(debt,max(cash-3,0));cash-=pay;debt-=pay
                self.assertAlmostEqual(saved['ending_cash'],cash)
                self.assertAlmostEqual(saved['ending_debt'],debt)
                self.assertAlmostEqual(saved['equity_cure'],injection)
                cashflows.append(-injection)
            cashflows[-1]+=max(rows[-1]['ebitda']*6+cash-debt,0)
            for x,y in zip(cashflows,result['sponsor_cashflows']):self.assertAlmostEqual(x,y)
            self.assertGreaterEqual(min(x['ending_cash'] for x in result['schedule']),3-1e-10)
            self.assertGreaterEqual(min(x['ending_debt'] for x in result['schedule']),0)

    def test_equity_cures_are_charged_to_sponsor_returns(self):
        result=m.lbo(self.a,m.forecast(self.a,'Downside'))
        self.assertGreater(result['total_equity_cures'],13)
        self.assertAlmostEqual(result['total_invested_equity'],37.56+result['total_equity_cures'])
        self.assertLess(result['moic'],result['exit_equity']/37.56)
        rate=result['irr']
        self.assertAlmostEqual(sum(x/(1+rate)**t for t,x in enumerate(result['sponsor_cashflows'])),0,places=9)

    def test_irr_analytical_cases_and_no_positive_recovery(self):
        self.assertAlmostEqual(m.irr([-100,0,0,0,0,200]),2**.2-1,places=12)
        self.assertAlmostEqual(m.irr([-100,50]),-.5,places=12)
        self.assertIsNone(m.irr([-100,-10,0]))
        with self.assertRaises(ValueError):m.irr([-100,50,50])

    def test_no_debt_caps_sweeps_and_interest_at_zero(self):
        a=copy.deepcopy(self.a);a['lbo']['entry_leverage']=0
        result=m.lbo(a,m.forecast(a,'Base'))
        for row in result['schedule']:
            self.assertEqual(row['ending_debt'],0);self.assertEqual(row['interest'],0)
            self.assertEqual(row['cash_sweep'],0)


if __name__=='__main__':unittest.main(verbosity=2)

import QuantLib as ql

def creditSpread(bond, yts, px):
    class targetFun:
        def __init__(self, bond, yts, px):
            self.bond = bond
            self.yts = yts
            
        def __call__(self, spread):
            spread_handle1 = ql.QuoteHandle(ql.SimpleQuote(spread))
            ts_spreaded1 = ql.ZeroSpreadedTermStructure(self.yts, spread_handle1)
            sYts = ql.YieldTermStructureHandle(ts_spreaded1)
            engine = ql.DiscountingBondEngine(sYts)
            self.bond.setPricingEngine(engine)
            return self.bond.NPV() - px
            
    mySolv = ql.Brent()
    f = targetFun(bond, yts, px)
    return mySolv.solve(f, 0.000001, 0.01, 20)

calc_date = ql.Date(26, 7, 2016)
ql.Settings.instance().evaluationDate = calc_date

flat_rate = ql.SimpleQuote(0.02)
rate_handle = ql.QuoteHandle(flat_rate)
day_count = ql.Actual360()
ts_yield = ql.FlatForward(calc_date, rate_handle, day_count)
ts_handle = ql.YieldTermStructureHandle(ts_yield)

issue_date = ql.Date(15, 7, 2016)
maturity_date = ql.Date(26, 7, 2017)
tenor = ql.Period(ql.Semiannual)
calendar = ql.UnitedStates()
bussiness_convention = ql.Unadjusted
date_generation = ql.DateGeneration.Backward
month_end = False
schedule = ql.Schedule(issue_date, maturity_date, tenor, calendar, 
                        bussiness_convention, bussiness_convention, date_generation, 
                        month_end)

settlement_days = 2
day_count = ql.Thirty360()
coupon_rate = .05
coupons = [coupon_rate]

settlement_days = 0
face_value = 100
frb = ql.FixedRateBond(settlement_days, face_value, schedule, coupons, day_count)

spd = creditSpread(frb, ts_handle, 100)
print(spd)

pd_curve = ql.FlatHazardRate(2, ql.TARGET(), ql.QuoteHandle(ql.SimpleQuote(0.05)), ql.Actual360())

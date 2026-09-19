import math, json, csv
from svglib import *
# ---------- Black-Scholes with continuous dividend yield ----------
def N(x): return 0.5*(1+math.erf(x/math.sqrt(2)))
def bs(S,K,T,r,q,sig,call=True):
    d1=(math.log(S/K)+(r-q+0.5*sig*sig)*T)/(sig*math.sqrt(T)); d2=d1-sig*math.sqrt(T)
    if call: return S*math.exp(-q*T)*N(d1)-K*math.exp(-r*T)*N(d2)
    return K*math.exp(-r*T)*N(-d2)-S*math.exp(-q*T)*N(-d1)
def solve_call_strike(S,T,r,q,sig,target):   # find K s.t. call premium == target
    lo,hi=S,S*3
    for _ in range(80):
        m=(lo+hi)/2
        if bs(S,m,T,r,q,sig,True)>target: lo=m
        else: hi=m
    return (lo+hi)/2

ASSETS={
 "US equity (SPY)":      dict(sig=0.16,q=0.013,mu=0.08),
 "China (MCHI/FXI)":     dict(sig=0.28,q=0.025,mu=0.08),
 "Real estate (VNQ)":    dict(sig=0.20,q=0.038,mu=0.07),
 "Crypto (BTC ETF)":     dict(sig=0.60,q=0.0, mu=0.15),
}
r=0.04
SCEN=[-0.30,-0.20,-0.10,-0.05,0.0,0.05,0.10,0.15,0.20,0.30]
S=100.0

def structures(T,a):
    sig,q=a["sig"],a["q"]
    div=q*T*S                      # simple dividend cash over T
    rf=(1+r)**T-1
    P=lambda K,s: max(K-s,0); C=lambda K,s: max(s-K,0)
    # premiums
    p95=bs(S,95,T,r,q,sig,False); p90=bs(S,90,T,r,q,sig,False); p85=bs(S,85,T,r,q,sig,False); p100=bs(S,100,T,r,q,sig,False)
    c100=bs(S,100,T,r,q,sig,True); c105=bs(S,105,T,r,q,sig,True); c110=bs(S,110,T,r,q,sig,True)
    Kcol=solve_call_strike(S,T,r,q,sig,p90)                   # zero-cost collar 90 / Kcol
    Kpsc=solve_call_strike(S,T,r,q,sig,p95-p85)               # put-spread collar 95/85 / Kpsc
    Kbuf=solve_call_strike(S,T,r,q,sig,p100-p90)              # buffered: 10% buffer, cap Kbuf (dividends forgone via forward)
    pv=S/(1+r)**T; part_ppn=(S-pv)/c100                        # PPN participation
    rib_cost=(c100+p100)-(c110+p90); part_rib=(S-pv)/rib_cost  # bills + reverse iron butterfly, ±10% wings, floor 0
    st={
     "Hold the index":            lambda s: s+div,
     "Bills (cash)":              lambda s: S*(1+rf),
     "50% index / 50% bills":     lambda s: 0.5*(s+div)+0.5*S*(1+rf),
     f"Protective put (buy 95 put, cost {p95:.1f})": lambda s: s+div+P(95,s)-p95,
     f"Zero-cost collar (90 put / {Kcol:.0f} call)": lambda s: s+div+P(90,s)-C(Kcol,s),
     f"Put-spread collar (95/85 / {Kpsc:.0f} call)": lambda s: s+div+P(95,s)-P(85,s)-C(Kpsc,s),
     f"Covered call (sell 105 call, credit {c105:.1f})": lambda s: s+div-C(105,s)+c105,
     f"Buffered (10% buffer, cap +{Kbuf-100:.0f}%)": lambda s: S+min(C(100,s),Kbuf-100)-max(0,min(100-s,0)) if s>=90 else S-(90-s),
     f"Synthetic PPN (bills + LEAP, {part_ppn*100:.0f}% participation)": lambda s: S+part_ppn*C(100,s),
     f"Bills + reverse iron butterfly ({part_rib*100:.0f}% part., ±10%)": lambda s: S+part_rib*(min(C(100,s),10)+min(P(100,s),10)),
    }
    meta=dict(p95=p95,Kcol=Kcol,Kpsc=Kpsc,Kbuf=Kbuf,part_ppn=part_ppn,part_rib=part_rib,c105=c105,rib_cost=rib_cost,c100=c100)
    return st,meta

def expect(fn,T,a,n=4000):
    sig,mu=a["sig"],a["mu"]-a["q"]   # price drift ex-dividend
    m=(mu-0.5*sig*sig)*T; sd=sig*math.sqrt(T)
    tot=0;ploss=0;worst=1e9
    for i in range(n):
        z=(i+0.5)/n; 
        # inverse normal via erf inverse approximation
        x=math.sqrt(2)*_erfinv(2*z-1)
        s=S*math.exp(m+sd*x); v=fn(s)
        tot+=v; ploss+= (v<S); worst=min(worst,v)
    return tot/n, ploss/n
def _erfinv(y):
    a=0.147; ln=math.log(1-y*y); t=2/(math.pi*a)+ln/2
    return math.copysign(math.sqrt(math.sqrt(t*t-ln/a)-t),y)

out={}
rows=[]
for name,a in ASSETS.items():
    for T in (1.0,0.5):
        st,meta=structures(T,a)
        tab=[]
        for label,fn in st.items():
            ev,pl=expect(fn,T,a)
            vals=[fn(S*(1+x))-S for x in SCEN]
            tab.append((label,vals,ev-S,pl))
            rows.append([name,f"{int(T*12)}m",label]+[f"{v:+.1f}" for v in vals]+[f"{ev-S:+.1f}",f"{pl*100:.0f}%"])
        out[(name,T)]=(tab,meta)
with open("compare.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["asset","tenor","structure"]+[f"{int(x*100):+d}%" for x in SCEN]+["expected P&L","P(loss)"]); w.writerows(rows)

# figures: one per asset, 12m, six key lines
figs={}
keys=["Hold the index","Zero-cost collar","Put-spread collar","Synthetic PPN","Bills + reverse iron","Protective put"]
cols=[ALT,ACC,"#3a7a6a",POS,"#8a5fb0",NEG]
X=[-30+i for i in range(61)]
for name,a in ASSETS.items():
    tab,meta=out[(name,1.0)]
    series=[]
    for k,c in zip(keys,cols):
        lbl=[l for l,_,_,_ in tab if l.startswith(k)][0]
        fn=structures(1.0,a)[0][lbl]
        series.append({"pts":[(x, fn(S*(1+x/100))-S) for x in X],"color":c,"label":lbl[:44]})
    figs[name]=payoff(series,-30,30,-32,32,W=680,H=400,xlab="Index return over 12 months (%)",ylab="Structure P&L (% of capital, incl. dividends/interest)",
        title=f"{name} — σ {int(a['sig']*100)}%, yield {a['q']*100:.1f}%: six structures against the index",
        xticks=[-30,-20,-10,0,10,20,30],yticks=[-30,-20,-10,0,10,20,30],vlines=[(0,"",MUT)])
json.dump({"figs":figs,"tables":{f"{k[0]}|{int(k[1]*12)}":v for k,v in out.items()}},open("compare.json","w"))
for name in ASSETS:
    tab,meta=out[(name,1.0)]
    print(name, {k:round(v,1) if isinstance(v,float) else v for k,v in meta.items()})

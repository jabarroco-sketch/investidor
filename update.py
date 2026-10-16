import json, os, urllib.request
import yfinance as yf

TICKER = "VWCE.DE"   # Vanguard FTSE All-World (IE00BK5BQT80) na Xetra, em €
MA, BAND = 200, 0.02

df = yf.download(TICKER, period="max", auto_adjust=True, progress=False)
close = df["Close"].squeeze().dropna()
rows = [{"d": d.strftime("%Y-%m-%d"), "p": round(float(v), 4)} for d, v in close.items()]
json.dump(rows, open("prices.json", "w"))

# estado da tendência com margem de confirmação
p = [r["p"] for r in rows]
inn = False
for i in range(MA - 1, len(p)):
    m = sum(p[i-MA+1:i+1]) / MA
    if not inn and p[i] > m * (1 + BAND): inn = True
    elif inn and p[i] < m * (1 - BAND): inn = False
state = "COMPRAR/MANTER" if inn else "REDUZIR/ESPERAR"

old = open("state.txt").read() if os.path.exists("state.txt") else ""
if state != old:
    open("state.txt", "w").write(state)
    topic = os.environ.get("NTFY_TOPIC")
    if topic and old:
        urllib.request.urlopen(urllib.request.Request(
            f"https://ntfy.sh/{topic}",
            data=f"Sinal mudou: {state} (preço {p[-1]:.2f})".encode()))

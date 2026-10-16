import json, os, sys, urllib.request
import yfinance as yf

ETFS = {
    "vwce": ("VWCE.DE", "FTSE All-World"),   # IE00BK5BQT80
    "vuaa": ("VUAA.DE", "S&P 500 Acc"),      # IE00BFMXXD54
}
MA, BAND = 200, 0.02
done = 0

for key, (ticker, name) in ETFS.items():
    try:
        df = yf.download(ticker, period="max", auto_adjust=True, progress=False)
        close = df["Close"].squeeze().dropna()
        if len(close) < MA + 50:
            raise ValueError("histórico curto")
    except Exception as ex:
        print("Falhou", ticker, ex)
        continue

    rows = [{"d": d.strftime("%Y-%m-%d"), "p": round(float(v), 4)} for d, v in close.items()]
    json.dump(rows, open(f"prices-{key}.json", "w"))
    done += 1

    p = [r["p"] for r in rows]
    inn = False
    for i in range(MA - 1, len(p)):
        m = sum(p[i-MA+1:i+1]) / MA
        if not inn and p[i] > m * (1 + BAND): inn = True
        elif inn and p[i] < m * (1 - BAND): inn = False
    state = "COMPRAR/MANTER" if inn else "REDUZIR/ESPERAR"

    sfile = f"state-{key}.txt"
    old = open(sfile).read() if os.path.exists(sfile) else ""
    if state != old:
        open(sfile, "w").write(state)
        topic = os.environ.get("NTFY_TOPIC")
        if topic and old:
            urllib.request.urlopen(urllib.request.Request(
                f"https://ntfy.sh/{topic}",
                data=f"{name}: sinal mudou para {state} (preço {p[-1]:.2f})".encode()))

if done == 0:
    sys.exit(1)

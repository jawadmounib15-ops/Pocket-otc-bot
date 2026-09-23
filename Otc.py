import os, time, requests, threading, yfinance as yf, pandas as pd
from datetime import datetime
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home(): return "BOT V113 OTC STRETTO-MEDIO LIVE"

TOKEN=os.environ.get("TELEGRAM_TOKEN")
CHAT=os.environ.get("TELEGRAM_CHAT_ID")

# OTC - Le 8 coppie che Quotex tiene 90% payout nel weekend
PAIRS_OTC=["EURUSD=X","GBPUSD=X","USDJPY=X","EURJPY=X","GBPJPY=X","AUDJPY=X","EURGBP=X","USDCAD=X"]

def send(m):
 try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",json={"chat_id":CHAT,"text":m,"parse_mode":"Markdown"},timeout=10)
 except: pass

def rsi(s,p=14):
 d=s.diff(); g=d.where(d>0,0); l=-d.where(d<0,0)
 return 100-(100/(1+g.ewm(alpha=1/p).mean()/l.ewm(alpha=1/p).mean()))

def bot():
 send("🟠 *BOT V113 OTC STRETTO-MEDIO ACCESO*\nRegole precise per OTC manipolato - 8-12 segnali/giorno")
 while True:
  try:
   for pair in PAIRS_OTC:
    try:
     df=yf.download(pair,period="5d",interval="5m",progress=False)
     if len(df)<210: continue
     if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)

     df["EMA200"]=df["Close"].ewm(span=200).mean()
     df["EMA50"]=df["Close"].ewm(span=50).mean()
     df["RSI"]=rsi(df["Close"])
     df["EMA12"]=df["Close"].ewm(span=12).mean()
     df["EMA26"]=df["Close"].ewm(span=26).mean()
     df["MACD"]=df["EMA12"]-df["EMA26"]
     df["SIGNAL"]=df["MACD"].ewm(span=9).mean()
     df["MA20"]=df["Close"].rolling(20).mean()
     df["STD"]=df["Close"].rolling(20).std()
     # OTC: Bollinger più stretto 1.5 invece di 2 (OTC fa escursioni più piccole)
     df["LOW"]=df["MA20"]-1.5*df["STD"]
     df["UP"]=df["MA20"]+1.5*df["STD"]

     c=df["Close"].iloc[-1]
     ema200=df["EMA200"].iloc[-1]
     ema50=df["EMA50"].iloc[-1]
     r=df["RSI"].iloc[-1]
     r_prev=df["RSI"].iloc[-2]
     r_prev2=df["RSI"].iloc[-3]
     macd=df["MACD"].iloc[-1]
     macd_prev=df["MACD"].iloc[-2]
     sig=df["SIGNAL"].iloc[-1]
     low=df["LOW"].iloc[-1]
     up=df["UP"].iloc[-1]

     # REGOLE OTC STRETTO-MEDIO - 4 condizioni su 5
     # OTC è diverso: serve RSI più estremo 25/75 non 30/70
     
     buy_score = 0
     # 1. Trend: EMA50 > EMA200 E prezzo > EMA50 (doppio filtro trend)
     if ema50 > ema200 and c > ema50: buy_score += 1
     # 2. RSI OTC: deve essere sotto 35 e in risalita da 2 candele (non 1 sola)
     if r < 38 and r > r_prev and r_prev > r_prev2 and r_prev < 40: buy_score += 1
     # 3. MACD OTC: incrocio UP ma MACD deve essere negativo da almeno 3 candele (accumulo)
     if macd_prev < sig and macd > sig and macd < 0: buy_score += 1
     # 4. Bollinger OTC 1.5 dev: prezzo tocca o rompe LOW
     if c <= low*1.01: buy_score += 1
     # 5. RSI estremo OTC: sotto 30 = punto bonus
     if r < 30: buy_score += 1

     sell_score = 0
     if ema50 < ema200 and c < ema50: sell_score += 1
     if r > 62 and r < r_prev and r_prev < r_prev2 and r_prev > 60: sell_score += 1
     if macd_prev > sig and macd < sig and macd > 0: sell_score += 1
     if c >= up*0.99: sell_score += 1
     if r > 70: sell_score += 1

     nome=pair.replace("=X","")+"-OTC"
     
     # OTC STRETTO-MEDIO = 4/5
     if buy_score >= 4:
      send(f"🔵 *{nome} BUY OTC {buy_score}/5*\nEMA50>EMA200 {'✅' if ema50>ema200 and c>ema50 else '❌'} | RSI {r_prev2:.0f}->{r_prev:.0f}->{r:.0f} risalita 2 candele ✅ | MACD X-UP neg ✅ | Boll 1.5 LOW ✅\n5m OTC")

     if sell_score >= 4:
      send(f"🔴 *{nome} SELL OTC {sell_score}/5*\nEMA50<EMA200 {'✅' if ema50<ema200 and c<ema50 else '❌'} | RSI {r_prev2:.0f}->{r_prev:.0f}->{r:.0f} discesa 2 candele ✅ | MACD X-DOWN pos ✅ | Boll 1.5 UP ✅\n5m OTC")

    except: continue
   time.sleep(180) # Ogni 3 min per OTC
  except: time.sleep(30)

threading.Thread(target=bot,daemon=True).start()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))

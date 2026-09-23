import os, time, requests, yfinance as yf, threading, pandas as pd
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home(): return "V106 OTC 0.05 65/35 ONLINE"
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT = os.environ.get("TELEGRAM_CHAT_ID")
PAIRS = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X","USDCHF=X","NZDUSD=X","EURGBP=X","EURJPY=X","GBPJPY=X","AUDJPY=X","EURAUD=X","EURCAD=X","EURCHF=X","GBPAUD=X","GBPCAD=X","AUDCAD=X","AUDCHF=X","CADJPY=X","CHFJPY=X","NZDJPY=X","EURNZD=X"]
IDX=0
def send(m):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id":CHAT,"text":m,"parse_mode":"Markdown"},timeout=10)
    except: pass
def rsi(s,p=14):
    d=s.diff(); g=d.where(d>0,0); l=-d.where(d<0,0)
    return 100-(100/(1+g.ewm(alpha=1/p).mean()/l.ewm(alpha=1/p).mean()))
def bot():
    global IDX
    send("💀 *V106 OTC 0.05 65/35 ONLINE - 22 coppie*")
    while True:
        try:
            batch=PAIRS[IDX:IDX+2]
            if not batch: IDX=0; batch=PAIRS[0:2]
            IDX+=2
            for pair in batch:
                df=yf.download(pair,period="5d",interval="5m",progress=False)
                if len(df)<210: continue
                if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
                df["RSI"]=rsi(df["Close"]); df["MA"]=df["Close"].rolling(20).mean(); df["STD"]=df["Close"].rolling(20).std(); df["UP"]=df["MA"]+2*df["STD"]; df["LOW"]=df["MA"]-2*df["STD"]; df["EMA200"]=df["Close"].ewm(span=200).mean()
                c=float(df["Close"].iloc[-1]); r=float(df["RSI"].iloc[-1]); up=float(df["UP"].iloc[-1]); low=float(df["LOW"].iloc[-1]); ema=float(df["EMA200"].iloc[-1])
                toll=(up-low)*0.05; sig=None
                if r>=70 and c>=up-toll and c>ema: sig="BUY"
                elif r<=30 and c<=low+toll and c<ema: sig="SELL"
                if sig:
                    nome=pair.replace('=X','')+" OTC"
                    send(f"💀 *{nome} {sig} RSI:{r:.0f}*")
                time.sleep(2)
        except: pass
        time.sleep(60)
threading.Thread(target=bot,daemon=True).start()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))

import datetime
import pandas as pd
import requests
import yfinance as yf

BOT_TOKEN = "8974475971:AAH1xec2QKZKiCiNySQG_8D7tCyxqo_tmLQ"
CHAT_ID = "8048497436"


def send_telegram(message):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
  try:
    requests.post(url, json=data, timeout=10)
  except Exception as e:
    print(f"Telegram error: {e}")


def check_market():
  now = datetime.datetime.now(datetime.timezone.utc)
  today_str = now.strftime("%Y-%m-%d")

  # Gold 5-minute data fetch
  try:
    df = yf.download("GC=F", period="2d", interval="5m", progress=False)
    if df.empty or len(df) < 50:
      print("Data nahi mila ya insufficient bars.")
      return
  except Exception as e:
    print(f"Data fetch error: {e}")
    return

  df.index = pd.to_datetime(df.index)

  # Asian Session Range (00:00 - 08:00 UTC)
  asia_mask = (df.index.strftime("%Y-%m-%d") == today_str) & (
      df.index.hour < 8
  )
  asia_data = df[asia_mask]

  if len(asia_data) == 0:
    print("Asian session data abhi complete nahi hua.")
    return

  asia_high = float(asia_data["High"].max())
  asia_low = float(asia_data["Low"].min())

  # London / NY Active Check (08:00 UTC ke baad)
  if now.hour < 8:
    print("Abhi Asian session chal raha hai, London open ka wait karo.")
    return

  recent_candles = df.tail(5)
  latest_candle = recent_candles.iloc[-1]
  curr_high = float(latest_candle["High"])
  curr_low = float(latest_candle["Low"])
  curr_close = float(latest_candle["Close"])

  # Bullish Sweep + FVG check
  if curr_low < asia_low and curr_close > asia_low:
    c1_high = float(recent_candles.iloc[-3]["High"])
    c3_low = float(recent_candles.iloc[-1]["Low"])
    if c3_low > c1_high:
      sl = round(curr_low - 1.5, 2)
      tp = round(curr_close + ((curr_close - sl) * 2), 2)
      msg = (
          f"🚨 *XAUUSD (GOLD) BUY SIGNAL!*\n\n"
          f"Setup: Asian Low Swept & FVG Formed\n"
          f"Entry: ~{curr_close:.2f}\n"
          f"SL: {sl}\n"
          f"TP (1:2): {tp}\n\n"
          f"_Phone me Exness khol kar execute karein!_"
      )
      send_telegram(msg)
      print("Buy Alert Sent!")
      return

  # Bearish Sweep + FVG check
  if curr_high > asia_high and curr_close < asia_high:
    c1_low = float(recent_candles.iloc[-3]["Low"])
    c3_high = float(recent_candles.iloc[-1]["High"])
    if c3_high < c1_low:
      sl = round(curr_high + 1.5, 2)
      tp = round(curr_close - ((sl - curr_close) * 2), 2)
      msg = (
          f"🚨 *XAUUSD (GOLD) SELL SIGNAL!*\n\n"
          f"Setup: Asian High Swept & FVG Formed\n"
          f"Entry: ~{curr_close:.2f}\n"
          f"SL: {sl}\n"
          f"TP (1:2): {tp}\n\n"
          f"_Phone me Exness khol kar execute karein!_"
      )
      send_telegram(msg)
      print("Sell Alert Sent!")
      return

  print("No trade condition met right now.")


if __name__ == "__main__":
  check_market()

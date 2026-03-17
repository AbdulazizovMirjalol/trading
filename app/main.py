from datetime import datetime
import time
import os

import MetaTrader5 as mt5
import matplotlib.pyplot as plt

from mt5_client import connect_mt5, disconnect_mt5
from analyzer import run_analysis
from config import SIGNAL_MODE, ENABLE_AUTO_TRADE, LOT_SIZE
from trader import place_market_order
from reporter import (
    show_analysis_report,
    show_price_table,
    save_analysis_to_file,
    save_bars_to_csv,
    show_final_decision,
    show_run_context,
    save_signal_journal,
    show_signal_stats,
    show_recent_signals,
    show_actionable_signals,
    show_hot_signals,
    show_ready_signal_banner,
    show_signal_mode,
    show_execution_signal_banner,
    send_telegram_alert,
    send_telegram_photo,
    play_signal_sound,
)


def run_once():
    if not connect_mt5():
        return

    try:
        result = run_analysis()

        # 1. Agar analysis natija bermasa
        if result is None:
            print("Tahlil natijasi olinmadi.")
            return

        # 2. News filter
        if result["is_news_time"]:
            result["final_signal"] = "WAIT"
            result["reason"] = f"STOP: {result['news_reason']}"

        # 3. D1 trend filter
        if result["final_signal"] == "BUY" and result["d1_trend"] == "BEARISH":
            result["final_signal"] = "WAIT"
            result["reason"] = "BUY bloklandi: D1 trend tushishda."

        elif result["final_signal"] == "SELL" and result["d1_trend"] == "BULLISH":
            result["final_signal"] = "WAIT"
            result["reason"] = "SELL bloklandi: D1 trend ko'tarilishda."

        # 4. DXY filter
        if result["final_signal"] == "BUY" and result["dxy_status"] == "STRENGTHENING":
            result["final_signal"] = "WAIT"
            result["reason"] = "BUY bloklandi: DXY kuchaymoqda."

        elif result["final_signal"] == "SELL" and result["dxy_status"] == "WEAKENING":
            result["final_signal"] = "WAIT"
            result["reason"] = "SELL bloklandi: DXY zaiflashmoqda."

        # 5. Konsolga hisobotlar
        show_run_context(
            symbol=result["symbol"],
            h1_timeframe_name=result["h1_timeframe_name"],
            m15_timeframe_name=result["m15_timeframe_name"],
        )

        show_signal_mode(SIGNAL_MODE)
        show_price_table(result["m15_df"])

        show_analysis_report(
            h1_timeframe_name=result["h1_timeframe_name"],
            m15_timeframe_name=result["m15_timeframe_name"],
            h1_trend=result["h1_trend"],
            m15_trend=result["m15_trend"],
            alignment_text=result["alignment_text"],
            rsi_value=result["last_rsi"],
            rsi_text=result["rsi_text"],
            macd_text=result["macd_text"],
            candle_confirmation=result["candle_confirmation"],
            support=result["support"],
            resistance=result["resistance"],
            atr_value=result["atr_value"],
            price_location=result["price_location"],
            entry_zone_text=result["entry_zone_text"],
            summary=result["summary"],
            trade_comment=result["trade_comment"],
            setup_status=result["setup_status"],
            signal_strength=result["signal_strength"],
            trade_plan=result["trade_plan"],
            final_signal=result["final_signal"],
            alert_message=result["alert_message"],
            reason=result["reason"],
            suggested_entry=result["suggested_entry"],
            suggested_sl=result["suggested_sl"],
            suggested_tp=result["suggested_tp"],
            risk_reward_ratio=result["risk_reward_ratio"],
        )

        show_final_decision(
            h1_timeframe_name=result["h1_timeframe_name"],
            m15_timeframe_name=result["m15_timeframe_name"],
            final_signal=result["final_signal"],
            setup_status=result["setup_status"],
            signal_strength=result["signal_strength"],
            trade_plan=result["trade_plan"],
            alert_message=result["alert_message"],
            reason=result["reason"],
            signal_mode=SIGNAL_MODE,
        )

        # 6. Ovoz va bannerlar
        play_signal_sound(
            setup_status=result["setup_status"],
            final_signal=result["final_signal"],
        )

        show_ready_signal_banner(result)
        show_execution_signal_banner(result)

                # Avto trade: default holatda OFF
        if result["final_signal"] in ["BUY", "SELL"]:
            if ENABLE_AUTO_TRADE:
                success, order_message = place_market_order(
                    symbol=result["symbol"],
                    signal=result["final_signal"],
                    lot_size=LOT_SIZE,
                    sl=result["suggested_sl"],
                    tp=result["suggested_tp"],
                )

                print(order_message)
                result["reason"] = f"{result['reason']} | {order_message}"
            else:
                print("AUTO TRADE OFF: order ochilmadi")
                result["reason"] = f"{result['reason']} | AUTO TRADE OFF"

        # 7. Telegramga signal bo'lsa rasm yuborish
        if result["final_signal"] in ["BUY", "SELL"]:
            screenshot_path = os.path.join(os.getcwd(), "chart_snapshot.png")

            try:
                chart_df = result["m15_df"]

                plt.figure(figsize=(12, 6))
                plt.plot(chart_df["time"], chart_df["close"])
                plt.title(f"{result['symbol']} M15 Chart")
                plt.xlabel("Time")
                plt.ylabel("Price")
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(screenshot_path)
                plt.close()

                emoji = "🚀 BUY" if result["final_signal"] == "BUY" else "🔥 SELL"
                caption = (
                    f"<b>{emoji} SIGNAL DETECTED</b>\n"
                    f"Symbol: {result['symbol']}\n"
                    f"Entry: {result['suggested_entry']}\n"
                    f"SL: {result['suggested_sl']} | TP: {result['suggested_tp']}"
                )

                send_telegram_photo(screenshot_path, caption)

            except Exception as e:
                print(f"Chart yaratishda xatolik: {e}")
                send_telegram_alert(result)

        # 8. Log va statistika
        save_analysis_to_file(result)
        save_bars_to_csv(result)
        save_signal_journal(result)
        show_signal_stats()
        show_recent_signals()
        show_actionable_signals()
        show_hot_signals()

    finally:
        disconnect_mt5()


def start():
    print("======================================")
    print("   GOLD TRADING BOT: AUTO-SCAN MODE   ")
    print("   Bot har 15 daqiqada tahlil qiladi  ")
    print("======================================")

    while True:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{now}] Tahlil boshlandi...")

        try:
            run_once()
        except Exception as e:
            print(f"Xatolik yuz berdi: {e}")
            print("1 daqiqadan so'ng qayta urinib ko'ramiz...")
            time.sleep(60)
            continue

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Tahlil tugadi.")
        print("Keyingi tahlilga qadar 15 daqiqa kutilmoqda (To'xtatish uchun Ctrl+C)...")

        # 900 soniya = 15 daqiqa
        time.sleep(900)


if __name__ == "__main__":
    start()
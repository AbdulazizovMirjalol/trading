from rich.console import Console
from rich.table import Table
from datetime import datetime
from pathlib import Path
import pandas as pd
from config import SIGNAL_MODE, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ENABLE_TELEGRAM_NOTIFICATIONS
from colorama import init, Fore, Style
import winsound
import requests
import os
init(autoreset=True)

def color_signal_text(text: str) -> str:
    t = str(text).upper()

    if "BUY" in t and "WATCH" not in t:
        return Fore.GREEN + str(text) + Style.RESET_ALL

    if "SELL" in t and "WATCH" not in t:
        return Fore.RED + str(text) + Style.RESET_ALL

    if "READY BUY" in t:
        return Fore.CYAN + str(text) + Style.RESET_ALL

    if "READY SELL" in t:
        return Fore.MAGENTA + str(text) + Style.RESET_ALL

    if "BUY WATCH" in t:
        return Fore.BLUE + str(text) + Style.RESET_ALL

    if "SELL WATCH" in t:
        return Fore.YELLOW + str(text) + Style.RESET_ALL

    if "WAIT" in t:
        return Fore.YELLOW + str(text) + Style.RESET_ALL

    if "NO TRADE" in t:
        return Fore.WHITE + str(text) + Style.RESET_ALL

    if "STRONG" in t:
        return Fore.GREEN + str(text) + Style.RESET_ALL

    if "MEDIUM" in t:
        return Fore.YELLOW + str(text) + Style.RESET_ALL

    if "WEAK" in t:
        return Fore.RED + str(text) + Style.RESET_ALL

    return str(text)

def play_signal_sound(setup_status: str, final_signal: str):
    try:
        if final_signal == "BUY":
            winsound.Beep(1200, 500)
            winsound.Beep(1400, 500)
            return

        if final_signal == "SELL":
            winsound.Beep(900, 500)
            winsound.Beep(700, 500)
            return

        if setup_status == "READY BUY":
            winsound.Beep(1000, 400)
            return

        if setup_status == "READY SELL":
            winsound.Beep(800, 400)
            return
    except:
        pass

console = Console()

def show_analysis_report(
    h1_timeframe_name: str,
    m15_timeframe_name: str,
    h1_trend: str,
    m15_trend: str,
    alignment_text: str,
    rsi_value: float,
    rsi_text: str,
    macd_text: str,
    candle_confirmation: str,
    support: float,
    resistance: float,
    atr_value: float,
    price_location: str,
    entry_zone_text: str,
    summary: str,
    trade_comment: str,
    setup_status: str,
    signal_strength: str,
    trade_plan: str,
    final_signal: str,
    alert_message: str,
    reason: str,
    suggested_entry,
    suggested_sl,
    suggested_tp,
    risk_reward_ratio,
):
    table = Table(title="GOLD TRADING ANALYSIS REPORT")

    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    table.add_row("Higher Timeframe", h1_timeframe_name)
    table.add_row("Entry Timeframe", m15_timeframe_name)
    table.add_row("H1 Trend", h1_trend)
    table.add_row("M15 Trend", m15_trend)
    table.add_row("Timeframe Alignment", alignment_text)
    table.add_row("RSI", f"{rsi_value:.2f}")
    table.add_row("RSI Status", rsi_text)
    table.add_row("MACD Status", macd_text)
    table.add_row("Candle Confirmation", candle_confirmation)
    table.add_row("Support", f"{support:.2f}")
    table.add_row("Resistance", f"{resistance:.2f}")
    table.add_row("ATR", f"{atr_value:.2f}")
    table.add_row("Price Location", price_location)
    table.add_row("Entry Zone", entry_zone_text)
    table.add_row("Summary", summary)
    table.add_row("Trade Comment", trade_comment)
    table.add_row("Setup Status", setup_status)
    table.add_row("Signal Strength", signal_strength)
    table.add_row("Trade Plan", trade_plan)
    table.add_row("Final Signal", final_signal)
    table.add_row("Alert Message", alert_message)
    table.add_row("Reason", reason)

    if suggested_entry is not None:
        table.add_row("Suggested Entry", f"{suggested_entry:.2f}")
    else:
        table.add_row("Suggested Entry", "N/A")

    if suggested_sl is not None:
        table.add_row("Suggested Stop Loss", f"{suggested_sl:.2f}")
    else:
        table.add_row("Suggested Stop Loss", "N/A")

    if suggested_tp is not None:
        table.add_row("Suggested Take Profit", f"{suggested_tp:.2f}")
    else:
        table.add_row("Suggested Take Profit", "N/A")

    if risk_reward_ratio is not None:
        table.add_row("Risk/Reward Ratio", f"{risk_reward_ratio:.2f}")
    else:
        table.add_row("Risk/Reward Ratio", "N/A")

    console.print(table)

def show_price_table(df):
    table = Table(title="XAUUSD M15 - Last 5 Bars")

    columns = ["time", "open", "high", "low", "close", "EMA_20", "EMA_50", "RSI", "MACD", "MACD_signal"]

    for col in columns:
        table.add_column(col, style="cyan")

    last_rows = df.tail(5)

    for _, row in last_rows.iterrows():
        table.add_row(
            str(row["time"]),
            f"{row['open']:.2f}",
            f"{row['high']:.2f}",
            f"{row['low']:.2f}",
            f"{row['close']:.2f}",
            f"{row['EMA_20']:.2f}",
            f"{row['EMA_50']:.2f}",
            f"{row['RSI']:.2f}",
            f"{row['MACD']:.2f}",
            f"{row['MACD_signal']:.2f}",
        )

    console.print(table)

from datetime import datetime
from pathlib import Path


from datetime import datetime
from pathlib import Path


def save_analysis_to_file(result: dict):
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = logs_dir / f"analysis_{timestamp}.txt"

    m15_df = result["m15_df"].tail(5)

    lines = []
    lines.append("GOLD TRADING ANALYSIS REPORT")
    lines.append("=" * 50)
    lines.append("")
    lines.append("XAUUSD M15 - Last 5 Bars")
    lines.append("-" * 50)
    lines.append(m15_df.to_string(index=False))
    lines.append("")
    lines.append("FINAL ANALYSIS")
    lines.append("-" * 50)
    lines.append(f"Higher Timeframe: {result['h1_timeframe_name']}")
    lines.append(f"Entry Timeframe: {result['m15_timeframe_name']}")
    lines.append(f"H1 Trend: {result['h1_trend']}")
    lines.append(f"M15 Trend: {result['m15_trend']}")
    lines.append(f"D1 Trend: {result.get('d1_trend', 'N/A')}")
    lines.append(f"DXY Status: {result.get('dxy_status', 'N/A')}")
    lines.append(f"News Time: {result.get('is_news_time', False)}")
    lines.append(f"News Reason: {result.get('news_reason', 'N/A')}")
    lines.append(f"Timeframe Alignment: {result['alignment_text']}")
    lines.append(f"RSI: {result['last_rsi']:.2f}")
    lines.append(f"RSI Status: {result['rsi_text']}")
    lines.append(f"MACD Status: {result['macd_text']}")
    lines.append(f"Candle Confirmation: {result['candle_confirmation']}")
    lines.append(f"Support: {result['support']:.2f}")
    lines.append(f"Resistance: {result['resistance']:.2f}")
    lines.append(f"ATR: {result['atr_value']:.2f}")
    lines.append(f"Price Location: {result['price_location']}")
    lines.append(f"Entry Zone: {result['entry_zone_text']}")
    lines.append(f"Summary: {result['summary']}")
    lines.append(f"Trade Comment: {result['trade_comment']}")
    lines.append(f"Setup Status: {result['setup_status']}")
    lines.append(f"Signal Strength: {result['signal_strength']}")
    lines.append(f"Trade Plan: {result['trade_plan']}")
    lines.append(f"Final Signal: {result['final_signal']}")
    lines.append(f"Alert Message: {result['alert_message']}")
    lines.append(f"Reason: {result['reason']}")
    lines.append(f"Suggested Entry: {result['suggested_entry'] if result['suggested_entry'] is not None else 'N/A'}")
    lines.append(f"Suggested Stop Loss: {result['suggested_sl'] if result['suggested_sl'] is not None else 'N/A'}")
    lines.append(f"Suggested Take Profit: {result['suggested_tp'] if result['suggested_tp'] is not None else 'N/A'}")
    lines.append(f"Risk/Reward Ratio: {result['risk_reward_ratio'] if result['risk_reward_ratio'] is not None else 'N/A'}")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    cleanup_old_logs(max_files=30)
    print(f"\nAnalysis faylga saqlandi: {file_path}")


def cleanup_old_logs(max_files: int = 30):
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log_files = sorted(logs_dir.glob("analysis_*.txt"), key=lambda f: f.stat().st_mtime)

    while len(log_files) > max_files:
        oldest_file = log_files.pop(0)
        oldest_file.unlink()

def save_bars_to_csv(result: dict):
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = logs_dir / f"bars_{timestamp}.csv"

    result["m15_df"].tail(5).to_csv(file_path, index=False)

    cleanup_old_logs(max_files=30)
    print(f"Bars CSV faylga saqlandi: {file_path}")

def save_signal_journal(result: dict):
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    file_path = logs_dir / "signal_journal.csv"

    row = {
    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "symbol": result["symbol"],
    "higher_tf": result["h1_timeframe_name"],
    "entry_tf": result["m15_timeframe_name"],
    "h1_trend": result["h1_trend"],
    "m15_trend": result["m15_trend"],
    "alignment": result["alignment_text"],
    "rsi": round(result["last_rsi"], 2),
    "rsi_status": result["rsi_text"],
    "macd_status": result["macd_text"],
    "candle_confirmation": result["candle_confirmation"],
    "support": round(result["support"], 2),
    "resistance": round(result["resistance"], 2),
    "atr": round(result["atr_value"], 2),
    "price_location": result["price_location"],
    "entry_zone": result["entry_zone_text"],
    "setup_status": result["setup_status"],
    "signal_strength": result["signal_strength"],
    "final_signal": result["final_signal"],
    "actionable": "YES" if result["setup_status"] in ["BUY WATCH", "SELL WATCH", "READY BUY", "READY SELL"] else "NO",
    "hot_signal": "YES" if result["setup_status"] in ["READY BUY", "READY SELL"] else "NO",
    "signal_mode": SIGNAL_MODE,
    "trade_plan": result["trade_plan"],
    "alert_message": result["alert_message"],
    "reason": result["reason"],
    "suggested_entry": result["suggested_entry"],
    "suggested_sl": result["suggested_sl"],
    "suggested_tp": result["suggested_tp"],
    "risk_reward_ratio": result["risk_reward_ratio"],
}

    df = pd.DataFrame([row])

    try:
        if file_path.exists():
            df.to_csv(file_path, mode="a", header=False, index=False, encoding="utf-8")
        else:
            df.to_csv(file_path, index=False, encoding="utf-8")

        print(f"Signal jurnal saqlandi: {file_path}")

    except PermissionError:
        print(f"Xatolik: {file_path} fayli ochiq turibdi. Avval faylni yoping.")

def show_signal_stats():
    file_path = Path("logs") / "signal_journal.csv"

    if not file_path.exists():
        print("Signal jurnal topilmadi.")
        return

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Signal statistikani o‘qishda xatolik: {e}")
        print("Ehtimol signal_journal.csv eski va yangi format aralashib ketgan.")
        print("logs/signal_journal.csv faylini o‘chirib, qayta yaratib ko‘ring.")
        return

    if df.empty:
        print("Signal jurnal bo‘sh.")
        return

    print("\nSIGNAL STATISTICS")
    print("-----------------")
    print(f"Jami signal yozuvlari: {len(df)}")

    if "final_signal" in df.columns:
        print("\nFinal Signal statistikasi:")
        print(df["final_signal"].value_counts().to_string())

    if "setup_status" in df.columns:
        print("\nSetup Status statistikasi:")
        print(df["setup_status"].value_counts().to_string())

    if "signal_strength" in df.columns:
        print("\nSignal Strength statistikasi:")
        print(df["signal_strength"].value_counts().to_string())

    if "signal_mode" in df.columns:
        print("\nSignal Mode statistikasi:")
        print(df["signal_mode"].value_counts().to_string())

    if "setup_status" in df.columns:
        ready_statuses = ["READY BUY", "READY SELL"]
        ready_df = df[df["setup_status"].isin(ready_statuses)]

        print("\nREADY SIGNAL statistikasi:")
        if ready_df.empty:
            print("Hozircha READY BUY yoki READY SELL yo‘q.")
        else:
            print(ready_df["setup_status"].value_counts().to_string())

        actionable_statuses = ["BUY WATCH", "SELL WATCH", "READY BUY", "READY SELL"]
        actionable_df = df[df["setup_status"].isin(actionable_statuses)]

        print("\nACTIONABLE SIGNAL statistikasi:")
        if actionable_df.empty:
            print("Hozircha actionable signal yo‘q.")
        else:
            print(actionable_df["setup_status"].value_counts().to_string())

        hot_statuses = ["READY BUY", "READY SELL"]
        hot_df = df[df["setup_status"].isin(hot_statuses)]

        print("\nHOT SIGNAL statistikasi:")
        if hot_df.empty:
            print("Hozircha READY BUY yoki READY SELL yo‘q.")
        else:
            print(hot_df["setup_status"].value_counts().to_string())

def show_recent_signals(limit: int = 10):
    file_path = Path("logs/signal_journal.csv")

    if not file_path.exists():
        print("\nOxirgi signallar topilmadi. signal_journal.csv hali yaratilmagan.\n")
        return

    try:
        df = pd.read_csv(file_path)

        if df.empty:
            print("\nSignal jurnal bo‘sh.\n")
            return

        recent_df = df.tail(limit)

        print("\nRECENT SIGNALS")
        print("-" * 40)

        columns_to_show = [
            "time",
            "symbol",
            "h1_trend",
            "m15_trend",
            "setup_status",
            "signal_strength",
            "final_signal",
            "actionable",
            "hot_signal",
            "signal_mode",
        ]

        existing_columns = [col for col in columns_to_show if col in recent_df.columns]

        if not existing_columns:
            print("Ko‘rsatish uchun mos ustunlar topilmadi.")
            return

        print(recent_df[existing_columns].to_string(index=False))

    except Exception as e:
        print(f"\nOxirgi signallarni o‘qishda xatolik: {e}\n")

def show_actionable_signals(limit: int = 10):
    file_path = Path("logs/signal_journal.csv")

    if not file_path.exists():
        print("\nACTIONABLE SIGNALS topilmadi. signal_journal.csv hali yaratilmagan.\n")
        return

    try:
        df = pd.read_csv(file_path)

        if df.empty:
            print("\nSignal jurnal bo‘sh.\n")
            return

        actionable_statuses = [
            "BUY WATCH",
            "SELL WATCH",
            "READY BUY",
            "READY SELL",
        ]

        filtered_df = df[df["setup_status"].isin(actionable_statuses)]

        if "reason_short" in filtered_df.columns:
            filtered_df["reason_short"] = filtered_df["reason_short"].astype(str).str.slice(0, 50)

        if filtered_df.empty:
            print("\nACTIONABLE SIGNALS")
            print("-" * 40)
            print("Hozircha muhim signal yo‘q.")
            return

        recent_df = filtered_df.tail(limit).copy()

        if "reason" in recent_df.columns:
            recent_df["reason_short"] = recent_df["reason"].astype(str).apply(
                lambda x: x[:60] + "..." if len(x) > 60 else x
            )

        print("\nACTIONABLE SIGNALS")
        print("-" * 40)


        columns_to_show = [
            "time",
            "symbol",
            "setup_status",
            "signal_strength",
            "final_signal",
            "actionable",
            "hot_signal",
            "signal_mode",
        ]

        existing_columns = [col for col in columns_to_show if col in recent_df.columns]

        if not existing_columns:
            print("Ko‘rsatish uchun mos ustunlar topilmadi.")
            return

        print(recent_df[existing_columns].to_string(index=False))

    except Exception as e:
        print(f"\nACTIONABLE SIGNALS ni o‘qishda xatolik: {e}\n")

def show_hot_signals(limit: int = 5):
    file_path = Path("logs/signal_journal.csv")

    if not file_path.exists():
        print("\nHOT SIGNALS topilmadi. signal_journal.csv hali yaratilmagan.\n")
        return

    try:
        df = pd.read_csv(file_path)

        if df.empty:
            print("\nHOT SIGNALS uchun jurnal bo‘sh.\n")
            return

        hot_statuses = ["READY BUY", "READY SELL"]
        filtered_df = df[df["setup_status"].isin(hot_statuses)]

        if "reason_short" in filtered_df.columns:
            filtered_df["reason_short"] = filtered_df["reason_short"].astype(str).str.slice(0, 50)

        print("\nHOT SIGNALS")
        print("-" * 40)

        if filtered_df.empty:
            print("Hozircha READY BUY yoki READY SELL yo‘q.")
            return

        recent_df = filtered_df.tail(limit).copy()

        if "reason" in recent_df.columns:
            recent_df["reason_short"] = recent_df["reason"].astype(str).apply(
                lambda x: x[:60] + "..." if len(x) > 60 else x
            )

        columns_to_show = [
            "time",
            "symbol",
            "setup_status",
            "signal_strength",
            "final_signal",
            "actionable",
            "hot_signal",
            "signal_mode",
        ]

        existing_columns = [col for col in columns_to_show if col in recent_df.columns]

        print(recent_df[existing_columns].to_string(index=False))

    except Exception as e:
        print(f"\nHOT SIGNALS ni o‘qishda xatolik: {e}\n")

def show_ready_signal_banner(result: dict):
    if result["setup_status"] not in ["READY BUY", "READY SELL"]:
        return

    print("\n" + "=" * 72)
    print(" " * 24 + "READY SIGNAL ALERT")
    print("=" * 72)
    print(f"Symbol       : {result['symbol']}")
    print(f"Higher TF    : {result['h1_timeframe_name']}")
    print(f"Entry TF     : {result['m15_timeframe_name']}")
    print(f"Setup Status : {color_signal_text(result['setup_status'])}")
    print(f"Final Signal : {color_signal_text(result['final_signal'])}")
    print(f"Strength     : {color_signal_text(result['signal_strength'])}")
    print(f"Entry        : {result['suggested_entry']}")
    print(f"Stop Loss    : {result['suggested_sl']}")
    print(f"Take Profit  : {result['suggested_tp']}")
    print(f"RR Ratio     : {result['risk_reward_ratio']}")
    print(f"Reason       : {result['reason']}")
    print(f"Alert        : {result['alert_message']}")
    print("=" * 72 + "\n")

def show_final_decision(
    h1_timeframe_name: str,
    m15_timeframe_name: str,
    final_signal: str,
    setup_status: str,
    signal_strength: str,
    trade_plan: str,
    alert_message: str,
    reason: str,
    signal_mode: str,
):
    print("\nFINAL DECISION")
    print("-" * 14)
    print(f"Higher TF: {h1_timeframe_name}")
    print(f"Entry TF: {m15_timeframe_name}")
    print(f"Mode: {signal_mode}")
    print(f"Signal: {color_signal_text(final_signal)}")
    print(f"Setup: {color_signal_text(setup_status)}")
    print(f"Strength: {color_signal_text(signal_strength)}")
    print(f"Plan: {trade_plan}")
    print(f"Alert: {Fore.CYAN + alert_message + Style.RESET_ALL}")
    print(f"Reason: {Fore.WHITE + reason + Style.RESET_ALL}")

def show_run_context(symbol: str, h1_timeframe_name: str, m15_timeframe_name: str):
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"SYMBOL: {symbol}")
    print(f"HIGHER TF: {h1_timeframe_name}")
    print(f"ENTRY TF: {m15_timeframe_name}")
    print(f"TIME: {now_text}\n")

def show_signal_mode(signal_mode: str):
    print(f"SIGNAL MODE: {signal_mode}")


def show_execution_signal_banner(result: dict):
    if result["final_signal"] not in ["BUY", "SELL"]:
        return

    print("\n" + "#" * 72)
    print(" " * 22 + "EXECUTION SIGNAL TRIGGERED")
    print("#" * 72)
    print(f"Symbol       : {result['symbol']}")
    print(f"Higher TF    : {result['h1_timeframe_name']}")
    print(f"Entry TF     : {result['m15_timeframe_name']}")
    print(f"Mode         : {result.get('signal_mode', 'normal')}")
    print(f"Final Signal : {color_signal_text(result['final_signal'])}")
    print(f"Setup Status : {color_signal_text(result['setup_status'])}")
    print(f"Strength     : {color_signal_text(result['signal_strength'])}")
    print(f"Entry        : {result['suggested_entry']}")
    print(f"Stop Loss    : {result['suggested_sl']}")
    print(f"Take Profit  : {result['suggested_tp']}")
    print(f"RR Ratio     : {result['risk_reward_ratio']}")
    print(f"Reason       : {result['reason']}")
    print(f"Alert        : {result['alert_message']}")
    print("#" * 72 + "\n")


def send_telegram_alert(result: dict):
    if not ENABLE_TELEGRAM_NOTIFICATIONS:
        return

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram sozlamalari to'liq emas")
        return

    emoji = "🚀 BUY" if result["final_signal"] == "BUY" else "🔥 SELL" if result["final_signal"] == "SELL" else "👀 WAIT"

    message = (
        f"{emoji} XAUUSD SIGNAL\n\n"
        f"Status: {result['setup_status']}\n"
        f"Strength: {result['signal_strength']}\n"
        f"Time: {datetime.now().strftime('%H:%M:%S')}\n"
        f"D1 Trend: {result.get('d1_trend', 'N/A')}\n"
        f"DXY Status: {result.get('dxy_status', 'N/A')}\n"
        f"News: {result.get('news_reason', 'N/A')}\n\n"
        f"Entry: {result['suggested_entry']}\n"
        f"SL: {result['suggested_sl']}\n"
        f"TP: {result['suggested_tp']}\n"
        f"RR: {result['risk_reward_ratio']}\n\n"
        f"Reason: {result['reason']}\n"
        f"Alert: {result['alert_message']}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }

    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code != 200:
            print(f"Telegram API xatosi: {response.text}")
    except Exception as e:
        print(f"Telegram xatolik: {e}")

def send_telegram_photo(photo_path, caption):
    if not ENABLE_TELEGRAM_NOTIFICATIONS:
        return

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram sozlamalari to'liq emas")
        return

    if not os.path.exists(photo_path):
        print(f"❌ Rasm topilmadi: {photo_path}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

    try:
        with open(photo_path, "rb") as photo:
            files = {"photo": photo}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML",
            }

            response = requests.post(url, files=files, data=data, timeout=15)

            if response.status_code == 200:
                print("✅ Rasm Telegramga yuborildi")
            else:
                print(f"❌ Telegram xatosi: {response.text}")

    except Exception as e:
        print(f"❌ Rasm yuborishda xatolik: {e}")
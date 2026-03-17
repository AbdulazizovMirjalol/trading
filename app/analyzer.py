import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

from config import (
    SYMBOL,
    EMA_FAST,
    EMA_SLOW,
    RSI_PERIOD,
    ATR_PERIOD,
    M15_BARS,
    H1_BARS,
    M15_TIMEFRAME_NAME,
    H1_TIMEFRAME_NAME,
    SIGNAL_MODE,
)

from mt5_client import get_gold_data

from indicators import (
    add_ema,
    detect_trend,
    add_rsi,
    interpret_rsi,
    generate_summary,
    add_macd,
    interpret_macd,
    find_support_resistance,
    analyze_timeframe_alignment,
    detect_price_location,
    detect_entry_zone,
    generate_trade_comment,
    add_atr,
    detect_setup_status,
    detect_signal_strength,
    generate_trade_plan,
    generate_risk_levels,
    calculate_risk_reward,
    generate_final_signal,
    generate_entry_price,
    generate_alert_message,
    generate_reason,
    detect_candle_confirmation,
)


def check_high_impact_news():
    """
    Hozircha soddalashtirilgan news filter.
    Keyin real calendar API yoki scraping bilan almashtiriladi.
    """
    try:
        now = datetime.now()
        current_hour = now.hour

        # O'zbekiston vaqti bo'yicha xavfli zona:
        # 16:00 dan 20:00 gacha
        if 16 <= current_hour <= 20:
            return True, "AQSH yangiliklari vaqti (xavfli vaqt)"

        return False, "Tinch vaqt"
    except Exception as e:
        print(f"Yangiliklarni tekshirishda xato: {e}")
        return False, "Aniqlanmadi"


def get_d1_trend(symbol):
    """
    D1 timeframe bo'yicha umumiy trendni aniqlaydi.
    20 kunlik EMA asosida:
    - close > EMA20 => BULLISH
    - close < EMA20 => BEARISH
    """
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 20)

    if rates is None or len(rates) < 20:
        return "NEUTRAL"

    df_d1 = pd.DataFrame(rates)
    ema20 = df_d1["close"].ewm(span=20, adjust=False).mean().iloc[-1]
    last_close = df_d1["close"].iloc[-1]

    if last_close > ema20:
        return "BULLISH"
    elif last_close < ema20:
        return "BEARISH"
    else:
        return "NEUTRAL"


def get_dxy_status():
    """
    DXY holatini aniqlaydi.
    Hozircha 2 ta M15 candle close orqali sodda tekshiruv.
    """
    dxy_symbol = "DXY"
    rates = mt5.copy_rates_from_pos(dxy_symbol, mt5.TIMEFRAME_M15, 0, 2)

    if rates is None or len(rates) < 2:
        return "UNKNOWN"

    prev_close = rates[0]["close"]
    last_close = rates[1]["close"]

    if last_close > prev_close:
        return "STRENGTHENING"
    elif last_close < prev_close:
        return "WEAKENING"
    else:
        return "FLAT"


def run_analysis():
    # 1. Market data olish
    m15_df = get_gold_data(bars=M15_BARS)
    h1_df = get_gold_data(timeframe=mt5.TIMEFRAME_H1, bars=H1_BARS)

    if m15_df is None or h1_df is None:
        return None

    # 2. Indicatorlarni hisoblash
    m15_df = add_ema(m15_df, [EMA_FAST, EMA_SLOW])
    m15_df = add_rsi(m15_df, RSI_PERIOD)
    m15_df = add_macd(m15_df)
    m15_df = add_atr(m15_df, ATR_PERIOD)

    h1_df = add_ema(h1_df, [EMA_FAST, EMA_SLOW])

    # 3. Trend va alignment
    m15_trend = detect_trend(m15_df, EMA_FAST, EMA_SLOW)
    h1_trend = detect_trend(h1_df, EMA_FAST, EMA_SLOW)
    alignment_text = analyze_timeframe_alignment(h1_trend, m15_trend)

    # 4. Asosiy qiymatlar
    current_price = m15_df["close"].iloc[-1]
    last_rsi = m15_df["RSI"].iloc[-1]
    rsi_text = interpret_rsi(last_rsi)
    macd_text = interpret_macd(m15_df)
    candle_confirmation = detect_candle_confirmation(m15_df)

    support, resistance = find_support_resistance(m15_df)
    price_location = detect_price_location(current_price, support, resistance)

    ema20_value = m15_df[f"EMA_{EMA_FAST}"].iloc[-1]
    atr_value = m15_df["ATR"].iloc[-1]

    # 5. Entry zone
    entry_zone_text = detect_entry_zone(
        m15_df,
        m15_trend,
        current_price,
        ema20_value,
        support,
        resistance,
        atr_value,
    )

    # 6. Setup status
    setup_status = detect_setup_status(
        h1_trend,
        m15_trend,
        rsi_text,
        macd_text,
        price_location,
        entry_zone_text,
        candle_confirmation,
    )

    # 7. Trade comment
    trade_comment = generate_trade_comment(
        h1_trend,
        m15_trend,
        rsi_text,
        macd_text,
        price_location,
        entry_zone_text,
        setup_status,
    )

    # 8. Signal strength
    signal_strength = detect_signal_strength(
        h1_trend,
        m15_trend,
        rsi_text,
        macd_text,
        setup_status,
        candle_confirmation,
    )

    # 9. Trade plan
    trade_plan = generate_trade_plan(
        setup_status,
        signal_strength,
        price_location,
    )

    # 10. Summary
    summary = generate_summary(
        h1_trend,
        m15_trend,
        last_rsi,
        macd_text,
        current_price,
        support,
        resistance,
    )

    # 11. Entry, SL, TP
    suggested_entry = generate_entry_price(
        setup_status,
        current_price,
        ema20_value,
        support,
        resistance,
    )

    suggested_sl, suggested_tp = generate_risk_levels(
        h1_trend,
        m15_trend,
        support,
        resistance,
        atr_value,
        setup_status,
    )

    risk_reward_ratio = calculate_risk_reward(
        setup_status,
        suggested_entry,
        suggested_sl,
        suggested_tp,
    )

    # 12. Final signal
    final_signal = generate_final_signal(
        setup_status,
        signal_strength,
        candle_confirmation,
        risk_reward_ratio,
    )

    # 13. Reason
    reason = generate_reason(
        h1_trend,
        m15_trend,
        rsi_text,
        macd_text,
        price_location,
        entry_zone_text,
        setup_status,
        final_signal,
        risk_reward_ratio,
        candle_confirmation,
        signal_strength,
    )

    # 14. Alert message
    alert_message = generate_alert_message(
        final_signal,
        setup_status,
        signal_strength,
    )

    # 15. Qo'shimcha filtrlar
    d1_trend = get_d1_trend(SYMBOL)
    dxy_status = get_dxy_status()
    is_news_time, news_reason = check_high_impact_news()

    # 16. Yakuniy natija
    return {
        "m15_df": m15_df,
        "symbol": SYMBOL,
        "m15_timeframe_name": M15_TIMEFRAME_NAME,
        "h1_timeframe_name": H1_TIMEFRAME_NAME,
        "h1_trend": h1_trend,
        "m15_trend": m15_trend,
        "d1_trend": d1_trend,
        "dxy_status": dxy_status,
        "is_news_time": is_news_time,
        "news_reason": news_reason,
        "alignment_text": alignment_text,
        "last_rsi": last_rsi,
        "rsi_text": rsi_text,
        "macd_text": macd_text,
        "candle_confirmation": candle_confirmation,
        "support": support,
        "resistance": resistance,
        "atr_value": atr_value,
        "price_location": price_location,
        "entry_zone_text": entry_zone_text,
        "summary": summary,
        "setup_status": setup_status,
        "trade_comment": trade_comment,
        "signal_strength": signal_strength,
        "trade_plan": trade_plan,
        "final_signal": final_signal,
        "alert_message": alert_message,
        "reason": reason,
        "suggested_entry": suggested_entry,
        "suggested_sl": suggested_sl,
        "suggested_tp": suggested_tp,
        "risk_reward_ratio": risk_reward_ratio,
        "signal_mode": SIGNAL_MODE,
    }
import pandas as pd
from config import (
    STATUS_NO_TRADE,
    STATUS_SELL_WATCH,
    SIGNAL_WEAK,
    SIGNAL_MEDIUM,
    SIGNAL_STRONG,
    FINAL_SIGNAL_BUY,
    FINAL_SIGNAL_SELL,
    FINAL_SIGNAL_WAIT,
    STATUS_BUY_WATCH,
    STATUS_SELL_WATCH,
    STATUS_READY_BUY,
    STATUS_READY_SELL,
    SIGNAL_MODE,
    SIGNAL_MODE_AGGRESSIVE,
    SIGNAL_MODE_NORMAL,
    SIGNAL_MODE_CONSERVATIVE,
)

def add_ema(df: pd.DataFrame, periods):
    """
    DataFramega ko'rsatilgan davrlar uchun EMA ustunlari qo'shadi.
    """
    for p in periods:
        df[f"EMA_{p}"] = df["close"].ewm(span=p, adjust=False).mean()
    return df

def detect_trend(df: pd.DataFrame, short: int, long: int) -> str:
    """
    EMA kesishlariga qarab trend holatini aniqlaydi.
    Qisqa EMA uzun EMAdan yuqori bo'lsa — Bullish, aks holda Bearish.
    """
    if df.empty:
        return "Unknown"

    if df[f"EMA_{short}"].iloc[-1] > df[f"EMA_{long}"].iloc[-1]:
        return "Bullish (Ko'tarilish)"
    elif df[f"EMA_{short}"].iloc[-1] < df[f"EMA_{long}"].iloc[-1]:
        return "Bearish (Tushish)"
    else:
        return "Sideways (Range)"
    
def add_rsi(df: pd.DataFrame, period: int = 14):
    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    return df

def interpret_rsi(rsi_value: float) -> str:
    if rsi_value >= 70:
        return "Overbought (bozor juda qizigan)"
    elif rsi_value <= 30:
        return "Oversold (bozor juda tushgan)"
    elif rsi_value > 50:
        return "Bullish momentum"
    elif rsi_value < 50:
        return "Bearish momentum"
    else:
        return "Neutral"
    
def generate_summary(
    h1_trend: str,
    m15_trend: str,
    rsi_value: float,
    macd_text: str,
    current_price: float,
    support: float,
    resistance: float
) -> str:
    distance_to_support = abs(current_price - support)
    distance_to_resistance = abs(resistance - current_price)

    bullish_rsi = rsi_value > 50
    bearish_rsi = rsi_value < 50
    bullish_macd = "Bullish" in macd_text
    bearish_macd = "Bearish" in macd_text

    bullish_alignment = "Bullish" in h1_trend and "Bullish" in m15_trend
    bearish_alignment = "Bearish" in h1_trend and "Bearish" in m15_trend
    mixed_bullish = "Bullish" in h1_trend and "Bearish" in m15_trend
    mixed_bearish = "Bearish" in h1_trend and "Bullish" in m15_trend

    if bullish_alignment and bullish_rsi and bullish_macd:
        if distance_to_resistance < distance_to_support:
            return "H1 va M15 bullish alignmentda. RSI va MACD ham bullish. Narx resistance ga yaqin, breakout kuzatish kerak."
        return "H1 va M15 bullish alignmentda. RSI va MACD ham bullish. Bozor yuqoriga bosim ko'rsatmoqda."

    elif bearish_alignment and bearish_rsi and bearish_macd:
        if distance_to_support < distance_to_resistance:
            return "H1 va M15 bearish alignmentda. RSI va MACD ham bearish. Narx support ga yaqin, breakdown xavfi bor."
        return "H1 va M15 bearish alignmentda. RSI va MACD ham bearish. Bozor pastga bosim ko'rsatmoqda."

    elif bullish_alignment and bullish_rsi and bearish_macd:
        return "H1 va M15 bullish alignmentda, RSI bullish, lekin MACD zaiflashishni ko'rsatmoqda."

    elif bearish_alignment and bearish_rsi and bullish_macd:
        return "H1 va M15 bearish alignmentda, RSI bearish, lekin MACD tiklanishga urinmoqda."

    elif mixed_bullish:
        return "H1 bullish, lekin M15 zaiflashgan. Bu pullback yoki vaqtinchalik tuzatish bo'lishi mumkin."

    elif mixed_bearish:
        return "H1 bearish, lekin M15 tiklanmoqda. Bu counter-trend rebound bo'lishi mumkin."

    elif "Bullish" in m15_trend and bearish_rsi:
        return "M15 trend bullish, lekin momentum zaiflashgan."

    elif "Bearish" in m15_trend and bullish_rsi:
        return "M15 trend bearish, lekin momentum tiklanishga urinmoqda."

    else:
        return "Bozor noaniq yoki range holatda."
    
def generate_trade_comment(
    h1_trend: str,
    m15_trend: str,
    rsi_text: str,
    macd_text: str,
    price_location: str,
    entry_zone_text: str,
    setup_status: str
) -> str:
    if setup_status == STATUS_READY_BUY:
        return "Buy setup tayyor. Trend, momentum va candle confirmation buy tomonida."

    elif setup_status == STATUS_BUY_WATCH:
        return "Buy setup shakllanmoqda. Support/EMA zonasi yaqinida kuzatish kerak."

    elif setup_status == STATUS_READY_SELL:
        return "Sell setup tayyor. Trend, momentum va candle confirmation sell tomonida."

    elif setup_status == STATUS_SELL_WATCH:
        return "Sell setup shakllanmoqda. Resistance/EMA zonasi yaqinida kuzatish kerak."

    else:
        return "Hozircha aniq trade setup yo‘q. Shoshilmasdan kutish kerak."
    
def detect_setup_status(
    h1_trend: str,
    m15_trend: str,
    rsi_text: str,
    macd_text: str,
    price_location: str,
    entry_zone_text: str,
    candle_confirmation: str,
) -> str:
    """
    PRO YONDASHUV: Qaror qabul qilish markazi (SMC logikasi).
    Faqat H1 va M15 trendi mos tushganda, narx FVG/Order Block'da bo'lganda 
    va Liquidity Sweep (Pin bar) tasdiqlangandagina trade ochishga ruxsat beradi.
    """
    candle_text = candle_confirmation.lower()
    entry_text = entry_zone_text.lower()
    h1_lower = h1_trend.lower()
    m15_lower = m15_trend.lower()

    # 1. Multi-Timeframe tasdig'i (H1 va M15 bir xil yo'nalishdami?)
    bullish_alignment = "bullish" in h1_lower and "bullish" in m15_lower
    bearish_alignment = "bearish" in h1_lower and "bearish" in m15_lower

    # 2. Narx biz kutgan Pro zonadami? (FVG, Order Block, EMA kesishmasi)
    in_bullish_zone = "bullish setup" in entry_text or "bullish fvg" in entry_text
    in_bearish_zone = "bearish setup" in entry_text or "bearish fvg" in entry_text

    # 3. Banklar izi tasdiqlandimi? (Liquidity Sweep, Pin Bar yoki Engulfing)
    strong_bullish_candle = "bullish" in candle_text and ("sweep" in candle_text or "engulfing" in candle_text or "strong" in candle_text)
    strong_bearish_candle = "bearish" in candle_text and ("sweep" in candle_text or "engulfing" in candle_text or "strong" in candle_text)

    # ===============================
    # BUY (SOTIB OLISH) LOGIKASI
    # ===============================
    if bullish_alignment:
        if in_bullish_zone:
            if strong_bullish_candle:
                return STATUS_READY_BUY   # Hamma narsa ideal, Olg'a!
            else:
                return STATUS_BUY_WATCH   # Narx zonada, lekin banklar izi yo'q (Kutamiz)
        elif strong_bullish_candle:
            return STATUS_BUY_WATCH       # Narx zonadan sal tashqarida, lekin kuchli sham bor (Kuzatamiz)

    # ===============================
    # SELL (SOTISH) LOGIKASI
    # ===============================
    if bearish_alignment:
        if in_bearish_zone:
            if strong_bearish_candle:
                return STATUS_READY_SELL  # Hamma narsa ideal, Olg'a!
            else:
                return STATUS_SELL_WATCH  # Narx zonada, lekin banklar izi yo'q (Kutamiz)
        elif strong_bearish_candle:
            return STATUS_SELL_WATCH      # Narx zonadan sal tashqarida, lekin kuchli sham bor (Kuzatamiz)

    # Agar yuqoridagi shartlar bajarilmasa, bozor noaniq.
    return STATUS_NO_TRADE
            

def generate_trade_plan(
    setup_status: str,
    signal_strength: str,
    price_location: str,
) -> str:
    if setup_status == STATUS_READY_BUY:
        return "Buy setup tayyor. Entry, SL va TP asosida buy ko'rib chiqilishi mumkin."

    if setup_status == STATUS_READY_SELL:
        return "Sell setup tayyor. Entry, SL va TP asosida sell ko'rib chiqilishi mumkin."

    if setup_status == STATUS_BUY_WATCH:
        return "Buy setup shakllanmoqda. Support/EMA yaqinida kuzatish kerak."

    if setup_status == STATUS_SELL_WATCH:
        return "Sell setup shakllanmoqda. Resistance/EMA yaqinida kuzatish kerak."

    return "Hozircha trade ochish tavsiya etilmaydi."
    
def add_macd(df: pd.DataFrame):
    ema_12 = df["close"].ewm(span=12, adjust=False).mean()
    ema_26 = df["close"].ewm(span=26, adjust=False).mean()

    df["MACD"] = ema_12 - ema_26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    return df

def add_atr(df: pd.DataFrame, period: int = 14):
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = true_range.rolling(window=period).mean()

    return df


def interpret_macd(df: pd.DataFrame) -> str:
    macd_value = df["MACD"].iloc[-1]
    signal_value = df["MACD_signal"].iloc[-1]

    if macd_value > signal_value:
        return "Bullish MACD momentum"
    elif macd_value < signal_value:
        return "Bearish MACD momentum"
    else:
        return "Neutral MACD"
    
def find_support_resistance(df: pd.DataFrame):
    """
    PRO YONDASHUV: Haqiqiy Market Structure (Swing) zonalarini topish.
    Oddiy oxirgi 20 ta sham emas, balki narx qaytgan kuchli 'Pivot' nuqtalarni qidiradi.
    """
    df = df.copy()
    
    # Swing High va Swing Low (Fractals) ni aniqlash
    # Sham o'zidan oldingi va keyingi 2 ta shamdan baland/past bo'lsa - bu kuchli zona hisoblanadi
    df['Swing_High'] = df['high'][(df['high'].shift(1) < df['high']) & (df['high'].shift(2) < df['high']) & 
                                  (df['high'].shift(-1) < df['high']) & (df['high'].shift(-2) < df['high'])]
    
    df['Swing_Low'] = df['low'][(df['low'].shift(1) > df['low']) & (df['low'].shift(2) > df['low']) & 
                                (df['low'].shift(-1) > df['low']) & (df['low'].shift(-2) > df['low'])]
    
    # Eng so'nggi tasdiqlangan kuchli Liquidity / Burilish zonalari
    recent_resistance = df['Swing_High'].dropna().tail(2).max() # So'nggi 2 ta kuchli tepalikning eng balandi
    recent_support = df['Swing_Low'].dropna().tail(2).min()     # So'nggi 2 ta kuchli pastlikning eng pasti
    
    # Fallback (Xavfsizlik tizimi): Agar bozor juda kuchli impulsiv trendda bo'lib, 
    # hali swing bermagan bo'lsa, oxirgi 30 ta shamdan qidiramiz.
    if pd.isna(recent_resistance):
        recent_resistance = df["high"].tail(30).max()
    if pd.isna(recent_support):
        recent_support = df["low"].tail(30).min()
        
    return recent_support, recent_resistance

def analyze_timeframe_alignment(h1_trend: str, m15_trend: str) -> str:
    if "Bullish" in h1_trend and "Bullish" in m15_trend:
        return "H1 va M15 bir tomonda. Bullish alignment kuchli."
    elif "Bearish" in h1_trend and "Bearish" in m15_trend:
        return "H1 va M15 bir tomonda. Bearish alignment kuchli."
    elif "Bullish" in h1_trend and "Bearish" in m15_trend:
        return "H1 bullish, M15 bearish. Bu pullback yoki vaqtinchalik tuzatish bo'lishi mumkin."
    elif "Bearish" in h1_trend and "Bullish" in m15_trend:
        return "H1 bearish, M15 bullish. Bu counter-trend rebound bo'lishi mumkin."
    else:
        return "Timeframe alignment noaniq."
    
def detect_price_location(current_price: float, support: float, resistance: float) -> str:
    distance_to_support = abs(current_price - support)
    distance_to_resistance = abs(resistance - current_price)
    total_range = resistance - support

    if total_range == 0:
        return "Narx diapazoni aniqlanmadi."

    support_ratio = distance_to_support / total_range
    resistance_ratio = distance_to_resistance / total_range

    if support_ratio < 0.25:
        return "Narx support ga yaqin."
    elif resistance_ratio < 0.25:
        return "Narx resistance ga yaqin."
    else:
        return "Narx support va resistance oralig'ida."
    
def detect_entry_zone(
    df: pd.DataFrame,
    trend: str,
    current_price: float,
    ema20: float,
    support: float,
    resistance: float,
    atr: float
) -> str:
    distance_to_ema20 = abs(current_price - ema20)
    distance_to_support = abs(current_price - support)
    distance_to_resistance = abs(resistance - current_price)
    threshold = atr if atr > 0 else 5

    # Pro yondashuv: FVG ni tekshirish
    fvg_type, fvg_bottom, fvg_top = find_latest_fvg(df)
    
    fvg_text = ""
    if fvg_type == "Bullish FVG":
        if fvg_bottom <= current_price <= fvg_top or abs(current_price - fvg_top) < threshold:
            fvg_text = " (Narx Bullish FVG zonasida!)"
    elif fvg_type == "Bearish FVG":
        if fvg_bottom <= current_price <= fvg_top or abs(current_price - fvg_bottom) < threshold:
            fvg_text = " (Narx Bearish FVG zonasida!)"

    if "Bullish" in trend:
        if distance_to_ema20 < threshold or distance_to_support < threshold or "Bullish FVG" in fvg_text:
            return f"Bullish setup: narx kuchli zonada (Support/EMA/FVG).{fvg_text}"
        else:
            return f"Bullish trend bor, lekin narx entry zonasidan uzoq.{fvg_text}"

    elif "Bearish" in trend:
        if distance_to_ema20 < threshold or distance_to_resistance < threshold or "Bearish FVG" in fvg_text:
            return f"Bearish setup: narx kuchli zonada (Resistance/EMA/FVG).{fvg_text}"
        else:
            return f"Bearish trend bor, lekin narx entry zonasidan uzoq.{fvg_text}"

    return "Aniq entry zona topilmadi."


def detect_signal_strength(
    h1_trend: str,
    m15_trend: str,
    rsi_text: str,
    macd_text: str,
    setup_status: str,
    candle_confirmation: str,
) -> str:
    if setup_status == STATUS_NO_TRADE:
        return SIGNAL_WEAK

    score = 0
    
    # 1. Trend mosligi (+2 ball)
    if "bullish" in h1_trend.lower() and "bullish" in m15_trend.lower():
        score += 2
    elif "bearish" in h1_trend.lower() and "bearish" in m15_trend.lower():
        score += 2

    # 2. Setup tayyorgarligi (+2 ball)
    if setup_status in [STATUS_READY_BUY, STATUS_READY_SELL]:
        score += 2
    elif setup_status in [STATUS_BUY_WATCH, STATUS_SELL_WATCH]:
        score += 1

    # 3. Banklar izi (Liquidity Sweep) (+3 ball - Eng muhimi!)
    candle_lower = candle_confirmation.lower()
    if "strong" in candle_lower or "sweep" in candle_lower or "engulfing" in candle_lower:
        score += 3
    elif "weak" not in candle_lower and "no clear" not in candle_lower:
        score += 1

    # Xulosa
    if score >= 6:
        return SIGNAL_STRONG
    elif score >= 4:
        return SIGNAL_MEDIUM
    else:
        return SIGNAL_WEAK


def generate_final_signal(
    setup_status: str,
    signal_strength: str,
    candle_confirmation: str,
    risk_reward_ratio,
) -> str:
    rr_ok = False
    if risk_reward_ratio is not None:
        try:
            rr_ok = float(risk_reward_ratio) >= 1.5
        except:
            rr_ok = False

    # Agar Status READY bo'lsa va Risk/Reward qoniqarli bo'lsa
    if setup_status == STATUS_READY_BUY:
        if signal_strength in [SIGNAL_MEDIUM, SIGNAL_STRONG] and rr_ok:
            return FINAL_SIGNAL_BUY

    if setup_status == STATUS_READY_SELL:
        if signal_strength in [SIGNAL_MEDIUM, SIGNAL_STRONG] and rr_ok:
            return FINAL_SIGNAL_SELL

    return FINAL_SIGNAL_WAIT

def generate_entry_price(
    setup_status: str,
    current_price: float,
    ema20_value: float,
    support: float,
    resistance: float,
):
    # PRO YONDASHUV: Agar setup READY bo'lsa, limit kutmasdan joriy narxda kiriladi
    if setup_status in [STATUS_READY_BUY, STATUS_READY_SELL]:
        return round(current_price, 2)

    return None

def generate_risk_levels(
    h1_trend: str,
    m15_trend: str,
    support: float,      
    resistance: float,   
    atr_value: float,
    setup_status: str
):
    # PRO YONDASHUV: Stop Loss Swing nuqtalari orqasiga yashiriladi + Spread buferi
    buffer = (atr_value * 0.2) if atr_value else 0.5 
    
    if setup_status == STATUS_READY_BUY:
        stop_loss = support - buffer
        take_profit = resistance 
        return round(stop_loss, 2), round(take_profit, 2)

    elif setup_status == STATUS_READY_SELL:
        stop_loss = resistance + buffer
        take_profit = support 
        return round(stop_loss, 2), round(take_profit, 2)

    return None, None

def calculate_risk_reward(
    setup_status: str,
    suggested_entry,
    suggested_sl,
    suggested_tp,
):
    # PRO YONDASHUV: Risk va Reward nisbatini aniq hisoblash
    if suggested_entry is None or suggested_sl is None or suggested_tp is None:
        return None

    if setup_status == STATUS_READY_BUY:
        risk = suggested_entry - suggested_sl
        reward = suggested_tp - suggested_entry
    elif setup_status == STATUS_READY_SELL:
        risk = suggested_sl - suggested_entry
        reward = suggested_entry - suggested_tp
    else:
        return None

    if risk <= 0:
        return None

    return round(reward / risk, 2)

def generate_alert_message(
    final_signal: str,
    setup_status: str,
    signal_strength: str,
) -> str:
    if final_signal == FINAL_SIGNAL_BUY:
        return "ALERT: Buy signali tayyor."
    elif final_signal == FINAL_SIGNAL_SELL:
        return "ALERT: Sell signali tayyor."
    elif setup_status == STATUS_BUY_WATCH:
        return "ALERT: Buy setup kuzatilyapti."
    elif setup_status == STATUS_SELL_WATCH:
        return "ALERT: Sell setup kuzatilyapti."
    elif setup_status in [STATUS_READY_BUY, STATUS_READY_SELL]:
        return "ALERT: Setup bor, lekin risk/reward yoki tasdiq yetarli emas."
    else:
        return "ALERT: Hozircha signal kuchsiz."
def generate_reason(
    h1_trend: str,
    m15_trend: str,
    rsi_text: str,
    macd_text: str,
    price_location: str,
    entry_zone_text: str,
    setup_status: str,
    final_signal: str,
    risk_reward_ratio,
    candle_confirmation: str,
    signal_strength: str,
) -> str:
    if final_signal == "BUY":
        return "BUY signal tasdiqlandi. Setup, candle confirmation va risk/reward mos keldi."

    if final_signal == "SELL":
        return "SELL signal tasdiqlandi. Setup, candle confirmation va risk/reward mos keldi."

    reasons = []

    if setup_status not in ["READY BUY", "READY SELL"]:
        reasons.append("setup hali READY holatiga kelmagan")

    if setup_status == "READY BUY" and final_signal == "WAIT":
        reasons.append("BUY uchun barcha final shartlar hali to‘liq bajarilmagan")

    if setup_status == "READY SELL" and final_signal == "WAIT":
        reasons.append("SELL uchun barcha final shartlar hali to‘liq bajarilmagan")

    if signal_strength not in ["MEDIUM", "STRONG"]:
        reasons.append("signal strength yetarli emas")

    candle_text = candle_confirmation.lower()

    if setup_status == "READY BUY" and "bullish" not in candle_text:
        reasons.append("bullish candle confirmation yo‘q")

    if setup_status == "READY SELL" and "bearish" not in candle_text:
        reasons.append("bearish candle confirmation yo‘q")

    rr_ok = False
    if risk_reward_ratio is not None:
        try:
            rr_ok = float(risk_reward_ratio) >= 1.5
        except:
            rr_ok = False

    if setup_status in ["READY BUY", "READY SELL"] and not rr_ok:
        reasons.append("risk/reward hali yetarli emas")

    if not reasons:
        return "Trade ochish uchun yetarli tasdiq yo‘q."

    return "WAIT sababi: " + ", ".join(reasons) + "."


def detect_candle_confirmation(df) -> str:
    """
    PRO YONDASHUV: Liquidity Sweep (Pin bar) va Momentum (Engulfing) tasdiqlari.
    Banklar stop-losslarni urib qaytgandagi izlarni qidiradi.
    """
    if len(df) < 3:
        return "No clear candle confirmation"

    last = df.iloc[-1]
    prev = df.iloc[-2]

    body_size = abs(last["close"] - last["open"])
    total_range = last["high"] - last["low"]
    
    if total_range == 0:
        return "No clear candle confirmation"

    upper_wick = last["high"] - max(last["open"], last["close"])
    lower_wick = min(last["open"], last["close"]) - last["low"]

    # 1. LIQUIDITY SWEEP (Pin Bar / Hammer)
    if lower_wick > (total_range * 0.6) and body_size < (total_range * 0.3):
        return "Strong Bullish confirmation (Liquidity Sweep / Pin Bar)"

    if upper_wick > (total_range * 0.6) and body_size < (total_range * 0.3):
        return "Strong Bearish confirmation (Liquidity Sweep / Pin Bar)"

    # 2. ENGULFING (Yutib yuborish)
    if last["close"] > last["open"] and prev["close"] < prev["open"] and last["close"] >= prev["open"] and last["open"] <= prev["close"]:
        return "Bullish candle confirmation (Engulfing)"

    if last["close"] < last["open"] and prev["close"] > prev["open"] and last["close"] <= prev["open"] and last["open"] >= prev["close"]:
        return "Bearish candle confirmation (Engulfing)"

    # 3. Oddiy momentum tasdiqlari
    if last["close"] > last["open"] and last["close"] > prev["high"]:
        return "Bullish candle confirmation"

    if last["close"] < last["open"] and last["close"] < prev["low"]:
        return "Bearish candle confirmation"
        
    if last["close"] > last["open"]:
        return "Weak bullish candle"

    if last["close"] < last["open"]:
        return "Weak bearish candle"

    return "No clear candle confirmation"

def find_latest_fvg(df: pd.DataFrame):
    """
    PRO YONDASHUV: Fair Value Gap (FVG) / Imbalance ni aniqlash.
    Oxirgi 20 ta sham ichidan eng so'nggi FVG bo'shlig'ini topadi.
    """
    if len(df) < 25:
        return "No FVG", None, None
        
    for i in range(1, 20):
        idx1 = -(i+2) # 1-sham
        idx3 = -i     # 3-sham
        
        c1_high = df['high'].iloc[idx1]
        c1_low = df['low'].iloc[idx1]
        c3_high = df['high'].iloc[idx3]
        c3_low = df['low'].iloc[idx3]
        
        # Bullish FVG (Yashil impuls bo'shlig'i)
        if c3_low > c1_high:
            return "Bullish FVG", c1_high, c3_low
            
        # Bearish FVG (Qizil impuls bo'shlig'i)
        if c3_high < c1_low:
            return "Bearish FVG", c3_high, c1_low
            
    return "No FVG", None, None
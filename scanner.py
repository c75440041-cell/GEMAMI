import logging
import pandas as pd

import config
from qm_detector import detect_qm

log = logging.getLogger("scanner")


def _ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def _atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def analyze_symbol(ex, symbol):
    # 1. Filtro de tendencia en HTF (1H por defecto)
    ohlcv_htf = ex.fetch_ohlcv(symbol, config.HTF_TIMEFRAME, limit=80)
    if not ohlcv_htf or len(ohlcv_htf) < 60:
        return None

    df_htf = pd.DataFrame(ohlcv_htf, columns=["ts", "open", "high", "low", "close", "vol"])
    ema50_htf = _ema(df_htf["close"], 50).iloc[-1]
    ema20_htf = _ema(df_htf["close"], 20).iloc[-1]
    close_htf = df_htf["close"].iloc[-1]

    htf_bull = close_htf > ema50_htf and ema20_htf >= ema50_htf
    htf_bear = close_htf < ema50_htf and ema20_htf <= ema50_htf
    if not (htf_bull or htf_bear):
        return None

    # 2. Datos en timeframe operativo (5m)
    ohlcv = ex.fetch_ohlcv(symbol, config.TIMEFRAME, limit=120)
    if not ohlcv or len(ohlcv) < 80:
        return None

    df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "vol"])
    df_closed = df.iloc[:-1].copy()

    atr_series = _atr(df_closed, 14)
    atr = float(atr_series.iloc[-1])
    if atr <= 0:
        return None

    highs = df_closed["high"].tolist()
    lows = df_closed["low"].tolist()
    closes = df_closed["close"].tolist()

    qm = detect_qm(highs, lows, closes, atr, recent_bars=config.QM_RECENT_BARS)
    if not qm:
        return None

    side = qm["dir"]

    if side == "LONG" and not htf_bull:
        return None
    if side == "SHORT" and not htf_bear:
        return None

    entry = float(closes[-1])
    head = float(qm["head"])
    qml = float(qm["qml"])

    # 3. Validación de distancia al nivel QM
    dist_to_qml = abs(entry - qml) / atr
    if dist_to_qml > config.MAX_ENTRY_DIST_ATR:
        return None

    # 4. Volumen relativo y compresión previa
    vol_ma = float(df_closed["vol"].iloc[-21:-1].mean())
    last_vol = float(df_closed["vol"].iloc[-1])
    vol_ratio = (last_vol / vol_ma) if vol_ma > 0 else 0.0

    if vol_ratio < config.MIN_VOL_RATIO:
        return None

    atr_ma = float(atr_series.iloc[-21:-1].mean())
    compression = (atr / atr_ma) if atr_ma > 0 else 1.0

    # 5. Cálculo estructural de SL y TP (detrás de la cabeza del QM + colchón ATR)
    buffer = config.SL_ATR * atr
    if side == "LONG":
        sl = head - buffer
        risk_dist = entry - sl
        if risk_dist <= 0:
            return None
        tp = entry + (risk_dist * config.TP_RR)
    else:
        sl = head + buffer
        risk_dist = sl - entry
        if risk_dist <= 0:
            return None
        tp = entry - (risk_dist * config.TP_RR)

    # 6. Sistema de puntuación (0-100)
    sweep_atr = abs(head - qm["ls"]) / atr
    score = 50
    score += min(20, int(sweep_atr * 25))
    score += min(20, int((vol_ratio - 1.0) * 15))
    score += 10 if dist_to_qml <= 1.2 else 0
    score = max(0, min(100, score))

    if score < config.MIN_SCORE:
        return None

    return {
        "symbol": symbol,
        "side": side,
        "qm": True,
        "score": score,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "vol_ratio": vol_ratio,
        "compression": compression,
    }


def scan(ex):
    symbols = ex.top_symbols(config.TOP_N)
    signals = []
    for sym in symbols:
        try:
            sig = analyze_symbol(ex, sym)
            if sig:
                signals.append(sig)
        except Exception as e:
            log.debug("Error analizando %s: %s", sym, e)

    signals.sort(key=lambda x: x["score"], reverse=True)
    return signals

import logging
from collections import Counter

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


def _htf_trend(ex, symbol):
    """Devuelve 'bull' | 'bear' | 'neutral' | None (sin datos)."""
    o = ex.fetch_ohlcv(symbol, config.HTF_TIMEFRAME, limit=80)
    if not o or len(o) < 60:
        return None
    df = pd.DataFrame(o, columns=["ts", "open", "high", "low", "close", "vol"])
    e50 = _ema(df["close"], 50).iloc[-1]
    e20 = _ema(df["close"], 20).iloc[-1]
    c = df["close"].iloc[-1]
    if c > e50 and e20 >= e50:
        return "bull"
    if c < e50 and e20 <= e50:
        return "bear"
    return "neutral"


def analyze_symbol(ex, symbol, stats):
    # 1. Datos operativos (5m) primero: es el filtro mas selectivo
    ohlcv = ex.fetch_ohlcv(symbol, config.TIMEFRAME, limit=150)
    if not ohlcv or len(ohlcv) < 80:
        stats["sin_datos"] += 1
        return None

    df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "vol"])
    df_closed = df.iloc[:-1].copy()  # solo velas cerradas

    atr_series = _atr(df_closed, 14)
    atr = float(atr_series.iloc[-1])
    if atr <= 0:
        stats["atr_cero"] += 1
        return None

    highs = df_closed["high"].tolist()
    lows = df_closed["low"].tolist()
    closes = df_closed["close"].tolist()

    qm = detect_qm(highs, lows, closes, atr, recent_bars=config.QM_RECENT_BARS, diag=stats)
    if not qm:
        stats["sin_qm"] += 1
        return None
    stats["qm_detectado"] += 1

    side = qm["dir"]
    entry = float(closes[-1])
    head = float(qm["head"])

    # 2. Distancia al nivel de ruptura (BOS)
    dist = abs(entry - float(qm["mid"])) / atr
    if dist > config.MAX_ENTRY_DIST_ATR:
        stats["rech_distancia"] += 1
        return None

    # 3. Volumen: maximo de las ultimas 3 velas vs media previa
    vol_ma = float(df_closed["vol"].iloc[-24:-3].mean())
    vol_recent = float(df_closed["vol"].iloc[-3:].max())
    vol_ratio = (vol_recent / vol_ma) if vol_ma > 0 else 0.0
    if vol_ratio < config.MIN_VOL_RATIO:
        stats["rech_volumen"] += 1
        return None

    atr_ma = float(atr_series.iloc[-21:-1].mean())
    compression = (atr / atr_ma) if atr_ma > 0 else 1.0

    # 4. SL detras de la cabeza + colchon; TP por RR
    buffer = config.SL_ATR * atr
    if side == "LONG":
        sl = head - buffer
        risk_dist = entry - sl
        if risk_dist <= 0:
            stats["rech_sl"] += 1
            return None
        tp = entry + risk_dist * config.TP_RR
    else:
        sl = head + buffer
        risk_dist = sl - entry
        if risk_dist <= 0:
            stats["rech_sl"] += 1
            return None
        tp = entry - risk_dist * config.TP_RR

    if risk_dist / atr > config.MAX_SL_ATR:
        stats["rech_sl_lejano"] += 1
        return None

    # 5. Filtro HTF (solo se pide si ya hay patron valido)
    htf_pts = 0
    if config.HTF_MODE != "off":
        want = "bull" if side == "LONG" else "bear"
        try:
            trend = _htf_trend(ex, symbol)
        except Exception as e:
            log.warning("HTF falló %s: %s", symbol, e)
            trend = None
        if trend is None:
            stats["htf_sin_datos"] += 1
            if config.HTF_MODE == "strict":
                return None
            trend = "neutral"  # en modo soft no bloquea la señal
        if config.HTF_MODE == "strict" and trend != want:
            stats["rech_htf"] += 1
            return None
        if trend == want:
            htf_pts = 10
        elif trend != "neutral":
            htf_pts = -10

    # 6. Score
    sweep_atr = abs(head - qm["ls"]) / atr
    score = 40
    score += min(20, int(sweep_atr * 30))
    score += min(20, int((vol_ratio - 1.0) * 20))
    score += 10 if dist <= 1.2 else 0
    score += 5 if qm["bos_age"] <= 2 else 0
    score += htf_pts
    score = max(0, min(100, score))

    if score < config.MIN_SCORE:
        stats["rech_score"] += 1
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
    stats = Counter()
    for sym in symbols:
        try:
            sig = analyze_symbol(ex, sym, stats)
            if sig:
                signals.append(sig)
        except Exception as e:
            stats["errores"] += 1
            log.warning("Error analizando %s: %s", sym, e)

    log.info("Escaneados %d | %s", len(symbols), dict(stats))
    signals.sort(key=lambda x: x["score"], reverse=True)
    return signals

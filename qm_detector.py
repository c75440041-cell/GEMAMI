from config import PIVOT_LEN, MIN_SWEEP_ATR, BOS_MAX_AGE


def pivots(highs, lows, n=PIVOT_LEN):
    """Swings confirmados (no repintan): (indice, 1=maximo/-1=minimo, precio), alternados."""
    raw = []
    for i in range(n, len(highs) - n):
        if highs[i] == max(highs[i - n:i + n + 1]):
            raw.append((i, 1, highs[i]))
        if lows[i] == min(lows[i - n:i + n + 1]):
            raw.append((i, -1, lows[i]))

    alt = []
    for p in raw:
        if alt and alt[-1][1] == p[1]:
            if (p[1] == 1 and p[2] > alt[-1][2]) or (p[1] == -1 and p[2] < alt[-1][2]):
                alt[-1] = p
        else:
            alt.append(p)
    return alt


def detect_qm(highs, lows, closes, atr, recent_bars=40):
    """
    Bajista: maximo (hombro) -> minimo -> maximo mas alto (cabeza) -> cierre bajo el minimo (BOS).
    Alcista: el espejo.
    Busca el patron en una ventana de pivotes (el BOS genera pivotes nuevos,
    por eso no basta con mirar los 3 ultimos). Devuelve dict o None.
    """
    sw = pivots(highs, lows)
    n = len(highs)
    if len(sw) < 3 or atr <= 0:
        return None

    for k in range(len(sw) - 1, 1, -1):
        (ia, ta, pa), (im, tm, pm), (ih, th, ph) = sw[k - 2], sw[k - 1], sw[k]
        if ih < n - recent_bars:
            break  # pivotes mas antiguos, no sirven

        after = slice(ih + 1, n)

        # Bajista
        if ta == 1 and th == 1 and pm < pa and ph > pa + MIN_SWEEP_ATR * atr:
            if after.start < n and max(highs[after]) > ph:
                continue  # la cabeza fue superada
            bos = next((j for j in range(ih + 1, n) if closes[j] < pm), None)
            if bos is not None and (n - 1 - bos) <= BOS_MAX_AGE and closes[-1] < pm + 0.5 * atr:
                return {"dir": "SHORT", "ls": pa, "mid": pm, "head": ph, "qml": pa,
                        "bos_age": n - 1 - bos}

        # Alcista
        if ta == -1 and th == -1 and pm > pa and ph < pa - MIN_SWEEP_ATR * atr:
            if after.start < n and min(lows[after]) < ph:
                continue
            bos = next((j for j in range(ih + 1, n) if closes[j] > pm), None)
            if bos is not None and (n - 1 - bos) <= BOS_MAX_AGE and closes[-1] > pm - 0.5 * atr:
                return {"dir": "LONG", "ls": pa, "mid": pm, "head": ph, "qml": pa,
                        "bos_age": n - 1 - bos}

    return None

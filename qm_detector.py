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


def detect_qm(highs, lows, closes, atr, recent_bars=40, diag=None):
    """
    Bajista: maximo (hombro) -> minimo -> maximo mas alto (cabeza) -> cierre bajo el minimo (BOS).
    Alcista: el espejo. Busca en una ventana de pivotes. `diag` (Counter) cuenta
    en que fase se cae el patron, para depurar.
    """
    d = diag if diag is not None else {}

    def inc(k):
        d[k] = d.get(k, 0) + 1

    sw = pivots(highs, lows)
    n = len(highs)
    if len(sw) < 3 or atr <= 0:
        inc("f0_pocos_pivotes")
        return None

    for k in range(len(sw) - 1, 1, -1):
        (ia, ta, pa), (im, tm, pm), (ih, th, ph) = sw[k - 2], sw[k - 1], sw[k]
        if ih < n - recent_bars:
            break

        if ta == 1:  # bajista: hombro, minimo, cabeza
            if ph <= pa + MIN_SWEEP_ATR * atr:
                inc("f1_cabeza_no_supera")
                continue
            if ih + 1 < n and max(highs[ih + 1:]) > ph:
                inc("f2_cabeza_superada")
                continue
            bos = next((j for j in range(ih + 1, n) if closes[j] < pm), None)
            if bos is None:
                inc("f3_sin_bos")
                continue
            if n - 1 - bos > BOS_MAX_AGE:
                inc("f4_bos_viejo")
                continue
            return {"dir": "SHORT", "ls": pa, "mid": pm, "head": ph, "qml": pa,
                    "bos_age": n - 1 - bos}
        else:  # alcista: hombro(min), maximo, cabeza(min mas bajo)
            if ph >= pa - MIN_SWEEP_ATR * atr:
                inc("f1_cabeza_no_supera")
                continue
            if ih + 1 < n and min(lows[ih + 1:]) < ph:
                inc("f2_cabeza_superada")
                continue
            bos = next((j for j in range(ih + 1, n) if closes[j] > pm), None)
            if bos is None:
                inc("f3_sin_bos")
                continue
            if n - 1 - bos > BOS_MAX_AGE:
                inc("f4_bos_viejo")
                continue
            return {"dir": "LONG", "ls": pa, "mid": pm, "head": ph, "qml": pa,
                    "bos_age": n - 1 - bos}

    return None

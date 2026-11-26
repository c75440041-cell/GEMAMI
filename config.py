import os


def _bool(name, default):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _float(name, default):
    return float(os.getenv(name, default))


def _int(name, default):
    return int(os.getenv(name, default))


# Credenciales
BINGX_API_KEY = os.getenv("BINGX_API_KEY", "").strip()
BINGX_SECRET = os.getenv("BINGX_SECRET", "").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Modo: signals | dry | live
TRADE_MODE = os.getenv("TRADE_MODE", "signals").strip().lower()

# Escaneo
TIMEFRAME = os.getenv("TIMEFRAME", "5m").strip().lower()
HTF_TIMEFRAME = os.getenv("HTF_TIMEFRAME", "1h").strip().lower()
# HTF_MODE: strict (debe alinear) | soft (suma/resta puntos) | off (ignorar)
HTF_MODE = os.getenv("HTF_MODE", "soft").strip().lower()
SCAN_INTERVAL = _int("SCAN_INTERVAL", 60)
TOP_N = _int("TOP_N", 45)
MIN_SCORE = _float("MIN_SCORE", 60)
COOLDOWN_MIN = _int("COOLDOWN_MIN", 45)

# QM y filtros de calidad
PIVOT_LEN = _int("PIVOT_LEN", 3)
MIN_SWEEP_ATR = _float("MIN_SWEEP_ATR", 0.1)
QM_RECENT_BARS = _int("QM_RECENT_BARS", 50)
BOS_MAX_AGE = _int("BOS_MAX_AGE", 12)          # velas máx. desde la ruptura (BOS)
MAX_ENTRY_DIST_ATR = _float("MAX_ENTRY_DIST_ATR", 2.5)  # distancia al nivel de BOS
MIN_VOL_RATIO = _float("MIN_VOL_RATIO", 1.1)
MAX_SL_ATR = _float("MAX_SL_ATR", 8)          # SL máximo en ATR

# Riesgo (RISK_USDT = pérdida máxima real estimada en SL)
RISK_USDT = _float("RISK_USDT", 5)
LEVERAGE = _int("LEVERAGE", 10)
MAX_OPEN = _int("MAX_OPEN", 2)
DAILY_LOSS_LIMIT = _float("DAILY_LOSS_LIMIT", 15)
SL_ATR = _float("SL_ATR", 0.5)
TP_RR = _float("TP_RR", 2.2)


VALID_TF = ("1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d")


def validate():
    errors = []
    for name, val in (("TIMEFRAME", TIMEFRAME), ("HTF_TIMEFRAME", HTF_TIMEFRAME)):
        if val not in VALID_TF:
            errors.append(f"{name} inválido: '{val}'. Usa uno de: {', '.join(VALID_TF)}")
    if TRADE_MODE not in ("signals", "dry", "live"):
        errors.append(f"TRADE_MODE inválido: '{TRADE_MODE}'. Usa: signals / dry / live")
    if HTF_MODE not in ("strict", "soft", "off"):
        errors.append(f"HTF_MODE inválido: '{HTF_MODE}'. Usa: strict / soft / off")

    if TRADE_MODE in ("live", "dry"):
        if not BINGX_API_KEY or not BINGX_SECRET:
            errors.append(
                "BINGX_API_KEY o BINGX_SECRET están vacíos. "
                "Obligatorios para TRADE_MODE=live o dry. "
                "Créalas en https://bingx.com/en/account/api (permisos Futures, sin IP whitelist)."
            )
    return errors

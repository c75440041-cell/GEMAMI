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

# Escaneo (optimizado para 5m)
TIMEFRAME = os.getenv("TIMEFRAME", "5m")
HTF_TIMEFRAME = os.getenv("HTF_TIMEFRAME", "1h")
SCAN_INTERVAL = _int("SCAN_INTERVAL", 60)
TOP_N = _int("TOP_N", 45)
MIN_SCORE = _float("MIN_SCORE", 75)
COOLDOWN_MIN = _int("COOLDOWN_MIN", 45)

# QM y Filtros de Calidad
PIVOT_LEN = _int("PIVOT_LEN", 4)
MIN_SWEEP_ATR = _float("MIN_SWEEP_ATR", 0.15)
QM_RECENT_BARS = _int("QM_RECENT_BARS", 30)
MAX_ENTRY_DIST_ATR = _float("MAX_ENTRY_DIST_ATR", 2.2)
MIN_VOL_RATIO = _float("MIN_VOL_RATIO", 1.3)

# Riesgo (RISK_USDT = pérdida máxima real estimada en SL)
RISK_USDT = _float("RISK_USDT", 5)
LEVERAGE = _int("LEVERAGE", 10)
MAX_OPEN = _int("MAX_OPEN", 2)
DAILY_LOSS_LIMIT = _float("DAILY_LOSS_LIMIT", 15)
SL_ATR = _float("SL_ATR", 0.5)
TP_RR = _float("TP_RR", 2.2)


def validate():
    errors = []
    if TRADE_MODE not in ("signals", "dry", "live"):
        errors.append(f"TRADE_MODE inválido: '{TRADE_MODE}'. Usa: signals / dry / live")

    if TRADE_MODE in ("live", "dry"):
        if not BINGX_API_KEY or not BINGX_SECRET:
            errors.append(
                "BINGX_API_KEY o BINGX_SECRET están vacíos. "
                "Obligatorios para TRADE_MODE=live o dry. "
                "Créalas en https://bingx.com/en/account/api (permisos Futures, sin IP whitelist)."
            )
    return errors

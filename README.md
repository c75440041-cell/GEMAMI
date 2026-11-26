# BingX QM Scanner Bot — Versión Optimizada 5m

## Mejoras principales

1. **Filtro HTF (`1h`):** valida tendencia mediante EMA 20 y EMA 50 en `1h` antes de operar patrones Quasimodo en `5m`.
2. **Confirmación de volumen y distancia:** filtra rupturas sin volumen (`MIN_VOL_RATIO`) y entradas tardías lejos del nivel QM (`MAX_ENTRY_DIST_ATR`).
3. **Gestión de riesgo por distancia de SL:** calcula la cantidad de contratos en base a `RISK_USDT / |Entrada - SL|`, colocando el Stop Loss detrás de la cabeza (`head`) del patrón QM.
4. **Cooldown inteligente:** no descarta señales si `MAX_OPEN` está lleno en modo `live`.

## Variables de entorno recomendadas (Railway)

```env
TRADE_MODE=signals
TIMEFRAME=5m
HTF_TIMEFRAME=1h
SCAN_INTERVAL=60
TOP_N=45
MIN_SCORE=75
COOLDOWN_MIN=45
PIVOT_LEN=4
MIN_SWEEP_ATR=0.15
QM_RECENT_BARS=30
MAX_ENTRY_DIST_ATR=2.2
MIN_VOL_RATIO=1.3
RISK_USDT=5
LEVERAGE=10
MAX_OPEN=2
DAILY_LOSS_LIMIT=15
SL_ATR=0.5
TP_RR=2.2
```

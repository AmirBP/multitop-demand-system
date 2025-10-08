import pandas as pd
import numpy as np
import joblib
from pathlib import Path

MODEL_PATH = Path("outputs/modelo_xgb_sku_global.joblib")

def _load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Modelo no encontrado. Entrena primero con POST /api/model/train."
        )
    return joblib.load(MODEL_PATH)

def robust_sigma(group: pd.Series) -> float:
    last = group.tail(30)
    sigma = last.std(ddof=0)
    if np.isnan(sigma):
        sigma = group.std(ddof=0)
    return 0.0 if np.isnan(sigma) else sigma

def procesar_prediccion_global(df: pd.DataFrame) -> pd.DataFrame:
    # Carga perezosa del modelo (evita fallo al importar el módulo)
    modelo = _load_model()

    # Limpieza y tipado
    df["Fechaventa"] = pd.to_datetime(df["Fechaventa"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["Fechaventa"])
    df["CodArticulo"] = df["CodArticulo"].astype("category")
    df["Temporada"] = df["Temporada"].astype("category")
    df["PrecioVenta"] = pd.to_numeric(df["PrecioVenta"], errors="coerce")
    df["CantidadVendida"] = pd.to_numeric(df["CantidadVendida"], errors="coerce")
    df["StockMes"] = pd.to_numeric(df["StockMes"], errors="coerce")
    df["TiempoReposicionDias"] = pd.to_numeric(df["TiempoReposicionDias"], errors="coerce")

    # Features temporales
    df["anio"] = df["Fechaventa"].dt.year
    df["mes"] = df["Fechaventa"].dt.month
    df["dia_semana"] = df["Fechaventa"].dt.dayofweek
    df["semana_mes"] = df["Fechaventa"].dt.day // 7 + 1
    df["es_fin_de_mes"] = df["Fechaventa"].dt.is_month_end.astype(int)
    df["Precio_log"] = np.log1p(df["PrecioVenta"])

    # Lags y medias móviles
    grp = df.groupby("CodArticulo", observed=True)
    df["lag_1d"] = grp["CantidadVendida"].shift(1)
    df["lag_7d"] = grp["CantidadVendida"].shift(7)
    df["ma_7d"] = grp["CantidadVendida"].shift(1).rolling(7).mean()
    df["ma_14d"] = grp["CantidadVendida"].shift(1).rolling(14).mean()
    df["ma_30d"] = grp["CantidadVendida"].shift(1).rolling(30).mean()
    df["rolling_std_7d"] = grp["CantidadVendida"].shift(1).rolling(7).std()

    df = df.dropna(subset=["lag_7d", "ma_7d", "ma_14d", "ma_30d", "rolling_std_7d"])

    # Selección de variables
    X = df[[
        "CodArticulo", "Temporada",
        "anio", "mes", "dia_semana", "semana_mes", "es_fin_de_mes",
        "lag_1d", "lag_7d", "ma_7d", "ma_14d", "ma_30d", "rolling_std_7d",
        "Promocion", "Precio_log", "DiaFestivo", "EsDomingo", "TiendaCerrada"
    ]]

    df["Pred"] = modelo.predict(X)

    # Agregados y alertas
    Z = 1.28  # 90% servicio
    d_media = df.groupby("CodArticulo", observed=True)["Pred"].mean()
    d_sigma = df.groupby("CodArticulo", observed=True)["CantidadVendida"].apply(robust_sigma)
    sku_stats = df.groupby("CodArticulo", observed=True).agg(
        StockMes=("StockMes", "last"),
        horizon=("TiempoReposicionDias", "first")
    )

    alerta = pd.concat([d_media, d_sigma], axis=1, keys=["d_media", "d_sigma"]).join(sku_stats)
    alerta["seguridad"] = Z * alerta["d_sigma"] * np.sqrt(alerta["horizon"])
    alerta["stock_objetivo"] = (alerta["d_media"] * alerta["horizon"] + alerta["seguridad"]).round()

    alerta["dias_cobertura"] = (alerta["StockMes"] / alerta["d_media"]).round(1)
    alerta["porcentaje_sobrestock"] = ((alerta["StockMes"] - alerta["stock_objetivo"]) / alerta["stock_objetivo"]).round(3)
    alerta["indice_riesgo_quiebre"] = (alerta["StockMes"] / alerta["seguridad"]).round(2)

    alerta["Estado"] = np.select(
        [
            alerta["StockMes"] < alerta["seguridad"],
            alerta["StockMes"] > 1.3 * alerta["stock_objetivo"]
        ],
        ["Quiebre Potencial", "Sobre-stock"],
        default="OK"
    )

    alerta["Accion"] = np.select(
        [
            alerta["Estado"] == "Quiebre Potencial",
            alerta["Estado"] == "Sobre-stock"
        ],
        [
            "Revisar forecast y activar orden de compra",
            "Evaluar rebaja de precio o promoción"
        ],
        default="Monitorear"
    )

    alerta = alerta.reset_index()

    return alerta[[
        "CodArticulo", "d_media", "d_sigma", "StockMes", "horizon",
        "seguridad", "stock_objetivo", "dias_cobertura",
        "porcentaje_sobrestock", "indice_riesgo_quiebre",
        "Estado", "Accion"
    ]]

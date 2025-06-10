import pandas as pd
import numpy as np
import joblib
from pathlib import Path

# Ruta relativa del modelo entrenado
MODEL_PATH = Path("modelo_xgb_sku_global.joblib")
modelo = joblib.load(MODEL_PATH)

def robust_sigma(group: pd.Series) -> float:
    """
    Devuelve desviación estándar robusta para las últimas 30 ventas del SKU.
    """
    last = group.tail(30)
    sigma = last.std(ddof=0)
    if np.isnan(sigma):
        sigma = group.std(ddof=0)
    return 0.0 if np.isnan(sigma) else sigma

def procesar_prediccion(df: pd.DataFrame) -> pd.DataFrame:
    # Asegurar tipos
    df["Fechaventa"] = pd.to_datetime(df["Fechaventa"])
    df["CodArticulo"] = df["CodArticulo"].astype("category")
    df["Temporada"] = df["Temporada"].astype("category")
    df["TipoProducto"] = df["TipoProducto"].astype("category")

    # Variables de calendario
    df["anio"]       = df["Fechaventa"].dt.year
    df["mes"]        = df["Fechaventa"].dt.month
    df["dia_semana"] = df["Fechaventa"].dt.dayofweek
    df["dia_mes"]    = df["Fechaventa"].dt.day

    # Horizonte (Nacional: 90d, Exterior: 180d)
    df["horizon"] = (
        df["TipoProducto"]
          .str.strip()
          .str.capitalize()
          .map({"Nacional": 90, "Exterior": 180})
          .astype(int)
    )

    # Calcular lags
    df = df.sort_values(["CodArticulo", "Fechaventa"])
    grp = df.groupby("CodArticulo", observed=True)
    df["lag_1d"] = grp["CantidadVendida"].shift(1)
    df["lag_7d"] = grp["CantidadVendida"].shift(7)
    df["ma_7d"]  = grp["CantidadVendida"].shift(1).rolling(7).mean()
    df = df.dropna(subset=["lag_7d", "ma_7d"]).reset_index(drop=True)

    # Seleccionar columnas para predicción
    X_cols = [
        "CodArticulo", "Temporada", "TipoProducto",
        "anio", "mes", "dia_semana", "dia_mes",
        "lag_1d", "lag_7d", "ma_7d"
    ]
    X = df[X_cols]
    df["Pred"] = modelo.predict(X)

    # Agrupaciones por SKU
    d_media = df.groupby("CodArticulo", observed=True)["Pred"].mean()
    d_sigma = df.groupby("CodArticulo", observed=True)["CantidadVendida"].apply(robust_sigma)

    sku_stats = df.groupby("CodArticulo", observed=True).agg(
        StockMes=("StockMes", "mean"),
        TipoProducto=("TipoProducto", "first"),
        CantidadVendida=("CantidadVendida", "sum"),
        horizon=("horizon", "first")
    )

    # Cálculo final
    Z = 1.28
    alert = pd.concat([d_media, d_sigma], axis=1, keys=["d_media", "d_sigma"]).join(sku_stats)

    alert["seguridad"] = Z * alert["d_sigma"] * np.sqrt(alert["horizon"])
    alert["stock_objetivo"] = (alert["d_media"] * alert["horizon"] + alert["seguridad"]).round()

    alert["diferencia_vs_objetivo"] = alert["StockMes"] - alert["stock_objetivo"]
    alert["porcentaje_desviacion"] = (
        (alert["diferencia_vs_objetivo"] / alert["stock_objetivo"]) * 100
    ).round(2)

    alert["Estado"] = np.select(
        [alert["StockMes"] < alert["stock_objetivo"] * 0.9,  # menos de 90% del necesario
        alert["StockMes"] > 1.1 * alert["stock_objetivo"]],  # más del 110%
        ["Quiebre Potencial", "Sobre-stock"],
        default="OK"
    )

    alert["DiasDuracionStock"] = (alert["StockMes"] / alert["d_media"]).round(1)
    alert["DiasDuracionStock"] = alert["DiasDuracionStock"].replace([np.inf, -np.inf], np.nan).fillna(0)

    alert = alert.reset_index()

    alert = alert.rename(columns={
        "CodArticulo": "Producto",
        "TipoProducto": "Tipo",
        "CantidadVendida": "Ventas_Totales",
        "StockMes": "Stock_Actual",
        "d_media": "Demanda_Diaria_Promedio",
        "stock_objetivo": "Stock_Recomendado",
        "diferencia_vs_objetivo": "Diferencia",
        "porcentaje_desviacion": "Porcentaje_Desviacion",
        "DiasDuracionStock": "Dias_Estimados",
        "Estado": "Estado"
    })

    return alert[[
    "Producto", "Tipo", "Ventas_Totales", "Demanda_Diaria_Promedio",
    "Stock_Actual", "Stock_Recomendado", "Dias_Estimados",
    "Diferencia", "Porcentaje_Desviacion", "Estado"
    ]]



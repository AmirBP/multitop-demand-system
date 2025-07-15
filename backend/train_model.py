import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)
MODEL_PATH = OUTPUT_DIR / "modelo_xgb_sku_global.joblib"

def entrenar_modelo(df: pd.DataFrame) -> dict:
    # Tipado robusto
    binarias = ["Promocion", "DiaFestivo", "EsDomingo", "TiendaCerrada"]
    for col in binarias:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["Fechaventa"] = pd.to_datetime(df["Fechaventa"], errors="coerce", dayfirst=True)
    df = df.dropna(subset=["Fechaventa"])
    df["CodArticulo"] = df["CodArticulo"].astype("category")
    df["Temporada"] = df["Temporada"].astype("category")
    df["PrecioVenta"] = pd.to_numeric(df["PrecioVenta"], errors="coerce")
    df["CantidadVendida"] = pd.to_numeric(df["CantidadVendida"], errors="coerce")
    df["StockMes"] = pd.to_numeric(df["StockMes"], errors="coerce")
    df["TiempoReposicionDias"] = pd.to_numeric(df["TiempoReposicionDias"], errors="coerce")

    df = df.sort_values(["CodArticulo", "Fechaventa"])

    # Features
    df["anio"] = df["Fechaventa"].dt.year
    df["mes"] = df["Fechaventa"].dt.month
    df["dia_semana"] = df["Fechaventa"].dt.dayofweek
    df["semana_mes"] = df["Fechaventa"].dt.day // 7 + 1
    df["es_fin_de_mes"] = df["Fechaventa"].dt.is_month_end.astype(int)
    df["Precio_log"] = np.log1p(df["PrecioVenta"])

    grp = df.groupby("CodArticulo", observed=True)
    df["lag_1d"] = grp["CantidadVendida"].shift(1)
    df["lag_7d"] = grp["CantidadVendida"].shift(7)
    df["ma_7d"] = grp["CantidadVendida"].shift(1).rolling(7).mean()
    df["ma_14d"] = grp["CantidadVendida"].shift(1).rolling(14).mean()
    df["ma_30d"] = grp["CantidadVendida"].shift(1).rolling(30).mean()
    df["rolling_std_7d"] = grp["CantidadVendida"].shift(1).rolling(7).std()

    df = df.dropna(subset=["lag_7d", "ma_7d", "ma_14d", "ma_30d", "rolling_std_7d"]).reset_index(drop=True)

    # Split temporal
    cutoff = "2024-10-01"
    train = df[df["Fechaventa"] < cutoff]
    test = df[df["Fechaventa"] >= cutoff]

    y_tr, y_te = train["CantidadVendida"], test["CantidadVendida"]
    X_cols = [
        "CodArticulo", "Temporada",
        "anio", "mes", "dia_semana", "semana_mes", "es_fin_de_mes",
        "lag_1d", "lag_7d", "ma_7d", "ma_14d", "ma_30d", "rolling_std_7d",
        "Promocion", "Precio_log", "DiaFestivo", "EsDomingo", "TiendaCerrada"
    ]
    X_tr, X_te = train[X_cols], test[X_cols]

    # X_tr["CodArticulo"] = X_tr["CodArticulo"].astype(str)
    X_tr.loc[:, "CodArticulo"] = X_tr["CodArticulo"].astype(str)
    # X_tr["Temporada"] = X_tr["Temporada"].astype(str)
    X_tr.loc[:, "Temporada"] = X_tr["Temporada"].astype(str)
    X_te["CodArticulo"] = X_te["CodArticulo"].astype(str)
    X_te["Temporada"] = X_te["Temporada"].astype(str)

    # Entrenamiento
    pipe = Pipeline([
        ("prep", ColumnTransformer([
            ("ohe", OneHotEncoder(handle_unknown="ignore"), ["CodArticulo", "Temporada"])
        ], remainder="passthrough")),
        ("xgb", XGBRegressor(
            n_estimators=500,
            learning_rate=0.03,
            max_depth=6,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_lambda=1.0,
            reg_alpha=0.5,
            objective="reg:squarederror",
            random_state=42
        ))
    ])

    pipe.fit(X_tr, y_tr)
    pred = pipe.predict(X_te)

    joblib.dump(pipe, MODEL_PATH)

    mae = round(mean_absolute_error(y_te, pred), 2)

    # Feature importances
    imp = pd.DataFrame({
        "feature": pipe.named_steps["prep"].get_feature_names_out(),
        "gain": pipe.named_steps["xgb"].feature_importances_
    }).sort_values("gain", ascending=False)

    # Guardar CSV
    imp.to_csv(OUTPUT_DIR / "importancia_features.csv", index=False)

    # Generar alerta
    def robust_sigma(group):
        last = group.tail(30)
        sigma = last.std(ddof=0)
        return 0.0 if np.isnan(sigma) else sigma

    df_pred = test.copy()
    df_pred["Pred"] = pred

    d_media = df_pred.groupby("CodArticulo")["Pred"].mean()
    d_sigma = df.groupby("CodArticulo")["CantidadVendida"].apply(robust_sigma)
    sku_stats = df.groupby("CodArticulo").agg(
        StockMes=("StockMes", "last"),
        horizon=("TiempoReposicionDias", "first")
    )

    Z = 1.28
    alert = pd.concat([d_media, d_sigma], axis=1, keys=["d_media", "d_sigma"]).join(sku_stats)
    alert["seguridad"] = Z * alert["d_sigma"] * np.sqrt(alert["horizon"])
    alert["stock_objetivo"] = (alert["d_media"] * alert["horizon"] + alert["seguridad"]).round()

    alert["Estado"] = np.select(
        [alert["StockMes"] < alert["seguridad"],
         alert["StockMes"] > 1.3 * alert["stock_objetivo"]],
        ["Quiebre Potencial", "Sobre-stock"],
        default="OK"
    )

    alert = alert.reset_index()
    alert.to_csv(OUTPUT_DIR / "alerta_stock_global.csv", index=False)

    df_plot = df_pred[["Fechaventa", "CodArticulo", "CantidadVendida", "Pred"]].dropna()
    df_plot = df_plot.rename(columns={"Pred": "Prediccion"})

    plot_data = (
        df_plot.groupby("Fechaventa", observed=True)
        .agg(real=("CantidadVendida", "sum"), predicho=("Prediccion", "sum"))
        .reset_index()
        .sort_values("Fechaventa")
    )

    plot_data["Fechaventa"] = plot_data["Fechaventa"].dt.strftime("%Y-%m-%d")

    # Limpiar NaNs para JSON
    imp_clean = imp.replace({np.nan: None}).to_dict(orient="records")
    alert_clean = alert.replace({np.nan: None}).to_dict(orient="records")

    return {
        "mae": mae,
        "importancia": imp_clean,
        "alerta": alert_clean,
        "plot_data": plot_data.to_dict(orient="records")
    }


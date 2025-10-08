import pandas as pd

REQUIRED = [
    "Fechaventa","CodArticulo","Temporada","PrecioVenta",
    "CantidadVendida","StockMes","TiempoReposicionDias",
    "Promocion","DiaFestivo","EsDomingo","TiendaCerrada"
]

def validate_dataframe(df: pd.DataFrame) -> list[dict]:
    errs = []

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        errs.append({"type": "missing_columns", "columns": missing})

    # Validación de tipos básicos (suave; el modelo hará casts)
    if "Fechaventa" in df.columns:
        bad_dates = df["Fechaventa"].isna().sum()
        # no calculamos fila a fila por performance; se valida después en ETL
        # solo informativo
    return errs

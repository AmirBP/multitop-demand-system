import base64
import io
import pandas as pd
import numpy as np
from typing import Dict, List
from app.repositories.predictions_repo import get_job_rows, set_job_mae

def _mae(y_true, y_pred):
    return float(np.mean(np.abs(np.array(y_true) - np.array(y_pred))))

def _mape(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mask = y_true != 0
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])))

def compare_with_real(job_id: str, ventas_real_csv_base64: str | None, nivel: str) -> Dict:
    preds = pd.DataFrame(get_job_rows(job_id))
    if preds.empty:
        return {"global": {"MAE": float("nan"), "MAPE": float("nan")}, "por_sku": [], "observaciones": "No hay predicciones."}

    if ventas_real_csv_base64:
        raw = base64.b64decode(ventas_real_csv_base64)
        real_df = pd.read_csv(io.BytesIO(raw))
    else:
        raise ValueError("Debe adjuntar ventas reales en base64 para la demo sin BD.")

    # esperamos columnas CodArticulo, Fechaventa, CantidadVendida
    real_df["CodArticulo"] = real_df["CodArticulo"].astype(str)

    # En esta demo, no tenemos series por fecha en preds; usamos d_media como pronóstico.
    merged = preds[["CodArticulo","d_media"]].merge(
        real_df.groupby("CodArticulo", as_index=False)["CantidadVendida"].sum(),
        on="CodArticulo", how="inner"
    ).rename(columns={"d_media": "Pred", "CantidadVendida": "Real"})

    mae = _mae(merged["Real"], merged["Pred"])
    mape = _mape(merged["Real"], merged["Pred"])

    set_job_mae(job_id, mae)

    por_sku = merged.assign(MAE=lambda x: np.abs(x["Real"]-x["Pred"]),
                            APE=lambda x: np.where(x["Real"]!=0, np.abs((x["Real"]-x["Pred"])/x["Real"]), np.nan)
                            ).to_dict(orient="records")

    return {
        "global": {"MAE": round(mae,3), "MAPE": round(mape,3) if np.isfinite(mape) else None},
        "por_sku": por_sku,
        "observaciones": "Comparación por agregación de periodo."
    }

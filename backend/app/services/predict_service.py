import pandas as pd
from typing import Dict, Tuple, List
from ml.model_prediction import procesar_prediccion_global
from app.services.etl_service import limpiar_df

def predict_from_df(df: pd.DataFrame, filtros: Dict) -> Tuple[Dict[str,int], List[dict]]:
    df = limpiar_df(df, filtros=filtros)
    resultado = procesar_prediccion_global(df)
    resumen = resultado["Estado"].value_counts().to_dict()
    predicciones = resultado.to_dict(orient="records")
    return resumen, predicciones

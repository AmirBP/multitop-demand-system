import pandas as pd
from ml.train_model import entrenar_modelo
from app.services.etl_service import limpiar_df

def train_from_df(df: pd.DataFrame, tuning: bool = False) -> dict:
    # Si deseas, aquí puedes aplicar tuning condicional
    df = limpiar_df(df)
    out = entrenar_modelo(df)
    # podrías adjuntar hiperparámetros usados si tuning=True
    return out

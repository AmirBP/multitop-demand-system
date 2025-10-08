import pandas as pd
from typing import Optional, Dict

def limpiar_df(df: pd.DataFrame, filtros: Optional[Dict] = None) -> pd.DataFrame:
    # filtros (HU007)
    if filtros:
        for k, v in filtros.items():
            if v and k in df.columns:
                df = df[df[k] == v]

    # tu pipeline ya hace el tipado y limpieza; aquí solo retornamos
    return df.reset_index(drop=True)

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from io import StringIO
from model_prediction import procesar_prediccion

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/prediction")
async def predecir(file: UploadFile = File(...)):
    contenido = await file.read()
    df = pd.read_csv(StringIO(contenido.decode("utf-8")))
    resultado = procesar_prediccion(df)

    resumen = resultado["Estado"].value_counts().to_dict()
    predicciones = resultado.to_dict(orient="records")

    return {"predictions": predicciones, "summary": resumen}

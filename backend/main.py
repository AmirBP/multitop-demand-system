from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from io import StringIO
from train_model import entrenar_modelo
from model_prediction import procesar_prediccion_global  

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/train-model")
async def entrenar(file: UploadFile = File(...)):
    contenido = await file.read()
    # df = pd.read_csv(StringIO(contenido.decode("utf-8")))
    df = pd.read_csv(StringIO(contenido.decode("utf-8")), low_memory=False)
    resultado = entrenar_modelo(df)

    return resultado

@app.post("/api/prediction")
async def predecir(file: UploadFile = File(...)):
    contenido = await file.read()
    df = pd.read_csv(StringIO(contenido.decode("utf-8")))
    resultado = procesar_prediccion_global(df)

    resumen = resultado["Estado"].value_counts().to_dict()
    predicciones = resultado.to_dict(orient="records")

    return {"predictions": predicciones, "summary": resumen}

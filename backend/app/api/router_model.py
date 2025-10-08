from fastapi import APIRouter, UploadFile, File
from io import StringIO
import pandas as pd
from app.schemas import TrainResponse
from app.services.train_service import train_from_df

router = APIRouter()

@router.post("/model/train", response_model=TrainResponse)
async def train_model(file: UploadFile = File(...), tuning: bool = False):
    df = pd.read_csv(StringIO((await file.read()).decode("utf-8")), low_memory=False)
    out = train_from_df(df, tuning=tuning)
    return TrainResponse(**out)

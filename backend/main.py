from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import joblib


import preprocessing 

app = FastAPI(title="Customer Spending Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


model = joblib.load("model_pipeline.pkl")


class CustomerData(BaseModel):
    Year_Birth: float
    Education: str
    Marital_Status: str
    Income: Optional[float] = None
    Kidhome: float
    Teenhome: float
    Dt_Customer: str
    Recency: float
    NumDealsPurchases: float
    NumWebPurchases: float
    NumCatalogPurchases: float
    NumStorePurchases: float
    NumWebVisitsMonth: float
    AcceptedCmp3: float
    AcceptedCmp4: float
    AcceptedCmp5: float
    AcceptedCmp1: float
    AcceptedCmp2: float
    Complain: float
    Response: float

@app.post("/predict")
def predict_spending(data: CustomerData):
    try:
        df = pd.DataFrame([data.model_dump()])
        prediction = model.predict(df)
        return {"Total_Spent": float(prediction[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
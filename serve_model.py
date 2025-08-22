import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Load the model
model_path = 'fraud_prevention_model.pt'
model = torch.jit.load(model_path)
model.eval()

class TransactionRequest(BaseModel):
    amount: float
    time: int
    mismatch: int
    frequency: int


@app.post("/predict")
async def predict(featureset: TransactionRequest):
    try:
        # Assume input is already normalized
        features_tensor = torch.tensor([[
            featureset.amount,
            featureset.time, 
            featureset.mismatch,
            featureset.frequency
        ]], dtype=torch.float32)


        with torch.no_grad():
            output = model(features_tensor)
            prob = torch.sigmoid(output).item()
            prediction = bool(prob > 0.5)

        return {"fraud_probability": prob, "is_fraud": prediction}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# To run: fastapi dev serve_model.py
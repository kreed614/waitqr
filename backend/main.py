import os
import stripe
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

# Load .env only for local development
load_dotenv()

# Configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")

app = FastAPI()

# --- CORS SETTINGS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELS ---
class MenuItem(BaseModel):
    id: str
    name: str
    price: int 
    quantity: int

class OrderRequest(BaseModel):
    items: List[MenuItem]

# --- ENDPOINTS ---
@app.get("/")
def root():
    return {
        "message": "WaitQr API is online",
        "environment": "production" if os.getenv("VERCEL") else "development"
    }

@app.post("/create-payment-intent")
async def create_payment(order: OrderRequest):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe Secret Key not configured.")
        
    try:
        # Calculate total in cents
        total_amount = sum(item.price * item.quantity for item in order.items)

        # Create the PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=total_amount,
            currency="usd",
            automatic_payment_methods={"enabled": True},
            metadata={"integration_check": "waitqr_pilot"},
        )

        return {
            "clientSecret": intent.client_secret,
            "publishableKey": STRIPE_PUBLISHABLE_KEY
        }
    except Exception as e:
        # Vercel logs this to their 'Logs' tab
        print(f"Stripe Error: {e}") 
        raise HTTPException(status_code=400, detail=str(e))

# Note: No uvicorn.run here. Vercel's Serverless Functions handle the invocation.
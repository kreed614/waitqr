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
async def create_payment(order: OrderRequest, platform: str = "mobile"):
    try:
        total_amount = sum(item.price * item.quantity for item in order.items)

        if platform == "web":
            # Create a Checkout Session for the browser
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': 'The Blue Light Order'},
                        'unit_amount': total_amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='https://your-app-url.com/success',
                cancel_url='https://your-app-url.com/cart',
            )
            return {"url": session.url}

        # Original Mobile Logic
        intent = stripe.PaymentIntent.create(
            amount=total_amount,
            currency="usd",
            automatic_payment_methods={"enabled": True},
        )
        return {
            "clientSecret": intent.client_secret,
            "publishableKey": STRIPE_PUBLISHABLE_KEY
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Note: No uvicorn.run here. Vercel's Serverless Functions handle the invocation.

import os
import stripe
from fastapi import FastAPI, HTTPException, Request # Added Request here
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

# Load .env only for local development
load_dotenv()

# Configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")

app = FastAPI() # Vercel looks for this variable at the top level

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
async def create_payment(request: Request):
    try:
        body = await request.json()
        items = body.get("items", [])
        platform = body.get("platform", "mobile")

        # Calculate total in cents
        total_amount = sum(item['price'] * item['quantity'] for item in items)

        if platform == "web":
            # --- WEB LOGIC: Create a Checkout Session ---
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': 'WaitQr Order'},
                        'unit_amount': total_amount,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='https://waitqr.vercel.app/success',
                cancel_url='https://waitqr.vercel.app/cart',
            )
            return {"url": session.url}
        
        else:
            # --- MOBILE LOGIC: Create Payment Intent ---
            intent = stripe.PaymentIntent.create(
                amount=total_amount,
                currency="usd",
                automatic_payment_methods={"enabled": True},
            )
            return {"clientSecret": intent.client_secret}

    except Exception as e:
        print(f"Stripe Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

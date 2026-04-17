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
async def create_payment(request: Request):
    body = await request.json()
    items = body.get("items", [])
    platform = body.get("platform", "mobile") # Default to mobile if not sent

    # Calculate total in cents
    total_amount = sum(item['price'] * item['quantity'] for item in items)

    if platform == "web":
        # --- WEB LOGIC: Create a Checkout Session ---
        try:
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
                # Update these to your actual Vercel app URL
                success_url='https://waitqr.vercel.app/success',
                cancel_url='https://waitqr.vercel.app/cart',
            )
            return {"url": session.url}
        except Exception as e:
            print(f"Stripe Web Error: {e}")
            return {"error": str(e)}, 400
    
    else:
        # --- MOBILE LOGIC: Create Payment Intent (What's happening now) ---
        try:
            intent = stripe.PaymentIntent.create(
                amount=total_amount,
                currency="usd",
                automatic_payment_methods={"enabled": True},
            )
            return {"clientSecret": intent.client_secret}
        except Exception as e:
            print(f"Stripe Mobile Error: {e}")
            return {"error": str(e)}, 400
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Note: No uvicorn.run here. Vercel's Serverless Functions handle the invocation.

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
    data = await request.json()
    items = data.get('items')
    platform = data.get('platform') # 'web' or 'mobile'

    if platform == 'web':
        # --- WEB: Create a Checkout Session ---
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': item['name']},
                        'unit_amount': item['price'],
                    },
                    'quantity': item['quantity'],
                } for item in items],
                mode='payment',
                success_url='https://your-site.vercel.app/success',
                cancel_url='https://your-site.vercel.app/cart',
            )
            return {"url": checkout_session.url}
        except Exception as e:
            return {"error": str(e)}, 400
    else:
        # --- MOBILE: Create a Payment Intent ---
        intent = stripe.PaymentIntent.create(
            amount=calculate_total(items),
            currency='usd',
        )
        return {"clientSecret": intent.client_secret}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Note: No uvicorn.run here. Vercel's Serverless Functions handle the invocation.

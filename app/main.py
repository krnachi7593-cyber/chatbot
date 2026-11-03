import os
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
from dotenv import load_dotenv

from .database import Base, engine, get_db, SessionLocal
from .models import User, Product, Conversation, Message, Order, CartItem
from .security import hash_password, verify_password
from .assistant import build_assistant_reply
from .catalog import search_products, product_to_dict

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="ShopMate AI", version="1.0.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("APP_SECRET_KEY", "dev-only-change-this-secret-before-deploying"),
    same_site="lax",
    https_only=os.getenv("COOKIE_SECURE", "false").lower() == "true"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"]
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def current_user(request: Request, db: Session):
    uid = request.session.get("user_id")
    if not uid:
        return None
    return db.query(User).filter(User.id == uid).first()

def require_user(request: Request, db: Session):
    user = current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Please sign in to continue.")
    return user

def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(Product).first():
            products = [
                Product(sku="SM-LAP-001", name="AeroBook 14 Laptop", category="Electronics", brand="Aero", price=58990, original_price=64990, rating=4.6, stock=12, description="Lightweight 14-inch laptop for study, work and everyday productivity.", features="16GB RAM; 512GB SSD; Full HD display; 10-hour battery", image_url="https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800"),
                Product(sku="SM-LAP-002", name="Creator Pro 15 Laptop", category="Electronics", brand="Nova", price=84990, original_price=92990, rating=4.7, stock=7, description="Performance laptop for creative work and demanding multitasking.", features="16GB RAM; 1TB SSD; dedicated graphics; 15.6-inch display", image_url="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800"),
                Product(sku="SM-PHN-001", name="PixelWave X Smartphone", category="Electronics", brand="PixelWave", price=32999, original_price=36999, rating=4.5, stock=20, description="Everyday smartphone with a bright display and versatile camera.", features="128GB storage; OLED display; 50MP camera; 5G", image_url="https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800"),
                Product(sku="SM-PHN-002", name="Orbit Max Smartphone", category="Electronics", brand="Orbit", price=45999, original_price=49999, rating=4.4, stock=9, description="Large-screen smartphone for entertainment, photography and productivity.", features="256GB storage; AMOLED; 108MP camera; 5G", image_url="https://images.unsplash.com/photo-1592899677977-9c10ca588bbd?w=800"),
                Product(sku="SM-AUD-001", name="Pulse ANC Headphones", category="Audio", brand="Pulse", price=2799, original_price=3999, rating=4.5, stock=34, description="Over-ear wireless headphones with active noise cancellation.", features="ANC; 40-hour battery; Bluetooth 5.3; foldable", image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800"),
                Product(sku="SM-AUD-002", name="AirBeat Wireless Earbuds", category="Audio", brand="AirBeat", price=1799, original_price=2499, rating=4.3, stock=50, description="Compact wireless earbuds for calls, music and commuting.", features="30-hour total battery; IPX4; touch controls; low-latency mode", image_url="https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?w=800"),
                Product(sku="SM-AUD-003", name="StudioSound Bluetooth Speaker", category="Audio", brand="StudioSound", price=3499, original_price=4299, rating=4.4, stock=18, description="Portable Bluetooth speaker with balanced sound and deep bass.", features="20W output; 12-hour battery; IP67; USB-C", image_url="https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800"),
                Product(sku="SM-WAT-001", name="FitTrack Smartwatch", category="Wearables", brand="FitTrack", price=3999, original_price=5499, rating=4.2, stock=22, description="Smartwatch for everyday activity tracking and notifications.", features="Heart-rate tracking; sleep tracking; GPS; 7-day battery", image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800"),
                Product(sku="SM-FAS-001", name="Urban Everyday Backpack", category="Fashion", brand="UrbanTrail", price=1299, original_price=1699, rating=4.6, stock=40, description="Versatile backpack for college, commuting and short trips.", features="24L capacity; padded laptop sleeve; water-resistant fabric", image_url="https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800"),
                Product(sku="SM-FAS-002", name="CloudWalk Running Shoes", category="Fashion", brand="CloudWalk", price=2499, original_price=2999, rating=4.4, stock=16, description="Lightweight running shoes with cushioned everyday comfort.", features="Breathable mesh; cushioned sole; flexible outsole", image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800"),
                Product(sku="SM-HOM-001", name="BrewMate Coffee Maker", category="Home", brand="BrewMate", price=2199, original_price=2799, rating=4.3, stock=11, description="Compact coffee maker for quick home brewing.", features="600ml capacity; reusable filter; auto shut-off", image_url="https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800"),
                Product(sku="SM-HOM-002", name="GlowDesk LED Lamp", category="Home", brand="GlowDesk", price=899, original_price=1199, rating=4.1, stock=29, description="Adjustable desk lamp for reading and focused study.", features="Three brightness levels; touch control; USB powered", image_url="https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800"),
            ]
            db.add_all(products)
            db.commit()

        demo = db.query(User).filter(User.email == "demo@shopmate.ai").first()
        if not demo:
            demo = User(name="Demo Shopper", email="demo@shopmate.ai", password_hash=hash_password("ShopMate123!"))
            db.add(demo)
            db.commit()
            db.refresh(demo)
        if not db.query(Order).filter(Order.user_id == demo.id).first():
            db.add_all([
                Order(user_id=demo.id, order_number="SM-20481", status="Shipped", carrier="ShopMate Logistics", tracking_number="SML882041", total=45999, estimated_delivery="2-3 business days", items_summary="1 × Orbit Max Smartphone"),
                Order(user_id=demo.id, order_number="SM-20317", status="Delivered", carrier="ShopMate Logistics", tracking_number="SML771902", total=2799, estimated_delivery="Delivered on 28 Oct 2026", items_summary="1 × Pulse ANC Headphones")
            ])
            db.commit()
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    seed_data()

@app.get("/health")
def health():
    return {"status": "ok", "service": "ShopMate AI"}

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    conversations = db.query(Conversation).filter(Conversation.user_id == user.id).order_by(desc(Conversation.updated_at)).all()
    products = db.query(Product).filter(Product.active.is_(True)).order_by(desc(Product.rating)).limit(4).all()
    return templates.TemplateResponse(request=request, name="index.html", context={
        "user": user, "conversations": conversations,
        "featured_products": [product_to_dict(p) for p in products]
    })

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth.html", context={"mode": "login", "error": None})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth.html", context={"mode": "register", "error": None})

@app.post("/auth/register")
def register(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    email = email.strip().lower()
    if len(name.strip()) < 2 or len(password) < 10 or "@" not in email:
        return templates.TemplateResponse(request=request, name="auth.html", context={"mode": "register", "error": "Enter a valid name and email. Password must be at least 10 characters."}, status_code=400)
    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse(request=request, name="auth.html", context={"mode": "register", "error": "An account with this email already exists."}, status_code=400)
    user = User(name=name.strip(), email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)

@app.post("/auth/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request=request, name="auth.html", context={"mode": "login", "error": "Invalid email or password."}, status_code=401)
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)

@app.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

@app.get("/api/me")
def me(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    return {"id": user.id, "name": user.name, "email": user.email}

@app.get("/api/products")
def products(q: str = "", category: str = "", max_price: float | None = None, db: Session = Depends(get_db)):
    return [product_to_dict(p) for p in search_products(db, q, category, max_price, 20)]

@app.get("/api/conversations")
def list_conversations(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    rows = db.query(Conversation).filter(Conversation.user_id == user.id).order_by(desc(Conversation.updated_at)).all()
    return [{"id": c.id, "title": c.title, "updated_at": c.updated_at.isoformat()} for c in rows]

@app.post("/api/conversations")
def create_conversation(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    c = Conversation(user_id=user.id, title="New conversation")
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "title": c.title}

@app.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    c = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {
        "id": c.id, "title": c.title,
        "messages": [{"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in c.messages]
    }

@app.patch("/api/conversations/{conversation_id}")
async def rename_conversation(conversation_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    payload = await request.json()
    title = str(payload.get("title", "")).strip()[:180]
    c = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if not title:
        raise HTTPException(status_code=400, detail="Title cannot be empty.")
    c.title = title
    db.commit()
    return {"id": c.id, "title": c.title}

@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    c = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    db.delete(c)
    db.commit()
    return {"deleted": True}

@app.post("/api/conversations/{conversation_id}/messages")
async def send_message(conversation_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    payload = await request.json()
    content = str(payload.get("content", "")).strip()
    if not content or len(content) > 4000:
        raise HTTPException(status_code=400, detail="Message must contain 1–4,000 characters.")
    c = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    prior = [{"role": m.role, "content": m.content} for m in c.messages[-10:]]
    db.add(Message(conversation_id=c.id, role="user", content=content))
    db.commit()
    reply, matched_products = build_assistant_reply(db, content, prior, user.id, user.name)
    db.add(Message(conversation_id=c.id, role="assistant", content=reply))
    if c.title == "New conversation":
        c.title = content[:55] + ("…" if len(content) > 55 else "")
    c.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "reply": reply,
        "products": matched_products,
        "conversation_id": c.id,
        "llm_enabled": os.getenv("LLM_ENABLED", "false").lower() == "true" and bool(os.getenv("GROQ_API_KEY"))
    }

@app.get("/api/orders")
def get_orders(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    orders = db.query(Order).filter(Order.user_id == user.id).order_by(desc(Order.created_at)).all()
    return [{"order_number": o.order_number, "status": o.status, "carrier": o.carrier,
             "tracking_number": o.tracking_number, "total": o.total,
             "estimated_delivery": o.estimated_delivery, "items_summary": o.items_summary} for o in orders]

@app.get("/api/cart")
def get_cart(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    rows = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    items = []
    for row in rows:
        p = row.product
        items.append({"id": row.id, "quantity": row.quantity, "product": product_to_dict(p)})
    return {"items": items, "count": sum(x["quantity"] for x in items)}

@app.post("/api/cart")
async def add_to_cart(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    payload = await request.json()
    product_id = int(payload.get("product_id", 0))
    quantity = max(1, min(int(payload.get("quantity", 1)), 10))
    product = db.query(Product).filter(Product.id == product_id, Product.active.is_(True)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    if product.stock < quantity:
        raise HTTPException(status_code=400, detail="Requested quantity is not available.")
    row = db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.product_id == product.id).first()
    if row:
        if row.quantity + quantity > product.stock:
            raise HTTPException(status_code=400, detail="Requested quantity exceeds available stock.")
        row.quantity += quantity
    else:
        db.add(CartItem(user_id=user.id, product_id=product.id, quantity=quantity))
    db.commit()
    return get_cart(request, db)

@app.delete("/api/cart/{item_id}")
def remove_cart_item(item_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    row = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    db.delete(row)
    db.commit()
    return {"deleted": True}

@app.get("/api/health")
def api_health():
    return {"status": "ok"}

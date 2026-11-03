from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base
def utcnow():
    return datetime.now(timezone.utc)
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    brand: Mapped[str] = mapped_column(String(80))
    price: Mapped[float] = mapped_column(Float)
    original_price: Mapped[float] = mapped_column(Float, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text)
    features: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(180), default="New conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    conversation = relationship("Conversation", back_populates="messages")
class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    order_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(40))
    carrier: Mapped[str] = mapped_column(String(80), default="ShopMate Logistics")
    tracking_number: Mapped[str] = mapped_column(String(80), default="")
    total: Mapped[float] = mapped_column(Float)
    estimated_delivery: Mapped[str] = mapped_column(String(80), default="To be confirmed")
    items_summary: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user = relationship("User", back_populates="orders")
class CartItem(Base):
    __tablename__ = "cart_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product")

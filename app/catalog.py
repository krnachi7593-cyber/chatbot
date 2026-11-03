from sqlalchemy import or_
from sqlalchemy.orm import Session
from .models import Product
def product_to_dict(p: Product):
    return {"id": p.id, "sku": p.sku, "name": p.name, "category": p.category, "brand": p.brand, "price": p.price, "original_price": p.original_price, "rating": p.rating, "stock": p.stock, "description": p.description, "features": p.features, "image_url": p.image_url}
def search_products(db: Session, query: str = "", category: str = "", max_price: float | None = None, limit: int = 8):
    q = db.query(Product).filter(Product.active.is_(True))
    if category:
        q = q.filter(Product.category.ilike(f"%{category}%"))
    if max_price is not None:
        q = q.filter(Product.price <= max_price)
    terms = [t.strip() for t in query.lower().split() if len(t.strip()) > 1]
    if terms:
        clauses = []
        for term in terms:
            like = f"%{term}%"
            clauses.extend([Product.name.ilike(like), Product.brand.ilike(like), Product.category.ilike(like), Product.description.ilike(like), Product.features.ilike(like)])
        q = q.filter(or_(*clauses))
    return q.order_by(Product.rating.desc(), Product.price.asc()).limit(limit).all()

# ShopMate AI — E-commerce Shopping Assistant

ShopMate AI is a Python full-stack, ChatGPT-style assistant focused on online retail. It helps customers discover products, compare options, find products within a budget, check demo orders, understand store policies, and manage a demo shopping cart.

## Features

- Account registration and login
- Persistent conversations and chat history
- Natural-language e-commerce assistant
- Product search and recommendations from a seeded catalogue
- Product comparison
- Budget-aware matching
- Demo order lookup
- Shipping, returns, refund, cancellation, warranty and payment-policy answers
- Add/remove items from a persistent cart
- Optional OpenAI LLM integration
- Responsive web interface

## Technology

- Python 3.11+
- FastAPI
- SQLAlchemy
- SQLite by default (PostgreSQL can be configured)
- Jinja2 templates
- HTML, CSS and vanilla JavaScript
- Optional OpenAI API integration

## Run locally (Windows)

```powershell
cd shopmate_ai
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## Run locally (macOS/Linux)

```bash
cd shopmate_ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## Demo account

- Email: `demo@shopmate.ai`
- Password: `ShopMate123!`

The demo account is seeded automatically on first startup with sample orders and products. Change or remove these demo credentials before deploying publicly.

## Optional LLM integration

The app works without an API key using its local e-commerce domain engine.

To enable OpenAI-powered conversational phrasing:

1. Create an API key through your model provider.
2. Put it in `.env` as `OPENAI_API_KEY=...`.
3. Set `LLM_ENABLED=true`.
4. Set `OPENAI_MODEL` to a model available to your API account.
5. Restart the server.

The local catalogue and policy engine remain the source of truth for product and store-specific facts. If the LLM call fails, the application falls back to the local domain engine.

## Project structure

```text
shopmate_ai/
├── app/
│   ├── main.py
│   ├── assistant.py
│   ├── catalog.py
│   ├── database.py
│   ├── models.py
│   ├── security.py
│   ├── templates/
│   └── static/
├── tests/
├── docs/
├── requirements.txt
├── .env.example
└── README.md
```

## API overview

- `GET /health`
- `GET /api/me`
- `GET /api/products?q=&category=&max_price=`
- `GET /api/conversations`
- `POST /api/conversations`
- `GET /api/conversations/{id}`
- `PATCH /api/conversations/{id}`
- `DELETE /api/conversations/{id}`
- `POST /api/conversations/{id}/messages`
- `GET /api/orders`
- `GET /api/cart`
- `POST /api/cart`
- `DELETE /api/cart/{item_id}`

Interactive API documentation: http://127.0.0.1:8000/docs

## Test

```bash
pytest -q
```

## Important limitations

This is a functional local/demo application, not a production-ready marketplace:
- Checkout and real payments are intentionally disabled.
- Product, inventory, order and tracking information are sample data.
- Order status is not connected to a real courier or commerce platform.
- The local assistant uses deterministic domain logic; advanced open-ended conversation requires enabling an LLM provider.
- The simple policy matcher is a starter knowledge retrieval implementation, not a production vector RAG pipeline.
- Before public deployment, add CSRF protection for form/session flows, rate limiting, secure secret management, robust session lifecycle controls, migrations, audit logging, upload scanning if uploads are added, and production-grade monitoring.

## Security notes

- Set a long random `APP_SECRET_KEY`.
- Set `COOKIE_SECURE=true` behind HTTPS.
- Configure `ALLOWED_ORIGINS` to your exact frontend origin(s).
- Replace the demo account and sample data before public release.
- Use PostgreSQL and managed object storage for production.
- Never commit `.env`.

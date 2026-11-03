# Deploy ShopMate AI on Render (Local AI mode)

## Included deployment files
- `render.yaml`: Render Blueprint for a Python web service and PostgreSQL database.
- `Dockerfile`: optional container deployment path.
- `/health`: health-check endpoint.
- Local assistant mode is enabled by default; no model API key is required.

## Recommended deployment: Render Blueprint

1. Put the project in a GitHub repository. Do not commit `.env`, database files, logs, or secrets.
2. Sign in to Render at https://dashboard.render.com/.
3. Connect your GitHub account when Render asks. Authorize access to only the ShopMate repository if possible.
4. In Render, choose **New + → Blueprint**.
5. Select the ShopMate repository and branch containing `render.yaml`.
6. Review the resources and environment variables in the Blueprint. The manifest creates a web service and a PostgreSQL database.
7. Click **Apply**. Render builds the service and provisions the database.
8. Wait until the service is Live. Open the generated `https://<service-name>.onrender.com` URL.
9. Verify `https://<service-name>.onrender.com/health` returns `{"status":"ok","service":"ShopMate AI"}`.
10. Open the app, register a new account, test catalogue search, conversation history, policy answers and cart.

## Environment variables

| Variable | Value / source | Required |
|---|---|---|
| `APP_SECRET_KEY` | Render-generated secret | Yes |
| `DATABASE_URL` | Render PostgreSQL connection string | Yes |
| `COOKIE_SECURE` | `true` | Yes on HTTPS |
| `LLM_ENABLED` | `true` | Enable Groq model |
| `GROQ_API_KEY` | Leave unset | No |
| `GROQ_MODEL` | `openai/gpt-oss-120b` (unused in local mode) | No |
| `ALLOWED_ORIGINS` | Exact deployed origin | Recommended |
| `PYTHON_VERSION` | `3.12.8` | Build pin |

Render provides `PORT` to web services; the start command binds to it.

## Account authorization / credentials required

- A Render account (sign-up can use email or a supported identity provider).
- A GitHub account and authorization to connect the repository to Render.
- Permission to create a Render web service and PostgreSQL database in the chosen workspace.
- No OpenAI key, payment gateway key, or customer credentials are needed for Local AI mode.
- If the Render workspace requires billing verification or a paid plan for the selected resource, the account owner must complete that step directly in Render.

Never share your Render password, GitHub password, personal access token, or API token in chat. Use Render's and GitHub's official authorization screens.

## Important production checks before launch

1. Confirm Render Blueprint's selected plan and any current free-tier limits before applying.
2. For reliable persistent data, use the attached PostgreSQL database, not SQLite on an ephemeral service filesystem.
3. The current sample seed data is illustrative. Replace demo content and demo account handling before public customer use.
4. Add CSRF protection, rate limiting, login lockout, password reset, email verification, audit logging and structured error monitoring before public production use.
5. The app's demo order data is not connected to a carrier or commerce platform; do not advertise real tracking.
6. The sample cart is not a checkout system; no real payments are collected.
7. Configure the exact Render URL in `ALLOWED_ORIGINS` after the service name is finalized. If the service name differs from `shopmate-ai`, update this variable in Render.
8. Review logs and test all routes after deploy.

## Current app compatibility note

The requirements file includes `psycopg[binary]` so SQLAlchemy can connect to Render PostgreSQL. The Groq SDK is required for live model mode. Set `GROQ_API_KEY`, `LLM_ENABLED=true`, `GROQ_MODEL=openai/gpt-oss-120b`, and `GROQ_WEB_SEARCH_ENABLED=true` in Render. Keep the key out of GitHub and `.env.example`. Browser search can retrieve selected public web sources for current product research; it does not crawl the whole internet or guarantee comprehensive coverage. Store-specific price, stock, order, and policy answers must continue to use the ShopMate database as the source of truth.


## Free-tier data warning (read before choosing a plan)

Render's current documentation says Free web services spin down after 15 minutes of inactivity and their local filesystem is ephemeral. Free Render Postgres databases expire 30 days after creation (with a 14-day grace period before deletion). The Blueprint currently selects Free plans as a low-cost demo starting point. For data that must survive beyond the demo window, select a paid PostgreSQL plan before deploying, or change the Blueprint database plan to a paid plan. Do not use the Free database for real customer data. See https://render.com/docs/free.


### Groq environment setup

In Render, open the `shopmate-ai` service, choose **Environment**, add `GROQ_API_KEY` with the replacement secret generated in Groq, and set the four variables listed above. Save and redeploy. Revoke any API key that has been pasted into chats, screenshots, Git commits, or logs.

# Local setup and deployment

## Local backend

Install `requirements.txt`, configure a local `.env` with the exact names used by the backend (`OPENAI_API_KEY`, `OPENAI_MODEL`, `DATABASE_URL`, and any additional tool/pricing settings), then run:

```bash
uvicorn server:app --reload
```

Check `http://localhost:8000/api/health` and `http://localhost:8000/docs`. Database tables must exist before database-dependent operations; use the setup in `src/database.py`. Keep secrets out of Git.

## Local frontend

```bash
python -m http.server 5500 --directory frontend
```

Open `http://localhost:5500`. Set the shared JavaScript API helper to use the local backend for local backend testing, or the deployed API for UI-only development. In both cases, the backend must permit the frontend's exact origin in CORS.

## Backend Vercel project

| Setting | Value |
| --- | --- |
| Repository | travel-advisor |
| Root directory | Repository root |
| Framework | FastAPI |
| Application | app in server.py |
| Secrets | Backend project environment variables |

Do not mount `StaticFiles(directory="public")` in the backend. The Python function may not include that directory, causing an import-time crash. Frontend static hosting is a separate deployment.

Current API base: `https://travel-advisor-api-omega.vercel.app`.

## Frontend Vercel project

| Setting | Value |
| --- | --- |
| Repository | Same repository |
| Root directory | frontend |
| Framework | Other / static HTML |
| Build command | Empty |
| Output directory | . |

Use the production API URL in the shared Fetch helper. This URL is public configuration, not a secret. Plain browser JavaScript cannot read a server `.env` directly.

## CORS

Configure `CORSMiddleware` after creating the FastAPI app. Allow the exact deployed frontend origin and the local origins you use. For the current routes, GET and POST are sufficient; JSON requests require Content-Type. Use credentials only if the authentication design requires them. CORS is not access control for non-browser clients.

## Redeployment and checks

Push to the connected branch and check the newest Vercel deployment's commit and Ready status. Environment-variable changes require a new deployment. Both projects may redeploy from the same push.

Verify health, `/docs`, saved-history reads, new conversation creation, chat, itinerary rendering, Markdown export, weather, currency, and usage reporting. Test one paid AI action deliberately rather than repeatedly retrying a failed request.

For a 500 response, inspect runtime logs. A successful health response alone does not validate Neon or the model provider. For CORS failures, verify exact origins, preflight responses, deployment protection, and the underlying backend error.

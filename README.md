# LinkedIn Event Autopost

Single-user tool: throw event updates/milestones in, AI turns them into a LinkedIn
post, you preview + edit, you approve, it publishes to your LinkedIn profile.

## What changed vs the chat draft (read this)

The original chat had two half-finished branches (a single-event version and a
multi-event `event_id` version) plus a bolt-on OAuth patch that didn't match
either storage schema. This zip is ONE consistent version, built off your final
confirmed decisions (API-driven, manual trigger, preview+approve, FastAPI, light
theme, simple storage, local-first). Also fixed two real bugs in the original code:

1. **Approve was discarding your edits.** `scheduler.process_input` always
   regenerated text via the LLM even after you edited the preview. Now it uses
   your edited `generated_text` if present.
2. **LinkedIn/Gemini SDKs were already outdated.** `/v2/shares` + `/v2/me` are
   deprecated — moved to the current `/rest/posts` + OpenID `/v2/userinfo` flow.
   `google-generativeai` is deprecated too — moved to `google-genai`, model
   `gemini-2.5-flash`.

**Images:** fully wired now. Pick a file in the "New Input" form → it uploads
to LinkedIn (register asset → PUT binary → `urn:li:image:...`) right after the
input is created, and gets attached automatically when you approve & post.

## Setup

### 1. LinkedIn Developer App

1. https://www.linkedin.com/developers/apps → Create app.
2. Products tab → add **"Sign In with LinkedIn using OpenID Connect"** and
   **"Share on LinkedIn"** (self-serve, no manual approval needed for posting to
   your own profile).
3. Auth tab → add redirect URL: `http://localhost:8000/callback`.
4. Copy Client ID and Client Secret.

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Fill `.env`:
- `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` (from step 1)
- `GEMINI_API_KEY` (from https://aistudio.google.com/apikey)
- Leave `LINKEDIN_ACCESS_TOKEN` / `LINKEDIN_PERSON_URN` blank — filled
  automatically after you connect LinkedIn from the UI.

Run it:

```bash
uvicorn main:app --reload
```

### 3. Frontend

Just open `frontend/index.html` in your browser. No build step.

## Flow

1. Open the app → click **Connect LinkedIn** → authorize.
2. Fill **Event Config** once (name, tagline, audience, tone, hashtags).
3. Add an **Input** whenever something happens (registrations crossed, judging
   done, winners announced, etc.) — or have your event platform call the API
   directly (see below).
4. Click **Generate Preview** on a pending input → AI drafts the post.
5. Edit the text if you want → **Approve & Post** → it goes live on LinkedIn.
6. Posted history shows under **Posts**.

## API reference

- `GET  /auth/linkedin` — get OAuth authorization URL
- `GET  /callback` — OAuth redirect target (handled automatically)
- `GET  /auth/status` — check if LinkedIn is connected
- `POST /event/config` / `GET /event/config`
- `POST /inputs` — create an input `{type, title, text, image_url?, priority}`
- `POST /inputs/{id}/image` — multipart file upload, attaches image URN to the input
- `GET  /inputs/pending`
- `POST /inputs/{id}/generate` — AI draft
- `POST /inputs/{id}/approve` — body `{generated_text?}` → publishes
- `GET  /posts`
- `POST /event/stats` — your platform pushes live stats, auto-creates an input
- `POST /event/milestone` — your platform pushes a milestone, auto-creates an input

Example: your event platform hits this whenever registrations cross a mark:

```bash
curl -X POST http://localhost:8000/event/milestone \
  -H "Content-Type: application/json" \
  -d '{"milestone_type": "registrations_crossed", "value": 300}'
```

That creates a pending input — you still preview + approve before it posts.

## Deploy later

- Backend → Render/Railway: build `pip install -r requirements.txt`, start
  `uvicorn main:app --host 0.0.0.0 --port $PORT`, set the same env vars, and
  update `LINKEDIN_REDIRECT_URI` + the app's redirect URL to the deployed URL.
- Frontend → any static host (Vercel/Netlify), just update `API_BASE` in `app.js`.

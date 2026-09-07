import secrets
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

import scheduler
from config import Config
from linkedin_client import upload_image
from llm_client import generate_linkedin_post
from oauth_client import exchange_code_for_token, get_authorization_url, get_person_urn
from storage import (
    add_input,
    get_all_posts,
    get_event_config,
    get_input,
    get_oauth_state,
    get_pending_inputs,
    get_stored_tokens,
    set_event_config,
    set_oauth_state,
    store_tokens,
    update_input,
)

app = FastAPI(title="LinkedIn Event Autopost")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def load_stored_oauth() -> None:
    # If we already connected LinkedIn in a previous run, restore the token
    # from db.json so a server restart doesn't force reconnecting.
    tokens = get_stored_tokens()
    if tokens:
        Config.LINKEDIN_ACCESS_TOKEN = tokens["access_token"]
        Config.LINKEDIN_PERSON_URN = tokens["person_urn"]


# ---------- Request/response models ----------

class InputCreate(BaseModel):
    type: str = "update"
    title: str
    text: str
    image_url: Optional[str] = None
    priority: str = "normal"


class ApproveInput(BaseModel):
    generated_text: Optional[str] = None


class EventConfigInput(BaseModel):
    event_name: str
    tagline: str
    audience: str
    tone: str
    default_hashtags: List[str]


class StatsInput(BaseModel):
    registrations: int
    submissions: int
    judging_round: int
    certificates_issued: int


class MilestoneInput(BaseModel):
    milestone_type: str  # e.g. "registrations_crossed", "judging_round_completed"
    value: int
    text_override: Optional[str] = None


# ---------- LinkedIn OAuth ----------

@app.get("/auth/linkedin")
def start_linkedin_auth():
    state = secrets.token_urlsafe(16)
    set_oauth_state(state)
    return RedirectResponse(get_authorization_url(state))


@app.get("/callback")
async def linkedin_callback(code: str, state: str):
    stored_state = get_oauth_state()
    if state != stored_state:
        raise HTTPException(status_code=400, detail="Invalid state")

    token_data = await exchange_code_for_token(code)
    access_token = token_data["access_token"]
    person_urn = await get_person_urn(access_token)

    store_tokens(access_token, person_urn)
    Config.LINKEDIN_ACCESS_TOKEN = access_token
    Config.LINKEDIN_PERSON_URN = person_urn

    return RedirectResponse(url="http://127.0.0.1:3000/index.html?connected=true")


@app.get("/auth/status")
def auth_status():
    tokens = get_stored_tokens()
    if tokens:
        return {"connected": True, "person_urn": tokens["person_urn"]}
    return {"connected": False}


# ---------- Event config ----------

@app.post("/event/config")
def configure_event(cfg: EventConfigInput):
    data = cfg.model_dump()
    set_event_config(data)
    return {"status": "configured", "config": data}


@app.get("/event/config")
def get_event_configuration():
    return get_event_config()


# ---------- Inputs (manual or from your event platform) ----------

@app.post("/inputs")
def create_input(inp: InputCreate):
    return add_input(inp.model_dump())


@app.get("/inputs/pending")
def list_pending_inputs():
    return get_pending_inputs()


@app.get("/inputs/{input_id}")
def get_input_detail(input_id: str):
    inp = get_input(input_id)
    if not inp:
        raise HTTPException(status_code=404, detail="Input not found")
    return inp


@app.post("/inputs/{input_id}/image")
async def attach_image(input_id: str, file: UploadFile = File(...)):
    inp = get_input(input_id)
    if not inp:
        raise HTTPException(status_code=404, detail="Input not found")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        image_urn = await upload_image(image_bytes, file.content_type or "image/jpeg")
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    update_input(input_id, {"image_url": image_urn})
    return {"input_id": input_id, "image_url": image_urn}


@app.post("/inputs/{input_id}/generate")
def generate_preview(input_id: str):
    inp = get_input(input_id)
    if not inp:
        raise HTTPException(status_code=404, detail="Input not found")
    post_text = generate_linkedin_post(inp)
    return {"input_id": input_id, "generated_text": post_text}


@app.post("/inputs/{input_id}/approve")
async def approve_and_post(input_id: str, body: ApproveInput = ApproveInput()):
    inp = get_input(input_id)
    if not inp:
        raise HTTPException(status_code=404, detail="Input not found")

    if body.generated_text:
        inp["generated_text"] = body.generated_text
        update_input(input_id, {"generated_text": body.generated_text})

    return await scheduler.process_input(inp)


@app.get("/posts")
def list_posts():
    return get_all_posts()


# ---------- Custom event-platform integration ----------
# Your live platform (registrations/submissions/judging/certificates) calls these
# directly; each call just creates a pending input like any manual one, which
# you then preview + approve from the UI same as everything else.

@app.post("/event/stats")
def submit_stats(stats: StatsInput):
    inp_data = {
        "type": "stats_update",
        "title": "Stats Update",
        "text": (
            f"Registrations: {stats.registrations} | "
            f"Submissions: {stats.submissions} | "
            f"Judging Round: {stats.judging_round} | "
            f"Certificates: {stats.certificates_issued}"
        ),
        "priority": "normal",
        "meta": stats.model_dump(),
    }
    return add_input(inp_data)


@app.post("/event/milestone")
def submit_milestone(milestone: MilestoneInput):
    text = milestone.text_override or (
        f"Milestone: {milestone.milestone_type} reached at value {milestone.value}"
    )
    inp_data = {
        "type": "milestone",
        "title": f"Milestone: {milestone.milestone_type}",
        "text": text,
        "priority": "high",
        "meta": milestone.model_dump(),
    }
    return add_input(inp_data)
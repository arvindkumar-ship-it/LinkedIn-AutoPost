import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
    LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
    LINKEDIN_REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/callback")

    # These get populated at runtime once OAuth is completed (see storage.get_stored_tokens
    # and main.py's startup hook). Leave blank in .env — no need to hardcode a token.
    LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN") or None
    LINKEDIN_PERSON_URN = os.getenv("LINKEDIN_PERSON_URN") or None

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    EVENT_NAME = os.getenv("EVENT_NAME", "HackFest 2026")
    EVENT_TAGLINE = os.getenv("EVENT_TAGLINE", "48-hour AI hackathon")
    EVENT_AUDIENCE = os.getenv("EVENT_AUDIENCE", "students, startups, AI engineers")
    EVENT_TONE = os.getenv("EVENT_TONE", "energetic, professional, slightly casual")
    DEFAULT_HASHTAGS = os.getenv("DEFAULT_HASHTAGS", "#HackFest2026,#AI,#Hackathon").split(",")

from google import genai

from config import Config
from storage import get_event_config

_client = genai.Client(api_key=Config.GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"


def generate_linkedin_post(input_data: dict) -> str:
    event_config = get_event_config()
    event_name = event_config.get("event_name", Config.EVENT_NAME)
    tagline = event_config.get("tagline", Config.EVENT_TAGLINE)
    audience = event_config.get("audience", Config.EVENT_AUDIENCE)
    tone = event_config.get("tone", Config.EVENT_TONE)
    default_hashtags = ", ".join(event_config.get("default_hashtags", Config.DEFAULT_HASHTAGS))

    prompt = f"""You are an expert LinkedIn content writer for tech events.

Event context:
- Event name: {event_name}
- Tagline: {tagline}
- Audience: {audience}
- Tone: {tone}
- Default hashtags: {default_hashtags}

Input data:
- Type: {input_data.get("type", "update")}
- Title: {input_data.get("title", "")}
- Text: {input_data.get("text", "")}
- Image present: {"Yes" if input_data.get("image_url") else "No"}

Task:
Create a LinkedIn post with:
- 1-2 line hook
- 2-4 short paragraphs describing the update in a story-like way
- Highlight any stats/metrics if present
- End with a soft call-to-action if relevant (e.g., "Stay tuned", "Register now")
- Add 3-5 relevant hashtags at the end (include some from default hashtags)

Keep it professional but human, energetic, and easy to read.
Output ONLY the post text, no extra explanations.
"""

    response = _client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return response.text.strip()

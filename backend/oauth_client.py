import httpx
from urllib.parse import urlencode

from config import Config

LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

# Modern LinkedIn apps use OpenID Connect (openid + profile) to identify the member,
# plus w_member_social to publish posts on their behalf. The old r_liteprofile /
# /v2/me route is deprecated for new apps.
LINKEDIN_SCOPE = "openid profile w_member_social"


def get_authorization_url(state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": Config.LINKEDIN_CLIENT_ID,
        "redirect_uri": Config.LINKEDIN_REDIRECT_URI,
        "scope": LINKEDIN_SCOPE,
        "state": state,
    }
    return f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> dict:
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": Config.LINKEDIN_REDIRECT_URI,
        "client_id": Config.LINKEDIN_CLIENT_ID,
        "client_secret": Config.LINKEDIN_CLIENT_SECRET,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(LINKEDIN_TOKEN_URL, data=payload)
        if resp.status_code != 200:
            print("LinkedIn token error:", resp.status_code, resp.text)
        resp.raise_for_status()
        return resp.json()


async def get_person_urn(access_token: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            LINKEDIN_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return f"urn:li:person:{data['sub']}"
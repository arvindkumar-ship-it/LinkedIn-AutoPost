from typing import Optional

import httpx

from config import Config

# LinkedIn deprecated /v2/shares and /v2/ugcPosts in favor of the versioned Posts API.
LINKEDIN_POSTS_URL = "https://api.linkedin.com/rest/posts"
LINKEDIN_IMAGES_URL = "https://api.linkedin.com/rest/images"
LINKEDIN_VERSION = "202601"  # required "Linkedin-Version" header, format YYYYMM


def _auth_headers() -> dict:
    token = Config.LINKEDIN_ACCESS_TOKEN
    if not token:
        raise RuntimeError(
            "LinkedIn not connected. Open the app, click 'Connect LinkedIn', "
            "authorize, then try again."
        )
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "Linkedin-Version": LINKEDIN_VERSION,
    }


async def upload_image(image_bytes: bytes, content_type: str = "image/jpeg") -> str:
    """Register + upload an image to LinkedIn, return its urn:li:image:... URN.

    Two-step LinkedIn Images API flow:
    1. POST /rest/images?action=initializeUpload -> get a pre-signed uploadUrl + URN.
    2. PUT the raw image bytes to that uploadUrl.
    The URN is usable in a post immediately after step 2 for normal-sized images.
    """
    person_urn = Config.LINKEDIN_PERSON_URN
    if not person_urn:
        raise RuntimeError(
            "LinkedIn not connected. Open the app, click 'Connect LinkedIn', "
            "authorize, then try again."
        )
    headers = _auth_headers()

    async with httpx.AsyncClient() as client:
        init_resp = await client.post(
            f"{LINKEDIN_IMAGES_URL}?action=initializeUpload",
            headers=headers,
            json={"initializeUploadRequest": {"owner": person_urn}},
        )
        if init_resp.status_code not in (200, 201):
            raise RuntimeError(
                f"LinkedIn image init error: {init_resp.status_code} {init_resp.text}"
            )
        value = init_resp.json()["value"]
        upload_url = value["uploadUrl"]
        image_urn = value["image"]

        put_resp = await client.put(
            upload_url,
            content=image_bytes,
            headers={
                "Authorization": headers["Authorization"],
                "Content-Type": content_type,
            },
        )
        if put_resp.status_code not in (200, 201):
            raise RuntimeError(
                f"LinkedIn image upload error: {put_resp.status_code} {put_resp.text}"
            )

    return image_urn


async def post_to_linkedin(text: str, image_url: Optional[str] = None) -> dict:
    person_urn = Config.LINKEDIN_PERSON_URN
    if not person_urn:
        raise RuntimeError(
            "LinkedIn not connected. Open the app, click 'Connect LinkedIn', "
            "authorize, then try again."
        )
    headers = _auth_headers()

    payload = {
        "author": person_urn,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    # image_url must already be a urn:li:image:... URN — call upload_image() first
    # (main.py's POST /inputs/{id}/image endpoint does this for you) to get one.
    if image_url and image_url.startswith("urn:li:image:"):
        payload["content"] = {"media": {"title": "", "id": image_url}}

    async with httpx.AsyncClient() as client:
        resp = await client.post(LINKEDIN_POSTS_URL, json=payload, headers=headers)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"LinkedIn API error: {resp.status_code} {resp.text}")
        post_urn = resp.headers.get("x-restli-id") or resp.headers.get("X-RestLi-Id")
        return {"status_code": resp.status_code, "post_urn": post_urn}

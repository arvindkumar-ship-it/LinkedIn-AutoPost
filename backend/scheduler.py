from linkedin_client import post_to_linkedin
from llm_client import generate_linkedin_post
from storage import add_post, update_input


async def process_input(input_data: dict) -> dict:
    # If the user already generated + edited a preview, use that text as-is.
    # (Regenerating here would silently throw away their edits.)
    post_text = input_data.get("generated_text") or generate_linkedin_post(input_data)

    linkedin_response = await post_to_linkedin(
        text=post_text,
        image_url=input_data.get("image_url"),
    )

    post_record = {
        "input_id": input_data["id"],
        "text": post_text,
        "image_url": input_data.get("image_url"),
        "linkedin_response": linkedin_response,
        "status": "posted",
    }
    add_post(post_record)
    update_input(input_data["id"], {"status": "posted", "post_id": post_record["id"]})

    return post_record

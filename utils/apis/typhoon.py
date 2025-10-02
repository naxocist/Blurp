from openai import OpenAI
from credentials import TYPHOON_API_KEY

from utils.apis.jikanv4 import get_anime_characters


client = OpenAI(api_key=TYPHOON_API_KEY, base_url="https://api.opentyphoon.ai/v1")


async def get_synopsis_clue(anime) -> str:
    mal_id = anime["mal_id"]
    characters = await get_anime_characters(mal_id)
    names = ", ".join([ch["character"]["name"] for ch in characters])

    task_en = f"Summarize and rephrase this anime's synopsis while ignoring these words '{names}' and other words that are possibly character names"
    synopsis = anime.synopsis
    content = task_en + synopsis
    response = client.chat.completions.create(
        model="typhoon-v2-70b-instruct",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful anime expert assistant.",
            },
            {"role": "user", "content": content},
        ],
    )

    synopsis_clue = response.choices[0].message.content

    return synopsis_clue or "Cannot generate synopsis clue 🥲"

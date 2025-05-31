from openai import OpenAI
from credentials import TYPHOON_API_KEY

from .jikanv4 import get_anime_characters

client = OpenAI(api_key=TYPHOON_API_KEY, base_url="https://api.opentyphoon.ai/v1")


async def get_synopsis_clue(anime) -> str:
    mal_id = anime.mal_id
    characters_data = (await get_anime_characters(mal_id)).data
    names = ", ".join([c.character.name for c in characters_data])

    task_th = f"สรุปเรื่องย่อของอนิเมะเรื่องนี้เป็นภาษาไทยโดยไม่ใช้คำว่า {names} หรือคำอื่น ๆ ที่มีโอกาสเป็นชื่อของตัวละครในเรื่อง เรื่องย่อมีดังนี้"
    task_en = f"Summarize this anime's synopsis without using these words '{names}' and other words that are possibly character names"
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

    return synopsis_clue

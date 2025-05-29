from typing import Union
from nekosbest import Client, Result
import lemminflect

client = Client()

# Gifs in nekos.best API is divided into two categories:
# 1. Actions to others (e.g., "hug", "kick")
# 2. Expressions (e.g., "happy", "think")

actions_to_others = [ 
  "baka", "bite", "cuddle", "dance",
  "facepalm", "feed", "handhold", "handshake",
  "highfive", "hug", "kick", "kiss",
  "pat", "peck", "poke", "punch",
  "slap", "tickle", "yeet"
]

# Expressions are also divided into two categories:
# 1. Verbs (e.g., "laugh", "nod")
# 2. Adjectives or non-verbs (e.g., "angry", "happy")

expressions = [
  "angry", "blush", "bored", "cry", "happy", "laugh", "lurk", "nod", "nom", 
  "nope", "pout", "run", "shoot", "shrug", "sleep", "smile", "smug", 
  "stare", "think", "thumbsup", "wave", "wink", "yawn"
]

print(f"There are total of {len(actions_to_others) + len(expressions)} nekosbest actions")

adjectives_or_non_verbs = ["angry", "bored", "happy", "smug", "thumbsup", "nope"]


# Convert a word to an "is" phrase
def to_is_phrase(word: str) -> str:
  if word in adjectives_or_non_verbs:
    return f"is {word}"
  inflected = lemminflect.getInflection(word, tag="VBG")

  if inflected:
    return f"is {inflected[0]}"
  return f"is {word}ing" 


# Get an image from nekos.best API based on the type and amount specified (default to 1).
async def get_img(type: str, amount: int = 1) -> Union[Result, list[Result]]:
  return await client.get_image(type, amount)

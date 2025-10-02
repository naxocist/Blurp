import lemminflect
from nekosbest import Client, Result

client = Client()

# 2 types of gifs in nekos.best API - self & other


other_actions_map = {
    "baka": "A calls B baka",
    "bite": "A bites B",
    "cuddle": "A cuddles B",
    "feed": "A feeds B",
    "handhold": "A holds B's hand",
    "handshake": "A shakes hands with B",
    "highfive": "A gives B a highfive",
    "hug": "A hugs B",
    "kick": "A kicks B",
    "kiss": "A kisses B",
    "nom": "A noms B",
    "pat": "A pats B",
    "peck": "A pecks B",
    "poke": "A pokes B",
    "punch": "A punches B",
    "shoot": "A shoots B",
    "slap": "A slaps B",
    "tickle": "A tickles B",
    "yeet": "A yeets B",
}
other_actions = [key for key in other_actions_map]


self_actions_map = {
    "angry": "A looks angry",
    "blush": "A blushes",
    "bored": "A looks bored",
    "cry": "A cries",
    "happy": "A looks happy",
    "nod": "A nods",
    "nom": "A noms noms..",
    "laugh": "A laughs",
    "lurk": "A lurks",
    "dance": "A dances",
    "facepalm": "A facepalms",
    "nope": "A says *nope*",
    "pout": "A pouts",
    "run": "A runs",
    "shrug": "A shrugs",
    "sleep": "A sleeps",
    "smile": "A smiles",
    "smug": "A looks smug",
    "stare": "A stares",
    "think": "A thinks",
    "thumbsup": "A gives a thumbs up",
    "wave": "A waves",
    "wink": "A winks",
    "yawn": "A yawns",
}
self_actions = [key for key in self_actions_map]


print(f"There are total of {len(other_actions) + len(self_actions)} nekosbest actions")


def get_phrase(word: str, A: str, B: str = "") -> str:
    if word in other_actions:
        return other_actions_map[word].replace("A", A).replace("B", B)

    return self_actions_map[word].replace("A", A)


async def get_img(type: str, amount: int = 1) -> Result | list[Result]:
    return await client.get_image(type, amount)

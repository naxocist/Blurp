from random import choice, randint

from HF import text_gen
from jikan import random_anime

def get_response(user_input: str) -> str:

    title, synopsis, names = random_anime()

    names_str = ""
    for n in names:
        names_str += f"\"{n}\", "

    setup = f"""Now, you are anime related bot helper. Generate 5 hints of the anime named {title} with following rules
                1. do not use these words [{names_str}]
                2. do not reveal the anime name
                """

    prompt = setup + synopsis

    print(prompt)

    res = text_gen(prompt) +  f"||{title}||"

    return res

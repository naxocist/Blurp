from dotenv import load_dotenv
import os

from huggingface_hub import InferenceClient


load_dotenv()
HF_TOKEN: str = os.getenv('HF_ACCESS_TOKEN')

def text_gen(prompt: str):

    model = 'mistralai/Mistral-7B-Instruct-v0.3'
    client = InferenceClient(token=HF_TOKEN, model=model)

    return client.text_generation(prompt=prompt, max_new_tokens=1000)





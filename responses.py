from random import choice, randint

def get_response(user_input: str) -> str:
    lowered: str = user_input.lower()

    if(lowered == ''):
        return 'Well, you\'re awfully silent..'

    if('hello' in lowered):
        return 'Hello there!'

    if('roll dice' in lowered):
        return f'You rolled: {randint(1, 6)}'
    
    return choice(['I do not understand..', 'What are you talking about?'])
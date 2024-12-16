from jikanpy import Jikan
import json


def format(data):
  return json.dumps(data, indent=4)


def random_anime():
  jikan = Jikan()
  data = jikan.random(type='anime')['data']
  # print(format(data))

  id = data['mal_id']
  title = data['title']
  synopsis = data['synopsis']

  characters = jikan.anime(id, extension='characters')['data']

  names = []

  for character in characters:
      name = character['character']['name']
      names.append(name)

  return title, synopsis, names

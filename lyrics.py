import requests, json, discord, re
from bs4 import BeautifulSoup

auth = "QvjH6ZEacPNNXoud80FUphH0nAEhwnv41gNYwSZaz_mcDo1NJMNf2aDhc6rW4X09"
genius = "https://api.genius.com"
search = genius + "/search"

class BearerAuth(requests.auth.AuthBase):
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + auth
        return r

class Lyrics():
    def SearchForLyrics(query):
        params = {
            'q': query
        }
        r = requests.get(search, params=params, auth=BearerAuth())
        rson = r.json()
        if rson["meta"]["status"] == 200:
            return rson["response"]["hits"]
        else:
            return None
    def GenerateEmbed(hits):
        embed=discord.Embed(title="Lyric Search Results", description="Type number in chat for correct song")
        for item in hits:
            embed.add_field(name=str(hits.index(item)+1), value=item["result"]["full_title"], inline=False)
        return embed    
    def lyrics_from_song_api_path(song_api_path):
        song_url = genius + song_api_path
        response = requests.get(song_url, params={'access_token':auth})
        json = response.json()
        path = json["response"]["song"]["path"]
        page_url = "https://genius.com" + path
        page = requests.get(page_url)
        html = BeautifulSoup(page.text.replace("<br/>", "\n"), "html.parser")
        lyrics = html.find("div", class_=re.compile("^lyrics$|Lyrics__Root")).get_text()
        lyrics = lyrics[:-29]
        return lyrics
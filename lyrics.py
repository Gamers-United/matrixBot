import requests, json, discord, re
from bs4 import BeautifulSoup
from config import settings as dsettings

class BearerAuth(requests.auth.AuthBase):
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + dsettings.genius_token
        return r

class Lyrics():
    def SearchForLyrics(query):
        params = {
            'q': query
        }
        r = requests.get(f"{dsettings.genius_api}{dsettings.genius_route_search}", params=params, auth=BearerAuth())
        rson = r.json()
        if rson["meta"]["status"] == 200:
            return rson["response"]["hits"]
        else:
            return None
    def GenerateEmbed(hits):
        embed=discord.Embed(title=dsettings.lyrics_search_result, description=dsettings.lyrics_search_description)
        for item in hits:
            embed.add_field(name=str(hits.index(item)+1), value=item["result"]["full_title"], inline=False)
        return embed
    def lyrics_from_song_api_path(song_api_path):
        song_url = dsettings.genius_api + song_api_path
        response = requests.get(song_url, params={'access_token':dsettings.genius_token})
        json = response.json()
        path = json["response"]["song"]["path"]
        page_url = dsettings.genius_api + path
        page = requests.get(page_url)
        html = BeautifulSoup(page.text.replace("<br/>", "\n"), "html.parser")
        lyrics = html.find("div", class_=re.compile("^lyrics$|Lyrics__Root")).get_text()
        lyrics = lyrics[:-29]
        return lyrics
    def ProduceLyrics(results, selection: int):
        lyrics = Lyrics.lyrics_from_song_api_path(results[selection]["result"]["api_path"])
        return discord.Embed(title="Lyrics for "+str(results[selection]["result"]["full_title"]), description=lyrics)
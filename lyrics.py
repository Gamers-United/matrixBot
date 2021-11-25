import requests, json, discord

auth = "QvjH6ZEacPNNXoud80FUphH0nAEhwnv41gNYwSZaz_mcDo1NJMNf2aDhc6rW4X09"
genius = "https://api.genius.com/"
search = genius + "search"

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
        print(rson)
        if rson["meta"]["status"] == 200:
            return rson["response"]["hits"]
        else:
            return None
    def GenerateEmbed(hits):
        embed=discord.Embed(title="Lyric Search Results")
        for item in hits:
            embed.add_field(name=item["result"]["full_title"], value=str(hits.index(item)), inline=False)
        return embed
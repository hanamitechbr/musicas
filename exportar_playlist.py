import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
playlist_id = os.getenv("PLAYLIST_ID")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope="playlist-read-private"
))

results = sp.playlist_tracks(playlist_id)
tracks = results['items']

# Paginação (caso tenha mais de 100 músicas)
while results['next']:
    results = sp.next(results)
    tracks.extend(results['items'])

with open("musicas.txt", "w", encoding="utf-8") as f:
    for item in tracks:
        track = item['track']
        name = track['name']
        artists = ", ".join([artist['name'] for artist in track['artists']])
        f.write(f"{name} - {artists}\n")

print("✅ Arquivo criado com sucesso: musicas.txt")

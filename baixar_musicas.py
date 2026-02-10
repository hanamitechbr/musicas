import os
import sys
import time
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    from rich.console import Console
    from dotenv import load_dotenv
except ImportError:
    print("Erro: Bibliotecas necessárias não encontradas.")
    print("Por favor, instale-as executando: pip install spotipy rich yt-dlp python-dotenv")
    sys.exit(1)

# Carrega variáveis do arquivo .env
load_dotenv()

# --- CONFIGURAÇÃO ---
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback" )
PLAYLIST_ID = os.getenv("PLAYLIST_ID")

OUTPUT_DIR = "Musicas"
LOG_DIR = "Logs"
MAX_WORKERS = 5
DELAY_BETWEEN_QUERIES = 0.5

# --- INICIALIZAÇÃO ---
console = Console()
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# --- FUNÇÕES ---
def log_message(filename, message):
    with open(Path(LOG_DIR) / filename, "a", encoding="utf-8") as f:
        f.write(f"{message}\n")

def fetch_spotify_playlist_tracks(playlist_id):
    try:
        sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope="playlist-read-private",
                open_browser=False,
                cache_path=".spotify_cache"
            )
        )
        console.print("[bold cyan]Buscando músicas da playlist do Spotify...[/bold cyan]")
        results = sp.playlist_tracks(playlist_id)
        if not results:
            return []
        tracks = results.get('items', [])
        while results and results['next']:
            results = sp.next(results)
            if results:
                tracks.extend(results.get('items', []))
        track_list = [
            {"title": item['track']['name'], "artist": ", ".join([artist['name'] for artist in item['track']['artists']])}
            for item in tracks if item and item.get('track')
        ]
        console.print(f"[bold green]✓ Encontradas {len(track_list)} músicas.[/bold green]\n")
        return track_list
    except Exception as e:
        console.print(f"[bold red]❌ Erro ao conectar com o Spotify:[/bold red] {e}")
        sys.exit(1)

def search_youtube_video(query):
    try:
        yt_query = f'ytsearch1:"{query}"'
        cmd = [sys.executable, "-m", "yt_dlp", "--no-warnings", "--dump-single-json", yt_query]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        data = json.loads(result.stdout)
        return data.get("entries", [data])[0] if data else None
    except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError):
        return None

def download_audio(video_info, track):
    video_url = video_info.get("webpage_url")
    video_id = video_info.get("id")
    sanitized_title = "".join(c for c in track['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename_template = Path(OUTPUT_DIR) / f"{sanitized_title} - {video_id}.%(ext)s"
    if any(filename_template.with_suffix(s).exists() for s in ['.mp3', '.part']):
        return "skipped", track, "Arquivo já existe."
    cmd = [
        sys.executable, "-m", "yt_dlp", "-x", "--audio-format", "mp3",
        "--add-metadata", "--embed-metadata", "--no-warnings",
        "-o", str(filename_template), video_url
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True, encoding="utf-8")
        return "success", track, str(filename_template.with_suffix('.mp3'))
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip().splitlines()[-1] if e.stderr else "Erro desconhecido"
        return "error", track, error_message

def process_track(track):
    query = f"{track['title']} {track['artist']}"
    console.print(f"[cyan]🔎 Buscando:[/cyan] {track['title']} - {track['artist']}")
    video_info = search_youtube_video(query)
    time.sleep(DELAY_BETWEEN_QUERIES)
    if not video_info:
        console.print(f"[yellow]   ↪ Nenhum resultado para:[/yellow] {track['title']}")
        log_message("nao_encontrados.log", f"{track['title']} - {track['artist']}")
        return "not_found", track, "Nenhum vídeo encontrado."
    console.print(f"[magenta]   ↪ Encontrado:[/magenta] {video_info.get('title', 'N/A')}")
    status, track, message = download_audio(video_info, track)
    if status == "success":
        console.print(f"[green]   ✓ Baixado:[/green] {track['title']}")
    elif status == "skipped":
        console.print(f"[blue]   ↪ Pulado:[/blue] {track['title']}")
    else:
        console.print(f"[red]   ❌ Erro:[/red] {track['title']} -> {message}")
        log_message("erros_download.log", f"{track['title']} - {track['artist']} | Erro: {message}")
    return status, track, message

def main():
    if not all([SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, PLAYLIST_ID]):
        console.print("[bold yellow]Aviso:[/bold yellow] Suas credenciais do Spotify ou o ID da playlist não foram encontrados.")
        console.print("Certifique-se de ter um arquivo `.env` ou de ter definido as variáveis de ambiente.")
        return
        
    tracks_to_download = fetch_spotify_playlist_tracks(PLAYLIST_ID)
    if not tracks_to_download:
        console.print("[bold red]Nenhuma música para baixar.[/bold red]")
        return
        
    total_tracks = len(tracks_to_download)
    console.print(f"\n[bold]Iniciando download de {total_tracks} músicas...[/bold]\n")
    counts = {"success": 0, "skipped": 0, "error": 0, "not_found": 0}
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_track = {executor.submit(process_track, track): track for track in tracks_to_download}
        for future in as_completed(future_to_track):
            try:
                status, _, _ = future.result()
                counts[status] += 1
            except Exception as exc:
                track = future_to_track[future]
                console.print(f"[bold red]Exceção ao processar {track['title']}: {exc}[/bold red]")
                counts["error"] += 1
                
    console.print("\n---")
    console.print("[bold underline]✨ Processo Finalizado! ✨[/bold underline]\n")
    console.print(f"[green]Baixadas:[/green] {counts['success']}")
    console.print(f"[blue]Puladas:[/blue] {counts['skipped']}")
    console.print(f"[yellow]Não Encontradas:[/yellow] {counts['not_found']}")
    console.print(f"[red]Falhas:[/red] {counts['error']}")
    console.print(f"\n[cyan]Arquivos salvos em:[/cyan] '{os.path.abspath(OUTPUT_DIR)}'")
    console.print(f"[cyan]Logs salvos em:[/cyan] '{os.path.abspath(LOG_DIR)}'")
    console.print("\n---")

if __name__ == "__main__":
    main()

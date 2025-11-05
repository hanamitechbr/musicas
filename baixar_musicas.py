#!/usr/bin/env python3
# coding: utf-8

"""
baixar_musicas.py
Baixa conforme o arquivo .txt:
Nome da Música - Autor

Busca combinando música + autor para melhorar precisão.
"""

import subprocess, shlex, json, os, sys, time, argparse, csv
from pathlib import Path

INPUT_FILE = "./musicas.txt"
OUTPUT_DIR = "musicas"
LOG_DIR = "logs"
DELAY_BETWEEN = 1.0

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

def run_cmd(cmd):
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode(errors="ignore"), p.stderr.decode(errors="ignore")

def parse_line(line):
    # Ex: "Nome do vídeo - Autor"
    if " - " in line:
        title, author = line.split(" - ", 1)
        return title.strip(), author.strip()
    return line.strip(), ""

def search_video(title, author):
    query = f"{title} {author}".strip()
    yt_query = f'ytsearch1:"{query}"'
    cmd = f'yt-dlp --no-warnings --dump-single-json {yt_query}'
    code, out, err = run_cmd(cmd)
    if code != 0: return None, err
    try:
        data = json.loads(out)
        if "entries" in data:
            return data["entries"][0], None
        return data, None
    except Exception as e:
        return None, str(e)

def sanitize(s):
    for c in '\\/:*?"<>|':
        s = s.replace(c, "_")
    return s[:180].strip()

def download(url, template):
    cmd = (
        "yt-dlp -x --audio-format mp3 "
        "--add-metadata --embed-metadata "
        f'-o "{template}" "{url}"'
    )
    return run_cmd(cmd)

def log(file, text):
    with open(os.path.join(LOG_DIR, file), "a", encoding="utf-8") as f:
        f.write(text + "\n")

def main(auto=False, start=0):
    if not Path(INPUT_FILE).exists():
        print(f"Arquivo {INPUT_FILE} não encontrado.")
        sys.exit(1)

    lines = [l.strip() for l in open(INPUT_FILE, encoding="utf-8") if l.strip()]
    total = len(lines)
    print(f"{total} entradas encontradas\n")

    for i, line in enumerate(lines[start:], start=start+1):
        title, author = parse_line(line)
        print(f"[{i}/{total}] Buscando: {title} ({author})")

        info, err = search_video(title, author)
        if not info:
            print(" ❌ Sem resultados\n")
            log("skipped.log", f"{line} -> sem resultados ({err})")
            time.sleep(DELAY_BETWEEN)
            continue

        found_title = info.get("title", "")
        url = info.get("webpage_url", "")
        uploader = info.get("uploader", "")
        vid = info.get("id", "")

        print(f" ✅ Encontrado: {found_title}")
        print(f" 🔗 URL: {url}")
        print(f" 👤 Canal: {uploader}")

        if not auto:
            ans = input("Baixar? [Y/n/s=parar]: ").lower().strip()
            if ans == "s":
                print("Saindo.")
                return
            if ans in ["n","no"]:
                print("⏭ Pulado\n")
                log("skipped.log", f"{line} -> pulado pelo usuário")
                continue

        safe = sanitize(found_title)
        out = os.path.join(OUTPUT_DIR, f"{safe} - {vid}.%(ext)s")

        print("⬇️ Baixando...")
        code, out_log, err_log = download(url, out)
        if code == 0:
            print(" ✅ Concluído\n")
            log("downloaded.log", f"{line} -> {url}")
        else:
            print(" ❌ Erro no download\n")
            log("errors.log", f"{line} -> erro: {err_log}")

        time.sleep(DELAY_BETWEEN)

    print("\n✅ Finalizado!")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--auto", action="store_true")
    p.add_argument("--start", type=int, default=0)
    args = p.parse_args()
    main(auto=args.auto, start=args.start)

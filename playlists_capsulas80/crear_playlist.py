"""
Crea una playlist en Spotify a partir de spotify_YYYY.csv, solo con coincidencias verificadas.

Uso:
  python crear_playlist.py spotify_1986.csv "Cápsulas 80 - 1986"          # crea la playlist
  python crear_playlist.py spotify_1986.csv "Cápsulas 80 - 1986" --prueba # solo genera el reporte

Genera reporte_<archivo>.csv con lo que encontró y lo que NO agregó.
"""
import csv, os, re, sys, unicodedata
from difflib import SequenceMatcher

import spotipy
from spotipy.oauth2 import SpotifyOAuth

CLIENT_ID = os.environ.get("SPOTIPY_CLIENT_ID", "PEGA_AQUI_TU_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET", "PEGA_AQUI_TU_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8888/callback"
UMBRAL_TITULO = 0.75  # 0-1; súbelo si aún entran canciones equivocadas


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\(.*?\)|\[.*?\]|- .*remaster.*|- .*version.*|- .*live.*|- .*en vivo.*", "", s)
    return re.sub(r"[^a-z0-9 ]", "", s).strip()


def parecido(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def artista_ok(buscado, track):
    if not buscado:
        return True
    b = norm(buscado)
    for art in track["artists"]:
        n = norm(art["name"])
        if n and (n in b or b in n or parecido(n, b) >= 0.8):
            return True
    return False


def buscar(sp, titulo, artista):
    consultas = [f'track:"{titulo}" artist:"{artista}"', f"{titulo} {artista}"] if artista else [titulo]
    mejor = None
    for q in consultas:
        res = sp.search(q=q, type="track", limit=10, market="MX")["tracks"]["items"]
        for t in res:
            if not artista_ok(artista, t):
                continue
            score = parecido(titulo, t["name"])
            if score >= UMBRAL_TITULO and (mejor is None or score > mejor[0]):
                mejor = (score, t)
        if mejor:
            break
    return mejor


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    archivo, nombre = sys.argv[1], sys.argv[2]
    prueba = "--prueba" in sys.argv

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI,
        scope="playlist-modify-private playlist-modify-public"))

    with open(archivo, encoding="utf-8-sig") as fh:
        filas = list(csv.DictReader(fh))

    uris, reporte = [], []
    for f in filas:
        titulo, artista = f["Track name"].strip(), f["Artist name"].strip()
        r = buscar(sp, titulo, artista)
        if r:
            score, t = r
            if t["uri"] not in uris:
                uris.append(t["uri"])
            reporte.append([artista, titulo, "AGREGADA", t["artists"][0]["name"], t["name"], f"{score:.2f}"])
        else:
            reporte.append([artista, titulo, "NO ENCONTRADA", "", "", ""])
        print(f'{reporte[-1][2]:14} {artista} - {titulo}')

    rep = f"reporte_{os.path.splitext(os.path.basename(archivo))[0]}.csv"
    with open(rep, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Artista buscado", "Título buscado", "Estado", "Artista Spotify", "Título Spotify", "Similitud"])
        w.writerows(reporte)

    print(f"\nAgregables: {len(uris)} / {len(filas)}  ->  reporte: {rep}")
    if prueba:
        print("Modo prueba: no se creó playlist.")
        return

    pl = sp.user_playlist_create(sp.me()["id"], nombre, public=False)
    for i in range(0, len(uris), 100):
        sp.playlist_add_items(pl["id"], uris[i:i + 100])
    print(f'Playlist creada: {pl["external_urls"]["spotify"]}')


if __name__ == "__main__":
    main()

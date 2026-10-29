"""Gera playlists personalizadas conforme o clima e as preferências musicais."""

import json
import os
import random
import re
from typing import Any

import requests
import spotipy
from dotenv import load_dotenv
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth

try:
    from google import genai
except ImportError:  # Gemini é opcional; existe curadoria de fallback.
    genai = None


load_dotenv()

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
GEMINI_MODEL = "gemini-2.5-flash"
FALLBACK_GENRES = ["pop", "rock", "hip-hop", "chill", "latin"]

TOTAL_TRACKS = 50
KNOWN_ARTIST_PERCENT = 0.70
MAX_PER_ARTIST = 5


def get_current_weather() -> tuple[str | None, float | None]:
    """Retorna a condição principal e a temperatura atual da cidade configurada."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    city_query = os.getenv("CITY_QUERY")

    if not api_key or not city_query:
        print("❌ Configure OPENWEATHER_API_KEY e CITY_QUERY no arquivo .env.")
        return None, None

    try:
        response = requests.get(
            WEATHER_URL,
            params={
                "q": city_query,
                "appid": api_key,
                "units": "metric",
                "lang": "pt",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        weather = data["weather"][0]
        temperature = float(data["main"]["temp"])
        condition = str(weather["main"]).lower()

        print(
            f"🌎 Clima em {city_query}: "
            f"{weather.get('description', condition)} ({temperature:.1f}°C)"
        )
        return condition, temperature
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as exc:
        print(f"❌ Não foi possível consultar o clima: {exc}")
        return None, None


def get_gemini_recommendations(
    condition: str,
    temperature: float,
    top_genres: list[str],
    top_artists: list[str],
) -> dict[str, Any] | None:
    """Pede ao Gemini gêneros e um artista de referência em JSON estruturado."""
    api_key = os.getenv("GEMINI_API_KEY")
    if genai is None or not api_key:
        print("ℹ️ Gemini indisponível ou sem chave; será usada a curadoria alternativa.")
        return None

    prompt = f"""
Você é um curador musical. Sugira gêneros de busca do Spotify e um artista
de referência que combinem com o clima e respeitem o gosto musical informado.

Clima atual: {condition}, {temperature:.1f}°C.
Gêneros favoritos: {", ".join(top_genres) or "não disponíveis"}.
Artistas favoritos: {", ".join(top_artists) or "não disponíveis"}.

Retorne um objeto JSON com:
- "generos": uma lista de até cinco gêneros curtos para consultas de música;
- "artista_nome": o nome de um artista relacionado à atmosfera sugerida.
Não inclua texto fora do JSON.
""".strip()

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        response_text = response.text
        if not response_text:
            raise ValueError("O Gemini retornou uma resposta vazia.")

        result = json.loads(response_text)
        if not isinstance(result, dict):
            raise ValueError("A resposta do Gemini não é um objeto JSON.")

        genres = result.get("generos", result.get("gêneros", []))
        if isinstance(genres, str):
            genres = [genres]
        if not isinstance(genres, list):
            genres = []

        clean_genres = [
            str(genre).strip().lower()
            for genre in genres
            if str(genre).strip()
        ]
        artist_name = str(result.get("artista_nome", "")).strip()

        return {
            "generos": clean_genres[:5],
            "artista_nome": artist_name,
        }
    except Exception as exc:
        print(f"⚠️ Falha na curadoria do Gemini; usando alternativas: {exc}")
        return None


def _track_key(track: dict[str, Any]) -> str | None:
    """Retorna um identificador estável para evitar faixas duplicadas."""
    return track.get("id") or track.get("uri")


def _primary_artist_id(track: dict[str, Any]) -> str | None:
    artists = track.get("artists") or []
    if not artists or not isinstance(artists[0], dict):
        return None
    return artists[0].get("id")


def curate_track_candidates(
    known_pool: list[dict[str, Any]],
    discovery_pool: list[dict[str, Any]],
    total_tracks: int = TOTAL_TRACKS,
    known_ratio: float = KNOWN_ARTIST_PERCENT,
    max_per_artist: int = MAX_PER_ARTIST,
) -> list[dict[str, Any]]:
    """Seleciona faixas conhecidas e de descoberta, sem duplicatas e limitando artistas."""
    if total_tracks <= 0 or max_per_artist <= 0:
        return []
    known_ratio = min(max(known_ratio, 0.0), 1.0)
    known_target = round(total_tracks * known_ratio)

    known = list(known_pool)
    discovery = list(discovery_pool)
    random.shuffle(known)
    random.shuffle(discovery)

    selected: list[dict[str, Any]] = []
    selected_keys: set[str] = set()
    artist_counts: dict[str, int] = {}

    def add_from(pool: list[dict[str, Any]], target: int | None = None) -> None:
        added = 0
        for track in pool:
            if len(selected) >= total_tracks or (target is not None and added >= target):
                break
            key = _track_key(track)
            artist_id = _primary_artist_id(track)
            if not key or not artist_id or key in selected_keys:
                continue
            if artist_counts.get(artist_id, 0) >= max_per_artist:
                continue

            selected.append(track)
            selected_keys.add(key)
            artist_counts[artist_id] = artist_counts.get(artist_id, 0) + 1
            added += 1

    # Tenta cumprir cada quota de forma independente antes de preencher vagas restantes.
    add_from(known, known_target)
    add_from(discovery, total_tracks - known_target)

    # Se um dos pools for insuficiente, aproveita as faixas restantes do outro.
    if len(selected) < total_tracks:
        add_from(known)
    if len(selected) < total_tracks:
        add_from(discovery)

    return selected


def _get_artist_tracks(sp: spotipy.Spotify, artist_id: str) -> list[dict[str, Any]]:
    """Busca faixas de álbuns/singles de um artista, isolando falhas por artista."""
    tracks: list[dict[str, Any]] = []
    try:
        albums = sp.artist_albums(
            artist_id,
            album_type="album,single",
            country="BR",
            limit=5,
        ).get("items", [])
        for album in albums:
            try:
                album_tracks = sp.album_tracks(album["id"], limit=50).get("items", [])
                tracks.extend(
                    track for track in album_tracks
                    if track and track.get("id") and track.get("uri")
                )
            except SpotifyException as exc:
                print(f"⚠️ Não foi possível ler faixas de um álbum: {exc}")
    except SpotifyException as exc:
        print(f"⚠️ Não foi possível consultar um artista ({artist_id}): {exc}")
    return tracks


def generate_recommendations(
    sp: spotipy.Spotify,
    gemini_result: dict[str, Any] | None,
    top_artists_ids: list[str],
) -> list[str]:
    """Gera URIs para uma playlist, tentando manter a proporção 70/30."""
    known_ids = list(dict.fromkeys(top_artists_ids))
    known_pool: list[dict[str, Any]] = []

    # As faixas deste grupo vêm dos artistas mais ouvidos pelo usuário.
    artists_to_sample = random.sample(known_ids, min(5, len(known_ids)))
    for artist_id in artists_to_sample:
        known_pool.extend(_get_artist_tracks(sp, artist_id))

    known_pool = list({
        _track_key(track): track
        for track in known_pool
        if _track_key(track)
    }.values())

    genres = []
    if gemini_result:
        raw_genres = gemini_result.get("generos", gemini_result.get("gêneros", []))
        if isinstance(raw_genres, str):
            raw_genres = [raw_genres]
        if isinstance(raw_genres, list):
            genres = [str(genre).strip().lower() for genre in raw_genres if str(genre).strip()]
    genres = list(dict.fromkeys(genres))[:5] or FALLBACK_GENRES

    discovery_pool: list[dict[str, Any]] = []
    seen_discovery: set[str] = set()
    known_keys = {_track_key(track) for track in known_pool}

    # Consultar mais de um gênero melhora a chance de obter candidatos diversos.
    for genre in genres:
        safe_genre = re.sub(r'["\\]', " ", genre).strip()
        if not safe_genre:
            continue
        try:
            result = sp.search(q=f'genre:"{safe_genre}"', type="track", limit=50)
            tracks = result.get("tracks", {}).get("items", [])
            for track in tracks:
                key = _track_key(track) if track else None
                artist_id = _primary_artist_id(track) if track else None
                if (
                    key
                    and track.get("uri")
                    and artist_id
                    and key not in known_keys
                    and key not in seen_discovery
                    and artist_id not in known_ids
                ):
                    discovery_pool.append(track)
                    seen_discovery.add(key)
        except SpotifyException as exc:
            print(f"⚠️ A busca pelo gênero '{genre}' falhou: {exc}")

    if not known_pool and not discovery_pool:
        print("❌ Nenhuma faixa foi encontrada para montar a playlist.")
        return []

    selected = curate_track_candidates(known_pool, discovery_pool)
    track_uris = [track["uri"] for track in selected if track.get("uri")]

    print(
        f"🎶 Faixas selecionadas: {len(track_uris)} "
        f"(alvo: {TOTAL_TRACKS}; artistas conhecidos: até {round(TOTAL_TRACKS * KNOWN_ARTIST_PERCENT)}, "
        f"descoberta: até {TOTAL_TRACKS - round(TOTAL_TRACKS * KNOWN_ARTIST_PERCENT)})."
    )
    if len(track_uris) < TOTAL_TRACKS:
        print("ℹ️ A playlist terá menos faixas que o alvo porque os resultados disponíveis foram limitados.")
    return track_uris


def create_and_populate_playlist(
    sp: spotipy.Spotify,
    user_id: str,
    track_uris: list[str],
    condition: str,
) -> None:
    """Cria uma playlist pública, adiciona as faixas e tenta iniciar a reprodução."""
    if not track_uris:
        print("❌ Não há faixas para adicionar à playlist.")
        return

    playlist_name = f"Clima Musical - {condition.capitalize()}"
    try:
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=True,
            description=f"Playlist curada com base no clima: {condition}.",
        )
        playlist_id = playlist["id"]

        # A API do Spotify aceita no máximo 100 faixas por chamada.
        for start in range(0, len(track_uris), 100):
            sp.playlist_add_items(playlist_id, track_uris[start:start + 100])
        print(f"✅ Playlist criada com {len(track_uris)} faixas: {playlist_name}")

        try:
            sp.start_playback(context_uri=playlist["uri"])
            print("▶️ Solicitação de reprodução enviada ao Spotify.")
        except SpotifyException as exc:
            print(
                "ℹ️ A playlist foi criada, mas não foi possível iniciar a reprodução. "
                f"Confira se há um dispositivo Spotify ativo e permissões disponíveis. Detalhe: {exc}"
            )
    except SpotifyException as exc:
        print(f"❌ Não foi possível criar ou preencher a playlist: {exc}")


def _validate_spotify_config() -> tuple[str, str, str, str] | None:
    """Valida credenciais mínimas antes de iniciar o fluxo OAuth."""
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback")
    scope = os.getenv(
        "SPOTIPY_SCOPE",
        "user-top-read,playlist-modify-public,user-modify-playback-state,"
        "user-read-playback-state,user-read-private",
    )

    missing = [
        name for name, value in (
            ("SPOTIPY_CLIENT_ID", client_id),
            ("SPOTIPY_CLIENT_SECRET", client_secret),
        )
        if not value
    ]
    if missing:
        print(f"❌ Configure estas variáveis no arquivo .env: {', '.join(missing)}")
        return None
    return client_id, client_secret, redirect_uri, scope


def main() -> None:
    print("☁️🎶 Iniciando SpotWeather-AI...")

    spotify_config = _validate_spotify_config()
    if not spotify_config:
        return

    client_id, client_secret, redirect_uri, scope = spotify_config
    try:
        sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
                show_dialog=True,
            ),
            requests_timeout=15,
            retries=2,
        )
        user_id = sp.current_user()["id"]
        print("✅ Autenticação Spotify concluída.")
    except (SpotifyException, KeyError, ValueError) as exc:
        print(f"❌ Falha na autenticação com o Spotify: {exc}")
        return

    condition, temperature = get_current_weather()
    if condition is None or temperature is None:
        return

    try:
        top_artists_data = sp.current_user_top_artists(
            limit=10,
            time_range="medium_term",
        )
        top_artists = top_artists_data.get("items", [])
        top_artists_names = [artist["name"] for artist in top_artists if artist.get("name")]
        top_artists_ids = [artist["id"] for artist in top_artists if artist.get("id")]
        all_genres = {
            genre
            for artist in top_artists
            for genre in artist.get("genres", [])
            if genre
        }
        top_genres = sorted(all_genres)[:5]
        if not top_artists:
            print("ℹ️ O Spotify não retornou artistas favoritos; usando sugestões gerais.")
        else:
            print(f"🎵 Artistas favoritos encontrados: {', '.join(top_artists_names[:3])}")
    except SpotifyException as exc:
        print(f"⚠️ Não foi possível consultar o perfil musical: {exc}")
        top_artists_names, top_artists_ids, top_genres = [], [], []

    gemini_result = get_gemini_recommendations(
        condition,
        temperature,
        top_genres,
        top_artists_names,
    )
    track_uris = generate_recommendations(sp, gemini_result, top_artists_ids)
    create_and_populate_playlist(sp, user_id, track_uris, condition)


if __name__ == "__main__":
    main()

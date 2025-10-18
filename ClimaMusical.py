import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import json
import random

# --- CONFIGURAÇÃO E CARREGAMENTO DE VARIÁVEIS ---
load_dotenv()

# Credenciais do Spotify (carregadas do .env)
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SCOPE = os.getenv("SPOTIPY_SCOPE")

# Credenciais do Clima e Gemini
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
CITY_QUERY = os.getenv("CITY_QUERY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- 1. AUTENTICAÇÃO DO SPOTIFY ---
# Garante que o usuário se autentique com o Scope Mestre necessário
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    show_dialog=True
))
user_id = sp.current_user()['id']
print(f"✅ Autenticação Spotify bem-sucedida! Usuário: {user_id}")
print("-" * 50)


# --- 2. FUNÇÃO DE CLIMA ---
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"

def get_current_weather():
    """Busca os dados de clima atual para a cidade definida no .env."""
    
    params = {
        'q': CITY_QUERY,
        'appid': WEATHER_API_KEY,
        'units': 'metric',
        'lang': 'pt'
    }

    try:
        response = requests.get(WEATHER_URL, params=params)
        response.raise_for_status() 
        data = response.json()
        
        weather_main = data['weather'][0]['main'].lower()
        temp_celsius = data['main']['temp']
        description = data['weather'][0]['description']

        print(f"🌎 Clima em {CITY_QUERY}: {description} ({temp_celsius}°C)")
        return weather_main, temp_celsius

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao buscar dados de clima: {e}.")
        return None, None


# --- 3. INTEGRAÇÃO GEMINI (O Curador Musical Pessoal) ---
try:
    from google import genai
except ImportError:
    genai = None

def get_gemini_recommendations(clima_principal, temperatura, top_genres_names, top_artists_names):
    """Solicita a sugestão de Gêneros e Artistas ao Gemini em formato JSON."""
    
    if not genai or not GEMINI_API_KEY:
        return None

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""
        Atue como um Curador Musical avançado. Sua tarefa é sugerir gêneros e artistas que combinem 
        com a atmosfera de hoje, respeitando o gosto do usuário.

        1. CLIMA ATUAL: {clima_principal}, {temperatura}°C.
        2. TOP GÊNEROS DO USUÁRIO: {', '.join(top_genres_names)}.
        3. TOP ARTISTAS DO USUÁRIO: {', '.join(top_artists_names)}.

        TAREFA: Sugira 5 gêneros musicais (Spotify format) e 1 Artista Semente que combinem.
        Responda APENAS com um objeto JSON. Nenhuma explicação é necessária, apenas o JSON. 
        As chaves do JSON devem ser 'gêneros' (lista de strings) e 'artista_nome' (string).
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        response_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(response_text)

    except Exception as e:
        print(f"❌ Erro na chamada do Gemini: {e}")
        return None


# --- 4. GERAÇÃO DE RECOMENDAÇÕES (CURADORIA 70/30) ---

def generate_recommendations(sp, gemini_result, top_artists_ids):
    """
    Gera uma lista de 50 faixas aplicando a regra 70% Artistas Conhecidos / 30% Novos,
    com limite de 5 músicas por artista, usando a busca robusta.
    """
    TOTAL_TRACKS = 50
    KNOWN_ARTIST_PERCENT = 0.7
    KNOWN_TRACKS_COUNT = int(TOTAL_TRACKS * KNOWN_ARTIST_PERCENT) 
    NEW_TRACKS_COUNT = TOTAL_TRACKS - KNOWN_TRACKS_COUNT          
    MAX_PER_ARTIST = 5
    
    seed_artists_list = []
    seed_genres_list = []
    
    # Processa o resultado do Gemini (ou usa fallback)
    if gemini_result and 'gêneros' in gemini_result:
        seed_genres_list = [g.lower().replace(' ', '-') for g in gemini_result['gêneros'][:5]]
        print(f"✨ Gêneros Sugeridos pelo Gemini: {', '.join(seed_genres_list)}")
        
        if 'artista_nome' in gemini_result:
            search_result = sp.search(q=gemini_result['artista_nome'], type='artist', limit=1)
            if search_result['artists']['items']:
                artist_id = search_result['artists']['items'][0]['id']
                seed_artists_list.append(artist_id)
                print(f"🎤 Artista Semente Sugerido: {gemini_result['artista_nome']}")
    
    if not seed_genres_list:
         seed_genres_list = random.sample(['pop', 'rock', 'hip-hop', 'chill', 'latin'], 5)


    # --- A. GERAÇÃO DO POOL CONHECIDO (70% - Dos Top Artistas) ---
    known_pool_uris = []
    
    # Garante que sempre terá artistas para amostrar (Gemini ou Top do usuário)
    artists_to_sample = seed_artists_list + random.sample(top_artists_ids, min(5, len(top_artists_ids)))
    
    for artist_id in artists_to_sample:
        # Busca álbuns/singles do artista e pega 3 músicas de cada
        albums = sp.artist_albums(artist_id, album_type='album,single', country='BR', limit=2)['items']
        for album in albums:
             top_tracks = sp.album_tracks(album['id'], limit=3)['items']
             known_pool_uris.extend([t['uri'] for t in top_tracks if t['id']])
             
    # Remove duplicatas
    known_pool_uris = list(set(known_pool_uris)) 


    # --- B. GERAÇÃO DO POOL (30% - De Busca por Gêneros) ---
    new_pool_uris = []
    
    if seed_genres_list:
        # Usa um gênero aleatório do Gemini ou do Fallback
        query_genre = random.choice(seed_genres_list)
        query = f"genre:\"{query_genre}\""
        
        # Pega mais faixas que o necessário para garantir a variedade
        search_results = sp.search(q=query, type='track', limit=50)['tracks']['items']
        new_pool_uris.extend([t['uri'] for t in search_results])
    
    new_pool_uris = list(set(new_pool_uris))


    # --- C. CURADORIA FINAL (APLICANDO AS REGRAS 70/30 e LIMITE POR ARTISTA) ---
    final_uris = []
    artist_counts = {}
    
    # Prepara a lista total para curadoria
    tracks_to_curate = []
    random.shuffle(known_pool_uris)
    random.shuffle(new_pool_uris)
    
    # 1. Combina 70% Conhecido + 30% Novo
    # Alterna entre os pools para garantir a distribuição
    for i in range(TOTAL_TRACKS * 2):
        if i < KNOWN_TRACKS_COUNT and known_pool_uris:
            tracks_to_curate.append(known_pool_uris.pop())
        elif i < NEW_TRACKS_COUNT and new_pool_uris:
             tracks_to_curate.append(new_pool_uris.pop())
        elif known_pool_uris:
             tracks_to_curate.append(known_pool_uris.pop())
        elif new_pool_uris:
             tracks_to_curate.append(new_pool_uris.pop())


    # 2. Mapeia e Aplica a Regra do Limite de 5
    # Tenta obter os dados das faixas em lotes
    if not tracks_to_curate:
        print("❌ Não foi possível gerar um pool de faixas para curadoria.")
        return []

    # O Spotipy.tracks() aceita até 50 URIs por vez
    for i in range(0, len(tracks_to_curate), 50):
        batch = tracks_to_curate[i:i + 50]
        tracks_data = sp.tracks(batch)['tracks']
        
        for track in tracks_data:
            if not track or not track['artists']: continue
            artist_id = track['artists'][0]['id']
            
            # Aplica a regra do limite de 5 por artista
            if artist_counts.get(artist_id, 0) < MAX_PER_ARTIST:
                final_uris.append(track['uri'])
                artist_counts[artist_id] = artist_counts.get(artist_id, 0) + 1
                
            # Se a lista final estiver completa, pare
            if len(final_uris) >= TOTAL_TRACKS:
                break
        
        if len(final_uris) >= TOTAL_TRACKS:
            break

            
    print(f"\n✅ Total de {len(final_uris)} músicas curadas (Regra 70/30 aplicada).")
    return final_uris


# --- 5. AUTOMACAO DE PLAYLIST E REPRODUCAO ---

def create_and_populate_playlist(sp, user_id, track_uris, clima_principal):
    """Cria a playlist, adiciona as faixas e inicia a reprodução."""
    
    playlist_name = f"Clima Musical - {clima_principal.capitalize()}"
    
    # 1. Cria a nova playlist
    print(f"\n🎧 Criando/Atualizando playlist: {playlist_name}")
    try:
        new_playlist = sp.user_playlist_create(
            user=user_id, 
            name=playlist_name, 
            public=True, 
            description=f"Curadoria 70/30 gerada por Gemini e Spotipy para o clima: {clima_principal}."
        )
        playlist_id = new_playlist['id']

        # 2. Adiciona as músicas
        if track_uris:
            sp.playlist_add_items(playlist_id, track_uris)
            print(f"✅ {len(track_uris)} faixas adicionadas à playlist.")
        
        # 3. Inicia a reprodução (Contexto URI)
        sp.start_playback(context_uri=new_playlist['uri']) 
        print("▶️ Reprodução iniciada! Confira seu Spotify.")
        
    except Exception as e:
        print(f"❌ Erro ao criar/tocar playlist: {e}")


# --- FUNÇÃO PRINCIPAL ---

def main():
    print(f"Iniciando Mago Musical (Powered by Gemini)...")
    
    # 1. Obter o Clima
    clima_principal, temperatura = get_current_weather()
    
    if not clima_principal:
        return

    # 2. Coletar Gosto Pessoal
    try:
        # Coleta os 10 artistas mais ouvidos e seus IDs
        top_artists_data = sp.current_user_top_artists(limit=10, time_range='medium_term')
        top_artists_names = [a['name'] for a in top_artists_data['items']]
        top_artists_ids = [a['id'] for a in top_artists_data['items']]
        
        # Coleta os 5 gêneros mais ouvidos (derivado dos artistas)
        all_genres = set()
        for artist in top_artists_data['items']:
            all_genres.update(artist['genres'])
        top_genres_names = list(all_genres)[:5]

        print(f"🎵 Gosto Musical Coletado: {', '.join(top_artists_names[:3])}...")

    except Exception as e:
        print(f"❌ Erro ao buscar dados pessoais: {e}. Usando dados de fallback.")
        top_artists_names = ["rock alternativo", "pop dos anos 80"]
        top_genres_names = ['pop', 'rock']
        top_artists_ids = []

        
    # 3. Chamar o Gemini (Curador)
    gemini_result = get_gemini_recommendations(
        clima_principal, 
        temperatura, 
        top_genres_names,    
        top_artists_names    
    )
    
    # 4. Gerar Recomendações no Spotify
    # A função de recomendação agora usa o resultado do Gemini e o ID dos seus artistas
    track_uris = generate_recommendations(sp, gemini_result, top_artists_ids)

    # 5. Criar e Tocar a Playlist
    if track_uris:
        create_and_populate_playlist(sp, user_id, track_uris, clima_principal)
    else:
        print("Nenhuma música encontrada para criar a playlist.")


if __name__ == "__main__":

    main()

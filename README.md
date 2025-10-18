# SpotWeather-AI
SpotWeather-AI is an intelligent Python application designed to create personalized, context-aware Spotify playlists based on real-time weather conditions.

# ☁️ SpotWeather-AI 🎶

**Curador Musical Inteligente: Geração de Playlists no Spotify baseadas no Clima Local e no seu Gosto Pessoal, potencializado por Gemini AI.**

---

## 💡 Sobre o Projeto

O **SpotWeather-AI** é um sistema de recomendação de música em Python que preenche a lacuna entre as condições climáticas e o seu humor musical.

Ele utiliza a **Gemini AI** como um curador pessoal, que interpreta o clima em tempo real (ex: "Nublado") e o seu perfil de Top Artistas e Gêneros para sugerir o estilo de música perfeito para o momento. Em seguida, ele cria e inicia a reprodução de uma playlist no seu Spotify.

### Principais Funcionalidades

* **Curadoria Contextualizada:** Gemini traduz o clima e o seu gosto em gêneros e um artista semente.
* **Regra de Diversidade (70/30):** As playlists são curadas com **70% de faixas de artistas que você já ouve** (para familiaridade) e **30% de faixas de descoberta** (para novidade), limitando a 5 músicas por artista para máxima variedade.
* **Automação Completa:** Cria a playlist (`Clima Musical - [Condição]`) e inicia a reprodução automaticamente.

---

## 🚀 Configuração Rápida (Quick Start)

Para rodar o **SpotWeather-AI**, você precisa obter quatro chaves de API e configurar um ambiente Python.

### 1. Pré-requisitos

* Python 3.8+
* Conta de Desenvolvedor Spotify
* Chave de API do Gemini (Google AI Studio)
* Chave de API do OpenWeatherMap

### 2. Instalação do Projeto

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/SeuNome/SpotWeather-AI.git](https://github.com/SeuNome/SpotWeather-AI.git)
    cd SpotWeather-AI
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows, use: venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    # O arquivo requirements.txt deve listar: spotipy, python-dotenv, requests, google-genai
    ```

---

## 🔑 Configuração das APIs e Chaves Secretas

📄 Conteúdo do Arquivo .env (Configuração)
Crie um arquivo chamado .env na pasta raiz do seu projeto e cole o seguinte conteúdo, substituindo os valores entre aspas pelo seu respectivo token ou chave.

### A. Chaves do Spotify

1.  Vá para o [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
2.  Crie um novo aplicativo e obtenha seu **`Client ID`** e **`Client Secret`**.
3.  **Configuração de Redirect URI:** No seu aplicativo Spotify, clique em **Edit Settings** e adicione o seguinte URI à lista de **Redirect URIs**:
    `http://localhost:8888/callback`
4.  **Definição dos Scopes:** O projeto requer o acesso à leitura do seu histórico e controle de playback. Use a seguinte lista de `SCOPE`:
    `user-top-read,playlist-modify-public,user-modify-playback-state,user-read-playback-state,user-read-private`

### B. Chave do Gemini (Google AI)

1.  Obtenha sua chave de API no [Google AI Studio](https://ai.google.dev/gemini-api/docs/api-key).

### C. Chave do Clima (OpenWeatherMap)

1.  Crie uma conta no [OpenWeatherMap](https://openweathermap.org/) e gere uma chave de API.

### 📄 Seu arquivo `.env` deve ser assim:

```env
# --- SPOTIFY ---
SPOTIPY_CLIENT_ID="SUA_SPOTIFY_CLIENT_ID"
SPOTIPY_CLIENT_SECRET="SUA_SPOTIFY_CLIENT_SECRET"
SPOTIPY_REDIRECT_URI="http://localhost:8888/callback"
SPOTIPY_SCOPE="user-top-read,playlist-modify-public,user-modify-playback-state,user-read-playback-state,user-read-private"

# --- GEMINI AI ---
GEMINI_API_KEY="SUA_GEMINI_API_KEY"

# --- OPENWEATHERMAP ---
OPENWEATHER_API_KEY="SUA_OPENWEATHER_API_KEY"
CITY_QUERY="Nome da sua cidade,BR"  # Ex: "Sao Paulo,BR"

```

### 🛠️ Modificações e Customização

Você pode personalizar o funcionamento do curador modificando as variáveis definidas no início da função **`generate_recommendations`** dentro do arquivo `ClimaMusical.py`.

Ajuste estes parâmetros para alterar o tamanho da playlist e a distribuição entre músicas conhecidas e descobertas.

| Variável | O que controla? | Padrão |
| :--- | :--- | :--- |
| **`TOTAL_TRACKS`** | Quantidade total de músicas na playlist. | `50` |
| **`KNOWN_ARTIST_PERCENT`** | Proporção de faixas de artistas que você já ouve. Controla a regra **70/30** (0.7 = 70%). | `0.7` (70%) |
| **`MAX_PER_ARTIST`** | Limite máximo de músicas de um mesmo artista para garantir a diversidade. | `5` |

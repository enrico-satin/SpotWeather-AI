# SpotWeather-AI ☁️🎶

Aplicação em Python que combina condições meteorológicas, preferências musicais e IA generativa para criar uma playlist personalizada no Spotify.

O Gemini atua como curador musical: recebe o clima atual e informações sobre artistas e gêneros que o usuário costuma ouvir, sugere direções musicais e o projeto usa a API do Spotify para montar uma playlist.

## Funcionalidades

- Consulta o clima atual de uma cidade usando a API do OpenWeatherMap.
- Consulta artistas e gêneros relacionados ao perfil musical do usuário no Spotify.
- Usa o Gemini para sugerir gêneros e um artista de referência com base no clima e nas preferências musicais.
- Busca faixas no Spotify e aplica regras de diversidade, incluindo um limite pretendido de músicas por artista.
- Cria uma playlist no Spotify e tenta iniciar sua reprodução.

> **Observação:** a distribuição 70/30 é a regra pretendida pelo projeto. A seleção depende dos resultados disponíveis nas APIs e pode não produzir exatamente 50 faixas nem uma proporção exata em todas as execuções.

## Tecnologias

- Python
- Spotify Web API, por meio de [Spotipy](https://spotipy.readthedocs.io/)
- Gemini API, por meio do SDK `google-genai`
- OpenWeatherMap API
- `requests` e `python-dotenv`

## Requisitos

- Python 3.10 ou superior
- Conta de desenvolvedor do Spotify e um aplicativo configurado no [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
- Chave de API do [Google AI Studio](https://aistudio.google.com/apikey)
- Chave de API do [OpenWeatherMap](https://openweathermap.org/api)
- Uma conta Spotify com acesso à reprodução para a funcionalidade de iniciar playback

## Instalação

Clone este repositório:

```bash
git clone https://github.com/enrico-satin/SpotWeather-AI.git
cd SpotWeather-AI
```

Crie e ative um ambiente virtual:

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

## Configuração

Crie um arquivo `.env` na raiz do projeto com suas próprias credenciais:

```env
SPOTIPY_CLIENT_ID="seu_spotify_client_id"
SPOTIPY_CLIENT_SECRET="seu_spotify_client_secret"
SPOTIPY_REDIRECT_URI="http://localhost:8888/callback"
SPOTIPY_SCOPE="user-top-read,playlist-modify-public,user-modify-playback-state,user-read-playback-state,user-read-private"

GEMINI_API_KEY="sua_chave_gemini"
OPENWEATHER_API_KEY="sua_chave_openweathermap"
CITY_QUERY="Indaiatuba,BR"
```

No Spotify Developer Dashboard, configure o Redirect URI exatamente como o valor de `SPOTIPY_REDIRECT_URI`. Os escopos solicitados permitem consultar informações musicais e criar playlists; os escopos de playback são usados para tentar iniciar a reprodução.

**Segurança:** nunca compartilhe nem faça commit do arquivo `.env`, tokens OAuth ou chaves de API. Use apenas credenciais próprias e revise as permissões solicitadas antes de autorizar o aplicativo.

## Executar

Com o ambiente virtual ativado e o arquivo `.env` configurado:

```bash
python ClimaMusical.py
```

Na primeira execução, o Spotipy pode abrir o navegador para autenticação com o Spotify. A reprodução automática depende de uma sessão/dispositivo Spotify compatível e das permissões disponíveis para a conta.

## Como funciona

1. Busca as condições meteorológicas atuais para a cidade configurada.
2. Consulta artistas mais ouvidos e deriva gêneros musicais dessas informações.
3. Envia o contexto para o Gemini, que sugere gêneros e um artista de referência.
4. Busca faixas no Spotify e tenta selecionar uma mistura de familiaridade e descoberta.
5. Cria uma playlist chamada `Clima Musical - [Condição]` e tenta iniciar sua reprodução.

## Configurações de curadoria

Os parâmetros principais estão dentro de `generate_recommendations` em `ClimaMusical.py`:

| Parâmetro | Finalidade | Valor padrão |
| --- | --- | ---: |
| `TOTAL_TRACKS` | Quantidade pretendida de faixas | 50 |
| `KNOWN_ARTIST_PERCENT` | Proporção pretendida para artistas conhecidos | 0.7 |
| `MAX_PER_ARTIST` | Limite de faixas por artista na seleção | 5 |

## Limitações conhecidas

- A qualidade e a quantidade das recomendações dependem das respostas das APIs externas e da disponibilidade de faixas.
- A resposta do modelo generativo é interpretada como JSON; respostas inesperadas podem exigir tratamento adicional.
- A reprodução automática depende das condições e permissões da API do Spotify.
- A regra 70/30 é uma intenção de curadoria e não uma garantia matemática na versão atual.

## Licença

Este projeto está disponibilizado sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE).

# SpotWeather-AI ☁️🎶

Aplicação em Python que combina condições meteorológicas, preferências musicais e IA generativa para criar uma playlist personalizada no Spotify.

O Gemini atua como curador musical: recebe o clima atual e informações sobre artistas e gêneros que o usuário costuma ouvir, sugere direções musicais e o projeto usa a API do Spotify para montar uma playlist.

## Funcionalidades

- Consulta o clima atual de uma cidade usando a API do OpenWeatherMap.
- Consulta artistas e gêneros relacionados ao perfil musical do usuário no Spotify.
- Usa o Gemini para sugerir gêneros e um artista de referência com base no clima e nas preferências musicais.
- Busca faixas no Spotify e tenta equilibrar familiaridade e descoberta, respeitando um limite de faixas por artista.
- Cria uma playlist no Spotify e tenta iniciar sua reprodução.
- Inclui testes automatizados para a lógica de seleção de faixas.

> **Observação:** a proporção 70/30 é uma meta de curadoria. A quantidade e a distribuição finais dependem das faixas retornadas pelas APIs e podem variar.

## Tecnologias

- Python 3.10+
- Spotify Web API, por meio de [Spotipy](https://spotipy.readthedocs.io/)
- Gemini API, por meio do SDK `google-genai`
- OpenWeatherMap API
- `requests`, `python-dotenv` e `unittest`

## Requisitos

- Python 3.10 ou superior
- Aplicativo configurado no [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
- Chave de API do [Google AI Studio](https://aistudio.google.com/apikey) (opcional; sem ela, o projeto usa gêneros de fallback)
- Chave de API do [OpenWeatherMap](https://openweathermap.org/api)
- Conta Spotify e um dispositivo compatível para tentar iniciar a reprodução

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

Copie `.env.example` para `.env` e preencha as credenciais:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Linux/macOS:**
```bash
cp .env.example .env
```

Edite o arquivo `.env` com seus próprios valores. No Spotify Developer Dashboard, configure o Redirect URI igual a `SPOTIPY_REDIRECT_URI`.

O projeto solicita permissões para consultar artistas favoritos, criar playlists públicas e tentar controlar a reprodução. Revise as permissões antes de autorizar o aplicativo.

**Segurança:** nunca publique o arquivo `.env`, tokens OAuth ou chaves de API. O `.gitignore` exclui arquivos de ambiente e caches locais, mas sempre confira o que será enviado antes de fazer commit.

## Executar

Com o ambiente virtual ativado e o arquivo `.env` configurado:

```bash
python ClimaMusical.py
```

Na primeira execução, o Spotipy pode abrir o navegador para autenticação com o Spotify. A reprodução automática depende de um dispositivo compatível ativo e das permissões disponíveis para a conta. Se não houver dispositivo disponível, a playlist ainda pode ter sido criada.

## Como funciona

1. Consulta o clima atual da cidade configurada.
2. Busca artistas mais ouvidos e deriva gêneros musicais dessas informações.
3. Envia o contexto ao Gemini para sugerir gêneros e um artista de referência.
4. Busca faixas nos artistas favoritos e em consultas de gênero.
5. Seleciona faixas sem duplicatas, tentando respeitar a proporção 70/30 e o limite por artista.
6. Cria uma playlist chamada `Clima Musical - [Condição]` e tenta iniciar sua reprodução.

## Configurações de curadoria

Os parâmetros principais estão no início de `ClimaMusical.py`:

| Parâmetro | Finalidade | Valor padrão |
| --- | --- | ---: |
| `TOTAL_TRACKS` | Quantidade desejada de faixas | 50 |
| `KNOWN_ARTIST_PERCENT` | Proporção desejada de faixas dos artistas favoritos | 0.70 |
| `MAX_PER_ARTIST` | Limite de faixas por artista principal | 5 |

Se um pool não tiver candidatos suficientes, a seleção tenta preencher as vagas com faixas disponíveis no outro pool. Por isso, a proporção final pode diferir da meta.

## Testes

Execute os testes da lógica de curadoria com:

```bash
python -m unittest discover -s tests -v
```

Os testes não chamam as APIs externas; eles verificam a seleção, a remoção de duplicatas, o limite por artista e o comportamento com poucos candidatos.

## Limitações conhecidas

- Os resultados dependem da disponibilidade e das respostas das APIs externas.
- A resposta do Gemini pode falhar; nesse caso, o projeto usa gêneros alternativos.
- A reprodução automática depende das condições e permissões da API do Spotify.
- O projeto ainda é um script de linha de comando; não possui interface web ou implantação hospedada.

## Licença

Este projeto está disponibilizado sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE).

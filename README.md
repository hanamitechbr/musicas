# Script para baixar músicas

## Dependências

`pip install spotipy python-dotenv`
`pip install yt-dlp`
## Baixe também o ffmpeg:
  Acesse o site `https://www.gyan.dev/ffmpeg/builds/`
  Se o site gyan.dev não estiver online, acesse: `https://www.videohelp.com/software/ffmpeg`
  Clique em: `ffmpeg-release-essentials.zip`

  ### Adicione a pasta `bin` do ffmpeg ao PATH

## Configurar credenciais do spotify

- Acesse `https://developer.spotify.com/dashboard`
- Faça login
- Clique em `"Create App"`
- Pegue seu `Client ID` e `Client Secret`
- Cadastre o direct URI: `http://127.0.0.1:8080`

## Crie e configure o arquivo .env

  ### Renomeie o arquivo `sample.env` para `.env` e faça a configuração:

  - `SPOTIFY_CLIENT_ID=`SEU_CLIENT_ID_AQUI
  - `SPOTIFY_CLIENT_SECRET=`SEU_CLIENT_SECRET_AQUI
  - `SPOTIFY_REDIRECT_URI=`http://127.0.0.1:8080
  - `PLAYLIST_ID=`COLOQUE_AQUI_O_ID_DA_PLAYLIST

## Como pegar o ID da playlist
  Vá no spotify, clique com o botão direito na playlist, clique `Compartilhar` depois `Copiar link da playlist`
  O ID vai vir depois do "playlist/" e antes da interrogação "?" na URL.
  Exemplo: https://open.spotify.com/playlist/`4oVp13aYinT4LXu4n0JNsr?si=7dd0abd53f794a9e`
  No meu caso, o ID é: `4oVp13aYinT4LXu4n0JNsr` (Apaguei a parte depois da interrogação "?")

## Rode o script: ``python exportar_playlist.py`` e depois: ``python baixar_musicas.py``

  Ele vai criar uma pasta ``musicas`` com todas as músicas.
  Depois basta você decidir o que vai fazer com elas (se vai mandar tudo para o celular via cabo USB ou deixar no PC pra escutar)

### Dependendo da quantidade de músicas, ele vai demorar pra um caramba pra baixar tudo 👍

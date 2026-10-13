# Fio de Amanhã

Modelo base de visual novel em Python com Pygame. O projeto abre sem imagens ou sons externos: cenários e personagens vetoriais servem como placeholders até você colocar seus próprios arquivos.

## Executar

Requer Python 3.10 ou superior.

```powershell
python -m pip install -r requirements.txt
python main.py
```

No Windows, também é possível iniciar com `run.bat` depois de instalar as dependências.

## Controles

- Clique em **Continuar** ou pressione `Enter`/`Espaço` para avançar o diálogo.
- Clique em uma opção para seguir por uma das ramificações.
- `Esc` volta à tela anterior.
- Os botões no canto superior durante o jogo abrem salvar, configurações e título.

## Editar a história

Abra `story.json`. Cada cena tem um identificador, um fundo, uma lista ordenada de falas e, opcionalmente, opções ou uma cena seguinte. As opções apontam para outra cena com `goto`; `set` guarda valores simples na partida.

```json
{
  "background": "minha_cena",
  "lines": [
    {
      "speaker": {"pt": "Personagem", "en": "Character"},
      "sprite": "personagem",
      "text": {"pt": "Sua fala aqui.", "en": "Your line here."}
    }
  ]
}
```

Para um idioma novo, adicione as traduções em `story.json` e em `TEXT`, no começo de `main.py`. As chaves `assets.backgrounds` e `assets.sprites` ligam IDs usados nas cenas aos arquivos de imagem.

## Trocar placeholders por arte

- Fundos: coloque imagens PNG/JPG em `assets/backgrounds/` e atualize o caminho correspondente em `story.json`. Recomenda-se 16:9 (por exemplo, 1920 × 1080).
- Sprites: coloque PNGs com transparência em `assets/sprites/`; a altura recomendada é 560 px ou mais. A base redimensiona o sprite para a área do personagem.
- Música: coloque um arquivo compatível com SDL_mixer em `assets/music/tema.ogg`, ou altere `audio.music` no JSON.
- Efeitos: adicione arquivos WAV em `assets/sfx/` e referencie-os em `audio.sfx`.

Se um arquivo estiver ausente ou não puder ser carregado, o jogo continua usando o placeholder desenhado pelo código.

## O que já vem funcionando

- Tela de título, novo jogo, continuar e sair.
- Prólogo em português e inglês, com duas decisões e finais de demonstração.
- Configurações persistentes: resolução, tela cheia, idioma e volumes geral/música/efeitos.
- Nove slots em grade, com data da partida e opção de apagar um slot.
- Saves e preferências ficam fora do projeto, em `%APPDATA%\FioDeAmanha` no Windows (ou `~/.fio_de_amanha` em outros sistemas).

O volume de música e efeitos já fica configurado para os arquivos adicionados; sem arquivos de áudio, o jogo permanece silencioso e funcional.
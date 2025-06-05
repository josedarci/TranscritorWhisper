# Transcritor Whisper

Este projeto é uma aplicação de transcrição de áudio que utiliza o modelo Whisper para converter arquivos de áudio em texto. A aplicação permite que os usuários enviem arquivos de áudio e recebam a transcrição correspondente.

## Estrutura do Projeto

```
transcritor-whisper
├── src
│   └── app.py          # Implementação principal do aplicativo
├── requirements.txt     # Dependências do projeto
└── README.md            # Documentação do projeto
```

## Instalação

Para instalar as dependências do projeto, você precisará do Python 3.7 ou superior. Você pode usar o `pip` para instalar as bibliotecas necessárias. Execute o seguinte comando no terminal:

```
pip install -r requirements.txt
```

## Execução do Aplicativo

Após instalar as dependências, você pode executar o aplicativo de transcrição de áudio. Navegue até o diretório `src` e execute o seguinte comando:

```
python app.py
```

## Uso

1. Acesse a interface do aplicativo em seu navegador.
2. Envie um arquivo de áudio no formato `.mp3`, `.wav`, etc.
3. Aguarde a transcrição ser gerada e exibida na tela.

## Dependências

As principais bibliotecas utilizadas neste projeto são:

- `whisper`: Para a transcrição de áudio.
- `gradio`: Para a criação da interface do usuário.

## Contribuição

Sinta-se à vontade para contribuir com melhorias ou correções. Para isso, faça um fork do repositório e envie um pull request com suas alterações.
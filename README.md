# APTO Maker

Programa em Python com interface gráfica que transforma uma lista de textos (por exemplo, `APTO 101`, `APTO 102`…) em um arquivo **DXF** com placas retangulares identificadas, já organizadas em folhas prontas para fabricação.

## O que o programa faz

Você digita (ou cola) os textos, **um por linha**, e cada linha vira uma placa com o texto centralizado. O programa:

- aceita **qualquer texto** (não precisa ser "APTO número"); linhas vazias são ignoradas;
- organiza as placas em **folhas** de 660×490 com borda vermelha, 10 de espaço entre uma folha e outra;
- cria novas folhas automaticamente quando as placas não cabem em uma só;
- permite várias **sequências** (por exemplo, uma por torre ou bloco), cada uma com seu nome e seu texto, desenhadas uma abaixo da outra;
- gera um único arquivo `.dxf` (formato R2010, texto em Arial) que abre direto no ZWCAD.

### Modos de desenho

Cada sequência escolhe o seu modo:

| Modo | O que desenha |
|---|---|
| **Normal** | 1× placa 50x15 e 2× placa 40x10 por texto |
| **Só 50x15** | apenas placas 50x15 |
| **Só 40x10** | apenas placas 40x10, uma vez |
| **Só 90x25** | apenas placas 90x25, uma vez |

As placas 50x15 e 90x25 levam dois furos (raio 1,5), a 4 de cada borda lateral. As 40x10 não têm furos.

### Faixa TODAS

Com a opção **"Faixa TODAS no topo"** marcada (padrão), o desenho ganha no topo uma faixa extra com **todas as sequências juntas**, agrupadas por sequência e seguindo as mesmas regras de folhas. Assim dá para fabricar tudo de uma vez, sem copiar folha por folha. As faixas individuais de cada sequência continuam logo abaixo, sem nenhuma mudança.

## Por que foi feito

Este projeto nasceu para **automatizar uma tarefa do meu trabalho atual**: montar à mão, no CAD, as folhas de placas de identificação de apartamentos, uma por uma, repetindo o mesmo desenho várias vezes. Era um trabalho lento, repetitivo e fácil de errar (um texto trocado, uma placa fora do lugar, uma folha esquecida). Agora basta colar a lista e gerar o arquivo.

## Como o fluxo funciona

1. **Entrada:** na interface, você cria uma ou mais sequências, dá um nome a cada uma, escolhe o modo de desenho e digita as placas, uma por linha.
2. **Leitura (`constructor.py`):** cada linha não vazia vira uma placa.
3. **Montagem das linhas (`layout.py`):** as placas são distribuídas em linhas de até 620 de largura, passada por passada (todas as de um tamanho primeiro, depois as do próximo).
4. **Divisão em folhas (`layout.py`):** as linhas são empilhadas na folha até esgotar a altura útil (360); o que sobra segue para a próxima folha.
5. **Desenho (`drawer.py` e `core.py`):** retângulos, textos, furos e bordas são escritos no DXF, uma faixa de folhas por sequência (mais a faixa TODAS, se marcada).
6. **Saída:** o arquivo é salvo no local escolhido e a pasta é aberta.

### Estrutura dos arquivos

| Arquivo | Função |
|---|---|
| `gui.py` | interface gráfica (customtkinter); é o que você executa |
| `core.py` | orquestra a geração: modos, sequências, folhas e faixa TODAS |
| `constructor.py` | transforma o texto em placas |
| `layout.py` | distribui as placas em linhas e folhas |
| `drawer.py` | desenha placa, furos, borda e nome da sequência com o ezdxf |
| `handmade.py` | ajusta a altura do texto para caber na placa |
| `Plaq.py` | classe simples de uma placa |

## Como executar

### Requisitos

- Python 3.10 ou superior
- [uv](https://docs.astral.sh/uv/) para gerenciar o ambiente
- Bibliotecas: `ezdxf` e `customtkinter`
- No Linux, o Tkinter precisa estar instalado no sistema (ex.: `sudo apt install python3-tk`). No Windows ele já vem com o Python.

### Instalação

Na pasta do projeto:

```bash
uv add ezdxf customtkinter
```

### Rodando

```bash
uv run gui.py
```

### Passo a passo de uso

1. Em **Nome da sequência**, dê um nome (ex.: `TORRE A`).
2. Escolha em **Desenhar** o modo desejado.
3. Digite ou cole as placas, uma por linha.
4. Use **+ Nova sequência** para adicionar outras.
5. Clique em **Salvar como...** e escolha onde salvar o `.dxf`.
6. Clique em **Gerar DXF**. A pasta do arquivo abre sozinha.

### Atalhos

| Atalho | Ação |
|---|---|
| `Ctrl+N` | nova sequência |
| `Ctrl+1…9` | trocar de sequência |
| `F2` | renomear |
| `Ctrl+S` | salvar como |
| `Ctrl+Enter` | gerar DXF |
| `Ctrl+Delete` | excluir sequência |

### Ajustes rápidos

- **Tamanho da interface:** `ESCALA` no início do `gui.py`.
- **Medidas das folhas, cor e espaçamentos:** constantes no início do `core.py`.
- **Abrir pasta no Windows:** em `gui.py`, na função `abrir_pasta`, troque o `xdg-open` por `os.startfile(pasta)`.

## Limitações conhecidas

- Cada linha é **uma** placa: `APTO 100 APTO 101` na mesma linha vira uma placa só.
- Códigos de texto do CAD como `%%d` ainda são interpretados (`%%d` vira `°`).
- Textos muito longos têm a letra reduzida para caber na placa.
- Nomes de sequência não podem se repetir.

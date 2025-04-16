# Bibliotecas usadas 

- [scrapy (webscraping)](https://anaconda.org/conda-forge/scrapy)
- [transformers (Hugginface)](https://huggingface.co/docs/transformers/installation#conda)

> Recomendo uso do Anaconda ou [Minicoda](https://www.anaconda.com/docs/getting-started/miniconda/install)

# Como rodas as Spiders

Entre no diretório `fin_web_scrap`

```
cd fin_web_scrap
```

Então rode as Spiders para as datas e palavras desejadas

```
scrapy crawl [spider] -a start_date=[data de inicio] -a end_date=[data final] -a search_str=[palavra pesquisada] -o [arquivo de saida].[extensão]
```

## Exemplo

```
scrapy crawl folha -a start_date=01/01/2025 -a end_date=10/01/2025 -a search_str=fiscal -o folha.csv
```

## Opções de spider

- estadao
- g1
- folha

## Opções de saída

- csv
- json
- jsonlines
- jsonl
- jl
- xml 
- marshal
- pickle

# Geração do índice

Definir os arquivos de input 

> O caminho do arquivo deve ser relativo ao diretório em que o usuário está executando o script

```
files = [<caminho do arquivo csv 1>, <caminho do arquivo csv 2>, ...]
```

```
python data_analysis/create_index.py
```
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import json
from urllib.parse import quote

def get_links(search_str, off, size, start_date, end_date):
    params = {
        "mode": "api",
        "size": size,
        "from": off,
        "sort": "date",
        "search_text": search_str,
        "date_range": f"{start_date},{end_date}"
    }
    query = {
        "params": json.dumps(params),
        "requestUri": "/busca"
    }
    query_encoded = quote(json.dumps(query))
    url = f"https://www.estadao.com.br/pf/api/v3/content/fetch/search-story?query={query_encoded}&d=1768&_website=estadao"

    response = requests.get(url)
    response.encoding = "utf-8"

    data = response.json()

    content_elements = data["content_elements"]

    links = []
    for element in content_elements:
        links.append(element["canonical_url"])

    if len(links) == size:
        next_links = get_links(search_str, off + size, size, start_date, end_date)
        return links + next_links
    
    return links

def scrap_estadao_page(url):
    base_url = 'https://www.estadao.com.br'
    
    page = requests.get(base_url + url)
    page.encoding = "utf-8"

    data = BeautifulSoup(page.text, 'html.parser')

    paragraphs = data.select('p[data-component-name="paragraph"], div.paragraph')
    
    paragraphs_list = []
    
    for p in paragraphs:
        paragraphs_list.append(p.text) 
    
    news = {
        "url": base_url + url,
        "paragraphs": paragraphs_list
    }

    return news

def scrap_estadao():
    links = get_all_links_estdadao(range=1)
    
    news = []
    for link in links:
        new = scrap_estadao_page(link)
        news.append(new)

    return news

def get_links_from_scrap(search_str, start_date, end_date, next_page_link=None):
    if next_page_link:
        page = requests.get(next_page_link)
    elif search_str and start_date and end_date:
        search_url = create_search_url(search_str, start_date, end_date)
    
        page = requests.get(search_url)
    else: return []

    data = BeautifulSoup(page.text, 'html.parser')

    links = data.select('div.content-noticias div.content a.headline')

    arrow_foward = data.select('button.arrow.right:not(.cancel)')

    print(arrow_foward)

if __name__ == "__main__":
    # scrap_estadao()
    # get_links_from_scrap('fiscal', '09/04/2015', '10/04/2015', next_page_link='https://www.estadao.com.br/busca/?token=%257B%2522query%2522%253A%2522fiscal%2522%252C%2522date_range%2522%253A%252209%252F04%252F2015%252C10%252F04%252F2015%2522%257D')
    # print(create_search_url('fiscal', '09/04/2015', '10/04/2015'))
    links = get_links('fiscal',0, 100, '11/04/2025', '11/04/2025')
    print(links)
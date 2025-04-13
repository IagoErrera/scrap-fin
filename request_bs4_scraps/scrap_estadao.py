import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import quote
from utils import estadao_date_to_iso

def get_links(search_str, off, size, start_date, end_date):
    base_url = 'https://www.estadao.com.br'

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
    search_url = f"https://www.estadao.com.br/pf/api/v3/content/fetch/search-story?query={query_encoded}&d=1768&_website=estadao"

    response = requests.get(search_url)
    response.encoding = "utf-8"

    data = response.json()

    links = []
    for element in data["content_elements"]:
        links.append(base_url + element["canonical_url"])

    if len(links) == size:
        next_links = get_links(search_str, off + size, size, start_date, end_date)
        return links + next_links
    
    return links

def scrap(url):
    page = requests.get(url)
    page.encoding = "utf-8"

    data = BeautifulSoup(page.text, 'html.parser')

    paragraphs = data.select('p[data-component-name="paragraph"], div.paragraph')
    
    paragraphs_list = []
    
    for p in paragraphs:
        paragraphs_list.append(p.text) 
    
    time = data.find('time')
    print(time.text)

    news = {
        "url": url,
        "paragraphs": '\n'.join(paragraphs_list)
    }

    return news

def scrap_estadao():
    links = get_links(range=1)
    
    news = []
    for link in links:
        new = scrap(link)
        news.append(new)

    return news

if __name__ == "__main__":
    # scrap_estadao()
    # get_links_from_scrap('fiscal', '09/04/2015', '10/04/2015', next_page_link='https://www.estadao.com.br/busca/?token=%257B%2522query%2522%253A%2522fiscal%2522%252C%2522date_range%2522%253A%252209%252F04%252F2015%252C10%252F04%252F2015%2522%257D')
    # print(create_search_url('fiscal', '09/04/2015', '10/04/2015'))
    links = get_links('fiscal',0, 100, '10/04/2025', '11/04/2025')
    # a = scrap(links)
    # print(a)
    print(len(links))
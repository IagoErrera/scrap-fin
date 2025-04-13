import requests
from bs4 import BeautifulSoup
from utils import format_date_folha

def get_links(search_str, start, end, next_page_link=None):
    if next_page_link:
        page = requests.get(next_page_link)
    elif search_str and start and end:
        start_date = format_date_folha(start)
        end_date = format_date_folha(end)
        search_url = f'https://search.folha.uol.com.br/search?q={search_str}&periodo=personalizado&sd={start_date}&ed={end_date}&site=todos'

        page = requests.get(search_url)
    else: return []

    data = BeautifulSoup(page.text, 'html.parser')

    links = data.select('div.c-headline__content a')

    pagination_arrow = data.select('li.c-pagination__arrow a')

    links_list = []
    for link in links:
        links_list.append(link['href'])

    if not pagination_arrow:
        return links_list
    
    next_page = ''
    if not next_page_link: next_page = pagination_arrow[0]['href']
    elif len(pagination_arrow) > 1: next_page = pagination_arrow[1]['href']
     
    if next_page:
        next_list = get_links('','','',next_page_link=next_page)
        
        return links_list + next_list
    
    return links_list

def scrap(link):
    page = requests.get(link)
    page.encoding = "utf-8"

    data = BeautifulSoup(page.text, 'html.parser')

    time = data.select('time')
    if time and time[0] and time[0]['datetime']: time = time[0]['datetime']
    else: time = "Not found"

    paragraphs = data.select('div.c-news__body > p')
    paragraph_list = []
    for p in paragraphs:
        paragraph_list.append(p.text)

    return {"paragraphs": '\n'.join(paragraph_list), "url": link, "pubDate": time}

if __name__ == "__main__":
    links = get_links('fiscal', '01/04/2025', '11/04/2025')

    news_list = []
    for link in links:
        news = scrap(link)
        news_list.append(news)

    print(news_list)
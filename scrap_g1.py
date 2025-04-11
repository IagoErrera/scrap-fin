import requests
from bs4 import BeautifulSoup
from iso_to_urldate import format_date_g1
import re

def get_links_from_scrap(search_str, start_date, end_date, page=1):
    from_date = format_date_g1(start_date)
    to_date = format_date_g1(end_date) # end > start
    search_url = f'https://g1.globo.com/busca/?q={search_str}&page={page}&order=recent&from={from_date}&to={to_date}&species=notícias'

    page = requests.get(search_url)
    page.encoding = "utf-8"

    data = BeautifulSoup(page.text, 'html.parser')

    links = data.select('a.widget--info__media')

    links_list = []
    for l in links:
        link = l.get('href')
        links_list.append(link)
    
    see_more = data.select('div.pagiantion')

    if not see_more: return links_list

    return links_list.extend(get_links_from_scrap(search_str, start_date, end_date, page + 1))

def scrap(link):
    page = requests.get(link)
    page.encoding = "utf-8"
    if ("window.location.replace" in page.text): 
        redirect_regex = re.compile(
            r'(?:window\.location\.replace\(["\']([^"\']+)["\']\)'
            r'|'
            r'<meta[^>]*content=["\'][^;]*URL=([^"\'>]+))'
        )

        match = redirect_regex.search(page.text)

        redirect_url = match.group(1) or match.group(2)

        return scrap(redirect_url)

    data = BeautifulSoup(page.text, 'html.parser')

    paragraph = data.select('p.content-text__container')
    time = data.select('time')
    if time and time[0] and time[0]['datetime']: time = time[0]['datetime']
    else: time = "Not found"

    paragraph_list = []
    for p in paragraph:
        paragraph_list.append(p.text)

    return {"paragraphs": '\n'.join(paragraph_list), "url": link, "pubDate": time }

if __name__ == "__main__":
    links = get_links_from_scrap('fiscal', '01/04/2025', '11/04/2025')

    news_content = []
    for link in links:
        content = scrap('https:' + link)
        news_content.append(content)
import scrapy

import json
from urllib.parse import quote

from fin_web_scrap.items import NewsItem

from datetime import datetime

class EstadaoSpider(scrapy.Spider):
    name = "estadao"
    allowed_domains = ["www.estadao.com.br"]
    
    # Query params
    size = 1000
    off = 0
    search_str = 'fiscal'
    start_date = '10/04/2025'
    end_date = '11/04/2025'
    base_url = 'https://www.estadao.com.br'

    # Auxiliar methods
    def format_date(self, date_time_str):
        data_str, hora_str = date_time_str.split(" | ")
        
        dia, mes, ano = map(int, data_str.split("/"))
        
        hora, minuto = map(int, hora_str.replace("h", ":").split(":"))
        
        data_hora = datetime(ano, mes, dia, hora, minuto)
        
        return data_hora.isoformat()

    def generate_api_url(self):
        params = {
            "mode": "api",
            "size": self.size,
            "from": self.off,
            "sort": "date",
            "search_text": self.search_str,
            "date_range": f"{self.start_date},{self.end_date}"
        }
        query = {
            "params": json.dumps(params),
            "requestUri": "/busca"
        }
        query_encoded = quote(json.dumps(query))
        return f"https://www.estadao.com.br/pf/api/v3/content/fetch/search-story?query={query_encoded}&d=1768&_website=estadao"
    
    # Scrap methods
    def start_requests(self):
        yield scrapy.Request(self.generate_api_url(), callback=self.parse_api)

    def parse_api(self, response):
        data = json.loads(response.text)

        for element in data["content_elements"]:
            yield scrapy.Request(self.base_url + element["canonical_url"], callback=self.parse_news)

        if data["count"] == self.size:
            self.off += self.size
            yield scrapy.Request(self.generate_api_url(), callback=self.parse_api)

    def parse_news(self, response):
        paragraphs = response.css('p[data-component-name="paragraph"]::text, div.paragraph::text').getall()
        time = response.css('time::text').get()

        item = NewsItem()
        item["url"] = response.url
        item["paragraphs"] = ''.join(paragraphs)
        item["pubDate"] = self.format_date(time)
        
        yield item

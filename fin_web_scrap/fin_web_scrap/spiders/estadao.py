import scrapy
from scrapy.spidermiddlewares.httperror import HttpError

import json
from urllib.parse import quote

from fin_web_scrap.items import NewsItem

from datetime import datetime
import math

class EstadaoSpider(scrapy.Spider):
    name = "estadao"
    allowed_domains = ["www.estadao.com.br"]
    
    # Query params
    size = 100
    off = 0
    search_str = 'fiscal'
    start_date = '01/01/2024'
    end_date = '01/01/2025'
    base_url = 'https://www.estadao.com.br'

    # Auxiliar methods
    def format_date(self, date_time_str):
        try:
            data_str, hora_str = date_time_str.split(" ")
            
            dia, mes, ano = map(int, data_str.split("/"))
            
            hora, minuto = map(int, hora_str.replace("h", ":").split(":")) if hora and minuto else 0, 0
            
            data_hora = datetime(ano, mes, dia, hora, minuto)
            
            return data_hora.isoformat()
        except:
            return math.nan

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
    
    def err_request(self, failure):
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error("HttpError on %s", response.url)

    # Scrap methods
    def start_requests(self):
        yield scrapy.Request(self.generate_api_url(), callback=self.parse_api)

    def parse_api(self, response):
        data = json.loads(response.text)

        for element in data["content_elements"]:
            yield scrapy.Request(self.base_url + element["canonical_url"], callback=self.parse_news)

        if len(data["content_elements"]) == self.size:
            self.off += self.size
            yield scrapy.Request(self.generate_api_url(), callback=self.parse_api, errback=self.err_request)

    def parse_news(self, response):
        paragraphs = response.css('p[data-component-name="paragraph"]::text, div.paragraph::text').getall()
        time = response.css('time::text').getall()

        if len(time) > 2 and "|" in time[1]:
            time = ''.join(time[0:3])
        else:
            time = time[0]

        item = NewsItem()
        item["url"] = response.url
        item["paragraphs"] = ''.join(paragraphs)
        item["pubDate"] = self.format_date(time) if time else math.nan
        
        yield item

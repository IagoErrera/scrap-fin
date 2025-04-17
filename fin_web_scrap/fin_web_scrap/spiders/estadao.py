import scrapy
from scrapy.spidermiddlewares.httperror import HttpError

import json
from urllib.parse import quote, urlencode

from fin_web_scrap.items import NewsItem

from datetime import datetime
import math

class EstadaoSpider(scrapy.Spider):
    name = "estadao"
    allowed_domains = ["www.estadao.com.br"]
    
    # Query params
    size = 100
    off = 0
    base_url = 'https://www.estadao.com.br'

    def __init__(self, start_date=None, end_date=None, search_str=None, start_url=None, *args, **kwargs):
        super(EstadaoSpider, self).__init__(*args, **kwargs)
        if start_date: self.start_date = start_date  
        if end_date: self.end_date = end_date  
        if search_str: self.search_str = search_str  

    # Auxiliar methods
    def format_date(self, date_time_str):
        try:
            split_data = date_time_str.split(" | ")

            date = split_data[0].split("/")

            if len(split_data) > 1:
                time = split_data[1].split("h")
            else:
                time = [0, 0]

            date_time = datetime(year=int(date[2]), month=int(date[1]), day=int(date[0]), hour=int(time[0]), minute=int(time[1]))

            return date_time.isoformat()
        except:
            return math.nan

    def generate_api_url(self):
        inner_params = {
            "mode": "api",
            "size": self.size,
            "from": self.off,
            "sort": "date",
            "search_text": self.search_str,
            "date_range": f"{self.start_date},{self.end_date}"
        }
        inner_params_str = json.dumps(inner_params, separators=(",", ":"))

        outer_query = {
            "params": inner_params_str,
            "requestUri": "/busca"
        }

        query_str = json.dumps(outer_query, separators=(",", ":"))

        url_params = {
            "query": query_str,
            "d": 1776,
            "_website": "estadao"
        }


        encoded_params = urlencode(url_params, quote_via=quote)

        base_url = "https://www.estadao.com.br/pf/api/v3/content/fetch/search-story"
        url = f"{base_url}?{encoded_params}"

        return url
    
    def err_request(self, failure):
        print("ERROR ON REQUEST")

        self.logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error("HttpError on %s", response.url)

    # Scrap methods
    def start_requests(self):
        yield scrapy.Request(self.generate_api_url(), callback=self.parse_api)

    def parse_api(self, response):
        try:
            data = json.loads(response.text)

            for element in data["content_elements"]:
                yield scrapy.Request(self.base_url + element["canonical_url"], callback=self.parse_news)

            if len(data["content_elements"]) == self.size:
                self.off += self.size
                url = self.generate_api_url()
                print(url)
                yield scrapy.Request(url, callback=self.parse_api, errback=self.err_request)
        except:
            print("ERROR ON PARSE API: ", response.uri)

    def parse_news(self, response):
        try: 
            paragraphs = response.css('p[data-component-name="paragraph"]::text, div.paragraph::text').getall()
            time = response.css('time::text').getall()

            if len(time) > 2 and "|" in time[1]:
                time = ''.join(time[0:3])
            else:
                time = time[0]

            paragraphs_str = ''.join(paragraphs)

            if not (self.search_str in paragraphs_str): return
            if time == "#": return
            if time and 'T' in time: time = time.split('T')[0]

            item = NewsItem()
            item["url"] = response.url
            item["paragraphs"] = paragraphs_str.replace('\n', '').replace('\r', '')
            item["pubDate"] = self.format_date(time)
            
            yield item
        except:
            print("ERROR ON PARSE NEWS: ", response.uri)

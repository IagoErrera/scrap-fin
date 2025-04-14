import scrapy
from scrapy.spidermiddlewares.httperror import HttpError

import json
from urllib.parse import quote

from fin_web_scrap.items import NewsItem

from datetime import datetime
import math

# from transformers import (
#     AutoTokenizer,
#     BertForSequenceClassification,
#     pipeline,
# )

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

        # self.finbert_pt_br_tokenizer = AutoTokenizer.from_pretrained("lucas-leme/FinBERT-PT-BR")
        # self.finbert_pt_br_model = BertForSequenceClassification.from_pretrained("lucas-leme/FinBERT-PT-BR")
        # self.finbert_pt_br_pipeline = pipeline(task='text-classification', model=self.finbert_pt_br_model, tokenizer=self.finbert_pt_br_tokenizer)

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

    # def get_chuncks(self, text, max_tokens=400, overlap=50):
    #     tokens = self.finbert_pt_br_tokenizer.tokenize(text)
    #     chunks = []

    #     start = 0
    #     while start < len(tokens):
    #         end = start + max_tokens
    #         chunk = tokens[start:end]
    #         chunks.append(self.finbert_pt_br_tokenizer.convert_tokens_to_string(chunk))
    #         start = end - overlap

    #     return chunks

    # def get_index(self, text):
    #     chunks = self.get_chuncks(text)
        
    #     pred = self.finbert_pt_br_pipeline(chunks)

    #     positive = 0
    #     negative = 0
    #     neutral = 0
    #     for p in pred:
    #         if p['label'] == "POSITIVE": positive += 1
    #         elif p['label'] == "NEGATIVE": negative += 1
    #         else: neutral += 1
        
    #     if positive > negative: return 1
    #     elif negative > positive: return -1
    #     else: return 0

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

        try:
            if len(time) > 2 and "|" in time[1]:
                time = ''.join(time[0:3])
            else:
                time = time[0]
        except:
            print(time)

        paragraphs_str = ''.join(paragraphs)

        item = NewsItem()
        item["url"] = response.url
        item["paragraphs"] = paragraphs_str
        item["pubDate"] = self.format_date(time)
        # item["sentiment"] = self.get_index(paragraphs_str)
        
        yield item

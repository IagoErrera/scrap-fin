import scrapy
from scrapy.spidermiddlewares.httperror import HttpError

from fin_web_scrap.items import NewsItem

from transformers import (
    AutoTokenizer,
    BertForSequenceClassification,
    pipeline,
)

class FolhaSpider(scrapy.Spider):
    name = "folha"
    # allowed_domains = ["search.folha.uol.com.br"]

    # search_str = 'fiscal'
    # start_date = '01/01/2010'
    # end_date = '13/04/2025'
    page = 1

    def __init__(self, start_date=None, end_date=None, search_str=None, start_url=None, *args, **kwargs):
        super(FolhaSpider, self).__init__(*args, **kwargs)
        self.start_date = start_date  
        self.end_date = end_date  
        self.search_str = search_str

        # self.finbert_pt_br_tokenizer = AutoTokenizer.from_pretrained("lucas-leme/FinBERT-PT-BR")
        # self.finbert_pt_br_model = BertForSequenceClassification.from_pretrained("lucas-leme/FinBERT-PT-BR")
        # self.finbert_pt_br_pipeline = pipeline(task='text-classification', model=self.finbert_pt_br_model, tokenizer=self.finbert_pt_br_tokenizer)

    def format_date(self, date_str):
        return date_str.replace("/", "%2F") 

    def generate_url(self):
        start_date = self.format_date(self.start_date)
        end_date = self.format_date(self.end_date)
        return f'https://search.folha.uol.com.br/search?q={self.search_str}&periodo=personalizado&sd={start_date}&ed={end_date}&site=todos'

    def get_chuncks(self, text, max_tokens=400, overlap=50):
        tokens = self.finbert_pt_br_tokenizer.tokenize(text)
        chunks = []

        start = 0
        while start < len(tokens):
            end = start + max_tokens
            chunk = tokens[start:end]
            chunks.append(self.finbert_pt_br_tokenizer.convert_tokens_to_string(chunk))
            start = end - overlap

        return chunks

    def get_index(self, text):
        chunks = self.get_chuncks(text)
        
        pred = self.finbert_pt_br_pipeline(chunks)

        positive = 0
        negative = 0
        neutral = 0
        for p in pred:
            if p['label'] == "POSITIVE": positive += 1
            elif p['label'] == "NEGATIVE": negative += 1
            else: neutral += 1
        
        if positive > negative: return 1
        elif negative > positive: return -1
        else: return 0

    def err_request(self, failure):
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error("HttpError on %s", response.url)

    def start_requests(self):
        yield scrapy.Request(self.generate_url(), callback=self.parse_search, errback=self.err_request)

    def parse_search(self, response):
        links = response.css('div.c-headline__content a::attr(href)').getall()
        page_navigator = response.css('li.c-pagination__arrow a::attr(href)').getall()

        for link in links:
            yield scrapy.Request(link, callback=self.parse_news, errback=self.err_request)
        
        if page_navigator:
            if self.page == 1:
                self.page += 1
                print("\r\n\r\n")
                print(f"Next Page: {self.page}")
                print(f"Next Page Link: {page_navigator[0]}")
                print("\r\n\r\n")
                yield scrapy.Request(page_navigator[0], callback=self.parse_search, errback=self.err_request)
            elif len(page_navigator) == 2:
                yield scrapy.Request(page_navigator[1], callback=self.parse_search, errback=self.err_request)

    def parse_news(self, response):
        paragraphs = response.css('div.c-news__body > p::text').getall()
        time = response.css('time::attr(datetime)').get()

        paragraphs_str = ''.join(paragraphs)

        item = NewsItem()
        item["url"] = response.url
        item["paragraphs"] = paragraphs_str 
        item["pubDate"] = time
        # item["sentiment"] = self.get_index(paragraphs_str)

        yield item
import scrapy
from scrapy.spidermiddlewares.httperror import HttpError

from fin_web_scrap.items import NewsItem

class FolhaSpider(scrapy.Spider):
    name = "folha"
    # allowed_domains = ["search.folha.uol.com.br"]

    search_str = 'fiscal'
    start_date = '01/01/2024'
    end_date = '01/01/2025'
    page = 1

    def format_date(self, date_str):
        return date_str.replace("/", "%2F") 

    def generate_url(self):
        start_date = self.format_date(self.start_date)
        end_date = self.format_date(self.end_date)
        return f'https://search.folha.uol.com.br/search?q={self.search_str}&periodo=personalizado&sd={start_date}&ed={end_date}&site=todos'

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
                yield scrapy.Request(page_navigator[0], callback=self.parse_search, errback=self.err_request)
            elif len(page_navigator) == 2:
                yield scrapy.Request(page_navigator[1], callback=self.parse_search, errback=self.err_request)

    def parse_news(self, response):
        paragraphs = response.css('div.c-news__body > p::text').getall()
        time = response.css('time::attr(datetime)').get()

        item = NewsItem()
        item["url"] = response.url
        item["paragraphs"] = ''.join(paragraphs)
        item["pubDate"] = time

        yield item
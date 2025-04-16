import re
import scrapy
from scrapy.spidermiddlewares.httperror import HttpError

from fin_web_scrap.items import NewsItem

from datetime import datetime

class FolhaSpider(scrapy.Spider):
    name = "folha"

    page = 1
    month_list = {
        'janeiro': 1,
        'fevereiro': 2,
        'março': 3,
        'abril': 4,
        'maio': 5,
        'junho': 6,
        'julho': 7,
        'agosto': 8,
        'setembro': 9,
        'outubro': 10,
        'novembro': 11,
        'dezembro': 12,
        'jan': 1,
        'fev': 2,
        'mar': 3,
        'abr': 4,
        'maio': 5,
        'jun': 6,
        'jul': 7,
        'ago': 8,
        'set': 9,
        'out': 10,
        'nov': 11,
        'dez': 12
    }

    def __init__(self, start_date=None, end_date=None, search_str=None, start_url=None, *args, **kwargs):
        super(FolhaSpider, self).__init__(*args, **kwargs)
        self.start_date = self.format_date(start_date)  
        self.end_date = self.format_date(end_date)  
        self.search_str = search_str

    def format_date(self, date_str):
        return date_str.replace("/", "%2F") 

    def parse_date(self, date_str):
        try:
            date = date_str.split(' às ')[0]
            date = date.split('.')
            month_n = self.month_list.get(date[1].lower())
            return datetime(day=int(date[0]), month=month_n, year=int(date[2])).date().isoformat()
        except:
            return
    
    def generate_url(self):
        start_date = self.format_date(self.start_date)
        end_date = self.format_date(self.end_date)
        return f'https://search.folha.uol.com.br/search?q={self.search_str}&periodo=personalizado&sd={start_date}&ed={end_date}&site=todos'

    def err_request(self, failure):
        print("Error on Request")
        
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
        try:
            paragraphs = response.css('div.contentContainer p::text').getall()
            time = response.css('meta[name=date]::attr(content)').get()
            if time:
                time = time.split(' ')[1]
                split_time = time.split('/')
                time = f"{split_time[2]}-{split_time[1]}-{split_time[0]}"
            if not paragraphs or not time:
                paragraphs = response.css('article.news div.news__content p::text').getall()
                time = response.css('time::attr(datetime)').get()
            if not paragraphs or not time:
                paragraphs = response.css('div[id=articleNew] p::text').getall()
                time = response.css('meta[name=date]::attr(content)').get()
                if time:
                    s_time = time.split(' ')
                    time = s_time[1] if len(s_time) > 1 else time
                    split_time = time.split('/')
                    time = f"{split_time[2]}-{split_time[1]}-{split_time[0]}"
                if not paragraphs or not time:
                    paragraphs = response.css('div.c-news__content p::text').getall()
                    time = response.css('time::attr(datetime)').get()
                    if time:
                        time = time.split(' ')[0] 
                if not paragraphs or not time:
                    paragraphs = response.css('article.news div.news__content p::text, article.c-news div.c-news__content p::text').getall()
                    time = response.css('time::text').get()
                    if not time: time = response.css('time::attr(datetime)').get()
                    if time: 
                        p_time = self.parse_date(time)
                        if not p_time:
                            time = time.split(' ')[0]
                        else:
                            time = p_time 
                if not paragraphs or not time:
                    paragraphs = response.xpath('//td/text()').getall()
                    time = response.css('meta[name=date]::attr(content)').get()
                    if time:
                        time = time.split(' ')[1]
                        split_time = time.split('/')
                        time = f"{split_time[2]}-{split_time[1]}-{split_time[0]}"
                if not paragraphs or not time:
                    paragraphs = response.css('article.news div.content p::text').getall()
                    time = response.css('time::attr(datetime)').getall()
                    if time:
                        time = time[len(time)-1]
                        time = time.split(' ')[0]
                if not paragraphs or not time:
                    paragraphs = response.css('div.content p::text').getall()
                    time = response.css('time::attr(datetime)').getall()
                    if time:
                        time = time[len(time)-1]
                        time = time.split(' ')[0]
                if not paragraphs or not time:
                    script = response.xpath('//script[contains(., "location.replace")]/text()').get()
                    if script:
                        redirect = re.search(r'location\.replace\(\s*"([^"]+)"\s*\)', script).group(1)

                        yield scrapy.Request(redirect, callback=self.parse_news, errback=self.err_request)
                        return
            if not paragraphs or not time:
                paragraphs = response.css('div.c-news__body > p::text').getall()
                time = response.css('time::attr(datetime)').get()

            paragraphs_str = ''.join(paragraphs)

            if paragraphs_str == "": print("Error: ", response.url)
            if not self.search_str in paragraphs_str: return 

            item = NewsItem()
            item["url"] = response.url
            item["paragraphs"] = paragraphs_str.replace('\n', '').replace('\r', '') 
            item["pubDate"] = time

            yield item
        except:
            print("ERROR: ", response.url)
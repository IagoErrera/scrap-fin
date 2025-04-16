import math
import scrapy
from scrapy.spidermiddlewares.httperror import HttpError

from fin_web_scrap.items import NewsItem

from datetime import datetime

class G1Spider(scrapy.Spider):
    name = "g1"
    allowed_domains = ["g1.globo.com"]
    start_urls = ["https://g1.globo.com/sitemap/g1/sitemap.xml"]
    iterator = "iternodes"
    itertag = "item"

    page = 1

    def __init__(self, start_date=None, end_date=None, search_str=None, start_url=None, *args, **kwargs):
        super(G1Spider, self).__init__(*args, **kwargs)
        self.start_date = start_date  
        self.end_date = end_date  
        self.search_str = search_str 

    def format_date(self, date_time_str):
        try:
            date, hour_str = date_time_str.split(" | ") if " | " in date_time_str else date_time_str, None
            
            day, month, year = map(int, date.split("/"))
            
            hour, minute = map(int, hour_str.replace("h", ":").split(":")) if hour_str else 0, 0
            
            date_hour = datetime(year, month, day, hour, minute)
            
            return date_hour.isoformat()
        except:
            return math.nan

    def generate_allowed_datas(self):
        s_day, s_month, s_year = self.start_date.split('/')
        e_day, e_month, e_year = self.end_date.split('/')
        
        s_day, s_month, s_year = int(s_day), int(s_month), int(s_year)
        e_day, e_month, e_year = int(e_day), int(e_month), int(e_year)
        
        e_day += 1
        if e_day > 31:
            e_month += 1
            e_day = 1
        if e_month > 12:
            e_year += 1
            e_month = 1

        self.dates_list = []
        while not (s_day == e_day and s_month == e_month and s_year == e_year):
            date = f"{s_year}/{s_month if s_month > 9 else f'0{s_month}'}/{s_day if s_day > 9 else f'0{s_day}'}"
            self.dates_list.append(date)

            s_day += 1
            if s_day > 31:
                s_month += 1
                s_day = 1
            if s_month > 12:
                s_year += 1
                s_month = 1

        date = f"{s_year}/{s_month if s_month > 9 else f'0{s_month}'}/{s_day if s_day > 9 else f'0{s_day}'}"
        self.dates_list.append(date)

    def err_request(self, failure):
        print("Error on Request")

        self.logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error("HttpError on %s", response.url)

    def start_requests(self):
        self.generate_allowed_datas()
        return super().start_requests()

    def parse(self, response):
        try:
            if not ('sitemap' in response.url):
                news_item = self.parse_news(response)
                if news_item and news_item is not None: yield news_item 
            else:
                response.selector.register_namespace("ns", "http://www.sitemaps.org/schemas/sitemap/0.9")
                items = response.xpath("//ns:sitemap/ns:loc/text()").getall() if response.url == 'https://g1.globo.com/sitemap/g1/sitemap.xml' else response.xpath("//ns:url/ns:loc/text()").getall()

                if response.url == "https://g1.globo.com/sitemap/g1/sitemap.xml":
                    for item in items:
                        for date in self.dates_list:
                            if date in item:
                                yield scrapy.Request(item, callback=self.parse, errback=self.err_request)
                else:
                    for item in items:
                        yield scrapy.Request(item, callback=self.parse_news, errback=self.err_request)
        except:
            print("PARSE ERROR: ", response.url)

    def parse_news(self, response):
        try:
            if 'ghtml' in response.url:
                paragraphs = response.css('p.content-text__container::text, blockquote.content-blockquote::text').getall()
                time = response.css('time::attr(datetime)').get()
            elif 'html' in response.url:
                # print('1')
                paragraphs = response.css('div.materia-conteudo p::text').getall()
                # print('2')
                time = response.css('meta[property="article:published_time"]::attr(content)').get()
                # print('3')
                if (not time) or (time == 'g1'):
                    time = response.css('time.post-date::attr(datetime)').get()
                # print('3.1')

                if not paragraphs:
                    paragraphs = response.css('section.post-content p::text').getall()
                
                # print('4')
            else:
                paragraphs = response.css('div.entry p::text').getall()
                time = response.css('div.time small:text').get()
                if time:
                    time = time.split(', ')[1]

            # print('5')
            # print('p: ', paragraphs)
            # print('t: ', time)
            paragraphs_str = ''.join(paragraphs) if paragraphs else ''
            # print('6')

            if not (self.search_str in paragraphs_str): return
            # print('7')

            item = NewsItem()
            item["url"] = response.url
            item["paragraphs"] = paragraphs_str
            item["pubDate"] = time

            return item
        except:
            print("PARSE NEWS ERROR: ", response.url)
            return
    

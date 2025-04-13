import math
import scrapy
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.http import HtmlResponse

from fin_web_scrap.items import NewsItem

from datetime import datetime

# Reestruturar de forma a usar o sitemap para pegar as notícias
# Fazer a busca das palavras manualmente nas notícias

class G1Spider(scrapy.Spider):
    name = "g1"
    allowed_domains = ["g1.globo.com"]
    start_urls = ["https://g1.globo.com/sitemap/g1/sitemap.xml"]
    # start_urls = ["https://g1.globo.com/jornal-nacional/noticia/2025/04/11/lula-usa-expressao-machista-para-se-referir-a-presidente-do-fmi-mulherzinha.ghtml"]
    # start_urls = ["https://g1.globo.com/sitemap/g1/2025/04/12_1.xml"]
    iterator = "iternodes"
    itertag = "item"

    search_str = 'fiscal'
    start_date ='10/04/2025'
    end_date = '11/04/2025'
    page = 1
    
    def format_date(self, date_time_str):
        try:
        
            data_str, hora_str = date_time_str.split(" | ") if " | " in date_time_str else date_time_str, None
            
            dia, mes, ano = map(int, data_str.split("/"))
            
            hora, minuto = map(int, hora_str.replace("h", ":").split(":")) if hora_str else 0, 0
            
            data_hora = datetime(ano, mes, dia, hora, minuto)
            
            return data_hora.isoformat()
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
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error("HttpError on %s", response.url)

    def start_requests(self):
        self.generate_allowed_datas()
        return super().start_requests()

    def parse(self, response):
        if not ('sitemap' in response.url):
            news_item = self.parse_news(response)
            if news_item: yield news_item 
        else:
            response.selector.register_namespace("ns", "http://www.sitemaps.org/schemas/sitemap/0.9")
            items = response.xpath("//ns:sitemap/ns:loc/text()").getall() if response.url == 'https://g1.globo.com/sitemap/g1/sitemap.xml' else response.xpath("//ns:url/ns:loc/text()").getall()

            for item in items:
                for date in self.dates_list:
                    if date in item:
                        print(item)
                        yield scrapy.Request(item, callback=self.parse, errback=self.err_request)

    def parse_news(self, response):
        try:
            if 'ghtml' in response.url:
                paragraphs = response.css('p.content-text__container::text, blockquote.content-blockquote::text').getall()
                time = response.css('time::attr(datetime)').get()
            else:
                paragraphs = response.css('div.materia-conteudo p::text').getall()
                time = response.css('abbr.published::attr(datetime)').get()

            paragraphs_str = ''.join(paragraphs) if paragraphs else ''

            if not (self.search_str in paragraphs_str): return None

            item = NewsItem()
            item["url"] = response.url
            item["paragraphs"] = paragraphs_str
            item["pubDate"] = time

            return item
        except:
            return None
    

import scrapy
from scrapy.spidermiddlewares.httperror import HttpError

from datetime import timezone, timedelta, datetime

# Reestruturar de forma a usar o sitemap para pegar as notícias
# Fazer a busca das palavras manualmente nas notícias

class G1Spider(scrapy.Spider):
    name = "g1"
    allowed_domains = ["g1.globo.com"]

    search_str = 'fiscal'
    start_date ='10/04/2025'
    end_date = '11/04/2025'
    page = 1
    
    def format_date(self, date_str):
        tz = timezone(timedelta(hours=-3))

        iso = datetime.strptime(date_str, "%d/%m/%Y").replace(hour=0, minute=0, second=0, tzinfo=tz).isoformat()
        iso = iso.replace("-03:00", "-0300")  
        iso = iso.replace(":", "%3A")  
        return iso

    def generate_search_news_url(self):
        from_date = self.format_date(self.start_date)
        to_date = self.format_date(self.end_date)
        return f'https://g1.globo.com/busca/?q={self.search_str}&page={self.page}&order=recent&from={from_date}&to={to_date}&species=notícias'

    def start_requests(self):
        # url = self.generate_search_news_url()
        yield {"status": 1}
        url = 'https://g1.globo.com/pa/santarem-regiao/noticia/2025/03/07/arquidiocese-de-santarem-abre-campanha-da-fraternidade-2025-com-missa-presidida-por-dom-irineu-roman.ghtml'
        yield scrapy.Request(url, callback=self.parse_search, errback=self.err_request)

    def err_request(self, failure):
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error("HttpError on %s", response.url)

        yield {"status": "error"}


    def parse_search(self, response):
        # yield { "url": response.url }
        yield {"status": 2}
        links = response.css('a.widget--info__media::attr(href)').getall()
        yield {"status": 3}

        for link in links:
            # yield scrapy.Request(link, callback=self.parse_news)
            pass

        yield {"status": 4}

        next_page = response.css('div.pagination').get()

        yield {"status": 5}

        if next_page:
            self.page += 1
            # yield scrapy.Request(self.generate_search_news_url(), callback=self.parse_search)
        
        yield {"status": 6}

    def parse_news(self, response):
        yield {"status": 7}
        yield { "url": response.url }
    

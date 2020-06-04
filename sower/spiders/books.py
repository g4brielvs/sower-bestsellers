# -*- coding: utf-8 -*-
import scrapy


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["simonandschuster.com"]
    start_urls = ["http://www.simonandschuster.com/search/books/"]

    def parse(self, response):

        for item in response.css(".is-clipped"):
            yield {
                "title": item.css("a.has-text-weight-bold::text").extract_first(),
                "author": item.css("p > a::text").extract(),
                "link": item.css("a.has-text-weight-bold::attr(href)").extract_first(),
            }

        # follow pagination
        next_page_url = response.css(".pagination-next::attr(href)").extract_first()
        next_page_url = response.urljoin(next_page_url)

        if next_page_url:
            yield scrapy.Request(url=next_page_url, callback=self.parse)

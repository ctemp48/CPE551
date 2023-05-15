import scrapy
import scrapy_splash
from scrapy.crawler import CrawlerProcess
from scrapy_splash import SplashRequest
from scrapy_selenium import SeleniumRequest
from scrapy.utils.response import open_in_browser
import json
import csv
import re

class IdeaSpider(scrapy.Spider):
    name = "IdeaSpider"

    # Lands at the browse page for ideas
    def start_requests(self):
        script = '''
        function main(splash)
            local num_scrolls = 110
            local scroll_delay = 1

            local scroll_to = splash:jsfunc("window.scrollTo")
            local get_body_height = splash:jsfunc(
                "function() {return document.body.scrollHeight;}"
            )
            assert(splash:go(splash.args.url))
            splash:wait(splash.args.wait)

            for _ = 1, num_scrolls do
                scroll_to(0, get_body_height())
                splash:wait(scroll_delay)
            end        
            return splash:html()
        end
            '''
        yield SplashRequest(url="https://community.amplitude-studios.com/amplitude-studios/endless-space-2/ideas",
                            callback=self.parse_url,
                            endpoint='execute',
                            args={
                                'wait': 2,
                                'timeout': 3600,
                                'lua_source': script
                            }
                            )

    def parse_url(self, response):
        post_links = response.xpath('//a[@class = "content-infos-link"]/@href').extract()
        post_links_to_follow = list()
        for link in post_links:
            link += "?page=0"
            link = "https://www.games2gether.com" + link
            link = link.replace("-redirect", "")
            post_links_to_follow.append(link)
        script2 = '''
        function main(splash, args)
            assert(splash:go(args.url))
            assert(splash:wait(splash.args.wait))
            return splash:html()
        end
'''

        for url in post_links_to_follow:
            yield SplashRequest(url=url,
                                callback=self.parse_idea,
                                args={'wait': 4}
                                )


# parses title, post, status, author, date

    def parse_idea(self, response):
        post_link = response.url
        thread_id = post_link[(post_link.find('ideas/') + 6):(post_link.find('ideas/') + 10)]
        thread_id = re.sub(r'[^\d]+', '', thread_id)
        post_id_def = '4_' + thread_id + '_'

        idea_list = list()
        idea_list.append(post_id_def + "1")
        idea_list.append(response.xpath('//span[@class = "username-content"]/text()').extract_first())
        idea_list.append("No")
        idea_list.append(response.xpath('//div[@class = "time-date"]/text()').extract_first())
        categories = response.xpath('//a[@class = "list-tags-item ng-star-inserted"]/text()').extract()
        if len(categories) > 1:
            categories_combined = ""
            for text in categories:
                categories_combined = categories_combined + text + ", "
            idea_list.append(categories_combined)
        elif len(categories) == 1:
            idea_list.append(categories[0])
        idea_list.append(response.xpath('//h1[@class = "title"]/text()').extract_first())
        status = response.xpath('//p[@class = "status-title"]/text()').extract()
        if len(status) == 0:
            idea_list.append("No Status")
        else:
            idea_list.append(status[0])
        main_body = response.xpath('//article[@class = "post-list-item clearfix ng-star-inserted"]//div[@class = "post-list-item-message-content post-content ng-star-inserted"]//text()').extract()
        if len(main_body) > 1:
            main_body_combined = ""
            for text in main_body:
                main_body_combined += text + " "
            idea_list.append(main_body_combined)
        elif len(main_body) == 1:
            idea_list.append(main_body[0])
        else:
            idea_list.append(" ")
        main_image_links = response.xpath('//article[@class = "post-list-item clearfix ng-star-inserted"]//div[@class = "post-list-item-message-content post-content ng-star-inserted"]//img/@src').extract()
        for link in main_image_links:
            if link.find('emoticons') == -1:
                idea_list.append(link)
        all_post_data.append(idea_list)

        dev_comment = response.xpath('//div[@class = "ideas-details-status clearfix u-bdcolor-2 u-bgcolor-2 ng-star-inserted"]//div[@class = "message post-content ng-star-inserted"]//text()').extract()
        if len(dev_comment) != 0:
            dev_comment_list = list()
            dev_comment_list.append(post_id_def + "2")
            dev_comment_list.append(response.xpath('//div[@class = "ideas-details-status-comment user-role u-bdcolor-2 dev"]//p[@class = "username user-role-username"]/text()').extract_first())
            dev_comment_list.append("Yes")
            dev_comment_list.append("N/A")
            if len(categories) > 1:
                categories_combined = ""
                for text in categories:
                    categories_combined += text + ", "
                dev_comment_list.append(categories_combined)
            elif len(categories) == 1:
                dev_comment_list.append(categories[0])
            dev_comment_list.append(response.xpath('//h1[@class = "title"]/text()').extract_first())
            if len(status) == 0:
                dev_comment_list.append("No Status")
            else:
                dev_comment_list.append(status[0])
            if len(dev_comment) > 1:
                dev_comment_combined = ""
                for text in dev_comment:
                    dev_comment_combined += text + " "
                dev_comment_list.append(dev_comment_combined)
            else:
                dev_comment_list.append(dev_comment[0])
            all_post_data.append(dev_comment_list)

        comment_number = len(response.xpath('//g2g-comments-list/section/div/g2g-comments-item'))
        comment_index = 1
        comment_index_adj = 1
        while comment_index <= comment_number:
            temp_list = list()

            post_path = '//g2g-comments-list/section/div/g2g-comments-item[1]'
            post_path = post_path.replace('1', str(comment_index))
            post = response.xpath(post_path)

            if len(post.xpath('.//p[@class = "status-title"]').extract()) != 0:
                comment_index += 1
                continue
            if len(dev_comment) != 0:
                post_id = post_id_def + str(comment_index_adj + 2)
            else:
                post_id = post_id_def + str(comment_index_adj + 1)
            temp_list.append(post_id)

            username = post.xpath('.//span[@class = "username-content"]/text()').extract_first()
            test = ""
            temp_list.append(username)

            role = post.xpath('.//p[@class = "username user-role-username"]//span[@class = "role ng-star-inserted"]/text()').extract_first()
            if role is not None:
                if role == 'DEV' or role == 'ADMIN':
                    temp_list.append('Yes')
                else:
                    temp_list.append('No')
            else:
                temp_list.append('No')

            timestamp = post.xpath('.//div[@class = "time-date"]/text()').extract_first()
            temp_list.append(timestamp)

            if len(categories) > 1:
                categories_combined = ""
                for text in categories:
                    categories_combined += text + ", "
                temp_list.append(categories_combined)
            elif len(categories) == 1:
                temp_list.append(categories[0])

            temp_list.append(response.xpath('//h1[@class = "title"]/text()').extract_first())

            if len(status) == 0:
                temp_list.append("No Status")
            else:
                temp_list.append(status[0])

            body = post.xpath('.//div[@class = "post-list-item-message-content post-content ng-star-inserted"]//text()').extract()
            num_quotes = len(post.xpath('.//blockquote'))
            quote_path = './/div[@class = "post-list-item-message-content post-content ng-star-inserted"]/blockquote[1]//text()'
            quotes_combined_edit = list()
            quote_count = 1
            quote = list()
            while quote_count <= num_quotes:
                quotes = post.xpath(quote_path.replace('1', str(quote_count))).extract()
                if len(quotes) > 1:
                    quotes_combined = ""
                    for text in quotes:
                        quotes_combined = quotes_combined + " " + text
                    quote.append(quotes_combined)
                elif len(quotes) == 1:
                    quotes_combined = quotes[0]
                    quote.append(quotes_combined)
                quote_count += 1
            for text in quote:
                quotes_combined_edit.append("<>" + text + "<*>")
            if len(body) > 1:
                body_combined = ""
                for text in body:
                    body_combined = body_combined + " " + text
                for q, qe in zip(quote, quotes_combined_edit):
                    body_combined = body_combined.replace(q, qe)
                temp_list.append(body_combined)
            elif len(body) == 1:
                if len(quote) != 0:
                    for q, qe in zip(quote, quotes_combined_edit):
                        body_combined = body_combined.replace(q, qe)
                else:
                    body_combined = body[0]
                temp_list.append(body_combined)
            else:
                temp_list.append("No post body.")


            comment_index += 1
            comment_index_adj += 1
            all_post_data.append(temp_list)

#must delete weird a with space after

all_post_data = list()

process = CrawlerProcess()
process.crawl(IdeaSpider)
process.start()
header = ["ID", "Username", "Dev/Admin", "Timestamp", "Categories", "Thread Title", "Status", "Text", "Image Link"]
with open('ideas.csv', 'w', newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(all_post_data)

# -*- coding: utf-8 -*-
import scrapy
import re
import json
from PIL import Image
from urllib import parse
from scrapy.loader import ItemLoader
# from zhihuCrawler.items import ZhihuQuestionItem, ZhihuAnswerItem
from zhihuCrawler.items import ZhihuAnswerItem, ZhihuQuestionItem

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['zhihu.com']
    start_urls = ['http://zhihu.com/']

    agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3141.7 Safari/537.36"

    headers = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com/",
        "User-Agent": agent
    }

    def parse(self, response):
        # dfs search: crawl all url(like /question/xxx) in a html file
        all_urls = [parse.urljoin(response.url, url) for url in response.css("a::attr(href)").extract()]
        all_urls = filter(lambda x: True if x.startswith("https://") else False, all_urls)
        for url in all_urls:
            match_obj = re.match("(.*?zhihu.com/question/(\d+))(/|$)", url)
            if match_obj:
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)
                yield scrapy.Request(request_url, headers=self.headers, meta={'question_id': question_id}, callback=self.parse_question)

    def parse_question(self, response):
        # extract question item
        # new version of zhihu question html

        question_id  = int(response.meta.get('question_id'))
        if "QuestionHeader-title" in response.text:
            item_loader = ItemLoader(item=ZhihuQuestionItem, response=response)
            item_loader.add_value('zhihu_id', question_id)
            item_loader.add_css('topics', '.Tag.QuestionTopic div.Popover::text')
            item_loader.add_value('url', response.url)
            item_loader.add_css('title', 'h1.QuestionHeader-title::text')
            item_loader.add_css('content', '.QuestionHeader-detail')
            item_loader.add_css('answer_num', 'h4.List-headerText span::text')
            item_loader.add_css('comments_num', 'div.QuestionHeader-Comment button::text')
            item_loader.add_css('watch_user_num', '.NumberBoard-value')
            item_loader.add_css('click_num', '.NumberBoard-value')
            # item_loader.add_value('crawl_time', '')

            question_item = item_loader.load_item()



        else:
            print("Old version of Zhihu, skip")

    def start_requests(self):
        # override default start_requests function
        # first do login
        return [scrapy.Request("https://www.zhihu.com/",headers=self.headers, callback=self.login)]

    def login(self, response):
        match_obj = re.match('.*name="_xsrf" value="(.*?)"', response.text, re.S)
        if match_obj:
            xsrf = match_obj.group(1)
        else:
            return

        post_data = {
            "_xsrf": xsrf,
            "phone_num": '18615762493',
            "password": '1234567890',
            "captcha": ""
        }

        # use callback to request captcha
        yield scrapy.Request("https://www.zhihu.com/captcha.gif?type=login", headers=self.headers, meta={"post_data": post_data}, callback=self.get_captcha_and_login)


    def get_captcha_and_login(self, response):

        with open("captcha.jpg", "wb") as f:
            f.write(response.body)
            f.close()

        try:
            im = Image.open('captcha.jpg')
            im.show()
        except:
            pass

        captcha = input("input captcha: ")
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = response.meta.get('post_data', {})
        post_data["captcha"] = captcha

        return [scrapy.FormRequest(
            url=post_url,
            formdata=post_data,
            headers=self.headers,
            callback=self.check_login
        )]

    def check_login(self, response):
        # check login, if success do request webpage
        text_json = json.loads(response.body)
        if "msg" in text_json and text_json['msg'] == "登录成功":
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.headers)

# -*- coding: utf-8 -*-
import scrapy
import re
import json
from PIL import Image

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
        pass

    def start_requests(self):
        return [scrapy.Request("https://www.zhihu.com/#signin",headers=self.headers, callback=self.login)]

    def login(self, response):
        match_obj = re.match('.*name="_xsrf" value="(.*?)"', response.text, re.S)
        xsrf = ""
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

        # request captcha
        yield scrapy.Request("https://www.zhihu.com/captcha.gif?type=login", headers=self.headers, meta={"post_data": post_data}, callback=self.login_after_captcha)


    def login_after_captcha(self, response):

        with open("captcha.jpg", "wb") as f:
            f.write(response.body)
            f.close()

        try:
            im = Image.open('captcha.jpg')
            im.show()
            im.close()
        except:
            pass

        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = response.meta.get('post_data', {})
        post_data["captcha"] = input("input captcha: ")

        return [scrapy.FormRequest(
            url=post_url,
            formdata=post_data,
            headers=self.headers,
            callback=self.check_login
        )]

    def check_login(self, response):
        # check login
        text_json = json.loads(response.body)
        pass

# -*- coding: utf-8 -*-
import scrapy
import re
import json
from PIL import Image
from urllib import parse
from scrapy.loader import ItemLoader
from zhihuCrawler.items import ZhihuAnswerItem, ZhihuQuestionItem
import datetime

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['zhihu.com']
    start_urls = ['http://zhihu.com/']
    # start_urls = ['https://www.zhihu.com/question/29372574']

    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}"

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
            # if question related page
            if match_obj:
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)
                yield scrapy.Request(request_url, headers=self.headers, meta={'question_id': question_id}, callback=self.parse_question)
            else:
                # do further url analysis
                # scrapy.Request(url, headers=self.headers, callback=self.parse)
                pass


    def parse_question(self, response):
        # extract question item
        # new version of zhihu question html

        question_id  = int(response.meta.get('question_id'))
        if "QuestionHeader-title" in response.text:
            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            item_loader.add_value('zhihu_id', question_id)
            item_loader.add_css('topics', '.Tag.QuestionTopic div.Popover::text')
            item_loader.add_value('url', response.url)
            item_loader.add_css('title', 'h1.QuestionHeader-title::text')
            item_loader.add_css('content', '.QuestionHeader-detail')
            item_loader.add_css('answer_num', 'h4.List-headerText span::text')
            item_loader.add_css('comments_num', 'div.QuestionHeader-Comment button::text')
            item_loader.add_css('watch_user_num', '.NumberBoard-value::text')
            item_loader.add_css('click_num', '.NumberBoard-value::text')
            # item_loader.add_value('crawl_time', '')

            question_item = item_loader.load_item()
            print(self.start_answer_url.format(question_id, 20, 0))
            yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), headers=self.headers, callback=self.parse_answers)
            yield question_item

        else:
            print("Old version of Zhihu, skip")

    def parse_answers(self, response):
        # parse answers
        ans_json = json.loads(response.body)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        # extract answer field
        for answer in ans_json['data']:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answers)
        else:
            pass


    # def start_requests(self):
    #     for url in self.start_urls:
    #         yield scrapy.Request(url, dont_filter=True, headers=self.headers)


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

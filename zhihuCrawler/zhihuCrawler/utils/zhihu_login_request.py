import requests
import re
import time
from PIL import Image

try:
    import http.cookiejar as cookieslib
except:
    import cookieslib # python2

session = requests.session()
session.cookies = cookieslib.LWPCookieJar(filename="cookies.txt")

try:
    session.cookies.load(ignore_discard=True)
    print("cookies loaded")
except:
    print("cookies not load")


agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3141.7 Safari/537.36"

headers = {
    "HOST": "www.zhihu.com",
    "Referer": "https://www.zhihu.com/",
    "User-Agent": agent
}


def get_xsrf():
    response = session.get("https://www.zhihu.com", headers=headers)
    match_group = re.match('.*name="_xsrf" value="(.*?)"', response.text, re.S)
    if match_group:
        return match_group.group(1)
    else:
        return ""

def get_captcha():
    t = str(int(time.time()*1000))
    captcha_url = "https://www.zhihu.com/captcha.gif?type=login"
    captcha_response = session.get(captcha_url, headers=headers)
    with open("captcha.jpg", "wb") as f:
        f.write(captcha_response.content)
        f.close()

    try:
        im = Image.open('captcha.jpg')
        im.show()
        im.close()
    except:
        pass
    captcha = input("input captcha: ")
    return captcha



def get_index():
    response = session.get("https://www.zhihu.com", headers=headers)
    with open("index_page.html", "wb") as f:
        f.write(response.text.encode('utf8'))
    print("ok")


def zhihu_login(account, password):
    if re.match("^1\d{10}", account):
        # indicate that account is phone number
        print("use phone to login")
        captcha = get_captcha()
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = {
            "_xsrf": get_xsrf(),
            "phone_num": account,
            "password": password,
            "captcha": captcha
        }
        print(post_data)
        response = session.post(post_url, data=post_data, headers=headers)
        print(response.content)
        session.cookies.save()
        get_index()


zhihu_login("18615762493", "1234567890")
# get_index()
# get_captcha()
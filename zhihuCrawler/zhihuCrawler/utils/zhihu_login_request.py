import requests
import re

try:
    import http.cookiejar as cookieslib
except:
    import cookieslib # python2


def get_xsrf():
    response = requests.get("https://www.zhihu.com")
    print(response.text)
    return ""



def zhihu_login(account, password):
    if re.match("^1\d{10}", account):
        # indicate that account is phone number
        print("use phone to login")
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = {
            "_xsrf": get_xsrf(),
            "phone_num": "",
            "password": ""
        }

if __name__=="__main__":
    get_xsrf()
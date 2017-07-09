import re


def extract_number(text):
    match_re = re.match(".*?(\d+).*", text);
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0
    return nums
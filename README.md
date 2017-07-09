# Zhihu Crawler

### environment
python3

### packages required
- scrapy
- requests
- pillow

### scrapy shell debug
```
scrapy shell -s USER_AGENT="xxx" xxxxxxxx
```

### solve pycharm import package Unresolved reference
http://blog.csdn.net/u014496330/article/details/55211398

### debug notes
1. TypeError: 'ItemMeta' object does not support item assignment
```python
# wrong
 item_loader = ItemLoader(item=ZhihuQuestionItem, response=response)
 
 # correct
  item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
```
reference: https://stackoverflow.com/questions/1806235/scrapy-basespider-how-does-it-work
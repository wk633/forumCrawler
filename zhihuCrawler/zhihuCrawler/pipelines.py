# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from MySQLdb.cursors import DictCursor
from twisted.enterprise import adbapi

class ZhihucrawlerPipeline(object):
    def process_item(self, item, spider):
        return item

# save to mysql async
class MysqlAsyncPipeline(object):
    @classmethod
    def from_crawler(cls, cralwer):
        settings = cralwer.settings
        dbParams = dict(
            host=settings["MYSQL_HOST"],
            db=settings["MYSQL_DBNAME"],
            user=settings["MYSQL_USER"],
            passwd=settings["MYSQL_PASSWORD"],
            charset='utf8',
            cursorclass=DictCursor,
            use_unicode=True
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbParams)
        return cls(dbpool)

    def __init__(self, dbPool):
        self.dbPool = dbPool

    def process_item(self, item, spider):
        insertion = self.dbPool.runInteraction(self.insertRow, item)
        insertion.addErrback = self.error_handler

    def insertRow(self, cursor, item):
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)
        # commit automatically

    def error_handler(self, e):
        print(e)
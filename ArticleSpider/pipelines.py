# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter

import codecs #用于打开Json文件，与open 的区别在于编码设置，开文件就用这个吧，保险一点
import json
import MySQLdb  #据说只支持python2被我换了
import pymysql


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        for ok, value in results:
            image_file_path = value['path']
        item['front_image_path'] = image_file_path

        return item


#在完成了网页翻页以及网页内容提取以及存取item中后，考虑如何建立数据库，并将数据保存在数据库中。
#因为item保存数据后，会被pipeline获取。而pipeline也是处理数据的地方，所以接下来还是在这里。
#先建立一个处理JSON的（为什么？不是很清楚，但因该就是为了导出爬下来的数据，为什么不直接倒入数据库？JSON文件有什么好的？）
class JsonWithEncodingPipeline(object):
    #这是一个自定义的JSON导出pipeline，还可以用scrapY自带的itemexporter，见下
    def __init__(self):
        self.file = codecs.open("article.json", "w", encoding="utf-8")  #首先打开JSON文件
    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"  #dumps必须传入dict，json.loads() & json.dumps()区别见笔记
        self.file.write(lines)
        return item
    def spider_close(self, spider):
        self.file.close()


class JsonExporterPipeline(object):
    #此处为调用scrapY提供的JSON export导出JSON文件
    def __init__(self):
        self.file = open('articleexport.json', 'wb')  #此处WB表示二进制格式，并且用了open的原因是下一步还是要解码，就懒得管了
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


class MysqlPipeline(object):
    def __init__(self):
        self.conn = pymysql.connect('localhost', 'root', '12345678', 'article_spider', charset="utf8", use_unicode=True)
        #这里本来用的是mysqlDB连接的，这里调试的时候怕是数据库连接的问题，换了连接的方式。这个是一个不错的案例，面试可以讲，具体见笔记。
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = 'INSERT INTO jobbole_article(url, create_date, fav_nums, url_object_id) VALUES ("%s", "%s", "%s", "%s")' % (item["url"], item["create_date"], item["fav_nums"], item["url_object_id"])
        self.cursor.execute(insert_sql)
        self.conn.commit()
        return item

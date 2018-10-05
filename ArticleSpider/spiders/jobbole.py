# -*- coding: utf-8 -*-
import scrapy
import re
import datetime #用于转换时间

from scrapy.http import Request  #用request将获取的对象交给SCRAPY
from urllib import parse   #用于URL的拼接

from ArticleSpider.items import JobBoleArticleItem  #引用item

from ArticleSpider.utils.common import get_md5

class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        # 如果不需要获取列表页其他内容，只需要网页地址，下面的就可以，如需要列表页比如封面图等，需要改成之后的。
        # post_nodes = response.css('#archive .floated-thumb .post-thumb a::attr(href)').extract()
        post_nodes = response.css('#archive .floated-thumb .post-thumb a')
        #将post-nodes设置为可以再次提取的可选择类型，而不是直接extract成一个数组
        for post_node in post_nodes:
            image_url = post_node.css('img::attr(src)').extract_first('')
            post_url = post_node.css('::attr(href)').extract_first('')
            # Request(url=post_url, callback=self.parse_detail) #url下载完成后调用callback函数，从列表页进入详情页
            # 有时URL没有域名，代表域名就是当前域名，需要进行拼接（response.url + post_url）,但是前者取出的可能是具体的文章而不是域名（？不太理解），所以用parse函数进行解析。
            yield Request(url=parse.urljoin(response.url, post_url), meta={'front_image_url': image_url}, callback=self.parse_detail)
            #request获取域名并解析，yield进行下载。 self后只用传入函数名称而不用传入函数, meta用于获取列表页独有的信息并传递给response

        #还要提取下一页的URL并交给SCRAPY进行下载
        next_url = response.css('.next.page-numbers::attr(href)').extract_first('') #这里两个.类之间从没有空格，表示是一个标签下的同一个类的两个字符段
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)
            #这里callback调用的是parse因为提取完下一页，就开始再次解析当前文章列表页的内容

    def parse_detail(self, response):
        #用于提取文章的具体字段

        article_item = JobBoleArticleItem()  #实例化一个item

        #使用xpath进行提取
        # title = response.xpath('//div[@class="entry-header"]/h1/text()').extract_first("")
        # #防止出现没有提取到值而报错，会自动默认none，可以传入""等。
        #
        # date = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/text()[1]').extract()[0].replace('·', '').strip()
        # vote_post_up = int(response.xpath('//span[contains(@class,"vote-post-up")]/h10/text()').extract()[0])
        # tag = response.xpath('//*[@id="post-109093"]/div[2]/p/a[3]/text()').extract()[0]
        # content = response.xpath('//div[@class="entry"]').extract()[0]
        #
        #
        # bookmark_btn_match = response.xpath('//span[contains(@class,"bookmark-btn")]/text()').extract()[0]
        # bookmark_btn = re.match(r'.*?(\d+).*', bookmark_btn_match).group(1)  #此处进行了贪婪匹配，所以之匹配了1位数，所以需要加入"？"非贪婪
        #
        # article_comment_match = response.xpath('//a[@href="#article-comment"]/span/text()').extract()[0] #before the href don't forget @
        # article_comment = re.match(r'.*?(\d+).*', article_comment_match).group(1)  #at here the article_comment_match do not need to add ""


        # use css to extract content:

        front_image_url = response.meta.get('front_image_url', '')  #获取从Request中得到的meta值，可以采用字典的方式，用get保险点，不会报错，后面是默认是空
        title = response.css('.entry-header h1::text').extract()
        create_date = response.css('p.entry-meta-hide-on-mobile::text').extract()[0].replace('·', '').strip()
        praise_nums = response.css('.vote-post-up h10::text').extract()[0]
        fav_nums = response.css('.bookmark-btn::text').extract()[0]
        match_re = re.match(r'.*?(\d+).*', fav_nums)
        if match_re:
            fav_nums = int(match_re.group(1))
        else:
            fav_nums = 0    #有一种情况是没有收藏或者评论，页面中提取评论两个字，无法正则匹配数字，所以返回评论。这里修改为0
        comment_nums = response.css('a[href="#article-comment"] span::text').extract()[0]
        match_re = re.match(r'.*?(\d+).*', comment_nums)
        if match_re:
            comment_nums = int(match_re.group(1))
        else:
            comment_nums = 0
        content = response.css('.entry').extract()
        tag_list = response.css('p.entry-meta-hide-on-mobile a::text').extract()
        tag_list = [element for element in tag_list if not element.strip().endswith("评论")]  #过滤掉以评论结尾的list内容
        tags = ",".join(tag_list)

        article_item['url_object_id'] = get_md5(response.url)
        article_item['title'] = title
        article_item['url'] = response.url
        try:
            create_date = datetime.datetime.strptime(create_date, "%Y/%m/%d").date()
        except Exception as e:
            create_date = datetime.datetime.now().date()
        article_item['create_date'] = create_date
        article_item['front_image_url'] = [front_image_url]  #解决了一个报错，可以正常保存图片到本地，但不是很理解为什么其他的不用加？是因为它是通过meta得到的还是其他原因？
        #依然存在一个问题：如何将保存的图片与网页的URL绑定？需要定义自己的pipeline
        article_item['praise_nums'] = praise_nums
        article_item['comment_nums'] = comment_nums
        article_item['fav_nums'] = fav_nums
        article_item['tags'] = tags
        article_item['content'] = content

        yield article_item #将数据填充后，调用yield将数据填充到 pipelines,需要在设置中开启pipeline

        #存在的问题；
        # 这个response是个什么属性呢？
        # 如何进行正确的调试，断点打在哪里才能看到和老师一样的结果？为什么我现在打在同样的位置没反应呢？ 因为之前的设置有了问题，要去回想并修改一下
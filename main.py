from scrapy.cmdline import execute

import sys
import os

# print(os.path.dirname(os.path.abspath(__file__)))
        # #abspth(__file__)表示当前文件目录，
        # dirname表示文件所在目录名，
        # sys.path.append将"引用的模块地址加入系统环境变量中"
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
execute(["scrapy", "crawl", "jobbole"])  #将其中字段拼接，组成命令，似乎是和在命令行中使用一样的
# _*_ encoding:utf-8 _*_
__author__ = 'pig'
__data__ = '2019\1\20 0020 20:23$'

from elasticsearch_dsl import Text, Date, Keyword, Integer, Document, Completion,DocType
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import analyzer
from elasticsearch_dsl.analysis import CustomAnalysis as _CustomAnalysis




connections.create_connection(hosts=["localhost"]) #连接es数据库
# my_analyzer = analyzer('ik_smart')

#搜索建议方法
my_analyzer = analyzer('ik_max_word') #搜索建议自动完成

class ArticleType(Document):
    suggest = Completion(analyzer=my_analyzer) #搜索建议自动完成
    title = Text(analyzer="ik_max_word")
    create_date = Date()
    url = Keyword()
    url_object_id = Keyword()
    front_image_url = Keyword()
    front_image_path = Keyword()
    praise_nums = Integer()
    comment_nums = Integer()
    fav_nums = Integer()
    content = Text(analyzer="ik_max_word")
    tags = Text(analyzer="ik_max_word")

    # class Meta:
    #     index = "jobbole"  #相当于数据库名字
    #     doc_type = "article" #相当于表名
    class Index:
        name = 'jobbole_blog'


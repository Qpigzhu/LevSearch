import json
import redis
from django.shortcuts import render
from django.views import View
from search.models import ArticleType
from django.http import HttpResponse
from elasticsearch import Elasticsearch
from datetime import datetime
# Create your views here.

clinet = Elasticsearch(hosts=["127.0.0.1"])

redis_cli = redis.StrictRedis() #连接redis

class IndexView(View):
    """首页get请求top-n排行榜"""
    def get(self,request):
        topn_search_clean = []
        topn_search = redis_cli.zrevrangebyscore(
            "search_keywords_set", "+inf", "-inf", start=0, num=5)
        for topn_key in topn_search:
            topn_key = str(topn_key, encoding="utf-8")
            topn_search_clean.append(topn_key)
        topn_search = topn_search_clean

        return render(request, "index.html", {"topn_search": topn_search})




#搜索建议
class SearchSuggest(View):
    def get(self,request):
        key_words = request.GET.get("s","") #获取搜索建议关键词
        return_suggest_list = [] #返回结果列表
        if key_words:
            s = ArticleType.search()
            """fuzzy模糊搜索, fuzziness 编辑距离, prefix_length前面不变化的前缀长度"""
            s = s.suggest('my_suggest',key_words,completion={
                "field":"suggest","fuzzy":{
                    "fuzziness":2
                },
                "size":10
            })

            #创建对es操作的对象
            suggestions = s.execute()

            #获取搜索建议的title
            for match in suggestions.suggest.my_suggest[0].options[:10]:
                source = match._source
                return_suggest_list.append(source["title"])
            #返回数据
            return HttpResponse(
                json.dumps(return_suggest_list),
                content_type="application/json")



#搜索关键词，返回页面
class SearchView(View):
    def get(self,request):
        key_words = request.GET.get("q","")   #获取搜索关键词
        page = request.GET.get("p","1")  #获取页面

        jobbole_count = redis_cli.get("jobbole_count")

        redis_cli.zincrby("search_keywords_set", key_words) #搜索关键词数量加一

        # 获取topn个搜索词
        topn_search_clean = []
        topn_search = redis_cli.zrevrangebyscore(
            "search_keywords_set", "+inf", "-inf", start=0, num=5)
        for topn_key in topn_search:
            topn_key = str(topn_key, encoding="utf-8")
            topn_search_clean.append(topn_key)

        top_search = topn_search_clean

        try:
            page = int(page)
        except:
            page = 1
        #搜索语句

        start_time = datetime.now()  #开始的时间,计算搜索的用时

        response =clinet.search(
            index="jobbole_blog",  #数据名
            body={
                "query":{
                    "multi_match":{
                        "query":key_words,  #搜索关键词
                        "fields":["tags","title","content"]  #要搜索的字段
                    }
                },
                "from": (page - 1) * 10,  #从第几个开始取
                "size": 10, #取多少个
                #关键词高亮显示
                "highlight": {
                    "pre_tags": ['<span class="keyWord">'],
                    "post_tags": ['</span>'],
                    "fields": {
                        "title": {},
                        "content": {},
                    }
                }
            },
        )

        end_time = datetime.now() #结束时间
        last_seconds = (end_time - start_time).total_seconds() #计算出搜索的用时

        total_nums = response["hits"]["total"]  #搜索到的总数量

        #计算器页码的总数
        if(page%10) > 0:
            page_nums = int(total_nums/10) + 1
        else:
            page_nums = int(total_nums / 10)


        hit_list = [] #最后返回的列表

        #循环搜索到的语句,并进入hit_dict,再加入hit_list,返回前端
        for hit in response["hits"]["hits"]:
            hit_dict = {}

            #取出高亮的title和conetnt

            #有些字段搜索不出highlight,只能通过异常处理
            try:
                if "title" in hit["highlight"]:
                    hit_dict["title"] = "".join(hit["highlight"]["title"])   #取得是一个列表，所以要join起来
                else:
                    hit_dict["title"] = hit["_source"]["title"]  #如果highlight没有这字段，就从_source取


                if "content" in hit["highlight"]:
                    hit_dict["content"] = "".join(hit["highlight"]["content"])[:500]
                else:
                    hit_dict["content"] = hit["_source"]["content"][:500]
            except Exception as e:
                hit_dict["title"] = hit["_source"]["title"]
                hit_dict["content"] = hit["_source"]["content"][:500]

            hit_dict["create_date"] = hit["_source"]["create_date"]  #取出创建时间
            hit_dict["url"] = hit["_source"]["url"] #取出URL
            hit_dict["score"] = hit["_score"] #取出分数

            hit_list.append(hit_dict) #加入到hit_list中,返回给前端

        return render(request,"result.html",{
            "all_hits":hit_list,
            "key_words":key_words,#搜索关键词返回前端
            "page":page, #页码
            "total_nums":total_nums,
            "page_nums":page_nums,
            "last_seconds":last_seconds,
            "jobbole_count":jobbole_count,
            "top_search":top_search
        })
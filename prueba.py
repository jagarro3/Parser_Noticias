import requests
from bs4 import BeautifulSoup
import os
import sys
import time
import datetime
from datetime import date, timedelta
from connectMongoDB import connectionMongoDB


def parseNewsTo2011(url):
    # r = requests.get(url)
    # soupPage = BeautifulSoup(r.text, "lxml")
    # # articles = soupPage.select('div .articulo__interior')
    # articles = soupPage.select('div .article')
    # # print(articles)

    # for article in articles:
    #     try:
    #         title = article.find(title="Ver noticia")
    #         link = title['href']
    #         # [0].get('href')
    #         # title = article.select('meta[itemprop=team]')[0].get('content').split('T')[0]
    #         # print(title.get_text())
    #         # print(link)
    #         print("-------------------------------------")
    r = requests.get(url)
    if r.ok:
        soupNews = BeautifulSoup(r.text, "lxml")
        bodyArticle = soupNews.find("div", {"id": "cuerpo_noticia"}).get_text()
        date = soupNews.select('meta[itemprop=datePublished]')[0].get('content').split('T')[0]
        author = soupNews.select('.autor-nombre')[0]
        listTags = [x.get_text() for x in soupNews.find_all("div", {"id": "articulo-tags__interior"})]
    print(listTags)
        # except Exception as e:
        #     continue
            # print(article)
    # print(title)
    # date = article.select('meta[itemprop=datePublished]')[0].get('content').split('T')[0]
    # link = title.select('a')[0].get('href')
    # title = article.select('.articulo-titulo')[0]

if __name__ == "__main__":
    os.system("cls")
    # parseNewsTo2011("https://elpais.com/tag/fecha/20030725")
    parseNewsTo2011("https://elpais.com/politica/2014/07/13/actualidad/1405256248_349096.html")

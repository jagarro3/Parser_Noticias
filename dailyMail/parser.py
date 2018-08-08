import requests
from bs4 import BeautifulSoup
import os
import sys
import time
import datetime
from datetime import date, timedelta
from connectMongoDB import connectionMongoDB

baseUrl = "http://www.dailymail.co.uk/home/sitemaparchive/day_"


def makeUrlOfDay(d1, d2):
    delta = d2 - d1  # timedelta
    for i in range(delta.days + 1):
        url = baseUrl + (d1 + timedelta(i)).strftime("%Y%m%d") + ".html"
        getLinkOfArticles(url)
        
def getLinkOfArticles(url):
    r = requests.get(url)
    soupPage = BeautifulSoup(r.text, "lxml")
    for article in soupPage.select('ul.archive-articles > li > a'):
        parserArticle('http://www.dailymail.co.uk' + article['href'])

def parserArticle(urlArticle):
    if(coleccion.find({"link": urlArticle}).count() == 0):
        r = requests.get(urlArticle)
        soupPage = BeautifulSoup(r.text, "lxml")

        title = soupPage.select_one('div.article-text > h2')
        body = ""
        for p in soupPage.select('div[itemprop=articleBody] > p'):
            body = body + p.get_text()

        date = soupPage.select_one('meta[itemprop=dateModified]').get('content').split('T')[0]
        author = soupPage.select_one('meta[itemprop=name]').get('content')
        tags = soupPage.select_one('meta[name=news_keywords]').get('content')
        description = soupPage.select_one('meta[name=description]').get('content')

        savePosts(urlArticle, date, title.get_text(), author, tags, description, body)

def savePosts(link, date, title, author, listTags, description, body):
    coleccion.save(
        {
            'link': link,
            'titulo': title,
            'fecha': date,
            'autor': author,
            'tags': listTags,
            'descripcion': description,
            'noticia': body
        })

def checkDates(d1, d2):
    return(d1 >= date(1994, 1, 1) and d1 <= d2 and d2 <= datetime.date.today())

if __name__ == "__main__":
    os.system("cls")
    if len(sys.argv) < 4:
        print("Introduce un rango de fecha Dia-Mes-Año y el nombre de la coleccion MongoDB")
        print("-> Ejemplo: python .\parser.py [02-06-2011] [12-11-2012] nombreColeccion")
        print("-> Nota: Año mínimo 1994 disponible")
    else:
        d1 = date(int(sys.argv[1].split('-')[2]), int(sys.argv[1].split('-')[1]), int(sys.argv[1].split('-')[0]))
        d2 = date(int(sys.argv[2].split('-')[2]), int(sys.argv[2].split('-')[1]), int(sys.argv[2].split('-')[0]))
        if(checkDates(d1, d2)):
            coleccion = connectionMongoDB(sys.argv[3])
            start_time = time.time()
            makeUrlOfDay(d1, d2)
            elapsed_time = time.time() - start_time
            print("Tiempo ejecución:", elapsed_time)
        else:
            print("Rango de fechas incorrecto")
            print("-------------------------------------------------------")
            print("Posibles causas:")
            print("-> La primera fecha tiene que ser menor que la segunda")
            print("-> El año de inicio no puede ser menor que el 1-1-1994")

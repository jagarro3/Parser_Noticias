import datetime
import json
import os
import sys
import time
from datetime import date, timedelta
from multiprocessing import Pool

import requests
from bs4 import BeautifulSoup

from connectMongoDB import connectionMongoDB

baseUrl = "http://www.dailymail.co.uk/home/sitemaparchive/day_"
urlLinks = []
coleccion = connectionMongoDB(sys.argv[3]) if len(sys.argv) == 4 else None
s = requests.Session()
s.max_redirects = 2

def generate_links(d1, d2):
    delta = d2 - d1
    for i in range(delta.days + 1):
        url = baseUrl + (d1 + timedelta(i)).strftime("%Y%m%d") + ".html"
        get_links_of_day(url)
        
def get_links_of_day(url):
    r = requests.get(url)
    soupPage = BeautifulSoup(r.text, "lxml")
    for article in soupPage.select('ul.archive-articles > li > a'):
        urlLinks.append('https://www.dailymail.co.uk' + article['href'])

def parse_links(urlArticle):
    title, body, date, author, tags, description = '', '', '', '', '', ''
    
    if(coleccion.find({"link": urlArticle}).count() == 0):
        try: 
            # start_time = time.time()
            r = s.get(urlArticle)
            print("Tamaño:", len(r.content), urlArticle)
            # elapsed_time = time.time() - start_time
            # print("Tiempo descarga noticia:", elapsed_time, " - ", datetime.datetime.now().time() , " ", urlArticle)
            soupPage = BeautifulSoup(r.text, "lxml")

            title = author = soupPage.select_one('meta[property="og:title"]').get('content')
            for p in soupPage.select('div[itemprop=articleBody] > p'):
                body = body + p.get_text()
            
            date = json.loads(soupPage.find('script', type='application/ld+json').text)

            if date["datePublished"]:
                date = datetime.datetime.strptime(date["datePublished"].split("T")[0], '%Y-%m-%d')
            elif date["dateModified"]:
                date = datetime.datetime.strptime(date["dateModified"].split("T")[0], '%Y-%m-%d')
            else:
                date = ""

            author = json.loads(soupPage.find('script', type='application/ld+json').text)["author"]["name"]
            tags = [tag for tag in soupPage.select_one('meta[name=news_keywords]').get('content').split(',')]
            description = soupPage.select_one('meta[name=description]').get('content')

            savePosts(urlArticle, date, title, author, tags, description, body, coleccion)
        except Exception as e:
            print("Error:", e, urlArticle)
            pass

def savePosts(link, date, title, author, listTags, description, body, coleccion):
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
            start_time = time.time()
            
            print("Generando links noticias - ", datetime.datetime.now().time())
            generate_links(d1, d2)

            # Multiprocessing
            print("Parseando noticias - ", datetime.datetime.now().time())
            with Pool(10) as p:
                p.map(parse_links, urlLinks)
            # END Multiprocessing
            
            elapsed_time = time.time() - start_time
            print("Tiempo ejecución:", elapsed_time, " - ", datetime.datetime.now().time())
        else:
            print("Rango de fechas incorrecto")
            print("-------------------------------------------------------")
            print("Posibles causas:")
            print("-> La primera fecha tiene que ser menor que la segunda")
            print("-> El año de inicio no puede ser menor que el 1-1-1994")

import requests
from bs4 import BeautifulSoup
import os
import sys
import time
import datetime
from datetime import date, timedelta
from connectMongoDB import connectionMongoDB


def createUrl(d1, d2):
    '''
    Crear una lista con todas las combinacion de YearMesDay
    Año inicio ElPais: 1976
    Año final ElPais con el mismo formato de url: 2011
    1976 - 2011:
        Formato final: https://elpais.com/tag/fecha/YearMesDay
    2012 - Actual
        Formato final: https://elpais.com/hemeroteca/elpais/YearMesDay/(m|t|n)
    '''
    delta = d2 - d1  # timedelta
    for i in range(delta.days + 1):
        if((d1 + timedelta(i)) < date(2012,1,1)):
            _listCreateUrl.append("https://elpais.com/tag/fecha/" + (d1 + timedelta(i)).strftime("%Y%m%d"))
        else:
            for x in ["/m", "/t", "/n"]:
                _listCreateUrl.append("https://elpais.com/hemeroteca/elpais/" + (d1 + timedelta(i)).strftime("%Y/%m/%d") + x)

def parseNewsTo2011(url):
    listOfNews = [url]
    # Loop para cada noticias teniendo en cuenta la paginacion de la web
    for linkArticle in listOfNews:
        # Procesar pagina
        try:
            r = requests.get(linkArticle)
        except Exception as e:
            pass

        if r.ok:
            isAnotherDom = False;
            soupPage = BeautifulSoup(r.text, "lxml")
            articles = soupPage.select('div .articulo__interior')
            
            # Si articles es [] es porque el año está entre el 2012-2016
            if(articles == []):
                articles = soupPage.select('div .article')
                isAnotherDom = True;
            
            # Obtener enlaces de paginación. Solo hasta el 2011 hay botón de paginación
            if(not isAnotherDom):
                nextButton = soupPage.find('li', class_="paginacion-siguiente")
                listOfNews.append(nextButton.a['href'])

            # Parsear noticias
            for article in articles:
                # Informacion de la noticia
                try:
                    if(not isAnotherDom):
                        title = article.select('.articulo-titulo')[0]
                        date = article.select('meta[itemprop=datePublished]')[0].get('content').split('T')[0]
                        link = title.select('a')[0].get('href')
                        if("elpais.com" not in link):
                            link = 'http://elpais.com' + link
                        else:
                            link = 'http:' + link
                        author = article.select('.autor-nombre')[0]
                    else:
                        #2012-2016
                        title = article.select('h2')[0]
                        link = 'http://elpais.com' + title.select('a')[0].get('href')
                    
                    # Comprobar que no haya sido insertado ya en MongoDB
                    if(coleccion.find({"link": link}).count() == 0):
                        # Cuerpo 
                        r = requests.get(link)
                        if r.ok:
                            soupNews = BeautifulSoup(r.text, "lxml")
                            if(not isAnotherDom):
                                bodyArticle = soupNews.find("div", {"id": "cuerpo_noticia"}).get_text()
                            else:
                                bodyArticle = soupNews.find("div", {"id": "cuerpo_noticia"}).get_text()
                                date = soupNews.select('meta[itemprop=datePublished]')[0].get('content').split('T')[0]
                                author = soupNews.select('.autor-nombre')[0]
                        # Guardar en MongoDB
                        savePosts(link, date, title.get_text(), author.get_text(), bodyArticle)
                except Exception as e:
                    continue

def setParser():
    # Loop para cada link generado (yearFrom to yearTo)
    for url in _listCreateUrl:
        print(url)
        parseNewsTo2011(url)

def savePosts(link, date, title, author, article):
    coleccion.save(
        {
            'link': link,
            'titulo': title,
            'fecha': date,
            'autor': author,
            'noticia': article
        })


def checkDates(d1, d2):        
    if(d1 <= d2):
        return d2 <= datetime.date.today()
    else:
        return False

if __name__ == "__main__":
    os.system("cls")
    if len(sys.argv) < 4:
        print("Introduce un rango de fecha Dia-Mes-Año y el nombre de la coleccion MongoDB")
        print("-> Ejemplo: python .\parserElPais.py [02-06-1970] [12-11-1986] nombreColeccion")
    else:
        d1 = date(int(sys.argv[1].split('-')[2]), int(sys.argv[1].split('-')[1]), int(sys.argv[1].split('-')[0]))
        d2 = date(int(sys.argv[2].split('-')[2]), int(sys.argv[2].split('-')[1]), int(sys.argv[2].split('-')[0]))
        if(d1 <= d2):
            if(d2 <= datetime.date.today()):
                coleccion = connectionMongoDB(sys.argv[3])
                start_time = time.time()
                _listCreateUrl = []
                createUrl(d1, d2)
                setParser()
                elapsed_time = time.time() - start_time
                print("Tiempo ejecución:", elapsed_time)

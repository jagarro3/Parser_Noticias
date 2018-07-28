import requests
from bs4 import BeautifulSoup
import os
import sys
import time
import datetime
from datetime import date, timedelta
from connectMongoDB import connectionMongoDB

baseUrlTo2011 = "https://elpais.com/tag/fecha/"
baseUrlToCurrent = "https://elpais.com/hemeroteca/elpais/"

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
            _listCreateUrl.append(baseUrlTo2011 + (d1 + timedelta(i)).strftime("%Y%m%d"))
        else:
            for x in ["/m", "/t", "/n"]:
                _listCreateUrl.append(baseUrlToCurrent + (d1 + timedelta(i)).strftime("%Y/%m/%d") + x)


def parserGeneric(url, classArticle, hasPagination, typeOfArticle):
    listOfNews = [url]
    # Loop para cada noticias teniendo en cuenta la paginación de la web
    for linkArticle in listOfNews:
        # Procesar pagina
        try:
            r = requests.get(linkArticle)
        except Exception as e:
            pass

        if r.ok:
            soupPage = BeautifulSoup(r.text, "lxml")
            articles = soupPage.select(classArticle)

        if(hasPagination):
            nextButton = soupPage.find('li', class_="paginacion-siguiente")
            if(nextButton):
                listOfNews.append(nextButton.a['href'])
    
        # Parsear noticias
        for article in articles:
            # Informacion de la noticia
            try:
                # Titulo y link
                if(typeOfArticle == 1):
                    title = article.select('.articulo-titulo')[0]
                    link = title.select('a')[0].get('href')
                    if("elpais.com" not in link):
                        link = 'http://elpais.com' + link
                    else:
                        link = 'http:' + link
                elif(typeOfArticle == 2):
                    title = article.find(title="Ver noticia")
                    link = 'http://elpais.com' + title['href']
   
                # Comprobar que no haya sido insertado ya en MongoDB
                if(coleccion.find({"link": link}).count() == 0):
                    # Cuerpo, autor y fecha
                    r = requests.get(link)
                    if r.ok:
                        soupNews = BeautifulSoup(r.text, "lxml")
                        bodyArticle = soupNews.find("div", {"id": "cuerpo_noticia"}).get_text()
                        date = soupNews.select('meta[itemprop=datePublished]')[0].get('content').split('T')[0]
                        author = soupNews.select('.autor-nombre')[0] if soupNews.select('.autor-nombre') else ""
                        print("PASA")
                        listTags = [x.get_text() for x in soupNews.find_all("div", {"id": "articulo-tags__interior"})]
                    # Guardar en MongoDB
                    savePosts(link, date, title.get_text(), author.get_text() if author != "" else "", listTags, bodyArticle)
            except Exception as e:
                print("Error:", e, link)
                continue

def setParser():
    # parserGeneric(url, classArticle, hasPagination, typeOfArticle):
    # typeOfArticle = (1: 1976 - 2011), (2: 2012-2016)
    for url in _listCreateUrl:
        print(url)
        if(baseUrlTo2011 in url):
            parserGeneric(url, 'div .articulo__interior', True, 1)
        # elif(baseUrlToCurrent in url):
        #     parserGeneric(url, 'div .article', False, 2)
        
# Guardar noticias en MongoDB
def savePosts(link, date, title, author, listTags, article):
    coleccion.save(
        {
            'link': link,
            'titulo': title,
            'fecha': date,
            'autor': author,
            'tags': listTags,
            'noticia': article
        })

# Comprobar rango de fechas
def checkDates(d1, d2): 
    if(d1 >= date(1976,1,1)):    
        if(d1 <= d2):
            return d2 <= datetime.date.today()
        else:
            return False
    else:
        return False

if __name__ == "__main__":
    os.system("cls")
    if len(sys.argv) < 4:
        print("Introduce un rango de fecha Dia-Mes-Año y el nombre de la coleccion MongoDB")
        print("-> Ejemplo: python .\parserElPais.py [02-06-1976] [12-11-1986] nombreColeccion")
        print("-> Nota: Año mínimo 1976")
    else:
        d1 = date(int(sys.argv[1].split('-')[2]), int(sys.argv[1].split('-')[1]), int(sys.argv[1].split('-')[0]))
        d2 = date(int(sys.argv[2].split('-')[2]), int(sys.argv[2].split('-')[1]), int(sys.argv[2].split('-')[0]))
        if(checkDates(d1,d2)):
            coleccion = connectionMongoDB(sys.argv[3])
            start_time = time.time()
            _listCreateUrl = []
            createUrl(d1, d2)
            setParser()
            elapsed_time = time.time() - start_time
            print("Tiempo ejecución:", elapsed_time)
        else:
            print("Rango de fechas incorrecto")
            print("-------------------------------------------------------")
            print("Posibles causas:")
            print("-> La primera fecha tiene que ser menor que la segunda")
            print("-> El año de inicio es como mínimo el 1-1-1976")

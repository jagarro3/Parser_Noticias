import requests
from bs4 import BeautifulSoup
import os
import sys
import time
import datetime
from datetime import date, timedelta
from connectMongoDB import connectionMongoDB
from multiprocessing import Pool, Value

baseUrlTo2011 = "https://elpais.com/tag/fecha/"
baseUrlToCurrent = "https://elpais.com/hemeroteca/elpais/"

# Lista de pares con este formato: {url, classArticle, hasPagination, typeOfArticle}
# Donde:
# url es la direccion web donde aparecen todas las noticias de un cierto dia
# classArticle es la clase css de la noticia. Esto varia según el año en la que se publicó
# hasPagination indica si la web tiene paginación o no
# typeOfArticle = (1: 1976-2011, 2016-Current), (2: 2012-2015)
listOfUrls = []
coleccion = connectionMongoDB(sys.argv[3]) if len(sys.argv) == 4 else None

def generate_links(d1, d2):
    '''
    Crear una lista con todas las combinacion de YearMesDay
    Año inicio ElPais: 1976
    Año final ElPais con el mismo formato de url: 2011
    1976 - 2011:
        Formato final: https://elpais.com/tag/fecha/YearMesDay
    2012 - Actual
        Formato final: https://elpais.com/hemeroteca/elpais/Year/Mes/Day/(m|t|n)
    '''
    delta = d2 - d1  # timedelta
    for i in range(delta.days + 1):
        if((d1 + timedelta(i)) < date(2012,1,1)):
            url = baseUrlTo2011 + (d1 + timedelta(i)).strftime("%Y%m%d")
            listOfUrls.append([url, 'div .articulo__interior', True, 1])
        elif((d1 + timedelta(i)) < date(2016,1,1)):
            for x in ["/m", "/t", "/n"]:
                url = baseUrlToCurrent + (d1 + timedelta(i)).strftime("%Y/%m/%d") + x
                listOfUrls.append([url, 'div .article', False, 2])
        else:
            for x in ["/m", "/t", "/n"]:
                url = baseUrlToCurrent + (d1 + timedelta(i)).strftime("%Y/%m/%d") + x
                listOfUrls.append([url, 'div .articulo__interior', False, 1])

def parse_links(listOfUrls):
    listOfNews = [listOfUrls[0]]
    bodyArticle = ''
    # Loop para cada noticias teniendo en cuenta la paginación de la web
    for linkArticle in listOfNews:
        
        # Procesar pagina
        try:
            r = requests.get(linkArticle)
            if r.status_code == requests.codes.ok:
                soupPage = BeautifulSoup(r.text, "lxml")
                articles = soupPage.select(listOfUrls[1])
                if(listOfUrls[2]):
                    nextButton = soupPage.find('li', class_="paginacion-siguiente")
                    if(nextButton):
                        listOfNews.append(nextButton.a['href'])
        
                # Parsear noticias
                for article in articles:
                    # Informacion de la noticia
                    try:
                        # Titulo y link
                        if(listOfUrls[3] == 1):
                            title = article.select('.articulo-titulo')[0]
                            link = title.select('a')[0].get('href')
                            
                            if("elpais.com" not in link):
                                link = 'elpais.com' + link
                                if("http" not in link):
                                    link = 'http://' + link
                        elif(listOfUrls[3] == 2):
                            title = article.find(title="Ver noticia")
                            link = 'http://elpais.com' + title['href']
        
                        # Comprobar que no haya sido insertado ya en MongoDB
                        if(coleccion.find({"link": link}).count() == 0):
                            r = requests.get(link)
                            if r.status_code == requests.codes.ok:
                                soupNews = BeautifulSoup(r.text, "lxml")
                                
                                # Body
                                for p in soupNews.select('div[itemprop="articleBody"] > p'):
                                    bodyArticle = bodyArticle + p.get_text()

                                # # Limpiar posibles script y style en el cuerpo de la noticia
                                # for script in bodyArticle(["script", "style"]):
                                #     script.extract()

                                date = soupNews.select('meta[itemprop=datePublished]')[0].get('content').split('T')[0]
                                author = soupNews.select('.autor-nombre')[0] if soupNews.select('.autor-nombre') else ""
                                description = soupNews.select_one('meta[name="description"]').get('content')
                                listTags = [tag for tag in soupNews.select_one('meta[name=news_keywords]').get('content').split(',')]
                            
                            # Guardar en MongoDB y comprobar por segunda vez si el link ya está insertado
                            # Se comprueba porque puede dar el caso de que otro hilo no lo haya insertado aun
                            if(coleccion.find({"link": link}).count() == 0):
                                save_articles(
                                    link, 
                                    datetime.datetime.strptime(date, '%Y-%m-%d'), 
                                    title.get_text().strip(), 
                                    author.get_text().strip() if author != "" else "", 
                                    listTags, 
                                    description,
                                    bodyArticle,
                                    coleccion)

                    except Exception as e:
                        #print("Error:", e, link)
                        continue
        except Exception as e:
            print('Error en Beautifullsoup', e)
            continue

# Guardar noticias en MongoDB
def save_articles(link, date, title, author, listTags, description, bodyArticle, coleccion):
    coleccion.save(
        {
            'link': link,
            'titulo': title,
            'fecha': date,
            'autor': author,
            'tags': listTags,
            'descripcion': description,
            'noticia': bodyArticle
        })

# Comprobar rango de fechas
def checkDates(d1, d2): 
    return(d1 >= date(1976,1,1) and d1 <= d2 and d2 <= datetime.date.today())

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
            start_time = time.time()
            
            print("Generando links noticias")
            generate_links(d1, d2)
            
            # Multiprocessing
            print("Parseando noticias")
            with Pool(6) as p:
                p.map(parse_links, listOfUrls)
            # END Multiprocessing
            
            elapsed_time = time.time() - start_time
            print("Tiempo ejecución:", elapsed_time)
        else:
            print("Rango de fechas incorrecto")
            print("-------------------------------------------------------")
            print("Posibles causas:")
            print("-> La primera fecha tiene que ser menor que la segunda")
            print("-> El año de inicio no puede ser menor que el 1-1-1976")

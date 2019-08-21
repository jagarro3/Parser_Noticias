import requests
from bs4 import BeautifulSoup
import os
import sys
import time
import datetime
from datetime import date, timedelta
from connectMongoDB import connectionMongoDB
from multiprocessing import Pool, Value

baseUrl = "https://www.levante-emv.com"
urlLinks = []

def generate_links(d1, d2):
    delta = d2 - d1
    for i in range(delta.days + 1):
        url = baseUrl + (d1 + timedelta(i)).strftime("/%Y/%m/%d")
        get_all_links(url)
        
def get_all_links(url):
    r = requests.get(url)
    soupPage = BeautifulSoup(r.text, "lxml")
    for link in soupPage.select('a[data-tipo="noticia"]'):
        if ('http' or 'https') in link['href']:
            urlLinks.append(link['href'])
        else:
            urlLinks.append(baseUrl + link['href'])

def parse_links(urlArticle, coleccion = connectionMongoDB(sys.argv[3])):
    title, body, date, author, tags, description = '', '', '', '', '', ''
    
    if(coleccion.find({"link": urlArticle}).count() == 0):
        try: 
            r = requests.get(urlArticle)
            soupPage = BeautifulSoup(r.text, "lxml")
            
            # Titulo
            title = soupPage.select_one('meta[itemprop=name]').get('content')

            # Noticia
            for p in soupPage.select('span[itemprop=articleBody] > p'):
                body = body + p.get_text()

            # Si el link es Ocio puede que la noticia esté en un div y no en un span
            if not body:
                for p in soupPage.select('div[itemprop=articleBody] > p'):
                    body = body + p.get_text()

            # Fecha
            date = soupPage.select_one('meta[name="cXenseParse:recs:publishtime"]').get('content').split('T')[0]

            # Autor
            author = soupPage.select_one('span[itemprop=author]')
            if author == None:
                author = soupPage.select_one('meta[name=author]').get('content').strip()
            else:
                author = author.get_text().strip()
            
            # Descripción
            description = soupPage.select_one('meta[name=description]').get('content')

            # Tags. Si no hay tags metemos los keywords en tags
            # tags = [',' + tag.get('content') for tag in soupPage.find_all('meta[name=cXenseParse:epi-tags]')]
            tags = [x.get_text() for x in soupPage.find_all('meta[name="cXenseParse:epi-tags"]')]
            if tags == []:
                tags = [tag for tag in soupPage.select_one('meta[name=keywords]').get('content').split(',')]

            # Guardar noticia. Comprobar una vez mas si existe en la base de datos.
            if(coleccion.find({"link": urlArticle}).count() == 0):
                save_articles(urlArticle, datetime.datetime.strptime(date, '%Y-%m-%d'), title, author, tags, description, body, coleccion)            
        except Exception as e:   
            # print("Error:", e, urlArticle)
            pass

# Guardar noticias en MongoDB
def save_articles(link, date, title, author, tags, description, body, coleccion):
    coleccion.save(
        {
            'link': link,
            'titulo': title,
            'fecha': date,
            'autor': author,
            'tags': tags,
            'descripcion': description,
            'noticia': body
        })

# Comprobar rango de fechas
def checkDates(d1, d2): 
    return(d1 >= date(2008,3,6) and d1 <= d2 and d2 <= datetime.date.today())

if __name__ == "__main__":
    os.system("cls")
    if len(sys.argv) < 4:
        print("Introduce un rango de fecha Dia-Mes-Año y el nombre de la coleccion MongoDB")
        print("-> Ejemplo: python .\parser.py [06-03-2008] [30-12-2018] levante")
        print("-> Nota: Fecha mínima 06-03-2008")
    else:
        d1 = date(int(sys.argv[1].split('-')[2]), int(sys.argv[1].split('-')[1]), int(sys.argv[1].split('-')[0]))
        d2 = date(int(sys.argv[2].split('-')[2]), int(sys.argv[2].split('-')[1]), int(sys.argv[2].split('-')[0]))
        if(checkDates(d1,d2)):
            start_time = time.time()
            generate_links(d1, d2)

            # Multiprocessing
            with Pool(10) as p:
                p.map(parse_links, urlLinks)
            # END Multiprocessing

            elapsed_time = time.time() - start_time
            print("Tiempo ejecución:", elapsed_time)
        else:
            print("Rango de fechas incorrecto")
            print("-------------------------------------------------------")
            print("Posibles causas:")
            print("-> La primera fecha tiene que ser menor que la segunda")
            print("-> El año de inicio no puede ser menor que el 06-03-2008")

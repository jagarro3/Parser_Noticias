# Parser notícias DailyMail

# Descripción

Este programa recopila todas la noticias del periodico DailyMail.

# Requisitos

Para poder guardar las notícias parseadas se necesita una base de datos. En este proyecto se usa MongoDB. 
El fichero connectMongoDB.py hace la conexión con la base de datos. El nombre de esta se especifica en el propio código:
Línea 9: db = client.periodicos

# Entrada del programa

Ejemplo:

python .\parser.py 02-06-2011 12-11-2015 nombreColeccionMongoDB

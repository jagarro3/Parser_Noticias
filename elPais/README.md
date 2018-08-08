# Parser notícias El País

# Descripción

Este programa recopila todas la noticias del periodico EL País. Su hemeroteca ofrece todas las noticias desde el 1976

# Requisitos

Para poder guardar las notícias parseadas se necesita una base de datos. En este proyecto se usa MongoDB. 
El fichero connectMongoDB.py hace la conexión con la base de datos. El nombre de esta se especifica en el propio código:
Línea 9: db = client.elPais

# Entrada del programa

Ejemplo:

python .\parser.py 02-06-1976 12-11-1986 nombreColeccionMongoDB

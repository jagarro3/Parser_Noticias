#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymongo
from pymongo import MongoClient

def connectionMongoDB(nameDb):
    client = MongoClient('localhost', 27017)
    db = client.periodicos
    hayColecciones = db.collection_names(include_system_collections=False)
    if nameDb not in hayColecciones:
        db.create_collection(nameDb)
    return db[nameDb]
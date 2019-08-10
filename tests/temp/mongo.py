import json
from dateutil.parser import parse
from pymongo import MongoClient


config_mongo = dict(
    host="47.112.122.242",
    port=27017
)


conn = MongoClient(**config_mongo)
collection = conn.scrapy_data['bbc']

# find_result = collection.find({"date": {"$gte": start_dt, "$lte": end_dt}})


def export_mongo_collection(conn, db_name, collection_name, condition={}):
    collection = conn[db_name][collection_name]
    results = collection.find()
    file = open(collection_name + ".json", "w")
    file.write('[')
    for i, doc in enumerate(results):
        del doc["_id"]
        file.write(json.dumps(doc))
        if i < results.count() - 1:
            file.write(',\n')
    file.write(']')


def test_export_mongo_collection():
    export_mongo_collection(conn, "scrapy_data", "bbc")
    with open("bbc.json", "r") as file:
        json_data = file.read()
        d_data = json.loads(json_data)


def export_bbc_cnn():
    export_mongo_collection(conn, "scrapy_data", "bbc")
    export_mongo_collection(conn, "scrapy_data", "cnn")

def export_news():
    export_mongo_collection(conn, "yuqingdb", "news")



if __name__ == '__main__':
    #test_export_mongo_collection()
    #export_bbc_cnn()
    export_news()


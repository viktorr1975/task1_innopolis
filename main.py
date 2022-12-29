#задачи:
#тестирование на нагрузку, как-то препод показывал график


import uvicorn
from typing import List

import databases
import sqlalchemy
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import random
import datetime

DB_USER = "postgres"
DB_NAME = "study"
DB_PASSWORD = "postgres"
DB_HOST = "127.0.0.1"

# SQLAlchemy specific code, as with any other app
DATABASE_URL = "sqlite:///./test.db"
# DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
print(DATABASE_URL)
database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

# Раскомментировать следующее в случае postgres
# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()
# также можно посмотреть этот репозиторий https://github.com/tiangolo/full-stack-fastapi-postgresql

notes = sqlalchemy.Table(
    "notes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("text", sqlalchemy.String),
    sqlalchemy.Column("completed", sqlalchemy.Boolean),
)
store = sqlalchemy.Table(
    "store",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("address", sqlalchemy.String),
)
items = sqlalchemy.Table(
    "items",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True,  autoincrement=True),
    sqlalchemy.Column("name", sqlalchemy.String, unique=True),
    sqlalchemy.Column("price", sqlalchemy.Float),
)

sales = sqlalchemy.Table(
    "sales",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True,  autoincrement=True),
    sqlalchemy.Column("sale_time", sqlalchemy.DateTime),
    sqlalchemy.Column("item_id", sqlalchemy.Integer, sqlalchemy.ForeignKey('items.id')),
    sqlalchemy.Column("store_id", sqlalchemy.Integer, sqlalchemy.ForeignKey('store.id')),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
    # Уберите параметр check_same_thread когда база не sqlite
)
metadata.drop_all(engine)       #отчистим таблицы
metadata.create_all(engine)


class WrongPostBody(Exception):     #описание ошибки если пользователь прислал некорректное тело запроса
    def __init__(self, name: str =""):
        self.name = name

class SaleIn(BaseModel):
#    sale_time: datetime.datetime = None
    item_id: int = 1
    store_id: int = 1

app = FastAPI()

@app.exception_handler(WrongPostBody)    #обработчик исключения когда пользователь прислал некорректное тело запроса
async def WrongPostBody_exception_handler(request: Request, exc: WrongPostBody):
    return JSONResponse(
        status_code=400,
        content={"error": "Не корректные данные"},
    )

@app.on_event("startup")
async def startup():
    await database.connect()
    # заполним таблицу items
    query = items.insert().values(name='Coleman', price=random.randrange(100))
    await database.execute(query)
    query = items.insert().values(name='Rossy', price=random.randrange(100))
    await database.execute(query)
    query = items.insert().values(name='Wallie', price=random.randrange(100))
    await database.execute(query)
#    last_record_id = await database.execute(query)
# заполним таблицу store
    query = store.insert()
    values = [
        {"address": "first_address"},
        {"address": "second_address"},
    ]
    await database.execute_many(query=query, values=values)
    # заполним таблицу sales
    query = "select id from store"
    store_ids = await database.fetch_all(query)
    store_ids = list(map(lambda a: a[0], store_ids))
    query = "select id from items"
    items_ids = await database.fetch_all(query)
    items_ids = list(map(lambda a: a[0], items_ids))
    for i in range(20):      #внесём 20 записей в таблицу sales
        query = sales.insert().values(item_id=random.choice(items_ids), store_id=random.choice(store_ids), sale_time=datetime.datetime.now())
        await database.execute(query)


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/items/")  #обрабатывает GET-запрос на получение всех товарных позиций
async def read_items():
    query = items.select()
    return await database.fetch_all(query)

@app.get("/stores/")  #обрабатывает GET-запрос на получение всех магазинов
async def read_stores():
    query = store.select()
    return await database.fetch_all(query)

@app.post("/sales/")   #обрабатывает POST-запрос с json-телом для сохранения данных о произведенной продаже (id товара + id магазина)
async def create_note(sale: SaleIn):
    query = "select id from store"
    store_ids = await database.fetch_all(query)
    store_ids = list(map(lambda a: a[0], store_ids))
    if sale.store_id not in store_ids:
        raise WrongPostBody()
    query = "select id from items"
    items_ids = await database.fetch_all(query)
    items_ids = list(map(lambda a: a[0], items_ids))
    if sale.item_id not in items_ids:
        raise WrongPostBody()
    sale_time = datetime.datetime.now()
    query = sales.insert().values(item_id=sale.item_id, store_id=sale.store_id, sale_time=sale_time)
    last_record_id = await database.execute(query)
    return {"id": last_record_id, "sale_time": sale_time.strftime("%Y-%m-%d %H:%M:%S"), **sale.dict()}


@app.get("/stores/top")  #обрабатывает GET-запрос на получение данных по топ 10 самых доходных магазинов за месяц (id + адрес + суммарная выручка)
async def read_top10stores():
    query = 'SELECT store.id as store_id, address, SUM(price) as income FROM store JOIN sales ON store.id = sales.store_id ' \
            'JOIN items ON items.id = sales.item_id ' \
            'GROUP BY store_id ' \
            'LIMIT 10 '
    return await database.fetch_all(query=query)

@app.get("/items/top/")  #обрабатывает GET-запрос на получение данных по топ 10 самых продаваемых товаров (id + наименование + количество проданных товаров)
async def read_top10items():
    query = 'SELECT items.id as item_id, name, COUNT(item_id) as sales_amount FROM store JOIN sales ON store.id = sales.store_id ' \
            'JOIN items ON items.id = sales.item_id ' \
            'GROUP BY item_id ' \
            'LIMIT 10'
    return await database.fetch_all(query=query)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
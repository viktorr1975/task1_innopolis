
# Project Title

A brief description of what this project does and who it's for

## API Reference

#### обрабатывает GET-запрос на получение всех товарных позиций

```
  GET http://0.0.0.0:8000/items
```
#### обрабатывает GET-запрос на получение всех магазинов

```
  GET http://0.0.0.0:8000/stores
```
#### обрабатывает GET-запрос на получение данных по топ 10 самых доходных магазинов за месяц (id + адрес + суммарная выручка)

```
  GET http://0.0.0.0:8000/stores/top
```
#### обрабатывает GET-запрос на получение данных по топ 10 самых продаваемых товаров (id + наименование + количество проданных товаров)

```
  GET http://0.0.0.0:8000/items/top
```

#### обрабатывает POST-запрос с json-телом для сохранения данных о произведенной продаже (id товара + id магазина)
```
  POST http://0.0.0.0:8000/items/top
```
BODY
```
{
  "item_id": 1,
  "store_id": 1
}
```
| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `item_id` | `integer` | **Required**. PK из таблицы items |
| `store_id` | `integer` | **Required**. PK из таблицы store |

## Инструкци запуска
1. Скачать проект
2. Установить зависимости
3. Запустить на исполнение
```
python main.py
```
В проекте используется sqlite. После запуска заполняется таблица items тремя записями, таблица store двумя записями и таблица sales двадцатью записями.
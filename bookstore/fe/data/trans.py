import pymongo
import sqlite3
import jwt
import time

def main():
    con = sqlite3.connect('book_lx.db')
    con.row_factory = dict_factory
    cur = con.cursor()
    sql = 'SELECT * FROM book'

    cur.execute(sql)
    books_data = cur.fetchall()

    client = pymongo.MongoClient("mongodb://127.0.0.1:27017")

    db = client["bookstore"]
    book_collection = db["book"]
    store_collection = db["store"]
    user_collection = db["user"]

    # 创建默认商店
    default_store_id = "1000001"
    store_doc = {
        "store_id": default_store_id,
        "owner_id": "test_user_001",
        "is_open": True
    }
    store_collection.insert_one(store_doc)

    # 创建虚构用户
    test_user_id = "test_user_001"
    terminal = "terminal_test"
    token = jwt_encode(test_user_id, terminal)
    user_doc = {
        "user_id": test_user_id,
        "password": "123456",
        "balance": 10000,  # 初始余额
        "token": token,
        "terminal": terminal
    }
    user_collection.insert_one(user_doc)

    for book in books_data:
        book_id = book['id']
        # 构建符合新结构的book文档（包含库存信息和所属商店ID）
        book_doc = {
            "author": book.get("author", ""),
            "author_intro": book.get("author_intro", ""),
            "binding": book.get("binding", ""),
            "book_id": book_id,
            "belong_store_id": default_store_id,
            "stock_level": 10,  # 默认库存
            "book_intro": book.get("book_intro", ""),
            "content": book.get("content", ""),
            "currency_unit": book.get("currency_unit", ""),
            "isbn": book.get("isbn", ""),
            "original_title": book.get("original_title", ""),
            "pages": book.get("pages", 0),
            "picture": book.get("pictures", []),
            "price": book.get("price", 0),
            "pub_year": book.get("pub_year", ""),
            "publisher": book.get("publisher", ""),
            "tags": book.get("tags", []),
            "title": book.get("title", ""),
            "translator": book.get("translator", "")
        }
        book_collection.insert_one(book_doc)

    cur.close()
    con.close()

def dict_factory(cursor, row):
   d = {}
   for idx, col in enumerate(cursor.description):
       d[col[0]] = row[idx]
   return d

def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    return encoded.decode("utf-8")

if __name__ == '__main__':
    main()
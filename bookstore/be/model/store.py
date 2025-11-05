import logging
import os
import threading
from pymongo import MongoClient


class Store:
    def __init__(self, db_path):
        # 连接到本地MongoDB的bookstore数据库
        self.client = MongoClient('localhost', 27017)
        self.db = self.client['bookstore']
        self.init_collections()

    def init_collections(self):
        # 确保必要的集合存在
        collections = ['user', 'store', 'order', 'book']
        for collection in collections:
            if collection not in self.db.list_collection_names():
                self.db.create_collection(collection)
        
        # 为user集合创建索引
        self.db.user.create_index("user_id", unique=True)

        # 为store集合创建索引
        self.db.store.create_index("store_id", unique=True)

        # 为book集合创建索引
        # book_id不应该全局唯一，应该是book_id和belong_store_id的组合唯一
        # 这样同一本书可以在不同商店中存在不同的记录
        # 创建复合唯一索引：book_id和belong_store_id的组合必须唯一
        self.db.book.create_index([("book_id", 1), ("belong_store_id", 1)], unique=True, name="book_id_store_id_unique")
        
        # 创建非唯一索引以优化查询性能
        self.db.book.create_index("book_id", unique=False)
        self.db.book.create_index("belong_store_id", unique=False)
        
        # 创建文本索引以支持全文搜索功能
        # 覆盖title、tags、content、book_intro、author、publisher，并设置权重
        try:
            self.db.book.drop_index("book_text_index")
        except Exception:
            pass
        self.db.book.create_index(
            [
                ("title", "text"),
                ("tags", "text"),
                ("content", "text"),
                ("book_intro", "text"),
                ("author", "text"),
                ("publisher", "text"),
            ],
            name="book_text_index",
            default_language="english",
            weights={
                "title": 10,
                "tags": 6,
                "book_intro": 5,
                "content": 3,
                "author": 2,
                "publisher": 1,
            },
        )
        
        # 为order集合创建索引    
        # 创建order_id的非唯一索引以优化查询性能
        self.db.order.create_index("order_id", unique=False)
        # 创建复合索引：同一订单中同一本书只能有一条记录
        self.db.order.create_index([("order_id", 1), ("book_id", 1)], unique=True, name="order_id_book_id_unique")
        

    def get_db(self):
        return self.db


database_instance: Store = None
# global variable for database sync
init_completed_event = threading.Event()


def init_database(db_path):
    global database_instance
    database_instance = Store(db_path)


def get_db():
    global database_instance
    return database_instance.get_db()

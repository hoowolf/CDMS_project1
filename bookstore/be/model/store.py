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
        self.db.store.create_index("store_id", unique=True)
        # 为book集合创建索引
        # book_id不应该全局唯一，应该是book_id和belong_store_id的组合唯一
        # 这样同一本书可以在不同商店中存在不同的记录
        
        # 先尝试删除旧的book_id唯一索引（如果存在）
        try:
            existing_indexes = self.db.book.list_indexes()
            for index in existing_indexes:
                if index.get("name") == "book_id_1" and index.get("unique"):
                    self.db.book.drop_index("book_id_1")
                    break
        except Exception:
            pass  # 忽略删除索引时的错误
        
        # 创建复合唯一索引：book_id和belong_store_id的组合必须唯一
        try:
            self.db.book.create_index([("book_id", 1), ("belong_store_id", 1)], unique=True, name="book_id_store_id_unique")
        except Exception:
            pass  # 索引可能已存在，忽略错误
        
        # 创建非唯一索引以优化查询性能
        self.db.book.create_index("book_id", unique=False)
        self.db.book.create_index("belong_store_id", unique=False)
        
        # 为order集合创建索引
        # 删除旧的order_id唯一索引（如果存在），因为一个订单可以有多条记录（每本书一条）
        try:
            existing_indexes = self.db.order.list_indexes()
            for index in existing_indexes:
                if index.get("name") == "order_id_1" and index.get("unique"):
                    self.db.order.drop_index("order_id_1")
                    break
        except Exception:
            pass  # 忽略删除索引时的错误
        
        # 创建order_id的非唯一索引以优化查询性能
        self.db.order.create_index("order_id", unique=False)
        # 创建复合索引：同一订单中同一本书只能有一条记录
        try:
            self.db.order.create_index([("order_id", 1), ("book_id", 1)], unique=True, name="order_id_book_id_unique")
        except Exception:
            pass  # 索引可能已存在，忽略错误

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

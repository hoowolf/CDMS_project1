from be.model import error
from be.model import db_conn


class Seller(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def add_book(
        self,
        user_id: str,
        store_id: str,
        book_id: str,
        book_json_str: str,
        stock_level: int,
    ):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            
            # 检查该商店中是否已存在该书籍ID（使用复合唯一索引保证）
            existing_book = self.conn.book.find_one({"book_id": book_id, "belong_store_id": store_id})
            if existing_book is not None:
                # 如果该商店中已存在该书籍ID，返回错误
                return error.error_exist_book_id(book_id)
            
            # 解析书籍信息
            import json
            book_info = json.loads(book_json_str)
            
            # 为当前商店插入新的书籍记录
            # 使用 book_id + store_id 作为 _id 确保唯一性
            book_detail_doc = {
                "_id": "{}_{}".format(book_id, store_id),
                "author": book_info.get("author", ""),
                "author_intro": book_info.get("author_intro", ""),
                "binding": book_info.get("binding", ""),
                "book_id": book_id,
                "belong_store_id": store_id,
                "stock_level": stock_level,
                "book_intro": book_info.get("book_intro", ""),
                "content": book_info.get("content", ""),
                "currency_unit": book_info.get("currency_unit", ""),
                "isbn": book_info.get("isbn", ""),
                "original_title": book_info.get("original_title", ""),
                "pages": book_info.get("pages", 0),
                "picture": book_info.get("pictures", []),
                "price": book_info.get("price", 0),
                "pub_year": book_info.get("pub_year", ""),
                "publisher": book_info.get("publisher", ""),
                "tags": book_info.get("tags", []),
                "title": book_info.get("title", ""),
                "translator": book_info.get("translator", "")
            }
            self.conn.book.insert_one(book_detail_doc)
            
        except Exception as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def add_stock_level(
        self, user_id: str, store_id: str, book_id: str, add_stock_level: int
    ):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            
            # 查找书籍并更新库存
            result = self.conn.book.update_one(
                {
                    "book_id": book_id,
                    "belong_store_id": store_id
                },
                {
                    "$inc": {
                        "stock_level": add_stock_level
                    }
                }
            )
            
            # 检查是否找到了匹配的文档
            if result.matched_count == 0:
                return error.error_non_exist_book_id(book_id)
                
        except Exception as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            # 检查商店是否已存在（通过检查store集合中是否有该store_id的记录）
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
            # 显式创建商店记录
            store_doc = {
                "store_id": store_id,
                "owner_id": user_id,
                "is_open": True
            }
            self.conn.store.insert_one(store_doc)
        except Exception as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def send(self, user_id: str, order_id: str) -> (int, str):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            
            # 查询订单信息
            orders = list(self.conn.order.find({"order_id": order_id}))
            if not orders:
                return error.error_invalid_order_id(order_id)
            
            # 获取订单对应的商店ID
            store_id = orders[0]["store_id"]
            
            # 查询商店信息，确认该用户是商店的所有者
            store_info = self.conn.store.find_one({"store_id": store_id})
            if store_info is None:
                return error.error_non_exist_store_id(store_id)
            
            seller_id = store_info["owner_id"]
            if seller_id != user_id:
                return error.error_authorization_fail()
            
            # 检查订单状态是否为已支付
            if orders[0].get("status") != "paid":
                return error.error_invalid_order_id(order_id)
            
            # 更新订单状态为已发货
            self.conn.order.update_many(
                {"order_id": order_id},
                {"$set": {"status": "sent"}}
            )
            
        except Exception as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

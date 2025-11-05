import uuid
import json
import logging
from datetime import datetime, timedelta
from be.model import db_conn
from be.model import error


class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def new_order(
        self, user_id: str, store_id: str, id_and_count: [(str, int)]
    ) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))
            order_id = uid  # 提前设置order_id，以便错误返回时使用
            order_records = []
            current_time = datetime.now()
            # 设置支付截止时间（一小时后）
            payment_deadline = current_time + timedelta(hours=1)

            for book_id, count in id_and_count:
                # 直接从book集合查询书籍信息和库存
                book_detail = self.conn.book.find_one({
                    "book_id": book_id,
                    "belong_store_id": store_id
                })
                
                if book_detail is None:
                    return error.error_non_exist_book_id(book_id) + (order_id,)
                
                stock_level = book_detail["stock_level"]
                price = book_detail["price"]

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                # 更新book集合中的库存
                result = self.conn.book.update_one(
                    {"book_id": book_id, "belong_store_id": store_id, "stock_level": {"$gte": count}},
                    {"$inc": {"stock_level": -count}}
                )
                if result.matched_count == 0:
                    return error.error_stock_level_low(book_id) + (order_id,)

                # 为每本书创建一条订单记录，status="pending"表示提交订单
                order_records.append({
                    "order_id": uid,
                    "buyer_id": user_id,
                    "store_id": store_id,
                    "book_id": book_id,
                    "count": count,
                    "total_price": price * count,  # 添加该书籍总价（数量*单价）
                    "status": "pending",  # 字符串描述状态：pending表示提交订单
                    "created_at": current_time,  # 添加创建时间
                    "payment_deadline": payment_deadline  # 添加支付截止时间
                })

            # 插入订单记录（每本书一条记录）
            if order_records:
                self.conn.order.insert_many(order_records)
        except Exception as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            # 查询该订单的所有记录
            orders = list(self.conn.order.find({"order_id": order_id}))
            if not orders:
                return error.error_invalid_order_id(order_id)

            # 检查订单是否已付款
            if orders[0].get("status") == "paid":
                return error.error_invalid_order_id(order_id)  # 订单已处理

            # 获取订单信息（从第一条记录获取buyer_id和store_id）
            buyer_id = orders[0]["buyer_id"]
            store_id = orders[0]["store_id"]

            if buyer_id != user_id:
                return error.error_authorization_fail()

            # 查询买家信息
            buyer = self.conn.user.find_one({"user_id": buyer_id})
            if buyer is None:
                return error.error_non_exist_user_id(buyer_id)
            
            balance = buyer["balance"]
            if password != buyer["password"]:
                return error.error_authorization_fail()

            # 查询商店信息（获取卖家ID）
            store_info = self.conn.store.find_one({"store_id": store_id})
            if store_info is None:
                return error.error_non_exist_store_id(store_id)

            # 从商店信息中获取卖家ID
            seller_id = store_info["owner_id"]

            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            # 计算订单总价：直接从订单记录中累加
            total_price = sum(order_record["total_price"] for order_record in orders)

            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)

            # 扣除买家余额
            result = self.conn.user.update_one(
                {"user_id": buyer_id, "balance": {"$gte": total_price}},
                {"$inc": {"balance": -total_price}}
            )
            if result.matched_count == 0:
                return error.error_not_sufficient_funds(order_id)

            # 增加卖家余额
            result = self.conn.user.update_one(
                {"user_id": seller_id},
                {"$inc": {"balance": total_price}}
            )

            if result.matched_count == 0:
                return error.error_non_exist_user_id(seller_id)

            # 更新所有订单记录的状态为"paid"（已付款）
            self.conn.order.update_many(
                {"order_id": order_id},
                {"$set": {"status": "paid"}}  # 字符串描述状态：paid表示付款
            )

        except Exception as e:
            return 528, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            # 查询用户信息
            user = self.conn.user.find_one({"user_id": user_id})
            if user is None:
                return error.error_non_exist_user_id(user_id)

            if user["password"] != password:
                return error.error_authorization_fail()

            # 更新用户余额
            result = self.conn.user.update_one(
                {"user_id": user_id},
                {"$inc": {"balance": add_value}}
            )
            if result.matched_count == 0:
                return error.error_non_exist_user_id(user_id)

        except Exception as e:
            return 528, "{}".format(str(e))

        return 200, "ok"

    def receive(self, user_id: str, order_id: str) -> (int, str):
        try:
            # 查询订单信息
            orders = list(self.conn.order.find({"order_id": order_id}))
            if not orders:
                return error.error_invalid_order_id(order_id)

            # 获取订单对应的买家ID
            buyer_id = orders[0]["buyer_id"]
            
            # 验证用户权限
            if buyer_id != user_id:
                return error.error_authorization_fail()

            # 检查订单状态是否为已发货
            if orders[0].get("status") != "sent":
                return error.error_invalid_order_id(order_id)

            # 更新订单状态为已收货
            self.conn.order.update_many(
                {"order_id": order_id},
                {"$set": {"status": "received"}}
            )

        except Exception as e:
            return 528, "{}".format(str(e))

        return 200, "ok"

    def query_order(self, user_id: str, order_id: str) -> (int, str, dict):
        try:
            # 查询订单信息
            orders = list(self.conn.order.find({"order_id": order_id}))
            if not orders:
                return error.error_invalid_order_id(order_id) + ({},)

            # 获取订单对应的买家ID
            buyer_id = orders[0]["buyer_id"]
            
            # 验证用户权限
            if buyer_id != user_id:
                return error.error_authorization_fail() + ({},)

            # 获取订单信息
            store_id = orders[0]["store_id"]
            status = orders[0]["status"]
            created_at = orders[0]["created_at"]
            
            # 计算订单总价
            total_price = sum(order["total_price"] for order in orders)
            
            # 构造书籍列表
            books = []
            for order in orders:
                books.append({
                    "book_id": order["book_id"],
                    "count": order["count"],
                    "price": order["total_price"]
                })
            
            # 构造返回数据
            data = {
                "order_id": order_id,
                "buyer_id": buyer_id,
                "store_id": store_id,
                "status": status,
                "created_at": created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at),
                "books": books,
                "total_price": total_price
            }

        except Exception as e:
            return 528, "{}".format(str(e)), {}

        return 200, "ok", data

    def cancel_order(self, user_id: str, order_id: str, password: str) -> (int, str):
        try:
            # 查询订单信息
            orders = list(self.conn.order.find({"order_id": order_id}))
            if not orders:
                return error.error_invalid_order_id(order_id)

            # 获取订单对应的买家ID和商店ID
            buyer_id = orders[0]["buyer_id"]
            store_id = orders[0]["store_id"]
            
            # 验证用户权限
            if buyer_id != user_id:
                return error.error_authorization_fail()

            # 检查订单状态是否为待付款
            if orders[0].get("status") != "pending":
                return error.error_invalid_order_id(order_id)

            # 查询买家信息以验证密码
            buyer = self.conn.user.find_one({"user_id": buyer_id})
            if buyer is None:
                return error.error_non_exist_user_id(buyer_id)
            
            if password != buyer["password"]:
                return error.error_authorization_fail()

            # 更新订单状态为已取消
            self.conn.order.update_many(
                {"order_id": order_id},
                {"$set": {"status": "canceled"}}
            )
            
            # 恢复库存
            for order in orders:
                book_id = order["book_id"]
                count = order["count"]
                # 增加book集合中的库存
                self.conn.book.update_one(
                    {"book_id": book_id, "belong_store_id": store_id},
                    {"$inc": {"stock_level": count}}
                )

        except Exception as e:
            return 528, "{}".format(str(e))

        return 200, "ok"

    def search_global(self, keyword: str, page: int = 1, limit: int = 10) -> (int, str, dict):
        try:
            # 计算分页参数
            skip = (page - 1) * limit
            
            # 使用MongoDB的文本搜索功能进行全站搜索
            # $text操作符用于执行文本搜索
            # $meta操作符用于获取搜索结果的相关性分数
            search_results = list(self.conn.book.find(
                {"$text": {"$search": keyword}},
                {
                    "_id": 0,
                    "book_id": 1,
                    "title": 1,
                    "author": 1,
                    "price": 1,
                    "publisher": 1,
                    "tags": 1,
                    "book_intro": 1,
                    "belong_store_id": 1,
                    "score": {"$meta": "textScore"},
                }
            ).sort([("score", {"$meta": "textScore"})]).skip(skip).limit(limit))
            
            # 获取总记录数
            total_count = self.conn.book.count_documents({"$text": {"$search": keyword}})
            
            # 处理搜索结果，移除不必要的字段
            books = []
            for book in search_results:
                # 移除MongoDB的_id字段和score字段
                book_data = {
                    "id": book.get("book_id"),
                    "title": book.get("title"),
                    "author": book.get("author"),
                    "price": book.get("price"),
                    "publisher": book.get("publisher"),
                    "tags": book.get("tags"),
                    "book_intro": book.get("book_intro"),
                    "belong_store_id": book.get("belong_store_id"),
                }
                books.append(book_data)
            
            # 构造返回数据，与接口文档保持一致
            data = {
                "books": books,
                "total": total_count,
                "page": page,
                "limit": limit
            }
            
        except Exception as e:
            return 528, "{}".format(str(e)), {}
        
        return 200, "ok", data

    def search_in_store(self, keyword: str, store_id: str, page: int = 1, limit: int = 10) -> (int, str, dict):
        try:
            # 检查商店是否存在
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + ({},)
            
            # 计算分页参数
            skip = (page - 1) * limit
            
            # 使用MongoDB的文本搜索功能进行店铺内搜索
            # 同时限定商店ID条件
            search_results = list(self.conn.book.find(
                {"$text": {"$search": keyword}, "belong_store_id": store_id},
                {
                    "_id": 0,
                    "book_id": 1,
                    "title": 1,
                    "author": 1,
                    "price": 1,
                    "publisher": 1,
                    "tags": 1,
                    "book_intro": 1,
                    "belong_store_id": 1,
                    "score": {"$meta": "textScore"},
                }
            ).sort([("score", {"$meta": "textScore"})]).skip(skip).limit(limit))
            
            # 获取总记录数
            total_count = self.conn.book.count_documents({"$text": {"$search": keyword}, "belong_store_id": store_id})
            
            # 处理搜索结果，移除不必要的字段
            books = []
            for book in search_results:
                # 移除MongoDB的_id字段和score字段
                book_data = {
                    "id": book.get("book_id"),
                    "title": book.get("title"),
                    "author": book.get("author"),
                    "price": book.get("price"),
                    "publisher": book.get("publisher"),
                    "tags": book.get("tags"),
                    "book_intro": book.get("book_intro"),
                    "belong_store_id": book.get("belong_store_id"),
                }
                books.append(book_data)
            
            # 构造返回数据，与接口文档保持一致
            data = {
                "books": books,
                "total": total_count,
                "page": page,
                "limit": limit
            }
            
        except Exception as e:
            return 528, "{}".format(str(e)), {}
        
        return 200, "ok", data

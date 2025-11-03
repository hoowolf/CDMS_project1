import uuid
import json
import logging
from datetime import datetime
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
                    "created_at": current_time  # 添加创建时间
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

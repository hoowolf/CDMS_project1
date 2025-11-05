import logging
import os
import threading
import time
from datetime import datetime
from flask import Flask
from flask import Blueprint
from flask import request
from be.view import auth
from be.view import seller
from be.view import buyer
from be.model.store import init_database, init_completed_event
from be.model.buyer import Buyer

bp_shutdown = Blueprint("shutdown", __name__)


def shutdown_server():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()


@bp_shutdown.route("/shutdown")
def be_shutdown():
    shutdown_server()
    return "Server shutting down..."


def check_expired_orders():
    """后台检查过期订单并取消它们"""
    buyer = Buyer()
    while True:
        try:
            # 查询所有待付款且已过期的订单
            current_time = datetime.now()
            expired_orders = list(buyer.conn.order.find({
                "status": "pending",
                "payment_deadline": {"$lt": current_time}
            }))
            
            # 按order_id分组订单
            order_groups = {}
            for order in expired_orders:
                order_id = order["order_id"]
                if order_id not in order_groups:
                    order_groups[order_id] = []
                order_groups[order_id].append(order)
            
            # 取消每个过期订单
            for order_id, orders in order_groups.items():
                if not orders:
                    continue
                    
                store_id = orders[0]["store_id"]
                
                # 更新订单状态为已取消
                buyer.conn.order.update_many(
                    {"order_id": order_id},
                    {"$set": {"status": "canceled"}}
                )
                
                # 恢复所有书籍的库存
                for order in orders:
                    book_id = order["book_id"]
                    count = order["count"]
                    buyer.conn.book.update_one(
                        {"book_id": book_id, "belong_store_id": store_id},
                        {"$inc": {"stock_level": count}}
                    )
            
            # 每隔一段时间检查一次（例如60秒）
            time.sleep(60)
        except Exception as e:
            logging.error("检查过期订单时出错: {}".format(str(e)))
            time.sleep(60)  # 出错时也继续检查


def start_background_tasks():
    """启动后台任务"""
    # 启动检查过期订单的线程
    order_check_thread = threading.Thread(target=check_expired_orders, daemon=True)
    order_check_thread.start()


def be_run():
    this_path = os.path.dirname(__file__)
    parent_path = os.path.dirname(this_path)
    log_file = os.path.join(parent_path, "app.log")
    init_database(parent_path)

    logging.basicConfig(filename=log_file, level=logging.ERROR)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    app = Flask(__name__)
    app.register_blueprint(bp_shutdown)
    app.register_blueprint(auth.bp_auth)
    app.register_blueprint(seller.bp_seller)
    app.register_blueprint(buyer.bp_buyer)
    init_completed_event.set()
    
    # 启动后台任务
    start_background_tasks()
    
    app.run()

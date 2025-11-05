from flask import Blueprint
from flask import request
from flask import jsonify
from be.model.buyer import Buyer

bp_buyer = Blueprint("buyer", __name__, url_prefix="/buyer")


@bp_buyer.route("/new_order", methods=["POST"])
def new_order():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    books: [] = request.json.get("books")
    id_and_count = []
    for book in books:
        book_id = book.get("id")
        count = book.get("count")
        id_and_count.append((book_id, count))

    b = Buyer()
    code, message, order_id = b.new_order(user_id, store_id, id_and_count)
    return jsonify({"message": message, "order_id": order_id}), code


@bp_buyer.route("/payment", methods=["POST"])
def payment():
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")
    password: str = request.json.get("password")
    b = Buyer()
    code, message = b.payment(user_id, password, order_id)
    return jsonify({"message": message}), code


@bp_buyer.route("/add_funds", methods=["POST"])
def add_funds():
    user_id = request.json.get("user_id")
    password = request.json.get("password")
    add_value = request.json.get("add_value")
    b = Buyer()
    code, message = b.add_funds(user_id, password, add_value)
    return jsonify({"message": message}), code


@bp_buyer.route("/receive", methods=["POST"])
def receive():
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")
    b = Buyer()
    code, message = b.receive(user_id, order_id)
    return jsonify({"message": message}), code


@bp_buyer.route("/search_global", methods=["POST"])
def search_global():
    keyword: str = request.json.get("keyword")
    page = request.json.get("page", 1)
    limit = request.json.get("limit", 10)
    
    # 参数验证
    if not keyword:
        return jsonify({"message": "Missing keyword parameter", "data": {}}), 400
    
    # 确保page和limit是正整数（容错字符串数字）
    try:
        page = int(page)
    except Exception:
        page = 1
    try:
        limit = int(limit)
    except Exception:
        limit = 10
    if page <= 0:
        page = 1
    if limit <= 0:
        limit = 10
    
    b = Buyer()
    code, message, data = b.search_global(keyword, page, limit)
    return jsonify({"message": message, "data": data}), code


@bp_buyer.route("/search_in_store", methods=["POST"])
def search_in_store():
    keyword: str = request.json.get("keyword")
    store_id: str = request.json.get("store_id")
    page = request.json.get("page", 1)
    limit = request.json.get("limit", 10)
    
    # 参数验证
    if not keyword:
        return jsonify({"message": "Missing keyword parameter", "data": {}}), 400
    if not store_id:
        return jsonify({"message": "Missing store_id parameter", "data": {}}), 400
    
    # 确保page和limit是正整数（容错字符串数字）
    try:
        page = int(page)
    except Exception:
        page = 1
    try:
        limit = int(limit)
    except Exception:
        limit = 10
    if page <= 0:
        page = 1
    if limit <= 0:
        limit = 10
    
    b = Buyer()
    code, message, data = b.search_in_store(keyword, store_id, page, limit)
    return jsonify({"message": message, "data": data}), code


@bp_buyer.route("/query_order", methods=["POST"])
def query_order():
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")
    
    # 参数验证
    if not user_id or not order_id:
        return jsonify({"message": "Missing required parameters", "data": {}}), 400
    
    b = Buyer()
    code, message, data = b.query_order(user_id, order_id)
    return jsonify({"message": message, "data": data}), code


@bp_buyer.route("/cancel_order", methods=["POST"])
def cancel_order():
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")
    password: str = request.json.get("password")
    
    # 参数验证
    if not user_id or not order_id or not password:
        return jsonify({"message": "Missing required parameters"}), 400
    
    b = Buyer()
    code, message = b.cancel_order(user_id, order_id, password)
    return jsonify({"message": message}), code

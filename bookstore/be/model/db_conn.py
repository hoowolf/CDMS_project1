from be.model import store


class DBConn:
    def __init__(self):
        self.conn = store.get_db()

    def user_id_exist(self, user_id):
        # 使用MongoDB查询用户是否存在
        user = self.conn.user.find_one({"user_id": user_id})
        if user is None:
            return False
        else:
            return True

    def book_id_exist(self, store_id, book_id):
        # 直接在book集合中查询书籍是否存在
        book = self.conn.book.find_one({
            "book_id": book_id,
            "belong_store_id": store_id
        })
        if book is None:
            return False
        else:
            return True

    def store_id_exist(self, store_id):
        # 使用MongoDB查询商店是否存在
        # 假设store集合中至少有一本书用来表示商店存在
        store = self.conn.store.find_one({"store_id": store_id})
        if store is None:
            return False
        else:
            return True

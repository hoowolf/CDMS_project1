import pytest
import uuid

from fe import conf
from fe.access.new_seller import register_new_seller
from fe.access.new_buyer import register_new_buyer
from fe.access import book
from fe.access.buyer import Buyer


class TestSend:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 注册卖家
        self.seller_id = "test_send_seller_{}".format(str(uuid.uuid1()))
        self.seller_password = self.seller_id
        self.seller = register_new_seller(self.seller_id, self.seller_password)

        # 注册买家
        self.buyer_id = "test_send_buyer_{}".format(str(uuid.uuid1()))
        self.buyer_password = self.buyer_id
        self.buyer = register_new_buyer(self.buyer_id, self.buyer_password)
        
        # 创建商店
        self.store_id = "test_send_store_{}".format(str(uuid.uuid1()))
        code = self.seller.create_store(self.store_id)
        assert code == 200
        
        # 添加资金给买家
        code = self.buyer.add_funds(100000)
        assert code == 200
        
        # 添加书籍到商店
        book_db = book.BookDB(conf.Use_Large_DB)
        self.books = book_db.get_book_info(0, 2)
        for bk in self.books:
            code = self.seller.add_book(self.store_id, 10, bk)
            assert code == 200
            
        # 创建订单
        self.buyer = Buyer(conf.URL, self.buyer_id, self.buyer_password)
        code, self.order_id = self.buyer.new_order(self.store_id, [(self.books[0].id, 1)])
        assert code == 200
        
        # 支付订单
        code = self.buyer.payment(self.order_id)
        assert code == 200
        
        yield

    def test_ok(self):
        # 正常发货
        code = self.seller.send(self.order_id)
        assert code == 200

    def test_error_user_id(self):
        # 错误的用户ID（非卖家）
        wrong_seller = register_new_seller(self.seller_id + "_x", self.seller_password)
        code = wrong_seller.send(self.order_id)
        assert code != 200

    def test_error_order_id(self):
        # 错误的订单ID
        code = self.seller.send(self.order_id + "_x")
        assert code != 200

    def test_error_non_paid_order(self):
        # 测试未支付的订单无法发货（需要重新创建一个未支付的订单）
        buyer = Buyer(conf.URL, self.buyer_id, self.buyer_password)
        code, order_id = buyer.new_order(self.store_id, [(self.books[1].id, 1)])
        assert code == 200
        
        # 尝试发货未支付的订单
        code = self.seller.send(order_id)
        assert code != 200
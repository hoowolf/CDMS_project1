import pytest
import uuid

from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.buyer import Buyer
from fe import conf


class TestOrder:
    buyer_id: str
    password: str
    buyer: Buyer
    order_id: str
    store_id: str
    seller_id: str

    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 初始化测试数据
        self.seller_id = "test_order_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_order_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_order_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        
        # 使用GenBook生成书籍和商店
        gen_book = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
        assert ok
        
        # 注册并登录买家
        self.buyer = register_new_buyer(self.buyer_id, self.password)
        assert self.buyer is not None
        
        # 创建订单
        code, self.order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        
        yield

    def test_query_order(self):
        # 测试正常查询订单
        code, message, data = self.buyer.query_order(self.order_id)
        assert code == 200
        assert data["order_id"] == self.order_id
        assert data["buyer_id"] == self.buyer_id
        assert data["store_id"] == self.store_id
        assert data["status"] == "pending"
        assert "books" in data
        assert "total_price" in data

    def test_query_order_error_non_exist_order_id(self):
        # 测试查询不存在的订单
        code, message, data = self.buyer.query_order(self.order_id + "_x")
        assert code != 200

    def test_query_order_error_non_exist_user_id(self):
        # 测试使用错误用户ID查询订单
        self.buyer.user_id = self.buyer.user_id + "_x"
        code, message, data = self.buyer.query_order(self.order_id)
        assert code != 200

    def test_cancel_order(self):
        # 测试正常取消订单
        code = self.buyer.cancel_order(self.order_id, self.password)
        assert code == 200

        # 验证订单状态已更新为取消
        code, message, data = self.buyer.query_order(self.order_id)
        assert code == 200
        assert data["status"] == "canceled"

    def test_cancel_order_error_non_exist_order_id(self):
        # 测试取消不存在的订单
        code = self.buyer.cancel_order(self.order_id + "_x", self.password)
        assert code != 200

    def test_cancel_order_error_wrong_password(self):
        # 测试使用错误密码取消订单
        code = self.buyer.cancel_order(self.order_id, self.password + "_x")
        assert code != 200

    def test_cancel_order_error_non_exist_user_id(self):
        # 测试使用错误用户ID取消订单
        self.buyer.user_id = self.buyer.user_id + "_x"
        code = self.buyer.cancel_order(self.order_id, self.password)
        assert code != 200

    def test_cancel_order_error_wrong_status(self):
        # 测试取消已发货的订单（需要先支付并发货）
        # 先支付订单
        code, message, data = self.buyer.query_order(self.order_id)
        total_price = data["total_price"]
        
        code = self.buyer.add_funds(total_price)
        assert code == 200
        
        code = self.buyer.payment(self.order_id)
        assert code == 200
        
        # 尝试取消已支付的订单
        code = self.buyer.cancel_order(self.order_id, self.password)
        assert code != 200
import requests
import simplejson
from typing import Tuple
from urllib.parse import urljoin
from fe.access.auth import Auth


class Buyer:
    def __init__(self, url_prefix, user_id, password):
        self.url_prefix = urljoin(url_prefix, "buyer/")
        self.user_id = user_id
        self.password = password
        self.token = ""
        self.terminal = "my terminal"
        self.auth = Auth(url_prefix)
        code, self.token = self.auth.login(self.user_id, self.password, self.terminal)
        assert code == 200

    def new_order(self, store_id: str, book_id_and_count: [(str, int)]) -> (int, str):
        books = []
        for id_count_pair in book_id_and_count:
            books.append({"id": id_count_pair[0], "count": id_count_pair[1]})
        json = {"user_id": self.user_id, "store_id": store_id, "books": books}
        # print(simplejson.dumps(json))
        url = urljoin(self.url_prefix, "new_order")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        return r.status_code, response_json.get("order_id")

    def payment(self, order_id: str):
        json = {
            "user_id": self.user_id,
            "password": self.password,
            "order_id": order_id,
        }
        url = urljoin(self.url_prefix, "payment")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def add_funds(self, add_value: str) -> int:
        json = {
            "user_id": self.user_id,
            "password": self.password,
            "add_value": add_value,
        }
        url = urljoin(self.url_prefix, "add_funds")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def __send_and_receive(self, url, method, json=None, headers=None):
        if headers is None:
            headers = {}
        headers["Content-Type"] = "application/json"
        
        if method == "POST":
            if json is None:
                r = requests.post(url, headers=headers)
            else:
                r = requests.post(url, headers=headers, json=json)
        elif method == "GET":
            r = requests.get(url, headers=headers, json=json)
        else:
            raise ValueError("Unsupported HTTP method")
            
        return r.status_code, r.text

    def __send_and_receive_json(self, url, method, json=None, headers=None):
        code, text = self.__send_and_receive(url, method, json, headers)
        if code == 200:
            try:
                response_json = simplejson.loads(text)
                return code, response_json.get("message", ""), response_json.get("data", {})
            except Exception as e:
                return code, f"Failed to parse JSON response: {str(e)}", {}
        else:
            return code, f"HTTP Error: {code}", {}

    def receive(self, order_id: str) -> int:
        json = {
            "user_id": self.user_id,
            "order_id": order_id,
        }
        url = urljoin(self.url_prefix, "receive")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code
    
    def search_global(self, keyword: str, page: int = 1, limit: int = 10) -> Tuple[int, str, dict]:
        json = {"keyword": keyword, "page": page, "limit": limit}
        url = urljoin(self.url_prefix, "search_global")
        headers = {"token": self.token}
        return self.__send_and_receive_json(url, "POST", json=json)
    
    def search_in_store(self, keyword: str, store_id: str, page: int = 1, limit: int = 10) -> Tuple[int, str, dict]:
        json = {"keyword": keyword, "store_id": store_id, "page": page, "limit": limit}
        url = urljoin(self.url_prefix, "search_in_store")
        headers = {"token": self.token}
        return self.__send_and_receive_json(url, "POST", json=json)

    def query_order(self, order_id: str) -> Tuple[int, str, dict]:
        json = {
            "user_id": self.user_id,
            "order_id": order_id,
        }
        url = urljoin(self.url_prefix, "query_order")
        headers = {"token": self.token}
        return self.__send_and_receive_json(url, "POST", json=json)

    def cancel_order(self, order_id: str, password: str) -> int:
        json = {
            "user_id": self.user_id,
            "order_id": order_id,
            "password": password,
        }
        url = urljoin(self.url_prefix, "cancel_order")
        headers = {"token": self.token}
        code, _ = self.__send_and_receive(url, "POST", json=json, headers=headers)
        return code

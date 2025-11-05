## 买家下单

#### URL：
POST http://[address]/buyer/new_order

#### Request

##### Header:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "user_id": "buyer_id",
  "store_id": "store_id",
  "books": [
    {
      "id": "1000067",
      "count": 1
    },
    {
      "id": "1000134",
      "count": 4
    }
  ]
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
store_id | string | 商铺ID | N
books | class | 书籍购买列表 | N

books数组：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
id | string | 书籍的ID | N
count | string | 购买数量 | N


#### Response

Status Code:

码 | 描述
--- | ---
200 | 下单成功
5XX | 买家用户ID不存在
5XX | 商铺ID不存在
5XX | 购买的图书不存在
5XX | 商品库存不足

##### Body:
```json
{
  "order_id": "uuid"
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
order_id | string | 订单号，只有返回200时才有效 | N


## 买家付款

#### URL：
POST http://[address]/buyer/payment

#### Request

##### Body:
```json
{
  "user_id": "buyer_id",
  "order_id": "order_id",
  "password": "password"
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单ID | N
password | string | 买家用户密码 | N 


#### Response

Status Code:

码 | 描述
--- | ---
200 | 付款成功
5XX | 账户余额不足
5XX | 无效参数
401 | 授权失败 


## 买家充值

#### URL：
POST http://[address]/buyer/add_funds

#### Request



##### Body:
```json
{
  "user_id": "user_id",
  "password": "password",
  "add_value": 10
}
```

##### 属性说明：

key | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
password | string | 用户密码 | N
add_value | int | 充值金额，以分为单位 | N


Status Code:

码 | 描述
--- | ---
200 | 充值成功
401 | 授权失败
5XX | 无效参数


## 买家收货

#### URL：
POST http://[address]/buyer/receive

#### Request

##### Header:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "user_id": "buyer_id",
  "order_id": "order_id"
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单号 | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 收货成功
5XX | 买家用户ID不存在
5XX | 订单无效或不存在
5XX | 用户权限不足（非订单所属买家）
5XX | 订单状态不是已发货状态


## 查询订单详情

#### URL：
POST http://[address]/buyer/query_order

#### Request

##### Header:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "user_id": "buyer_id",
  "order_id": "order_id"
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单号 | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 查询成功
5XX | 买家用户ID不存在
5XX | 订单无效或不存在
5XX | 用户权限不足（非订单所属买家）

##### Body:
```json
{
  "message": "ok",
  "data": {
    "order_id": "order_id",
    "buyer_id": "buyer_id",
    "store_id": "store_id",
    "status": "pending/paid/sent/received/canceled",
    "created_at": "2023-01-01T00:00:00",
    "books": [
      {
        "book_id": "1000067",
        "count": 1,
        "price": 1000
      }
    ],
    "total_price": 1000
  }
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
order_id | string | 订单号 | N
buyer_id | string | 买家用户ID | N
store_id | string | 商铺ID | N
status | string | 订单状态 | N
created_at | string | 订单创建时间 | N
books | array | 订单中的书籍列表 | N
total_price | int | 订单总价（单位：分） | N

books数组元素：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
book_id | string | 书籍ID | N
count | int | 购买数量 | N
price | int | 单价（单位：分） | N


## 取消订单

#### URL：
POST http://[address]/buyer/cancel_order

#### Request

##### Header:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "user_id": "buyer_id",
  "order_id": "order_id",
  "password": "password"
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单号 | N
password | string | 买家用户密码 | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 取消成功
5XX | 买家用户ID不存在
5XX | 订单无效或不存在
5XX | 用户权限不足（非订单所属买家）
5XX | 订单状态不允许取消（只有pending状态的订单可以取消）
401 | 密码错误


## 全站图书搜索

#### URL：
POST http://[address]/buyer/search_global

#### Request

##### Header:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "keyword": "search keyword",
  "page": 1,
  "limit": 10
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
keyword | string | 搜索关键词 | N
page | int | 页码，从1开始 | Y，默认为1
limit | int | 每页返回结果数量 | Y，默认为10

#### Response

Status Code:

码 | 描述
--- | ---
200 | 搜索成功
400 | 缺少必要参数

##### Body:
```json
{
  "message": "ok",
  "data": {
    "books": [
      {
        "id": "1000067",
        "title": "书籍标题",
        "tags": ["tag1", "tag2"],
        "content": "书籍内容摘要...",
        "book_intro": "书籍简介",
        "author": "作者",
        "price": 1000,
        "belong_store_id": "store_id"
      }
    ],
    "total": 100,
    "page": 1,
    "limit": 10
  }
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
books | array | 搜索到的书籍列表 | N
total | int | 符合搜索条件的书籍总数 | N
page | int | 当前页码 | N
limit | int | 每页返回结果数量 | N

books数组元素：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
id | string | 书籍ID | N
title | string | 书籍标题 | N
tags | array | 标签列表 | N
content | string | 书籍内容 | N
book_intro | string | 书籍简介 | N
author | string | 作者 | N
price | int | 价格（单位：分） | N
belong_store_id | string | 所属商店ID | N


## 店铺内图书搜索

#### URL：
POST http://[address]/buyer/search_in_store

#### Request

##### Header:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "keyword": "search keyword",
  "store_id": "store_id",
  "page": 1,
  "limit": 10
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
keyword | string | 搜索关键词 | N
store_id | string | 商店ID | N
page | int | 页码，从1开始 | Y，默认为1
limit | int | 每页返回结果数量 | Y，默认为10

#### Response

Status Code:

码 | 描述
--- | ---
200 | 搜索成功
400 | 缺少必要参数

##### Body:
```json
{
  "message": "ok",
  "data": {
    "books": [
      {
        "id": "1000067",
        "title": "书籍标题",
        "tags": ["tag1", "tag2"],
        "content": "书籍内容摘要...",
        "book_intro": "书籍简介",
        "author": "作者",
        "price": 1000,
        "belong_store_id": "store_id"
      }
    ],
    "total": 50,
    "page": 1,
    "limit": 10
  }
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
books | array | 搜索到的书籍列表 | N
total | int | 符合搜索条件的书籍总数 | N
page | int | 当前页码 | N
limit | int | 每页返回结果数量 | N

books数组元素：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
id | string | 书籍ID | N
title | string | 书籍标题 | N
tags | array | 标签列表 | N
content | string | 书籍内容 | N
book_intro | string | 书籍简介 | N
author | string | 作者 | N
price | int | 价格（单位：分） | N
belong_store_id | string | 所属商店ID | N
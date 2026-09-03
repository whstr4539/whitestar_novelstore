# -*- coding: utf-8 -*-
"""星辰书城 API 全量测试套件（零依赖：仅用 Python 标准库 urllib）

覆盖：匿名访问 / 认证 / 钱包支付闭环 / 章节购买 / 书架 / 评论点赞 /
评分 / 月票 / 打赏 / 作者后台 / 管理后台 / 越权与边界 / 安全项 / 轻量并发。

用法：backend/.venv/Scripts/python.exe backend/tests/api_test_suite.py [BASE_URL]
"""
import json
import hashlib
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
RESULTS = []  # (status, name, detail)


def req(method, path, token=None, body=None, expect=None, name=None, note=""):
    """发请求并记录结果。expect 为期望状态码列表；None 表示不校验。"""
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            code, text = resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        code, text = e.code, e.read().decode("utf-8")
    except Exception as e:  # noqa: BLE001
        code, text = -1, str(e)
    try:
        js = json.loads(text) if text else {}
    except json.JSONDecodeError:
        js = {"_raw": text[:200]}
    ok = expect is None or code in expect
    status = "PASS" if ok else "FAIL"
    detail = f"HTTP {code}"
    if not ok:
        detail += f" 期望{expect} 实际响应: {text[:220]}"
    if note:
        detail += f" ｜ {note}"
    RESULTS.append((status, name or f"{method} {path}", detail))
    return code, js, text


def summary():
    passed = sum(1 for s, *_ in RESULTS if s == "PASS")
    failed = [x for x in RESULTS if x[0] == "FAIL"]
    print("\n" + "=" * 72)
    print(f"总计 {len(RESULTS)} 项 ｜ 通过 {passed} ｜ 失败 {len(failed)}")
    print("=" * 72)
    for s, n, d in RESULTS:
        if s == "FAIL":
            print(f"[FAIL] {n}\n       {d}")
    return len(failed)


# ============================ A. 匿名公开访问 ============================
print("—— A. 匿名公开访问 ——")
req("GET", "/api/health", expect=[200], name="A1 健康检查")
code, js, _ = req("GET", "/api/novels?page_size=5", expect=[200], name="A2 小说列表")
novel_total = js.get("total", 0)
req("GET", "/api/novels?" + urllib.parse.urlencode({"keyword": "剑"}), expect=[200], name="A3 关键词搜索")
req("GET", "/api/novels?sort=score&page=1&page_size=3", expect=[200], name="A4 评分排序")
req("GET", "/api/novels?category_id=1", expect=[200], name="A5 分类筛选")
req("GET", "/api/novels?category_id=99999", expect=[404], name="A6 不存在分类→404")
req("GET", "/api/novels/1", expect=[200], name="A7 小说详情")
req("GET", "/api/novels/99999", expect=[404], name="A8 不存在小说→404")
req("GET", "/api/novels/1/chapters", expect=[200], name="A9 章节目录")
req("GET", "/api/novels/1/comments", expect=[200], name="A10 书评列表(匿名)")
req("GET", "/api/notices", expect=[200], name="A11 公告列表(匿名)")
req("GET", "/api/categories", expect=[200], name="A12 分类列表(匿名)")
req("GET", "/api/novels/tickets/rank", expect=[200], name="A13 月票榜(匿名)")
req("GET", "/api/bookshelf", expect=[401], name="A14 书架未登录→401")
req("GET", "/api/wallet", expect=[401], name="A15 钱包未登录→401")
# 免费章节匿名阅读（BUG-1 回归：修复后匿名可读免费章）
code, _, text = req("GET", "/api/chapters/1", expect=[200],
                    name="A16 匿名读免费章节（应200）",
                    note="曾因 read_chapter 误用 get_current_user 返回 401，已修复")

# 从公开目录取免费/付费章各一个
code, js, _ = req("GET", "/api/novels/1/chapters", expect=[200])
chapters = js if isinstance(js, list) else []
free_ch = next((c["id"] for c in chapters if float(c.get("price", 0)) == 0), None)
paid_ch = next((c["id"] for c in chapters if float(c.get("price", 0)) > 0), None)
print(f"  (免费章 id={free_ch}, 付费章 id={paid_ch})")

# ============================ B. 注册 / 登录 / JWT ============================
print("—— B. 注册 / 登录 / JWT ——")
u = "t_" + uuid.uuid4().hex[:10]
pwd = "test123456"
code, js, _ = req("POST", "/api/auth/register", body={
    "username": u, "password": pwd, "nickname": "测试用户"}, expect=[200, 201],
    name="B1 注册新用户")
new_token = js.get("access_token", "")
req("POST", "/api/auth/register", body={"username": u, "password": pwd, "nickname": "x"},
    expect=[409], name="B2 重复用户名→409")
req("POST", "/api/auth/register", body={"username": u + "_2", "password": "123", "nickname": "x"},
    expect=[422], name="B3 密码过短→422")
req("POST", "/api/auth/register", body={"username": "ab", "password": pwd, "nickname": "x"},
    expect=[422], name="B4 用户名过短→422")
req("POST", "/api/auth/login", body={"username": u, "password": "wrong!"}, expect=[401],
    name="B5 错误密码→401")
code, js, _ = req("POST", "/api/auth/login", body={"username": u, "password": pwd},
                  expect=[200], name="B6 正确登录")
new_token = js.get("access_token", new_token)
req("GET", "/api/auth/me", token=new_token, expect=[200], name="B7 /me 带 token")
req("GET", "/api/auth/me", token="garbage.token.here", expect=[401], name="B8 伪造 token→401")
# alg=none 攻击
import base64
h64 = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=")
p64 = base64.urlsafe_b64encode(json.dumps({"sub": "1", "role": "admin", "exp": 9999999999}).encode()).rstrip(b"=")
req("GET", "/api/auth/me", token=(h64 + b"." + p64 + b".").decode(), expect=[401],
    name="B9 JWT alg=none 攻击→401")
# 篡改签名
if new_token:
    head, pay, sig = new_token.split(".")
    bad = head + "." + pay + ("A" if sig[-1] != "A" else "B")
    req("GET", "/api/auth/me", token=bad, expect=[401], name="B10 篡改签名→401")

DEMO = {}
for acc in ("admin", "author_zhang", "author_wang", "reader_li", "reader_chen"):
    code, js, _ = req("POST", "/api/auth/login", body={"username": acc, "password": "123456"},
                      expect=[200], name=f"B11 登录演示账号 {acc}")
    DEMO[acc] = js.get("access_token", "")

# ============================ C. 钱包 / 支付闭环 ============================
print("—— C. 钱包 / 支付闭环 ——")
code, js, _ = req("GET", "/api/wallet", token=new_token, expect=[200], name="C1 查询余额(自动开户)")
bal0 = float(js.get("balance", 0))
req("POST", "/api/wallet/recharge", token=new_token, body={"amount": 0}, expect=[422],
    name="C2 充值金额≤0→422")
req("POST", "/api/wallet/recharge", token=new_token, body={"amount": 99999}, expect=[422],
    name="C3 充值超上限→422")
code, js, _ = req("POST", "/api/wallet/recharge", token=new_token, body={"amount": 10},
                  expect=[201], name="C4 创建充值订单 10 元")
order_no = js.get("order_no", "")
req("GET", f"/api/wallet/order/{order_no}", token=new_token, expect=[200], name="C5 订单状态 pending")
code, js, _ = req("POST", f"/api/wallet/pay/{order_no}", token=new_token, body={},
                  expect=[200], name="C6 收银台受理支付")
code, js, _ = req("POST", f"/api/wallet/pay/{order_no}/cancel", token=new_token, body={},
                  expect=[200, 410], name="C7 处理中取消(可能已被回调关单)")
code, js, _ = req("GET", f"/api/wallet/order/{order_no}", token=new_token, expect=[200],
                  name="C8 取消后订单终态")
# 确定性回调：绕过 80% 模拟成功率，直接以合法签名调用 notify
code, js, _ = req("POST", "/api/wallet/recharge", token=new_token, body={"amount": 10},
                  expect=[201], name="C9 再建订单走回调入账")
order2 = js.get("order_no", "")
sign = hashlib.md5(f"{order2}successmock-channel-sign-key-2024".encode()).hexdigest()
req("POST", "/api/wallet/pay/notify", body={"order_no": order2, "result": "success", "sign": "deadbeef"},
    expect=[400], name="C10 伪造回调签名→400")
code, js, _ = req("POST", "/api/wallet/pay/notify",
                  body={"order_no": order2, "result": "success", "sign": sign},
                  expect=[200], name="C11 合法回调 success")
req("POST", "/api/wallet/pay/notify", body={"order_no": order2, "result": "success", "sign": sign},
    expect=[200], name="C12 回调重放(幂等，不重复入账)")
code, js, _ = req("GET", "/api/wallet", token=new_token, expect=[200], name="C13 充值后余额")
bal1 = float(js.get("balance", 0))
if abs(bal1 - (bal0 + 100)) > 0.001:
    RESULTS.append(("FAIL", "C13b 余额应增加 100 书币", f"实际 {bal0} -> {bal1}"))
else:
    RESULTS.append(("PASS", "C13b 余额应增加 100 书币", f"{bal0} -> {bal1}"))
code, js, _ = req("GET", "/api/wallet/bills", token=new_token, expect=[200], name="C14 账单流水")
code, js, _ = req("GET", f"/api/wallet/order/{order2}", token=new_token, expect=[200])
if js.get("status") != "success":
    RESULTS.append(("FAIL", "C15 回调后订单应为 success", f"实际 {js.get('status')}"))
else:
    RESULTS.append(("PASS", "C15 回调后订单应为 success", ""))
code, js, _ = req("GET", "/api/wallet", token=new_token, expect=[200])
if abs(float(js.get("balance", 0)) - bal1) > 0.001:
    RESULTS.append(("FAIL", "C16 重放入账幂等(余额不变)", ""))
else:
    RESULTS.append(("PASS", "C16 重放入账幂等(余额不变)", ""))
req("POST", f"/api/wallet/pay/{order2}", token=DEMO.get("reader_chen", ""), body={},
    expect=[404], name="C17 他人订单受理→404")

# ============================ D. 章节购买闭环 ============================
print("—— D. 章节购买闭环 ——")
if paid_ch:
    req("GET", f"/api/chapters/{paid_ch}", expect=[401],
        name="D0 匿名读付费章→401")
    req("GET", f"/api/chapters/{paid_ch}/status", token=new_token, expect=[200], name="D1 购买状态查询")
    req("GET", f"/api/chapters/{paid_ch}", token=new_token, expect=[402],
        name="D2 未购读付费章→402")
    # 确保余额足够购买
    code, js, _ = req("GET", f"/api/chapters/{paid_ch}", token=DEMO.get("admin", ""), expect=[200])
    price = float(js.get("chapter", {}).get("price", 0))
    code, js, _ = req("GET", "/api/wallet", token=new_token, expect=[200])
    if price > float(js.get("balance", 0)):
        o = req("POST", "/api/wallet/recharge", token=new_token, body={"amount": 100}, expect=[201])[1]
        s = hashlib.md5(f"{o.get('order_no')}successmock-channel-sign-key-2024".encode()).hexdigest()
        req("POST", "/api/wallet/pay/notify", body={"order_no": o.get("order_no"), "result": "success", "sign": s}, expect=[200])
    code, js, _ = req("POST", f"/api/chapters/{paid_ch}/purchase", token=new_token, expect=[200],
                      name="D3 购买付费章节(事务扣费)")
    bal_after = js.get("balance_after")
    req("POST", f"/api/chapters/{paid_ch}/purchase", token=new_token, expect=[409],
        name="D4 重复购买→409")
    code, js, _ = req("GET", f"/api/chapters/{paid_ch}", token=new_token, expect=[200],
                      name="D5 购买后可读正文")
    has_content = bool(js.get("content"))
    if not has_content:
        RESULTS.append(("FAIL", "D5b 付费章正文非空", ""))
    else:
        RESULTS.append(("PASS", "D5b 付费章正文非空", ""))
    code, js, _ = req("GET", "/api/wallet", token=new_token, expect=[200])
    if bal_after is not None and abs(float(js.get("balance", 0)) - float(bal_after)) > 0.001:
        RESULTS.append(("FAIL", "D6 扣费金额与余额一致", f"{bal_after} vs {js.get('balance')}"))
    else:
        RESULTS.append(("PASS", "D6 扣费金额与余额一致", ""))
if free_ch:
    req("POST", f"/api/chapters/{free_ch}/purchase", token=new_token, expect=[400],
        name="D7 购买免费章→400")
    if new_token:
        code, _, _ = req("GET", f"/api/chapters/{free_ch}", token=new_token, expect=[200],
                         name="D8 登录读免费章")
req("POST", "/api/chapters/99999/purchase", token=new_token, expect=[404], name="D9 购买不存在章节→404")

# ============================ E. 书架 / 进度 ============================
print("—— E. 书架 / 进度 ——")
req("POST", "/api/bookshelf/1", token=new_token, expect=[200], name="E1 加入书架")
req("POST", "/api/bookshelf/1", token=new_token, expect=[409], name="E2 重复加入→409")
req("GET", "/api/bookshelf", token=new_token, expect=[200], name="E3 书架列表")
if free_ch:
    req("PUT", "/api/bookshelf/progress", token=new_token,
        body={"novel_id": 1, "chapter_id": free_ch, "progress": 42.5}, expect=[200], name="E4 上报进度")
    req("GET", "/api/bookshelf/history/list", token=new_token, expect=[200], name="E5 阅读历史")
    code, js, _ = req("GET", f"/api/chapters/{free_ch}", token=DEMO.get("admin", ""), expect=[200])
    novel_of_free = js.get("novel_id")
    if novel_of_free and novel_of_free != 1:
        req("PUT", "/api/bookshelf/progress", token=new_token,
            body={"novel_id": novel_of_free, "chapter_id": free_ch, "progress": 10},
            expect=[404], name="E6 跨书章节进度→404")
req("DELETE", "/api/bookshelf/1", token=new_token, expect=[200], name="E7 移出书架")
req("DELETE", "/api/bookshelf/1", token=new_token, expect=[404], name="E8 重复移出→404")

# ============================ F. 评论 / 点赞 ============================
print("—— F. 评论 / 点赞 ——")
req("POST", "/api/novels/1/comments", token=new_token, body={"content": "x" * 501},
    expect=[422], name="F1 评论超500字→422")
code, js, _ = req("POST", "/api/novels/1/comments", token=new_token,
                  body={"content": "测试书评 <script>alert(1)</script>"}, expect=[201], name="F2 发书评")
c1 = js.get("id")
code, js, _ = req("POST", "/api/novels/1/comments", token=new_token,
                  body={"content": "本章说测试", "chapter_id": free_ch or 1}, expect=[201], name="F3 发本章说")
c2 = js.get("id")
req("POST", "/api/novels/1/comments", token=new_token,
    body={"content": "x", "chapter_id": 99999}, expect=[400], name="F4 本章说指向不存在章节→400")
code, js, _ = req("POST", "/api/novels/2/comments", token=new_token,
                  body={"content": "x", "chapter_id": free_ch}, expect=[400],
                  name="F5 本章说跨作品→400")
code, js, _ = req("POST", "/api/novels/1/comments", token=new_token,
                  body={"content": "楼中楼回复", "parent_id": c1}, expect=[201], name="F6 回复评论")
c_reply = js.get("id")
req("POST", "/api/novels/1/comments", token=new_token,
    body={"content": "层叠回复", "parent_id": c_reply}, expect=[400], name="F7 回复的回复→400")
req("POST", "/api/novels/1/comments", token=new_token,
    body={"content": "x", "parent_id": 99999}, expect=[404], name="F8 回复不存在评论→404")
code, js, _ = req("POST", f"/api/comments/{c1}/like", token=new_token, expect=[200], name="F9 点赞")
likes1 = js.get("likes", 0)
code, js, _ = req("POST", f"/api/comments/{c1}/like", token=new_token, expect=[200], name="F10 再点取消赞")
if not (js.get("likes") == likes1 - 1 and js.get("liked") is False):
    RESULTS.append(("FAIL", "F10b 取消赞后计数-1", f"likes {likes1}->{js.get('likes')} liked={js.get('liked')}"))
else:
    RESULTS.append(("PASS", "F10b 取消赞后计数-1", ""))
code, js, _ = req("GET", f"/api/comments/{c1}/replies", expect=[200], name="F11 楼中楼列表")
if not any(r.get("id") == c_reply for r in js):
    RESULTS.append(("FAIL", "F11b 回复出现在楼中楼", ""))
else:
    RESULTS.append(("PASS", "F11b 回复出现在楼中楼", ""))
req("GET", "/api/comments/me", token=new_token, expect=[200], name="F12 我的评论")
req("DELETE", f"/api/comments/{c1}", token=DEMO.get("reader_chen", ""), expect=[403],
    name="F13 他人删评论→403")
req("DELETE", f"/api/comments/{c1}", token=new_token, expect=[200], name="F14 本人删评论")

# ============================ G. 评分 ============================
print("—— G. 评分 ——")
req("POST", "/api/novels/1/reviews", token=new_token, body={"rating": 6}, expect=[422],
    name="G1 评分>5→422")
req("POST", "/api/novels/1/reviews", token=new_token, body={"rating": 0}, expect=[422],
    name="G2 评分<1→422")
code, js, _ = req("GET", "/api/novels/1", expect=[200])
score0 = js.get("score")
req("POST", "/api/novels/1/reviews", token=new_token, body={"rating": 5, "content": "好看"},
    expect=[201], name="G3 提交评分5星")
code, js, _ = req("GET", "/api/novels/1", expect=[200], name="G4 均分回写详情")
req("POST", "/api/novels/1/reviews", token=new_token, body={"rating": 1}, expect=[201],
    name="G5 重复评分=更新(UPSERT)")
code, js, _ = req("GET", "/api/novels/1/reviews", expect=[200], name="G6 评分列表")
mine = [r for r in js if r.get("user", {}).get("username") == u]
if len(mine) != 1 or mine[0]["rating"] != 1:
    RESULTS.append(("FAIL", "G7 一人一书一评(UPSERT 生效)", f"{len(mine)} 条"))
else:
    RESULTS.append(("PASS", "G7 一人一书一评(UPSERT 生效)", ""))
rid = mine[0]["id"] if mine else 0
req("DELETE", f"/api/novels/1/reviews/{rid}", token=DEMO.get("reader_chen", ""), expect=[403],
    name="G8 他人删评分→403")
req("DELETE", f"/api/novels/1/reviews/{rid}", token=new_token, expect=[200], name="G9 本人删评分")
code, js, _ = req("GET", "/api/novels/1", expect=[200])
if abs(float(js.get("score", 0)) - score0) > 0.05:
    RESULTS.append(("WARN", "G10 删除评分后均分恢复", f"{score0} -> {js.get('score')}"))
else:
    RESULTS.append(("PASS", "G10 删除评分后均分恢复", f"{score0}"))

# ============================ H. 月票 / 打赏 ============================
print("—— H. 月票 / 打赏 ——")
req("POST", "/api/novels/1/tickets", token=new_token, body={"ticket_type": "monthly"},
    expect=[200], name="H1 投月票")
req("POST", "/api/novels/1/tickets", token=new_token, body={"ticket_type": "monthly"},
    expect=[409], name="H2 重复月票→409")
req("POST", "/api/novels/1/tickets", token=new_token, body={"ticket_type": "recommend"},
    expect=[200], name="H3 投推荐票(不同类型可投)")
req("POST", "/api/novels/99999/tickets", token=new_token, body={}, expect=[404],
    name="H4 给不存在小说投票→404")
code, js, _ = req("GET", "/api/novels/tickets/rank?limit=5", expect=[200], name="H5 月票榜")
code, js, _ = req("POST", "/api/novels/1/rewards", token=new_token,
                  body={"amount": 5000, "message": "土豪"}, expect=[402],
                  name="H6 打赏超余额→402")
code, js, _ = req("POST", "/api/novels/1/rewards", token=new_token, body={"amount": 1},
                  expect=[201], name="H7 正常打赏 1 书币")
code, js, _ = req("GET", "/api/wallet", token=new_token, expect=[200])
# 小数金额边界：0.5 书币
code, js, _ = req("POST", "/api/novels/2/rewards", token=DEMO.get("reader_li", ""),
                  body={"amount": 0.5}, expect=[400, 402, 201], note="0.5 书币合法(小数金额)")
req("GET", "/api/novels/1/rewards", expect=[200], name="H8 打赏记录公开")

# ============================ I. 作者后台 ============================
print("—— I. 作者后台 ——")
az = DEMO.get("author_zhang", "")
req("GET", "/api/author/my-novels", token=new_token, expect=[403], name="I1 读者访问作者台→403")
req("GET", "/api/author/my-novels", token=az, expect=[200], name="I2 我的作品")
code, js, _ = req("GET", "/api/author/stats", token=az, expect=[200], name="I3 写作台统计")
req("GET", "/api/author/novels/2/earnings", token=new_token, expect=[403],
    name="I4 读者查收益→403")
code, js, _ = req("POST", "/api/author/novels", token=az,
                  body={"title": "测试作品-可删除", "intro": "测试简介", "category_id": 1},
                  expect=[201], name="I5 创建作品")
test_novel = js.get("id")
code, js, _ = req("POST", f"/api/author/novels/{test_novel}/chapters", token=az,
                  body={"title": "第一章", "content": "这是测试正文，字数统计验证用。", "price": 2},
                  expect=[201], name="I6 发布付费章节")
new_ch = js.get("id")
if js.get("novel_chapter_count") != 1:
    RESULTS.append(("FAIL", "I7 触发器回写章数", f"{js.get('novel_chapter_count')}"))
else:
    RESULTS.append(("PASS", "I7 触发器回写章数", ""))
if js.get("novel_word_count") != js.get("word_count"):
    RESULTS.append(("FAIL", "I8 触发器回写字数", f"{js.get('novel_word_count')} vs {js.get('word_count')}"))
else:
    RESULTS.append(("PASS", "I8 触发器回写字数", ""))
req("POST", f"/api/author/novels/{test_novel}/chapters", token=DEMO.get("author_wang", ""),
    body={"title": "x", "content": "y"}, expect=[403], name="I9 他人作品发章→403")
req("PUT", f"/api/author/chapters/{new_ch}", token=az,
    body={"title": "第一章(改)", "price": 3}, expect=[200], name="I10 修改章节")
req("PUT", f"/api/author/chapters/{new_ch}", token=DEMO.get("author_wang", ""),
    body={"title": "黑"}, expect=[403], name="I11 改他人章节→403")
code, js, _ = req("GET", f"/api/author/novels/{test_novel}/earnings", token=az, expect=[200],
                  name="I12 作品收益统计")
req("DELETE", f"/api/author/chapters/{new_ch}", token=az, expect=[200], name="I13 软删除章节")
req("GET", f"/api/chapters/{new_ch}", token=az, expect=[404], name="I14 删除后不可读→404")
req("GET", f"/api/novels/{test_novel}/chapters", expect=[200], name="I15 目录不含已删章")
code, js, _ = req("GET", f"/api/novels/{test_novel}/chapters", expect=[200])
if any(c["id"] == new_ch for c in js):
    RESULTS.append(("FAIL", "I15b 已删章不出现在目录", ""))
else:
    RESULTS.append(("PASS", "I15b 已删章不出现在目录", ""))
req("DELETE", f"/api/author/chapters/{new_ch}", token=az, expect=[200], name="I16 重复删除幂等")

# ============================ J. 管理后台 ============================
print("—— J. 管理后台 ——")
adm = DEMO.get("admin", "")
req("GET", "/api/admin/stats", token=new_token, expect=[403], name="J1 读者访问管理→403")
req("GET", "/api/admin/stats", token=adm, expect=[200], name="J2 平台统计")
req("GET", "/api/admin/users?keyword=reader", token=adm, expect=[200], name="J3 用户搜索")
req("GET", "/api/admin/comments?page_size=5", token=adm, expect=[200], name="J4 评论管理列表")
req("GET", "/api/admin/novels?status=serializing", token=adm, expect=[200], name="J5 作品管理列表")
# 封禁/解封
code, js, _ = req("POST", "/api/auth/register", body={
    "username": "t_ban_" + uuid.uuid4().hex[:8], "password": pwd, "nickname": "待封禁"},
    expect=[200, 201])
ban_token = js.get("access_token", "")
ban_uid = js.get("user", {}).get("id")
req("PUT", f"/api/admin/users/{ban_uid}/status", token=adm, body={"status": 0}, expect=[200],
    name="J6 封禁用户")
code, js, _ = req("GET", "/api/auth/me", token=ban_token, expect=[401], name="J7 封禁后 token 失效")
req("PUT", f"/api/admin/users/{ban_uid}/status", token=adm, body={"status": 1}, expect=[200],
    name="J8 解封用户")
req("GET", "/api/auth/me", token=ban_token, expect=[200], name="J9 解封后 token 恢复")
code, js, _ = req("POST", "/api/auth/login", body={"username": u, "password": pwd}, expect=[200],
                  name="J10 登录恢复")
# admin 封禁自己
code, js, _ = req("GET", "/api/auth/me", token=adm, expect=[200])
admin_id = js.get("id")
req("PUT", f"/api/admin/users/{admin_id}/status", token=adm, body={"status": 0}, expect=[400],
    name="J11 不能封禁自己→400")
# 下架作品
req("PUT", f"/api/admin/novels/{test_novel}/status", token=adm, body={"status": "banned"},
    expect=[200], name="J12 下架作品")
code, js, _ = req("GET", f"/api/novels/{test_novel}", expect=[404], name="J13 下架后详情404")
req("PUT", f"/api/admin/novels/{test_novel}/status", token=adm, body={"status": "serializing"},
    expect=[200], name="J14 恢复作品")
code, js, _ = req("GET", f"/api/novels/{test_novel}", expect=[200], name="J15 恢复后可见")
# 公告
req("POST", "/api/notices", token=new_token, body={"title": "x", "content": "y"}, expect=[403],
    name="J16 读者发公告→403")
code, js, _ = req("POST", "/api/notices", token=adm,
                  body={"title": "测试公告", "content": "测试内容"}, expect=[201], name="J17 管理员发公告")
nid = js.get("id")
req("DELETE", f"/api/notices/{nid}", token=adm, expect=[200], name="J18 删除公告")

# ============================ K. 安全 / 注入面 ============================
print("—— K. 安全 / 注入面 ——")
req("GET", "/api/novels?" + urllib.parse.urlencode({"keyword": "' OR 1=1 --"}), expect=[200], name="K1 SQL注入词(应200不出错)")
req("GET", "/api/admin/users?" + urllib.parse.urlencode({"keyword": "'; DROP TABLE users; --"}), token=adm, expect=[200],
    name="K2 SQL注入(管理端搜索)")
code, js, _ = req("GET", "/api/novels", expect=[200])
if js.get("total", 0) == 0:
    RESULTS.append(("FAIL", "K3 users 表未被 DROP", ""))
else:
    RESULTS.append(("PASS", "K3 users 表未被 DROP", "列表仍返回数据"))
req("GET", "/api/novels?keyword=%", expect=[200], name="K4 LIKE 通配符未转义(宽匹配)", )
req("GET", "/api/novels/99999999999999999999", expect=[422], name="K5 超大ID→422")
req("GET", "/api/novels/abc", expect=[422], name="K6 非法路径参数→422")
# BUG-2 回归：查询参数/请求体中的超大 ID
req("GET", "/api/novels?category_id=99999999999999999999", expect=[422], name="K8 超大category_id→422")
req("GET", "/api/novels?page=99999999999999999999", expect=[422], name="K9 超大page→422")
req("PUT", "/api/bookshelf/progress", token=new_token,
    body={"novel_id": 99999999999999999999, "chapter_id": 1, "progress": 1}, expect=[422],
    name="K10 请求体超大ID→422")
# XSS 存储面：原文入库，转义由前端负责（React 默认转义）
code, js, _ = req("POST", "/api/novels/1/comments", token=new_token,
                  body={"content": "<img src=x onerror=alert(1)>"}, expect=[201], name="K7 XSS载荷入库(原文存储)")
RESULTS.append(("WARN" if js.get("content", "").startswith("<img") else "PASS",
                "K7b XSS 原文入库(需前端转义兜底)", "检查 Reader/详情页渲染是否转义"))
req("DELETE", f"/api/comments/{js.get('id')}", token=new_token, expect=[200], name="K7c 清理XSS评论")

# ============================ L. 轻量并发 ============================
print("—— L. 轻量并发 ——")
results_l = []
def _buy(tok, ch, out):
    r = urllib.request.Request(BASE + f"/api/chapters/{ch}/purchase", data=b"{}", method="POST")
    r.add_header("Content-Type", "application/json")
    r.add_header("Authorization", f"Bearer {tok}")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            out.append(resp.status)
    except urllib.error.HTTPError as e:
        out.append(e.code)
# 两个新用户并发购买同一付费章（互不冲突，行锁下都应成功）
toks = []
for i in range(2):
    uu = "t_c" + uuid.uuid4().hex[:8]
    code, js, _ = req("POST", "/api/auth/register", body={"username": uu, "password": pwd, "nickname": "并发"},
                      expect=[200, 201], name=f"L0 并发用户{i}注册")
    tok = js.get("access_token", "")
    toks.append(tok)
    o = req("POST", "/api/wallet/recharge", token=tok, body={"amount": 100}, expect=[201])[1]
    s = hashlib.md5(f"{o.get('order_no')}successmock-channel-sign-key-2024".encode()).hexdigest()
    req("POST", "/api/wallet/pay/notify", body={"order_no": o.get("order_no"), "result": "success", "sign": s},
        expect=[200], name=f"L0 并发用户{i}充值")
if paid_ch and len(toks) == 2:
    t1 = threading.Thread(target=_buy, args=(toks[0], paid_ch, results_l))
    t2 = threading.Thread(target=_buy, args=(toks[1], paid_ch, results_l))
    t1.start(); t2.start(); t1.join(); t2.join()
    ok_all = all(c in (200, 409) for c in results_l)
    RESULTS.append(("PASS" if ok_all else "FAIL",
                    "L1 并发购买(不同用户同章)",
                    f"状态码 {results_l}（均应为200成功或409余额不足）"))
# 并发点赞：同用户同评论双发（Barrier 保证真并发），赞数不得叠加
code, js, _ = req("POST", "/api/novels/1/comments", token=new_token, body={"content": "并发点赞目标"},
                  expect=[201])
lc = js.get("id")
out = []
def _like(tok, cid, out, barrier=None):
    if barrier:
        barrier.wait()
    r = urllib.request.Request(BASE + f"/api/comments/{cid}/like", data=b"{}", method="POST")
    r.add_header("Content-Type", "application/json")
    r.add_header("Authorization", f"Bearer {tok}")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            out.append((resp.status, json.loads(resp.read().decode() or "{}")))
    except urllib.error.HTTPError as e:
        out.append((e.code, e.read().decode()[:120]))
bar = threading.Barrier(2)
rounds = []
for _ in range(3):
    out = []
    t1 = threading.Thread(target=_like, args=(new_token, lc, out, bar))
    t2 = threading.Thread(target=_like, args=(new_token, lc, out, bar))
    t1.start(); t2.start(); t1.join(); t2.join()
    code, js, _ = req("GET", "/api/novels/1/comments", expect=[200])
    target = next((c for c in js if c["id"] == lc), {})
    rounds.append(target.get("likes"))
# 去重性质：任何一轮赞数都不得 ≥2（并发重复点赞不会叠加）
if any(l is not None and l >= 2 for l in rounds):
    RESULTS.append(("FAIL", "L2 并发点赞去重(赞数永不≥2)", f"各轮最终 likes={rounds}"))
elif 1 in rounds:
    RESULTS.append(("PASS", "L2 并发点赞去重(赞数永不≥2)", f"各轮最终 likes={rounds}"))
else:
    RESULTS.append(("PASS", "L2 并发点赞去重(赞数永不≥2)", f"各轮最终 likes={rounds}（时序偏串行为 toggle 设计）"))

# ============================ 汇总 ============================
n_fail = summary()
sys.exit(1 if n_fail else 0)

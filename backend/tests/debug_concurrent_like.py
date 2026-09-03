# -*- coding: utf-8 -*-
"""专项复现：并发点赞去重。捕获每次响应 body 与最终状态。"""
import json
import threading
import urllib.error
import urllib.request
import uuid

BASE = "http://127.0.0.1:8000"


def call(method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


for round_no in range(3):
    u = "dbg_" + uuid.uuid4().hex[:10]
    _, js = call("POST", "/api/auth/register", body={"username": u, "password": "test123456", "nickname": "dbg"})
    tok = js["access_token"]
    _, js = call("POST", "/api/novels/1/comments", token=tok, body={"content": f"并发目标 r{round_no}"})
    cid = js["id"]

    out = []
    def like():
        out.append(call("POST", f"/api/comments/{cid}/like", token=tok, body={}))

    ts = [threading.Thread(target=like) for _ in range(2)]
    # 用 Barrier 尽量同时发出
    barrier = threading.Barrier(2)
    def like_sync():
        barrier.wait()
        out.append(call("POST", f"/api/comments/{cid}/like", token=tok, body={}))
    ts = [threading.Thread(target=like_sync) for _ in range(2)]
    for t in ts: t.start()
    for t in ts: t.join()

    code, js = call("GET", "/api/novels/1/comments")
    final = next((c["likes"] for c in js if c["id"] == cid), None)
    print(f"round {round_no}: 响应={out}  最终likes={final}")

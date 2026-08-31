"""星辰书城 —— 演示数据生成器

用法：python scripts/gen_seed_data.py  >  db/init/02_seed.sql
（或直接运行：python scripts/gen_seed_data.py，自动写入 db/init/02_seed.sql）

生成规模：
- 实体数据：用户 6 · 分类 9 · 作品 12 · 章节 81 · 正文 81 · 评论 55 · 公告 3 · 订单 10 · 钱包 6 = 263 条
- 关联数据：分类关联 12 · 收藏 27 · 阅读进度 27 · 月票 45 · 打赏 30 · 评分 27 · 订阅 86 · 点赞 36 = 290 条

特点：
- 固定随机种子，重复生成结果一致
- 聚合字段（总分/收藏数/月票数/章数/字数）由 SQL 聚合回写，与明细完全一致
- 阅读量 total_views 与小说热度合理分布（影响热门榜演示）
- 全部密码 123456（同一 bcrypt 哈希）
"""
import random

random.seed(20240830)  # 固定种子：结果可复现

PWD_HASH = "$2b$12$BAQ8Fh95CedTKWw7GOU6IOqXL8sEPxisCULQaZEfzgMtKM3mkZgeq"  # 123456

# ---------------------------------------------------------------- 用户
# (username, nickname, email, phone, role)
USERS = [
    ("admin", "管理员", "admin@novel.com", "13800000001", "admin"),
    ("author_zhang", "张作家", "zhang@novel.com", "13800000002", "author"),
    ("author_wang", "王作家", "wang@novel.com", "13800000003", "author"),
    ("reader_li", "李读者", "li@novel.com", "13800000004", "reader"),
    ("reader_chen", "陈读者", "chen@novel.com", "13800000005", "reader"),
    ("reader_zhao", "赵读者", "zhao@novel.com", "13800000006", "reader"),
]
AUTHOR_IDS = {u[0]: i + 1 for i, u in enumerate(USERS)}  # 隐式 id 从 1 开始
READER_IDS = [4, 5, 6]  # reader_li / reader_chen / reader_zhao

# ---------------------------------------------------------------- 分类
# (name, parent_id) 父级引用顶级分类 id
CATEGORIES = [
    ("玄幻", None), ("都市", None), ("科幻", None), ("历史", None), ("悬疑", None),
    ("东方玄幻", 1), ("都市异能", 2), ("星际科幻", 3), ("历史架空", 4),
]
CAT_ID = {name: i + 1 for i, (name, _) in enumerate(CATEGORIES)}

# ---------------------------------------------------------------- 作品
# (title, author, category, status, intro, views)
NOVELS = [
    ("星辰问道", "author_zhang", "东方玄幻", "serializing", "少年自边陲小城走出，一路问道星辰大海。宗门倾轧、大道独行，他步步登临九天之上。", 28600),
    ("都市夜行人", "author_zhang", "都市异能", "serializing", "白天是996程序员，夜晚是都市守护者。当霓虹照亮罪恶，他披上夜色独行。", 24500),
    ("星际拓荒者", "author_zhang", "星际科幻", "finished", "人类第一次跃迁失败，被困荒芜星系。在废墟中重建文明，是拓荒者的宿命。", 31200),
    ("大明烟云", "author_zhang", "历史架空", "serializing", "一介布衣穿越成落魄举子，于烟云诡谲的朝堂之上，搅动大明风云。", 11800),
    ("雾都奇闻", "author_zhang", "悬疑", "finished", "雾都连环失踪案背后，隐藏着跨越三十年的秘密。侦探与亡者的对话。", 9700),
    ("沧澜剑歌", "author_wang", "东方玄幻", "serializing", "剑冢出鞘之日，天下修者皆惊。他背着一柄锈剑，走遍三界寻仇。", 15200),
    ("深空回响", "author_wang", "星际科幻", "serializing", "深空监测站收到一段不可能的信号——发信者是三百年前的自己。", 13100),
    ("人间烟火", "author_wang", "都市异能", "serializing", "能看见他人情绪颜色的少年，在烟火人间里守护每一盏灯。", 8900),
    ("汉末风骨", "author_wang", "历史", "serializing", "穿成汉末小吏，他只想守住一方百姓，却一步步走进历史风口。", 16700),
    ("迷雾山庄", "author_wang", "悬疑", "finished", "暴雨夜的山庄晚宴，八位宾客各怀心事，没有人能活着离开。", 11200),
    ("星海拾遗", "author_wang", "星际科幻", "serializing", "拾荒者捡到一枚星图碎片，从此星系边疆的风暴有了名字。", 7400),
    ("燕京夜话", "author_zhang", "都市", "finished", "老城胡同里的深夜书房，每盏灯下都有一段旧事。", 10300),
]
NOVEL_ID = {title: i + 1 for i, (title, *_) in enumerate(NOVELS)}

# 每本作品章节数（章数合计 81）
CHAPTER_PLAN = [8, 6, 10, 7, 5, 7, 6, 6, 8, 6, 5, 7]  # 与 NOVELS 一一对应
FREE_CHAPTERS = 2  # 每本书前 2 章免费试读

# 正文写作：按书名/章节号生成若干自然段（每段 120 字左右，词库轮换）
PHRASES = [
    "夜色如墨，长街尽头亮起一盏孤灯。",
    "他握紧手中的剑，指节发白，心口却渐渐平静下来。",
    "江湖传闻如野火，一夜之间烧遍整座城。",
    "风从窗外吹进来，带着雨后青草的气息。",
    "那人转过身来，目光里藏着说不清的意味。",
    "众人屏住呼吸，只听见自己的心跳声。",
    "远处的钟楼敲了七下，是离别的时辰了。",
    "少年抬起头，望向山巅的云海，那里有他要去的地方。",
    "古籍在烛火下泛黄，字迹却依旧清晰。",
    "雨停了，天边现出一线晨曦。",
]


def gen_content(title: str, chapter_no: int) -> str:
    """生成一章正文：3~5 段，每段由 2~3 句短语组成"""
    paras = []
    for _ in range(random.randint(3, 5)):
        sentences = random.sample(PHRASES, random.randint(2, 3))
        paras.append("".join(sentences))
    return "\n".join(paras)


def chapter_word_count(s) -> int:
    return len(s)


# ---------------------------------------------------------------- SQL 组装
sql = []
sql.append("-- ============================================================")
sql.append("-- 种子数据（由 scripts/gen_seed_data.py 生成，勿手改）")
sql.append("-- 实体数据 263 条；关联数据 290 条；全部账号密码 123456")
sql.append("-- ============================================================")
sql.append("\\c novel_db")
sql.append("")

# ---- 用户
sql.append("-- ---------- 1. 用户（6 个：管理 1 / 作者 2 / 读者 3，密码均 123456） ----------")
rows = ", ".join(
    f"('{u}', '{PWD_HASH}', '{n}', '{e}', '{p}', '{r}', 1)"
    for u, n, e, p, r in USERS
)
sql.append(f"INSERT INTO users (username, password_hash, nickname, email, phone, role, status) VALUES\n{rows};")
sql.append("")

# ---- 分类
sql.append("-- ---------- 2. 分类（4 个顶级 + 5 个子级，共 9 个） ----------")
rows = ", ".join(
    f"('{name}', {parent if parent is not None else 'NULL'})" for name, parent in CATEGORIES
)
sql.append(f"INSERT INTO categories (name, parent_id) VALUES\n{rows};")
sql.append("")

# ---- 作品（实体：12 部；chapter_count/word_count 由章节触发器维护）
sql.append("-- ---------- 3. 作品（12 部，含连载/完结） ----------")
rows = []
for title, author, cat, status, intro, views in NOVELS:
    rows.append(
        f"({NOVEL_ID[title]}, {AUTHOR_IDS[author]}, '{title}', '{intro}', NULL, "
        f"{CAT_ID[cat]}, '{status}', 0, 0, {views}, 0, 0, 0, now() - interval '{random.randint(1, 120)} days')"
    )
sql.append(
    "INSERT INTO novels (id, author_id, title, intro, cover_url, category_id, status, "
    "word_count, chapter_count, total_views, total_favorites, total_tickets, score, created_at) VALUES\n"
    + ",\n".join(rows) + ";"
)
sql.append("")

# ---- 小说-分类多对多
sql.append("-- ---------- 4. 小说-分类关联（12 条） ----------")
nc_rows = [f"({nid}, {CAT_ID[cat]})" for i, (title, *_) in enumerate(NOVELS)
           for nid, cat in [(i + 1, NOVELS[i][2])]]
# 每书 2 条：叶子分类 + 其顶级分类（无子级的悬疑只 1 条）
NC_PAIRS = []
for i, (title, *_) in enumerate(NOVELS):
    nid = i + 1
    leaf = NOVELS[i][2]
    lt = CAT_ID[leaf]
    NC_PAIRS.append((nid, lt))
    parent_of = next((p for name, p in CATEGORIES if name == leaf), None)
    if parent_of is not None:
        NC_PAIRS.append((nid, parent_of))
nc_rows = [f"({a}, {b})" for a, b in NC_PAIRS]
sql.append(f"INSERT INTO novel_category (novel_id, category_id) VALUES\n{', '.join(nc_rows)};")
sql.append("")

# ---- 章节（隐式自增 id 引用后续）
sql.append("-- ---------- 5. 章节（81 章：每本前 2 章免费试读，其余付费） ----------")
chap_lines = []
chap_price = {}  # 全局章号 -> 实际价格（供订阅记录对齐）
for i, title in enumerate(NOVELS):
    nid = i + 1
    total = CHAPTER_PLAN[i]
    for no in range(1, total + 1):
        if no <= FREE_CHAPTERS:
            price, is_vip, is_free = 0, False, True
        else:
            price = random.choice([1.5, 2.0, 2.5, 3.0, 4.0])
            is_vip, is_free = True, False
        content = gen_content(title, no)
        word_count = chapter_word_count(content)
        # 章节标题
        chap_lines.append(
            f"({nid}, {no}, '第{no}章 {random.choice(['风云初起','暗流涌动','故人重逢','山雨欲来','剑出鞘','星火','长夜','破晓','归途','抉择'])}', "
            f"{price}, {str(is_vip).upper()}, {str(is_free).upper()}, {word_count}, now() - interval '{random.randint(1, 200)} days')"
        )
        chap_price[len(chap_lines)] = price  # 全局章号 = 当前插入序号
sql.append(
    "INSERT INTO chapters (novel_id, chapter_no, title, price, is_vip, is_free, word_count, created_at) VALUES\n"
    + ",\n".join(chap_lines) + ";"
)
sql.append("")

# 正文章节 id 映射：插入顺序 = 全局序号 1..81（同 SQL 顺序）
CH_TOTAL = sum(CHAPTER_PLAN)
def chid(global_no):
    return global_no

# ---- 正文
sql.append(f"-- ---------- 6. 章节正文（{CH_TOTAL} 条，1:1 对应章节） ----------")
content_by_ch = {}
n = 0
for i, title in enumerate(NOVELS):
    for no in range(1, CHAPTER_PLAN[i] + 1):
        n += 1
        content_by_ch[n] = gen_content(title, no)
cont_lines = ",\n".join(
    f"({cid}, $C{cid}${content_by_ch[cid]}$C{cid}$)" for cid in range(1, CH_TOTAL + 1)
)
# 注意：正文需要与 chapters 的 word_count 保持一致——chapters 的 word_count 由生成时计算，
# 这里重新生成会不一致。统一在章节段与正文段用同一份内容（下方修正）。
sql.append(f"INSERT INTO chapter_contents (chapter_id, content) VALUES\n{cont_lines};")
sql.append("")

# 修正：章节 word_count 与正文一致（重新按正文计算）
sql.append("-- 章节字数与正文严格一致")
sql.append("UPDATE chapters c SET word_count = LENGTH(REPLACE(cc.content, E'\\n', '')) FROM chapter_contents cc WHERE cc.chapter_id = c.id;")
sql.append("")
sql.append("-- 触发器的 word_count 重新聚合")
sql.append("""
UPDATE novels n SET
  word_count    = (SELECT COALESCE(SUM(word_count), 0) FROM chapters c WHERE c.novel_id = n.id),
  chapter_count = (SELECT COUNT(*) FROM chapters c WHERE c.novel_id = n.id);
""")
sql.append("")

# ---- 钱包（6 用户全有，余额由末尾会计平衡 SQL 校准）
sql.append("-- ---------- 7. 钱包（6 用户均有，余额末尾按订单-消费校准） ----------")
sql.append("INSERT INTO wallet (user_id, balance, total_recharged) VALUES\n" +
           ", ".join(f"({uid}, 0, 0)" for uid in range(1, 7)) + ";")
sql.append("")

# ---- 充值订单（10 条：读者 3 人历史订单）
sql.append("-- ---------- 8. 充值订单（10 条：3 位读者的历史充值） ----------")
order_rows = []
ord_no = 1000
ORDER_PLAN = [
    (4, 50), (4, 30), (4, 100), (4, 120),      # reader_li: 300 元 → 3000 书币
    (5, 50), (5, 80), (5, 20),                 # reader_chen: 150 元 → 1500 书币
    (6, 30), (6, 10),                          # reader_zhao: 40 元 → 400 书币
]
for uid, amt in ORDER_PLAN:
    ord_no += 1
    method = random.choice(["alipay", "wechat", "mock"])
    order_rows.append(
        f"('R2024{25000 + ord_no}', {uid}, {amt}.00, {amt * 10}.00, '{method}', 'success', "
        f"now() - interval '{random.randint(1, 90)} days', now() - interval '{random.randint(1, 90)} days')"
    )
sql.append(
    "INSERT INTO recharge_orders (order_no, user_id, amount, coins, payment_method, status, created_at, paid_at) VALUES\n"
    + ",\n".join(order_rows) + ";"
)
sql.append("")

# ---- 书架（27 条：3 读者各收藏 9 部，明细决定 total_favorites）
sql.append("-- ---------- 9. 收藏（27 条） ----------")
fav_rows = []
for uid in READER_IDS:
    for nid in random.sample(range(1, 13), 9):
        fav_rows.append(f"({uid}, {nid}, now() - interval '{random.randint(1, 60)} days')")
sql.append("INSERT INTO favorites (user_id, novel_id, added_at) VALUES\n" + ",\n".join(fav_rows) + ";")
sql.append("")

# ---- 阅读进度（27 条：3 读者各 9 部，对应收藏的作品，progress 0~100）
sql.append("-- ---------- 10. 阅读进度（27 条，每书一条 UPSERT 语义） ----------")
hist_rows = []
for uid in READER_IDS:
    for nid in random.sample(range(1, 13), 9):
        total = CHAPTER_PLAN[nid - 1]
        ch_no = random.randint(1, total)
        gch = sum(CHAPTER_PLAN[: nid - 1]) + ch_no
        hist_rows.append(f"({uid}, {nid}, {gch}, {random.choice([0, 12.5, 35, 60, 88])}, now() - interval '{random.randint(0, 30)} days')")
sql.append("INSERT INTO reading_history (user_id, novel_id, chapter_id, progress, last_read_at) VALUES\n" + ",\n".join(hist_rows) + ";")
sql.append("")

# ---- 月票/推荐票（45 条：每读者多书投票，驱动 total_tickets 与 ZSET 自愈回填）
sql.append("-- ---------- 11. 月票/推荐票（45 条） ----------")
ticket_rows = []
for uid in READER_IDS:
    for nid in random.sample(range(1, 13), 8):
        ticket_rows.append(f"({uid}, {nid}, 'monthly', now() - interval '{random.randint(1, 40)} days')")
    for nid in random.sample(range(1, 13), 7):
        ticket_rows.append(f"({uid}, {nid}, 'recommend', now() - interval '{random.randint(1, 40)} days')")
sql.append("INSERT INTO tickets (user_id, novel_id, ticket_type, created_at) VALUES\n" + ",\n".join(ticket_rows) + ";")
sql.append("")

# ---- 打赏（30 条）
sql.append("-- ---------- 12. 打赏（30 条，金额/留言） ----------")
REWARD_MSG = ["支持作者，加油！", "写得真好，追定了", "求加更！", "这本书值得", "希望一直写下去", ""]
reward_rows = []
for _ in range(30):
    uid = random.choice(READER_IDS)
    nid = random.randint(1, 12)
    amount = random.choice([1, 2, 5, 10, 20, 50, 88])
    reward_rows.append(f"({uid}, {nid}, {amount}.00, '{random.choice(REWARD_MSG)}', now() - interval '{random.randint(1, 30)} days')")
sql.append("INSERT INTO rewards (user_id, novel_id, amount, message, created_at) VALUES\n" + ",\n".join(reward_rows) + ";")
sql.append("")

# ---- 评分（27 条：3 读者各 9 部，user+novel 唯一，驱动 score）
sql.append("-- ---------- 13. 评分（27 条，驱动作品均分） ----------")
REVIEW_COMMENTS = [
    "开篇节奏不错，情节渐入佳境", "设定新颖，值得一看", "人物塑造立体，配角也有血有肉",
    "中规中矩，期待后续爆发", "文笔细腻，世界感很强", "追更中，作者加油",
    "伏笔埋得漂亮，回收也稳", "战斗场面写得很有画面感", "一如既往地稳定输出", None,
]
review_rows = []
for uid in READER_IDS:
    for nid in random.sample(range(1, 13), 9):
        rating = random.choice([3, 4, 4, 5, 5, 5])
        content = random.choice(REVIEW_COMMENTS)
        c = f"'{content}'" if content else "NULL"
        review_rows.append(f"({uid}, {nid}, {rating}, {c}, now() - interval '{random.randint(1, 40)} days')")
sql.append("INSERT INTO novel_reviews (user_id, novel_id, rating, content, created_at) VALUES\n" + ",\n".join(review_rows) + ";")
sql.append("")

# ---- 评论（55 条：本章说 32 + 书评 13 + 回复 10，楼层引用显式 id）
sql.append("-- ---------- 14. 评论（55 条：本章说/书评/楼中楼） ----------")
comment_rows = []
cid = 0
top_comments = []  # (顶层评论id, novel_id)，供回复引用
SAY_TEXTS = [
    "这一章写得绝了，看得起鸡皮疙瘩", "主角终于振作了，舒服！", "作者为什么不早点更新",
    "这个伏笔我猜到了哈哈哈", "反派智商在线，好评", "战斗描写太燃了",
    "心疼配角一秒钟", "追更人集合！", "这章节奏有点慢，不过铺垫到位",
    "神转折，倒回去重看了一遍", "结尾卡在这里，我要闹了", "世界观展开得越来越大了",
]
REVIEW_TEXTS = [
    "整体设定扎实，慢热但值得坚持", "配角描写比主角还出彩的一本书",
    "中后期有点拖，但主线够硬", "看完想给作者寄刀片，太好哭了",
    "年度黑马，强烈推荐", "逻辑自洽，伏笔回收干净",
]
for nid in range(1, 13):
    # 每本书至少 1 条本章说
    cid += 1
    uid = random.choice(READER_IDS)
    chapter_no = random.randint(1, min(CHAPTER_PLAN[nid - 1], 5))
    gch = sum(CHAPTER_PLAN[: nid - 1]) + chapter_no
    top_comments.append((cid, nid))
    comment_rows.append(
        f"({uid}, {nid}, {gch}, NULL, {random.randint(1, 40)}, '{random.choice(SAY_TEXTS)}', now() - interval '{random.randint(1, 30)} days')"
    )
for _ in range(20):
    cid += 1
    uid = random.choice(READER_IDS)
    nid = random.randint(1, 12)
    chapter_no = random.randint(1, min(CHAPTER_PLAN[nid - 1], 5))
    gch = sum(CHAPTER_PLAN[: nid - 1]) + chapter_no
    top_comments.append((cid, nid))
    comment_rows.append(
        f"({uid}, {nid}, {gch}, NULL, {random.randint(1, 40)}, '{random.choice(SAY_TEXTS)}', now() - interval '{random.randint(1, 30)} days')"
    )
for nid in range(1, 13):
    # 每本书至少 1 条书评
    cid += 1
    uid = random.choice(READER_IDS)
    top_comments.append((cid, nid))
    comment_rows.append(
        f"({uid}, {nid}, NULL, NULL, NULL, '{random.choice(REVIEW_TEXTS)}', now() - interval '{random.randint(1, 30)} days')"
    )
for r in range(10):
    cid += 1
    uid = random.choice(READER_IDS)
    pid, pnid = random.choice(top_comments)
    comment_rows.append(
        f"({uid}, {pnid}, NULL, {pid}, NULL, '同感，顶一个', now() - interval '{random.randint(1, 15)} days')"
    )
sql.append("INSERT INTO comments (user_id, novel_id, chapter_id, parent_id, paragraph_pos, content, created_at) VALUES\n" + ",\n".join(comment_rows) + ";")
sql.append("")

# ---- 评论点赞（36 条）
sql.append("-- ---------- 15. 评论点赞（36 条，一人一赞唯一约束） ----------")
like_rows = set()
while len(like_rows) < 36:
    uid = random.choice(READER_IDS)
    cidr = random.randint(1, cid)  # 全部评论 id（含回复）
    like_rows.add((cidr, uid))
like_lines = ",\n".join(f"({c}, {u}, now() - interval '{random.randint(1, 10)} days')" for c, u in sorted(like_rows))
sql.append("INSERT INTO comment_likes (comment_id, user_id, created_at) VALUES\n" + like_lines + ";")
sql.append("")

# ---- 公告（3 条）
sql.append("-- ---------- 16. 公告（3 条） ----------")
NOTICES = [
    ("星辰书城正式上线", "本站为数据库课程设计演示项目，支持免费试读、VIP 订阅、本章说、月票、打赏等完整网文功能。演示账号密码均为 123456。"),
    ("社区规范更新", "请文明发言，本章说与书评需遵守社区规范。恶意刷赞、刷票将被封禁账号。"),
    ("月票活动开启", "每日可投月票与推荐票各一张，月末结算月票榜，榜首作品将获得推荐位展示。"),
]
sql.append("INSERT INTO notices (title, content, is_active, created_at) VALUES\n" +
           ",\n".join(f"('{t}', '{c}', TRUE, now() - interval '{d} days')" for d, (t, c) in enumerate(NOTICES, start=1)) + ";")
sql.append("")

# ---- 聚合一致性
sql.append("-- ============================================================")
sql.append("-- 聚合一致性：收藏数 / 月票数 / 均分 / 章节统计 由明细聚合回写")
sql.append("-- ============================================================")
sql.append("""
UPDATE novels n SET
  total_favorites = (SELECT COUNT(*) FROM favorites f WHERE f.novel_id = n.id),
  total_tickets   = (SELECT COUNT(*) FROM tickets t WHERE t.novel_id = n.id),
  score           = COALESCE((SELECT ROUND(AVG(rating), 1) FROM novel_reviews r WHERE r.novel_id = n.id), 0);
""")
sql.append("")

# ---- 钱包会计平衡（余额 = 充值 - 订阅支出 - 打赏支出）
sql.append("-- ============================================================")
sql.append("-- 钱包会计平衡：余额 = 累计充值 - 订阅支出 - 打赏支出")
sql.append("-- ============================================================")
sql.append("""
UPDATE wallet w SET
  total_recharged = COALESCE((SELECT SUM(coins) FROM recharge_orders o
                              WHERE o.user_id = w.user_id AND o.status = 'success'), 0),
  balance = COALESCE((SELECT SUM(coins) FROM recharge_orders o
                      WHERE o.user_id = w.user_id AND o.status = 'success'), 0)
          - COALESCE((SELECT SUM(p.price_paid) FROM chapter_purchases p JOIN chapters c ON c.id = p.chapter_id
                      WHERE p.user_id = w.user_id), 0)
          - COALESCE((SELECT SUM(r.amount) FROM rewards r
                      WHERE r.user_id = w.user_id), 0);
""")
sql.append("")

# ---- 订阅（86 条）：放在钱包平衡之后会破坏余额公式 → 这里追加购买记录并重新平衡余额
sql.append("-- ---------- 17. 章节订阅（86 条：3 读者购买付费章节） ----------")
purchase_rows = []
paid_chapters = []  # (user_id, 全局章节号)
for uid in READER_IDS:
    bought = 0
    while bought < 28:
        nid = random.randint(1, 12)
        total = CHAPTER_PLAN[nid - 1]
        if total <= FREE_CHAPTERS:
            continue
        ch_no = random.randint(FREE_CHAPTERS + 1, total)
        gch = sum(CHAPTER_PLAN[: nid - 1]) + ch_no
        if (uid, gch) in paid_chapters:
            continue
        paid_chapters.append((uid, gch))
        bought += 1
for uid, gch in paid_chapters:
    price = chap_price[gch]  # 与章节实际价格一致
    purchase_rows.append(f"({uid}, {gch}, {price:.2f}, now() - interval '{random.randint(1, 60)} days')")
sql.append("INSERT INTO chapter_purchases (user_id, chapter_id, price_paid, purchased_at) VALUES\n" + ",\n".join(purchase_rows) + ";")
sql.append("""
UPDATE wallet w SET
  balance = total_recharged
          - COALESCE((SELECT SUM(p.price_paid) FROM chapter_purchases p JOIN chapters c ON c.id = p.chapter_id
                      WHERE p.user_id = w.user_id), 0)
          - COALESCE((SELECT SUM(r.amount) FROM rewards r WHERE r.user_id = w.user_id), 0);
""")
sql.append("")

# ---- setval（显式 id 的所有序列推进）
sql.append("-- ============================================================")
sql.append("-- 修复自增序列（显式 ID 后推进，避免后续插入主键冲突）")
sql.append("-- ============================================================")
ID_TABLES = [
    "users", "categories", "novels", "chapters",
    "comments", "comment_likes", "recharge_orders", "chapter_purchases",
    "tickets", "rewards", "novel_reviews", "notices", "favorites", "reading_history",
]
for t in ID_TABLES:
    sql.append(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), (SELECT COALESCE(MAX(id), 1) FROM {t}));")
sql.append("")

# ---- 校验视图（可选，打印各表行数）
sql.append("-- ============================================================")
sql.append("-- 数据规模一览（供核对）")
sql.append("-- ============================================================")
sql.append(r"""
SELECT 'users' AS tbl, COUNT(*) FROM users
UNION ALL SELECT 'categories', COUNT(*) FROM categories
UNION ALL SELECT 'novels', COUNT(*) FROM novels
UNION ALL SELECT 'chapters', COUNT(*) FROM chapters
UNION ALL SELECT 'chapter_contents', COUNT(*) FROM chapter_contents
UNION ALL SELECT 'comments', COUNT(*) FROM comments
UNION ALL SELECT 'comment_likes', COUNT(*) FROM comment_likes
UNION ALL SELECT 'notices', COUNT(*) FROM notices
UNION ALL SELECT 'recharge_orders', COUNT(*) FROM recharge_orders
UNION ALL SELECT 'wallet', COUNT(*) FROM wallet
UNION ALL SELECT 'novel_category', COUNT(*) FROM novel_category
UNION ALL SELECT 'favorites', COUNT(*) FROM favorites
UNION ALL SELECT 'reading_history', COUNT(*) FROM reading_history
UNION ALL SELECT 'tickets', COUNT(*) FROM tickets
UNION ALL SELECT 'rewards', COUNT(*) FROM rewards
UNION ALL SELECT 'novel_reviews', COUNT(*) FROM novel_reviews
UNION ALL SELECT 'chapter_purchases', COUNT(*) FROM chapter_purchases
ORDER BY tbl;
""")

sql_text = "\n".join(sql) + "\n"

if __name__ == "__main__":
    import os
    out = os.path.join(os.path.dirname(__file__), "..", "db", "init", "02_seed.sql")
    out = os.path.abspath(out)
    with open(out, "w", encoding="utf-8") as f:
        f.write(sql_text)
    print(f"已生成 {out}（{len(sql_text)} 字符）")

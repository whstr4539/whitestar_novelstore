-- ============================================================
-- 种子数据：测试用户 / 分类 / 示例小说 / 章节 / 钱包 / 订阅记录
-- 所有演示账号密码均为：123456
-- ============================================================
\c novel_db

-- ---------- 用户（3 个测试账号） ----------
-- admin / author_zhang / reader_li 密码均为 123456
INSERT INTO users (username, password_hash, nickname, email, phone, role, status) VALUES
('admin',       '$2b$12$BAQ8Fh95CedTKWw7GOU6IOqXL8sEPxisCULQaZEfzgMtKM3mkZgeq', '管理员', 'admin@novel.com',  '13800000001', 'admin',  1),
('author_zhang', '$2b$12$BAQ8Fh95CedTKWw7GOU6IOqXL8sEPxisCULQaZEfzgMtKM3mkZgeq', '张作家', 'author@novel.com', '13800000002', 'author', 1),
('reader_li',   '$2b$12$BAQ8Fh95CedTKWw7GOU6IOqXL8sEPxisCULQaZEfzgMtKM3mkZgeq', '李读者', 'reader@novel.com',  '13800000003', 'reader', 1);

-- ---------- 分类 ----------
INSERT INTO categories (name, parent_id) VALUES
('玄幻', NULL), ('都市', NULL), ('科幻', NULL), ('历史', NULL), ('悬疑', NULL),
('东方玄幻', 1), ('都市异能', 2), ('星际科幻', 3);

-- ---------- 示例小说（作者 author_zhang 即 id=2） ----------
INSERT INTO novels (id, author_id, title, intro, category_id, status, is_vip) VALUES
(1, 2, '星辰问道', '少年自边陲小城走出，一路问道星辰大海……', 6, 'serializing', TRUE),
(2, 2, '都市夜行人', '白天是程序员，夜晚是都市守护者……', 7, 'serializing', FALSE),
(3, 2, '星际拓荒者', '人类第一次跃迁失败，被困在荒芜星系……', 8, 'finished',   TRUE);

-- ---------- 小说-分类 多对多 ----------
INSERT INTO novel_category (novel_id, category_id) VALUES
(1, 1), (1, 6),     -- 星辰问道：玄幻 + 东方玄幻
(2, 2), (2, 7),     -- 都市夜行人：都市 + 都市异能
(3, 3), (3, 8);     -- 星际拓荒者：科幻 + 星际科幻

-- ---------- 章节（每本书 3 章） ----------
-- 星辰问道：第1章免费试读，第2、3章 VIP 付费（2 书币/章）
INSERT INTO chapters (novel_id, chapter_no, title, price, is_vip, is_free, word_count) VALUES
(1, 1, '第一章 边陲少年', 0,    FALSE, TRUE,  3200),
(1, 2, '第二章 初入宗门', 2.00, TRUE,  FALSE, 4100),
(1, 3, '第三章 星辰之力', 2.00, TRUE,  FALSE, 3900),
(2, 1, '第一章 加班程序员', 0,   FALSE, TRUE,  2800),
(2, 2, '第二章 夜行衣', 0,     FALSE, FALSE, 3500),
(2, 3, '第三章 天台对决', 0,   FALSE, FALSE, 3700),
(3, 1, '第一章 跃迁失败', 0,   FALSE, TRUE,  4500),
(3, 2, '第二章 荒芜之地', 1.50, TRUE,  FALSE, 4800),
(3, 3, '第三章 希望信号', 1.50, TRUE,  FALSE, 5100);

-- ---------- 章节正文（用 repeat 生成占位内容，总字数约 3000 字） ----------
INSERT INTO chapter_contents (chapter_id, content)
SELECT c.id, repeat('这是《' || n.title || '》第' || c.chapter_no || '章的正文内容。', 500)
  FROM chapters c JOIN novels n ON n.id = c.novel_id;

-- ---------- 钱包：李读者初始余额 100 书币 ----------
INSERT INTO wallet (user_id, balance, total_recharged) VALUES
(3, 100.00, 100.00);

-- ---------- 充值订单（一条已成功的演示订单） ----------
INSERT INTO recharge_orders (order_no, user_id, amount, coins, payment_method, status, paid_at) VALUES
('R20240101000001', 3, 10.00, 100.00, 'alipay', 'success', now() - interval '1 day');

-- ---------- 订阅：李读者已购买《星辰问道》第2章 ----------
INSERT INTO chapter_purchases (user_id, chapter_id, price_paid) VALUES
(3, 2, 2.00);

-- ---------- 书架：李读者收藏了 2 本书 ----------
INSERT INTO favorites (user_id, novel_id) VALUES
(3, 1), (3, 2);

-- ---------- 阅读进度：李读者正看到《星辰问道》第2章 45% ----------
INSERT INTO reading_history (user_id, novel_id, chapter_id, progress) VALUES
(3, 1, 2, 45.00);

-- ---------- 评论：本章说 + 书评 + 楼中楼 ----------
INSERT INTO comments (user_id, novel_id, chapter_id, parent_id, paragraph_pos, content) VALUES
(3, 1, 2, NULL, 12, '这一章转折太精彩了！'),     -- 本章说
(3, 1, NULL, NULL, NULL, '近年少有的良心玄幻，推荐！'),  -- 书评
(2, 1, 2, 1, NULL, '谢谢支持，后续更精彩～');     -- 作者回复（楼中楼）

-- ---------- 书评评分（驱动 novels.score） ----------
INSERT INTO novel_reviews (user_id, novel_id, rating, content) VALUES
(3, 1, 5, '五星好评，追更中！');

-- 同步 novels.score / total_favorites（模拟聚合结果）
UPDATE novels SET score = 5.0 WHERE id = 1;

-- ---------- 公告 ----------
INSERT INTO notices (title, content) VALUES
('欢迎来到星辰书城', '本站为数据库课程设计演示项目，支持阅读、订阅、评论、打赏等完整网文功能。');

-- ---------- 修复自增序列（种子数据用了显式 ID，需推进序列避免主键冲突） ----------
SELECT setval(pg_get_serial_sequence('novels', 'id'), (SELECT COALESCE(MAX(id), 1) FROM novels));

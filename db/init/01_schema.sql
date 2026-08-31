-- ============================================================
-- 数据库结构
-- 12 张核心表 + 4 张可选表
-- 数据库：PostgreSQL 16
-- ============================================================

-- 建库（若不存在）
SELECT 'CREATE DATABASE novel_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'novel_db')\gexec
\c novel_db

-- 扩展：用于生成 UUID
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 1. users 用户表（读者/作者/管理员 同一张表，role 区分）
-- ============================================================
DROP TABLE IF EXISTS users CASCADE;
CREATE TABLE users (
    id            BIGSERIAL PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,          -- 登录名
    password_hash VARCHAR(255) NOT NULL,                 -- bcrypt 哈希
    nickname      VARCHAR(50)  NOT NULL,                 -- 显示昵称
    avatar        VARCHAR(255),                          -- 头像 URL
    email         VARCHAR(100) UNIQUE,
    phone         VARCHAR(20)  UNIQUE,
    role          VARCHAR(10)  NOT NULL DEFAULT 'reader' -- reader / author / admin
                 CHECK (role IN ('reader', 'author', 'admin')),
    status        SMALLINT     NOT NULL DEFAULT 1,       -- 1正常 0封禁
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
COMMENT ON TABLE users IS '用户表：读者/作者/管理员统一存储';
COMMENT ON COLUMN users.role IS '角色：reader读者 author作者 admin管理员';

-- ============================================================
-- 2. categories 分类表（支持二级分类 parent_id）
-- ============================================================
DROP TABLE IF EXISTS categories CASCADE;
CREATE TABLE categories (
    id        BIGSERIAL PRIMARY KEY,
    name      VARCHAR(30) NOT NULL UNIQUE,               -- 玄幻/都市/科幻...
    parent_id BIGINT REFERENCES categories(id)           -- NULL 为一级分类
);
COMMENT ON TABLE categories IS '小说分类表（可二级）';

-- ============================================================
-- 3. novels 小说表（作品）
-- ============================================================
DROP TABLE IF EXISTS novels CASCADE;
CREATE TABLE novels (
    id             BIGSERIAL PRIMARY KEY,
    author_id      BIGINT      NOT NULL REFERENCES users(id),  -- 作者
    title          VARCHAR(100) NOT NULL,
    intro          TEXT,                                       -- 简介
    cover_url      VARCHAR(255),
    category_id    BIGINT      REFERENCES categories(id),      -- 主分类（冗余，便于首页列表）
    status         VARCHAR(12) NOT NULL DEFAULT 'serializing'
                   CHECK (status IN ('serializing', 'finished', 'banned')), -- 连载中/已完结/已下架
    word_count     BIGINT      NOT NULL DEFAULT 0,             -- 总字数（可触发器维护）
    chapter_count  INT         NOT NULL DEFAULT 0,             -- 总章数
    total_views    BIGINT      NOT NULL DEFAULT 0,             -- 总点击
    total_favorites BIGINT     NOT NULL DEFAULT 0,             -- 总收藏
    total_tickets  BIGINT      NOT NULL DEFAULT 0,             -- 总月票
    score          NUMERIC(3,1) NOT NULL DEFAULT 0,            -- 均分（由 novel_reviews 聚合）
    is_vip         BOOLEAN     NOT NULL DEFAULT FALSE,         -- 是否 VIP 作品
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_novels_category ON novels(category_id);
CREATE INDEX idx_novels_status   ON novels(status);
CREATE INDEX idx_novels_views    ON novels(total_views DESC);
COMMENT ON TABLE novels IS '小说作品表';

-- ============================================================
-- 4. chapters 章节表（只存元信息，正文在 chapter_contents）
-- ============================================================
DROP TABLE IF EXISTS chapters CASCADE;
CREATE TABLE chapters (
    id          BIGSERIAL PRIMARY KEY,
    novel_id    BIGINT       NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    chapter_no  INT          NOT NULL,                    -- 章节序号（第几章）
    title       VARCHAR(200) NOT NULL,
    price       NUMERIC(10,2) NOT NULL DEFAULT 0,         -- 书币价格，0=免费
    is_vip      BOOLEAN      NOT NULL DEFAULT FALSE,      -- 是否付费章
    is_free     BOOLEAN      NOT NULL DEFAULT FALSE,      -- 是否试读章
    status      SMALLINT     NOT NULL DEFAULT 1,          -- 1正常 0删除
    word_count  INT          NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (novel_id, chapter_no)                         -- 同一本书章节号唯一
);
CREATE INDEX idx_chapters_novel ON chapters(novel_id, chapter_no);
COMMENT ON TABLE chapters IS '章节表（元信息与正文分离）';

-- ============================================================
-- 5. chapter_contents 章节内容表（与 chapters 一对一，大字段拆分）
-- ============================================================
DROP TABLE IF EXISTS chapter_contents CASCADE;
CREATE TABLE chapter_contents (
    chapter_id BIGINT PRIMARY KEY REFERENCES chapters(id) ON DELETE CASCADE,
    content    TEXT NOT NULL,                             -- 几万字正文大字段
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE chapter_contents IS '章节正文表（1:1 拆分，避免目录页加载大字段）';

-- ============================================================
-- 6. novel_category 小说-分类关联表（多对多）
-- ============================================================
DROP TABLE IF EXISTS novel_category CASCADE;
CREATE TABLE novel_category (
    novel_id    BIGINT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    category_id BIGINT NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (novel_id, category_id)
);
COMMENT ON TABLE novel_category IS '小说与分类多对多中间表';

-- ============================================================
-- 7. favorites 书架表（用户收藏）
-- ============================================================
DROP TABLE IF EXISTS favorites CASCADE;
CREATE TABLE favorites (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    novel_id   BIGINT      NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    added_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, novel_id)                            -- 同一本书不能重复收藏
);
CREATE INDEX idx_favorites_user ON favorites(user_id);
COMMENT ON TABLE favorites IS '书架/收藏表';

-- ============================================================
-- 8. reading_history 阅读记录表（每本书每用户一条最新进度）
-- ============================================================
DROP TABLE IF EXISTS reading_history CASCADE;
CREATE TABLE reading_history (
    id           BIGSERIAL PRIMARY KEY,
    user_id      BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    novel_id     BIGINT      NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    chapter_id   BIGINT      REFERENCES chapters(id),     -- 读到第几章
    progress     NUMERIC(5,2) NOT NULL DEFAULT 0,         -- 本章内阅读进度 0~100
    last_read_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, novel_id)                            -- 每本书只保留一条进度
);
CREATE INDEX idx_reading_history_user ON reading_history(user_id, last_read_at DESC);
COMMENT ON TABLE reading_history IS '阅读进度表';

-- ============================================================
-- 9. comments 评论表（本章说 + 书评 + 楼中楼回复，一表多用）
-- ============================================================
DROP TABLE IF EXISTS comments CASCADE;
CREATE TABLE comments (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    novel_id      BIGINT      NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    chapter_id    BIGINT      REFERENCES chapters(id) ON DELETE CASCADE, -- 空=书评，非空=本章说
    parent_id     BIGINT      REFERENCES comments(id) ON DELETE CASCADE, -- 空=顶层评论
    paragraph_pos INT,                                                  -- 段评定位（起点特色）
    content       VARCHAR(500) NOT NULL,
    likes         INT         NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_comments_novel  ON comments(novel_id, created_at DESC);
CREATE INDEX idx_comments_chapter ON comments(chapter_id, created_at DESC);
COMMENT ON TABLE comments IS '评论表：本章说/书评/回复';

-- ============================================================
-- 9b. comment_likes 评论点赞表（一人一赞，唯一约束防重复；可取消）
-- ============================================================
DROP TABLE IF EXISTS comment_likes CASCADE;
CREATE TABLE comment_likes (
    id         BIGSERIAL PRIMARY KEY,
    comment_id BIGINT      NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    user_id    BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_comment_likes UNIQUE (comment_id, user_id)  -- 一人一赞
);
CREATE INDEX idx_comment_likes_user ON comment_likes(user_id);
COMMENT ON TABLE comment_likes IS '评论点赞记录：唯一约束保证每人每评论仅一赞';

-- ============================================================
-- 10. wallet 书币账户表（与 users 1:1，避免读写余额锁用户主表）
-- ============================================================
DROP TABLE IF EXISTS wallet CASCADE;
CREATE TABLE wallet (
    user_id         BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    balance         NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (balance >= 0),  -- 书币余额
    total_recharged NUMERIC(12,2) NOT NULL DEFAULT 0,                       -- 累计充值
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT now()
);
COMMENT ON TABLE wallet IS '书币钱包表（1:1 users）';

-- ============================================================
-- 11. recharge_orders 充值订单表
-- ============================================================
DROP TABLE IF EXISTS recharge_orders CASCADE;
CREATE TABLE recharge_orders (
    id             BIGSERIAL PRIMARY KEY,
    order_no       VARCHAR(32)  NOT NULL UNIQUE,          -- 业务订单号
    user_id        BIGINT       NOT NULL REFERENCES users(id),
    amount         NUMERIC(10,2) NOT NULL,                -- 人民币
    coins          NUMERIC(10,2) NOT NULL,                -- 到账书币
    payment_method VARCHAR(20)  NOT NULL DEFAULT 'alipay',-- alipay/wechat/mock
    status         VARCHAR(10)  NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending', 'success', 'failed', 'cancelled')),
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    paid_at        TIMESTAMPTZ
);
CREATE INDEX idx_recharge_orders_user ON recharge_orders(user_id, created_at DESC);
COMMENT ON TABLE recharge_orders IS '充值订单表';

-- ============================================================
-- 12. chapter_purchases 章节订阅表（核心业务表：VIP 章是否可读）
-- ============================================================
DROP TABLE IF EXISTS chapter_purchases CASCADE;
CREATE TABLE chapter_purchases (
    id           BIGSERIAL PRIMARY KEY,
    user_id      BIGINT       NOT NULL REFERENCES users(id),
    chapter_id   BIGINT       NOT NULL REFERENCES chapters(id),
    price_paid   NUMERIC(10,2) NOT NULL,                  -- 成交价快照
    purchased_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (user_id, chapter_id)                          -- 防重复扣费
);
CREATE INDEX idx_purchases_user ON chapter_purchases(user_id, purchased_at DESC);
COMMENT ON TABLE chapter_purchases IS '章节订阅记录：VIP 章节购买凭证';

-- ============================================================
-- 可选表（加分项）
-- ============================================================

-- 13. tickets 月票/推荐票表（起点特色）
DROP TABLE IF EXISTS tickets CASCADE;
CREATE TABLE tickets (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT      NOT NULL REFERENCES users(id),
    novel_id    BIGINT      NOT NULL REFERENCES novels(id),
    ticket_type VARCHAR(10) NOT NULL DEFAULT 'monthly'    -- monthly月票 / recommend推荐票
                CHECK (ticket_type IN ('monthly', 'recommend')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_tickets_user_novel_type UNIQUE (user_id, novel_id, ticket_type) -- 每人每书每类一票
);
CREATE INDEX idx_tickets_novel ON tickets(novel_id, created_at DESC);
COMMENT ON TABLE tickets IS '月票/推荐票表';

-- 14. rewards 打赏表
DROP TABLE IF EXISTS rewards CASCADE;
CREATE TABLE rewards (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT       NOT NULL REFERENCES users(id),
    novel_id   BIGINT       NOT NULL REFERENCES novels(id),
    amount     NUMERIC(10,2) NOT NULL,                    -- 书币
    message    VARCHAR(200),
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);
COMMENT ON TABLE rewards IS '打赏表';

-- 15. novel_reviews 书评评分表（驱动 novels.score 聚合）
DROP TABLE IF EXISTS novel_reviews CASCADE;
CREATE TABLE novel_reviews (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT      NOT NULL REFERENCES users(id),
    novel_id   BIGINT      NOT NULL REFERENCES novels(id),
    rating     SMALLINT    NOT NULL CHECK (rating BETWEEN 1 AND 5),
    content    VARCHAR(1000),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, novel_id)                            -- 一人一书一评
);
COMMENT ON TABLE novel_reviews IS '书评评分表';

-- 16. notices 公告/推荐位表
DROP TABLE IF EXISTS notices CASCADE;
CREATE TABLE notices (
    id         BIGSERIAL PRIMARY KEY,
    title      VARCHAR(100) NOT NULL,
    content    TEXT         NOT NULL,
    is_active  BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);
COMMENT ON TABLE notices IS '公告表';

-- ============================================================
-- 触发器示例：新章节发布时自动更新 novels 的章数/字数
-- ============================================================
CREATE OR REPLACE FUNCTION fn_update_novel_stats() RETURNS TRIGGER AS $$
BEGIN
    UPDATE novels
       SET chapter_count = (SELECT COUNT(*) FROM chapters WHERE novel_id = NEW.novel_id),
           word_count    = (SELECT COALESCE(SUM(word_count),0) FROM chapters WHERE novel_id = NEW.novel_id),
           updated_at    = now()
     WHERE id = NEW.novel_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_chapter_insert ON chapters;
CREATE TRIGGER trg_chapter_insert
    AFTER INSERT ON chapters
    FOR EACH ROW EXECUTE FUNCTION fn_update_novel_stats();

-- ============================================================
-- 视图示例：月度订阅收入统计（课设答辩可用）
-- ============================================================
CREATE OR REPLACE VIEW v_monthly_revenue AS
SELECT date_trunc('month', purchased_at)::date AS month,
       COUNT(*)                               AS purchase_count,
       SUM(price_paid)                        AS revenue
  FROM chapter_purchases
 GROUP BY 1
 ORDER BY 1 DESC;

-- ============================================================
-- 汇总：共 16 张表
-- 核心：users, categories, novels, chapters, chapter_contents,
--       novel_category, favorites, reading_history, comments,
--       wallet, recharge_orders, chapter_purchases
-- 可选：tickets, rewards, novel_reviews, notices
-- ============================================================

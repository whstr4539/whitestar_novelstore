/* 账单：充值 / 订阅 / 打赏统一流水（入账绿色 +，出账默认 -）
   设计依据 novel-reading-ui skill：单卡片、hairline 分区、tabular-nums、无 emoji */
import { useEffect, useState } from 'react'
import { apiBills } from '../api'

const TYPE_META = {
  recharge: { label: '充值', cls: 'bill-type-in' },
  purchase: { label: '订阅', cls: 'bill-type-out' },
  reward: { label: '打赏', cls: 'bill-type-out' },
}
const FILTERS = [['all', '全部'], ['recharge', '充值'], ['purchase', '订阅'], ['reward', '打赏']]

export default function Bills() {
  const [bills, setBills] = useState(null)
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiBills().then(setBills).catch(() => setBills({ items: [], total_in: 0, total_out: 0 }))
      .finally(() => setLoading(false))
  }, [])

  const fmtDate = (s) => new Date(s).toLocaleString('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
  const items = (bills?.items || []).filter((b) => filter === 'all' || b.type === filter)

  return (
    <div className="container page-enter bills-page">
      <div className="page-head">
        <h1 className="page-title">账单</h1>
      </div>

      {bills && (
        <div className="bill-summary">
          <div className="bill-summary-item">
            <b className="bill-in">+{bills.total_in}</b>
            <span>累计收入（书币）</span>
          </div>
          <div className="bill-summary-item">
            <b>-{bills.total_out}</b>
            <span>累计支出（书币）</span>
          </div>
        </div>
      )}

      <div className="bill-tabs">
        {FILTERS.map(([key, label]) => (
          <button key={key} className={`tab ${filter === key ? 'tab-active' : ''}`}
            onClick={() => setFilter(key)}>
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="bill-loading">
          {[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 64, marginBottom: 12 }} />)}
        </div>
      ) : items.length === 0 ? (
        <div className="empty">暂无记录{bills?.items?.length ? '，试试其他类型' : ''}</div>
      ) : (
        <section className="bill-list">
          {items.map((b, i) => {
            const meta = TYPE_META[b.type]
            return (
              <div key={i} className="bill-item">
                <span className={`bill-type ${meta.cls}`}>{meta.label}</span>
                <div className="bill-body">
                  <p className="bill-title">{b.title}</p>
                  <p className="bill-detail">
                    {b.detail && <span>{b.detail} · </span>}
                    {fmtDate(b.created_at)}
                  </p>
                </div>
                <span className={`bill-amount ${b.direction === 'in' ? 'bill-in' : ''}`}>
                  {b.direction === 'in' ? '+' : '-'}{b.amount}
                </span>
              </div>
            )
          })}
        </section>
      )}

      <style>{`
        .bills-page { max-width: 720px; }
        .bill-summary {
          display: flex;
          gap: var(--space-5);
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius);
          padding: var(--space-4) var(--space-5);
          margin-bottom: var(--space-4);
        }
        .bill-summary-item { display: flex; flex-direction: column; gap: 2px; }
        .bill-summary-item b { font-size: var(--fs-18); font-variant-numeric: tabular-nums; }
        .bill-summary-item span { font-size: var(--fs-12); color: var(--ink-500); }
        .bill-in { color: var(--success); }
        .bill-tabs { display: flex; gap: var(--space-4); margin-bottom: var(--space-4); }
        .bill-list {
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius);
        }
        .bill-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3) var(--space-4);
          border-bottom: 1px solid var(--hairline);
        }
        .bill-item:last-child { border-bottom: none; }
        .bill-type {
          flex-shrink: 0;
          font-size: var(--fs-12);
          padding: 2px 8px;
          border-radius: 3px;
          line-height: 1.7;
        }
        .bill-type-in { background: var(--accent-weak); color: var(--accent-text); }
        .bill-type-out { background: #f0f0f2; color: var(--ink-500); }
        .bill-body { flex: 1; min-width: 0; }
        .bill-title {
          font-size: var(--fs-14);
          font-weight: 500;
          color: var(--ink-900);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .bill-detail { font-size: var(--fs-12); color: var(--ink-500); }
        .bill-amount {
          flex-shrink: 0;
          font-size: var(--fs-15);
          font-weight: 600;
          font-variant-numeric: tabular-nums;
          color: var(--ink-700);
        }
        .bill-loading { padding: var(--space-4) 0; }
      `}</style>
    </div>
  )
}

/* 全局确认弹窗：替代浏览器原生 window.confirm，统一站点视觉风格
   用法：
     const confirm = useConfirm()
     const ok = await confirm({ title: '删除评论', message: '确定删除？', confirmText: '删除', danger: true })
     if (!ok) return */
import { createContext, useContext, useEffect, useState } from 'react'

const ConfirmContext = createContext(() => Promise.resolve(false))

export function useConfirm() {
  return useContext(ConfirmContext)
}

export default function ConfirmProvider({ children }) {
  // state = { title, message, confirmText, danger, resolve }
  const [state, setState] = useState(null)

  const confirm = (opts) =>
    new Promise((resolve) => setState({ confirmText: '确定', ...opts, resolve }))

  const close = (ok) => {
    setState((s) => {
      s?.resolve(ok)
      return null
    })
  }

  // ESC 取消；Enter 确认由 autoFocus 按钮原生响应
  useEffect(() => {
    if (!state) return undefined
    const onKey = (e) => {
      if (e.key === 'Escape') close(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [state])

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {state && (
        <div className="confirm-mask" onClick={() => close(false)}>
          <div
            className="confirm-box"
            role="alertdialog"
            aria-modal="true"
            aria-label={state.title || '确认操作'}
            onClick={(e) => e.stopPropagation()}
          >
            {state.title && <h3 className="confirm-title">{state.title}</h3>}
            <p className="confirm-message">{state.message}</p>
            <div className="confirm-actions">
              <button className="btn btn-ghost" onClick={() => close(false)}>
                取消
              </button>
              <button
                className={`btn confirm-ok ${state.danger ? 'confirm-ok-danger' : 'btn-primary'}`}
                onClick={() => close(true)}
                autoFocus
              >
                {state.confirmText}
              </button>
            </div>
          </div>
        </div>
      )}
      <style>{`
        .confirm-mask {
          position: fixed;
          inset: 0;
          z-index: 100;
          background: rgba(20, 20, 24, 0.45);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: var(--space-5);
          animation: confirm-fade 0.15s ease;
        }
        .confirm-box {
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          box-shadow: 0 8px 30px rgba(38, 38, 42, 0.18);
          width: 100%;
          max-width: 380px;
          padding: var(--space-5);
          /* 注意不能复用 --ease（它是 "0.18s ease" 的 transition 简写值，
             放进 animation 简写会被解析为 delay，导致弹窗先渲染再闪一下重播动画） */
          animation: confirm-pop 0.18s cubic-bezier(0.22, 1, 0.36, 1);
          animation-fill-mode: backwards;
        }
        .confirm-title {
          font-size: var(--fs-16);
          font-weight: 600;
          margin-bottom: var(--space-2);
        }
        .confirm-message {
          font-size: var(--fs-14);
          color: var(--ink-700);
          line-height: 1.7;
          white-space: pre-line;
          margin-bottom: var(--space-5);
        }
        .confirm-actions {
          display: flex;
          justify-content: flex-end;
          gap: var(--space-2);
        }
        .confirm-ok-danger {
          background: var(--danger);
          border-color: var(--danger);
          color: #fff;
        }
        .confirm-ok-danger:hover {
          background: color-mix(in srgb, var(--danger) 88%, black);
        }
        @keyframes confirm-fade {
          from { opacity: 0; }
        }
        @keyframes confirm-pop {
          from { opacity: 0; transform: scale(0.96) translateY(6px); }
        }
        @media (max-width: 768px) {
          .confirm-box { max-width: none; }
        }
      `}</style>
    </ConfirmContext.Provider>
  )
}

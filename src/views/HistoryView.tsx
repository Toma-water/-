import { useRef, useState } from 'react';
import type { SharedProps } from '../App';
import type { DayLog } from '../types';
import { pastDates, formatDateShort } from '../utils';
import { exportJSON, importJSON } from '../storage';

function DayCard({ date, log }: { date: string; log: DayLog | undefined }) {
  const [open, setOpen] = useState(false);
  const plan   = log?.morningPlan;
  const review = log?.eveningReview;
  const tasks  = plan?.tasks ?? [];
  const doneCount = tasks.filter(t => t.status === 'done' || t.status === 'partial').length;

  const hasPlan   = !!plan;
  const hasReview = !!review;

  return (
    <div className="history-day">
      <div className="history-day-header" onClick={() => (hasPlan || hasReview) && setOpen(v => !v)}>
        <div className="history-date">{formatDateShort(date)}</div>
        {plan?.theme && <div className="history-theme">{plan.theme}</div>}
        <div className="history-indicators">
          <div className="history-dot" style={{
            background: hasPlan ? 'var(--c-primary)' : 'var(--c-border)',
          }} title="朝プラン" />
          <div className="history-dot" style={{
            background: hasReview ? 'var(--c-success)' : 'var(--c-border)',
          }} title="夜レビュー" />
        </div>
        {(hasPlan || hasReview) && (
          <span style={{ fontSize: '.7rem', color: 'var(--c-text3)', marginLeft: 4 }}>
            {open ? '▲' : '▼'}
          </span>
        )}
      </div>

      {open && (hasPlan || hasReview) && (
        <div className="history-detail">
          {plan && (
            <>
              <div style={{ fontSize: '.78rem', fontWeight: 600, color: 'var(--c-text3)', marginTop: 8 }}>
                朝のプラン
              </div>
              {plan.theme && (
                <div style={{ fontSize: '.88rem', marginTop: 4 }}>テーマ: {plan.theme}</div>
              )}
              {plan.intention && (
                <div style={{ fontSize: '.82rem', color: 'var(--c-text2)', marginTop: 2 }}>
                  意図: {plan.intention}
                </div>
              )}
              {tasks.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: '.78rem', color: 'var(--c-text3)', marginBottom: 4 }}>
                    タスク ({doneCount}/{tasks.length} 完了)
                  </div>
                  {tasks.map(t => (
                    <div key={t.id} style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 4 }}>
                      <span style={{ fontSize: '.8rem' }}>
                        {t.status === 'done' ? '✅' :
                         t.status === 'partial' ? '🔶' :
                         t.status === 'skipped' ? '⏭' :
                         t.status === 'cancelled' ? '❌' : '⬜'}
                      </span>
                      <span style={{ fontSize: '.85rem', color: t.status === 'done' ? 'var(--c-text3)' : 'var(--c-text)' }}>
                        {t.action}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
          {review && (
            <>
              <div style={{ fontSize: '.78rem', fontWeight: 600, color: 'var(--c-text3)', marginTop: 12 }}>
                夜のレビュー
              </div>
              {review.whatWentWell && (
                <div style={{ marginTop: 4 }}>
                  <span style={{ fontSize: '.75rem', color: 'var(--c-text3)' }}>うまくいったこと: </span>
                  <span style={{ fontSize: '.85rem' }}>{review.whatWentWell}</span>
                </div>
              )}
              {review.insight && (
                <div style={{ marginTop: 4 }}>
                  <span style={{ fontSize: '.75rem', color: 'var(--c-text3)' }}>気づき: </span>
                  <span style={{ fontSize: '.85rem' }}>{review.insight}</span>
                </div>
              )}
              {review.tomorrowFocus && (
                <div style={{ marginTop: 4 }}>
                  <span style={{ fontSize: '.75rem', color: 'var(--c-text3)' }}>明日: </span>
                  <span style={{ fontSize: '.85rem' }}>{review.tomorrowFocus}</span>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default function HistoryView({ data, updateData }: SharedProps) {
  const [importMsg, setImportMsg] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const dates = pastDates(60);

  async function handleImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const imported = await importJSON(file);
      if (!confirm(`インポートするとデータが上書きされます。続けますか？`)) {
        e.target.value = '';
        return;
      }
      updateData(() => imported);
      setImportMsg('インポート成功！');
    } catch (err: unknown) {
      setImportMsg(`エラー: ${err instanceof Error ? err.message : String(err)}`);
    }
    e.target.value = '';
    setTimeout(() => setImportMsg(''), 3000);
  }

  const recordedDates = dates.filter(d => data.days[d]);
  const totalTasks = Object.values(data.days).flatMap(d => d.morningPlan?.tasks ?? []).length;
  const doneTasks  = Object.values(data.days).flatMap(d => d.morningPlan?.tasks ?? []).filter(t => t.status === 'done').length;

  return (
    <div>
      <div className="section-title" style={{ marginBottom: 14 }}>📅 履歴</div>

      {/* Stats */}
      <div className="card" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 0, padding: 0 }}>
        {[
          { label: '記録した日', value: recordedDates.length },
          { label: '総タスク', value: totalTasks },
          { label: '完了タスク', value: doneTasks },
        ].map((s, i) => (
          <div key={i} style={{
            padding: '14px 12px',
            textAlign: 'center',
            borderRight: i < 2 ? '1px solid var(--c-border)' : undefined,
          }}>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--c-primary)' }}>{s.value}</div>
            <div style={{ fontSize: '.72rem', color: 'var(--c-text3)', marginTop: 2 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Export / Import */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, marginTop: 4 }}>
        <button className="btn btn-outline btn-sm" style={{ flex: 1 }} onClick={() => exportJSON(data)}>
          📤 JSONエクスポート
        </button>
        <button className="btn btn-ghost btn-sm" style={{ flex: 1 }} onClick={() => fileRef.current?.click()}>
          📥 インポート
        </button>
        <input ref={fileRef} type="file" accept=".json" style={{ display: 'none' }} onChange={handleImport} />
      </div>
      {importMsg && (
        <div className={`alert ${importMsg.startsWith('エラー') ? '' : 'alert-success'}`}
          style={importMsg.startsWith('エラー') ? { background: 'var(--c-danger-bg)', color: 'var(--c-danger)' } : {}}>
          {importMsg}
        </div>
      )}

      {/* Day list */}
      {dates.map(date => (
        <DayCard key={date} date={date} log={data.days[date]} />
      ))}
    </div>
  );
}

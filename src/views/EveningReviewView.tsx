import { useState } from 'react';
import type { SharedProps } from '../App';
import type { Task, TaskStatus } from '../types';
import { genId, now, formatDate } from '../utils';

const STATUS_OPTIONS: { value: TaskStatus; label: string }[] = [
  { value: 'done',      label: '✅ 完了' },
  { value: 'partial',   label: '🔶 部分完了' },
  { value: 'skipped',   label: '⏭ スキップ' },
  { value: 'cancelled', label: '❌ キャンセル' },
  { value: 'doing',     label: '🔄 継続中' },
];

function TaskReview({
  task, onChange,
}: {
  task: Task;
  onChange: (updated: Partial<Task>) => void;
}) {
  const showProgress = task.status === 'done' || task.status === 'partial';
  const showBlocked  = task.status === 'partial' || task.status === 'skipped';

  return (
    <div className="task-item" style={{ marginBottom: 12 }}>
      <div style={{ padding: 12 }}>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>{task.action}</div>
        <div style={{ fontSize: '.8rem', color: 'var(--c-text2)', marginBottom: 4 }}>
          完了条件: {task.completionCondition}
        </div>
        <div className="task-status-bar">
          {STATUS_OPTIONS.map(s => (
            <button
              key={s.value}
              className={`status-btn ${task.status === s.value ? `active-${s.value}` : ''}`}
              onClick={() => onChange({ status: s.value })}
            >
              {s.label}
            </button>
          ))}
        </div>
        {showProgress && (
          <div style={{ marginTop: 10 }}>
            <label className="field-label">実際の進捗</label>
            <textarea
              className="field-textarea"
              style={{ minHeight: 60 }}
              value={task.actualProgress ?? ''}
              onChange={e => onChange({ actualProgress: e.target.value })}
              placeholder="何をどこまでやったか"
            />
          </div>
        )}
        {showBlocked && (
          <div style={{ marginTop: 10 }}>
            <label className="field-label">できなかった理由</label>
            <textarea
              className="field-textarea"
              style={{ minHeight: 60 }}
              value={task.blockedReason ?? ''}
              onChange={e => onChange({ blockedReason: e.target.value })}
              placeholder="何が邪魔になったか"
            />
            <label className="field-label" style={{ marginTop: 8 }}>次のアクション</label>
            <input
              className="field-input"
              value={task.nextAction ?? ''}
              onChange={e => onChange({ nextAction: e.target.value })}
              placeholder="次に何をするか"
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default function EveningReviewView({ data, updateData, today }: SharedProps) {
  const dayLog = data.days[today];
  const plan   = dayLog?.morningPlan;
  const review = dayLog?.eveningReview;

  const [tasks, setTasks] = useState<Task[]>(plan?.tasks ?? []);
  const [form, setForm] = useState({
    whatWentWell:  review?.whatWentWell  ?? '',
    whatDidntWork: review?.whatDidntWork ?? '',
    insight:       review?.insight       ?? '',
    gratitude:     review?.gratitude     ?? '',
    tomorrowFocus: review?.tomorrowFocus ?? '',
  });
  const [saved, setSaved] = useState(false);

  function setField(key: keyof typeof form, value: string) {
    setForm(f => ({ ...f, [key]: value }));
  }

  function updateTask(taskId: string, patch: Partial<Task>) {
    setTasks(ts => ts.map(t => t.id === taskId ? { ...t, ...patch, updatedAt: now() } : t));
  }

  function handleSave() {
    const n = now();
    updateData(d => {
      const existing = d.days[today];
      return {
        ...d,
        days: {
          ...d.days,
          [today]: {
            ...existing,
            date: today,
            morningPlan: existing?.morningPlan
              ? { ...existing.morningPlan, tasks, updatedAt: n }
              : undefined,
            eveningReview: {
              id: existing?.eveningReview?.id ?? genId(),
              date: today,
              ...form,
              createdAt: existing?.eveningReview?.createdAt ?? n,
              updatedAt: n,
            },
          },
        },
      };
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div>
      <div className="date-heading">🌙 {formatDate(today)} の夜レビュー</div>

      {saved && <div className="alert alert-success">✓ 保存しました</div>}

      {/* Task review */}
      {tasks.length > 0 && (
        <>
          <div className="section-header">
            <div className="section-title">タスクの振り返り</div>
          </div>
          {tasks.map(t => (
            <TaskReview key={t.id} task={t} onChange={p => updateTask(t.id, p)} />
          ))}
          <div className="divider" />
        </>
      )}
      {!plan && (
        <div className="alert alert-info">
          今日の朝プランがまだ作成されていません。朝プランなしでレビューのみ記録できます。
        </div>
      )}

      {/* Reflection */}
      <div className="section-title" style={{ marginBottom: 14 }}>今日の振り返り</div>

      <div className="card">
        <div className="field">
          <label className="field-label">✅ うまくいったこと</label>
          <textarea className="field-textarea" value={form.whatWentWell}
            onChange={e => setField('whatWentWell', e.target.value)}
            placeholder="今日良かったこと、成功したことは？" />
        </div>
        <div className="field">
          <label className="field-label">🔶 うまくいかなかったこと</label>
          <textarea className="field-textarea" value={form.whatDidntWork}
            onChange={e => setField('whatDidntWork', e.target.value)}
            placeholder="難しかったこと、できなかったことは？" />
        </div>
        <div className="field">
          <label className="field-label">💡 気づき・学び</label>
          <textarea className="field-textarea" value={form.insight}
            onChange={e => setField('insight', e.target.value)}
            placeholder="今日気づいたこと、学んだことは？" />
        </div>
        <div className="field">
          <label className="field-label">🙏 感謝していること</label>
          <textarea className="field-textarea" value={form.gratitude}
            onChange={e => setField('gratitude', e.target.value)}
            placeholder="今日感謝していることは？" />
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label className="field-label">🎯 明日フォーカスすること</label>
          <textarea className="field-textarea" value={form.tomorrowFocus}
            onChange={e => setField('tomorrowFocus', e.target.value)}
            placeholder="明日最も大事にすることは？" />
        </div>
      </div>

      <button className="btn btn-primary btn-block" style={{ marginTop: 8 }} onClick={handleSave}>
        保存する
      </button>
    </div>
  );
}

import { useState } from 'react';
import type { SharedProps } from '../App';
import type { Task, TaskStatus } from '../types';
import { genId, now, formatDate, formatDateShort, daysUntil, dueRemainLabel, todayDate } from '../utils';
import { collectActiveTasks, updateTaskAnywhere, removeTaskAnywhere } from '../tasks';

const STATUS_OPTIONS: { value: TaskStatus; label: string }[] = [
  { value: 'todo',      label: '未着手' },
  { value: 'doing',     label: '実施中' },
  { value: 'done',      label: '完了' },
  { value: 'partial',   label: '部分完了' },
  { value: 'skipped',   label: 'スキップ' },
  { value: 'cancelled', label: 'キャンセル' },
];

function emptyTask(): Omit<Task, 'id' | 'createdAt' | 'updatedAt'> {
  return {
    action: '', completionCondition: '', firstAction: '',
    reason: '', plan: '', estimatedMinutes: undefined,
    status: 'todo', inquiryIds: [],
  };
}

type TaskFormState = ReturnType<typeof emptyTask>;

function TaskBadge({ status }: { status: TaskStatus }) {
  const map: Record<TaskStatus, string> = {
    todo: '未着手', doing: '実施中', done: '完了',
    partial: '部分完了', skipped: 'スキップ', cancelled: 'キャンセル',
  };
  return <span className={`badge badge-${status}`}>{map[status]}</span>;
}

function TaskItem({
  task, themes, carried, ownerDay, onStatusChange, onRemove,
}: {
  task: Task;
  themes: { id: string; title: string }[];
  carried?: boolean;
  ownerDay?: string;
  onStatusChange: (status: TaskStatus) => void;
  onRemove: () => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="task-item">
      <div className="task-item-header" onClick={() => setExpanded(e => !e)}>
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: 4 }}>
          <div className={`task-action${task.status === 'done' ? ' done' : ''}`}>
            {task.action || '（未入力）'}
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
            <TaskBadge status={task.status} />
            {carried && (
              <span className="badge" style={{ background: 'var(--c-danger-bg)', color: 'var(--c-danger)' }}>
                ⏳ 持ち越し
              </span>
            )}
            {task.dueDate && (
              <span
                className="badge"
                style={daysUntil(task.dueDate, todayDate()) < 0
                  ? { background: 'var(--c-danger-bg)', color: 'var(--c-danger)' }
                  : { background: 'var(--c-border)', color: 'var(--c-text2)' }}
              >
                〜{formatDateShort(task.dueDate)}（{dueRemainLabel(task.dueDate, todayDate())}）
              </span>
            )}
          </div>
        </div>
        <span className="task-expand-icon">{expanded ? '▲' : '▼'}</span>
      </div>
      {expanded && (
        <div className="task-detail">
          {carried && ownerDay && (
            <div className="task-detail-row">
              <div className="task-detail-label">登録日</div>
              <div className="task-detail-value">{formatDateShort(ownerDay)}（未完了のため持ち越し中）</div>
            </div>
          )}
          {task.dueDate && (
            <div className="task-detail-row">
              <div className="task-detail-label">期限</div>
              <div className="task-detail-value">{formatDateShort(task.dueDate)} まで（{dueRemainLabel(task.dueDate, todayDate())}）</div>
            </div>
          )}
          <div className="task-detail-row">
            <div className="task-detail-label">完了条件</div>
            <div className="task-detail-value">{task.completionCondition || '—'}</div>
          </div>
          <div className="task-detail-row">
            <div className="task-detail-label">最初の一手</div>
            <div className="task-detail-value">{task.firstAction || '—'}</div>
          </div>
          {task.reason && (
            <div className="task-detail-row">
              <div className="task-detail-label">理由</div>
              <div className="task-detail-value">{task.reason}</div>
            </div>
          )}
          {task.plan && (
            <div className="task-detail-row">
              <div className="task-detail-label">手順の見通し</div>
              <div className="task-detail-value" style={{ whiteSpace: 'pre-wrap' }}>{task.plan}</div>
            </div>
          )}
          {task.estimatedMinutes && (
            <div className="task-detail-row">
              <div className="task-detail-label">見積もり</div>
              <div className="task-detail-value">{task.estimatedMinutes} 分</div>
            </div>
          )}
          {task.inquiryIds.length > 0 && (
            <div className="task-detail-row">
              <div className="task-detail-label">テーマ</div>
              <div className="task-detail-value">
                {task.inquiryIds.map(id => themes.find(t => t.id === id)?.title ?? id).join(', ')}
              </div>
            </div>
          )}
          <div className="task-status-bar" style={{ marginTop: 12 }}>
            {STATUS_OPTIONS.map(s => (
              <button
                key={s.value}
                className={`status-btn ${task.status === s.value ? `active-${s.value}` : ''}`}
                onClick={() => onStatusChange(s.value)}
              >
                {s.label}
              </button>
            ))}
          </div>
          <div style={{ marginTop: 10, textAlign: 'right' }}>
            <button className="btn btn-ghost btn-sm" onClick={onRemove}>削除</button>
          </div>
        </div>
      )}
    </div>
  );
}

function TaskModal({
  themes,
  today,
  onSave,
  onClose,
}: {
  themes: { id: string; title: string }[];
  today: string;
  onSave: (t: TaskFormState) => void;
  onClose: () => void;
}) {
  const [form, setForm] = useState<TaskFormState>(emptyTask);
  const [error, setError] = useState('');

  function set(key: keyof TaskFormState, value: string | number | string[] | undefined) {
    setForm(f => ({ ...f, [key]: value }));
  }

  function handleSave() {
    if (!form.action.trim())              { setError('「やること」を入力してください'); return; }
    if (!form.completionCondition.trim()) { setError('「完了条件」を入力してください'); return; }
    if (!form.firstAction.trim())         { setError('「最初の一手」を入力してください'); return; }
    onSave(form);
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-title">タスクを追加</div>
        {error && <div className="alert alert-info" style={{ background: 'var(--c-danger-bg)', color: 'var(--c-danger)' }}>{error}</div>}

        <div className="field">
          <label className="field-label required">やること</label>
          <input className="field-input" value={form.action}
            onChange={e => set('action', e.target.value)}
            placeholder="例: レポートの第1章を書く" />
        </div>
        <div className="field">
          <label className="field-label required">完了条件</label>
          <input className="field-input" value={form.completionCondition}
            onChange={e => set('completionCondition', e.target.value)}
            placeholder="例: 1000字以上書いて保存した" />
          <div className="field-hint">「これができたら完了」という具体的な状態</div>
        </div>
        <div className="field">
          <label className="field-label required">最初の一手</label>
          <input className="field-input" value={form.firstAction}
            onChange={e => set('firstAction', e.target.value)}
            placeholder="例: エディタを開いてアウトラインを書く" />
          <div className="field-hint">今すぐできる最初のアクション</div>
        </div>
        <div className="field">
          <label className="field-label">理由（なぜやるか）</label>
          <input className="field-input" value={form.reason ?? ''}
            onChange={e => set('reason', e.target.value)}
            placeholder="例: 締め切りが明日なので" />
        </div>
        <div className="field">
          <label className="field-label">手順の見通し（段取り）</label>
          <textarea className="field-textarea" value={form.plan ?? ''}
            onChange={e => set('plan', e.target.value)}
            placeholder={'この時間で何をどの順でやるかのイメージ\n例:\n① アウトラインを箇条書き\n② 各見出しを2〜3行で埋める\n③ 通して読み直して整える'} />
          <div className="field-hint">この時間にやることの見通し・プランを立てる</div>
        </div>
        <div className="field">
          <label className="field-label">見積もり時間（分）</label>
          <input className="field-input" type="number" min={1}
            value={form.estimatedMinutes ?? ''}
            onChange={e => set('estimatedMinutes', e.target.value ? Number(e.target.value) : undefined)}
            placeholder="例: 60" />
        </div>
        <div className="field">
          {!form.dueDate ? (
            <button className="btn btn-outline btn-sm" type="button"
              onClick={() => set('dueDate', today)}>
              📅 期限を決める（基本は今日中）
            </button>
          ) : (
            <>
              <label className="field-label">期限（この日まで）</label>
              <input className="field-input" type="date" value={form.dueDate}
                min={today}
                onChange={e => set('dueDate', e.target.value || undefined)} />
              <div className="field-hint">
                未完了なら翌日以降に持ち越し。期限が先のものほどリストの下に並びます。
                <button className="btn btn-ghost btn-sm" type="button" style={{ marginLeft: 8 }}
                  onClick={() => set('dueDate', undefined)}>
                  今日中に戻す
                </button>
              </div>
            </>
          )}
        </div>
        {themes.length > 0 && (
          <div className="field">
            <label className="field-label">関連テーマ</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {themes.map(t => (
                <button
                  key={t.id}
                  className={`status-btn ${form.inquiryIds.includes(t.id) ? 'active-doing' : ''}`}
                  onClick={() => set('inquiryIds',
                    form.inquiryIds.includes(t.id)
                      ? form.inquiryIds.filter(id => id !== t.id)
                      : [...form.inquiryIds, t.id])}
                >
                  {t.title}
                </button>
              ))}
            </div>
          </div>
        )}
        <div className="modal-actions">
          <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleSave}>追加</button>
          <button className="btn btn-ghost" onClick={onClose}>キャンセル</button>
        </div>
      </div>
    </div>
  );
}

export default function MorningPlanView({ data, updateData, today }: SharedProps) {
  const dayLog = data.days[today];
  const plan = dayLog?.morningPlan;
  const [theme, setTheme] = useState(plan?.theme ?? '');
  const [intention, setIntention] = useState(plan?.intention ?? '');
  const [showModal, setShowModal] = useState(false);
  const [saved, setSaved] = useState(false);

  const tasks = plan?.tasks ?? [];
  const visible = collectActiveTasks(data, today);
  const themes = data.themes.filter(t => t.status === 'active');

  function save(newTasks?: Task[]) {
    const n = now();
    updateData(d => {
      const existing = d.days[today]?.morningPlan;
      return {
        ...d,
        days: {
          ...d.days,
          [today]: {
            ...d.days[today],
            date: today,
            morningPlan: {
              id: existing?.id ?? genId(),
              date: today,
              theme,
              intention,
              tasks: newTasks ?? existing?.tasks ?? [],
              createdAt: existing?.createdAt ?? n,
              updatedAt: n,
            },
          },
        },
      };
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  function addTask(form: TaskFormState) {
    const n = now();
    const newTask: Task = { id: genId(), ...form, createdAt: n, updatedAt: n };
    const newTasks = [...tasks, newTask];
    save(newTasks);
    setShowModal(false);
  }

  function updateTaskStatus(taskId: string, status: TaskStatus) {
    updateData(d => updateTaskAnywhere(d, taskId, { status }));
  }

  function removeTask(taskId: string) {
    if (!confirm('このタスクを削除しますか？')) return;
    updateData(d => removeTaskAnywhere(d, taskId));
  }

  return (
    <div>
      <div className="date-heading">📝 {formatDate(today)} の朝プラン</div>

      {saved && <div className="alert alert-success">✓ 保存しました</div>}

      <div className="card">
        <div className="field">
          <label className="field-label">今日のテーマ</label>
          <input className="field-input" value={theme}
            onChange={e => setTheme(e.target.value)}
            placeholder="例: 深い集中で仕事する" />
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label className="field-label">今日の意図・姿勢</label>
          <textarea className="field-textarea" value={intention}
            onChange={e => setIntention(e.target.value)}
            placeholder="例: 通知を切って2時間ブロックを確保する" />
        </div>
      </div>

      <div className="section-header">
        <div className="section-title">タスク ({visible.length})</div>
        <button className="btn btn-primary btn-sm" onClick={() => setShowModal(true)}>＋ 追加</button>
      </div>

      {visible.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">📋</div>
          <div className="empty-text">タスクがまだありません</div>
        </div>
      ) : (
        visible.map(v => (
          <TaskItem
            key={v.task.id}
            task={v.task}
            themes={themes}
            carried={v.carried}
            ownerDay={v.ownerDay}
            onStatusChange={s => updateTaskStatus(v.task.id, s)}
            onRemove={() => removeTask(v.task.id)}
          />
        ))
      )}

      <button className="btn btn-primary btn-block" style={{ marginTop: 16 }} onClick={() => save()}>
        保存する
      </button>

      {showModal && (
        <TaskModal themes={themes} today={today} onSave={addTask} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}

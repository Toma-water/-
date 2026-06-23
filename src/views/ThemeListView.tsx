import { useState } from 'react';
import type { SharedProps } from '../App';
import type { InquiryTheme } from '../types';
import { genId, now } from '../utils';

type StatusFilter = 'all' | 'active' | 'paused' | 'completed';

const STATUS_LABELS: Record<InquiryTheme['status'], string> = {
  active: '進行中', paused: '一時停止', completed: '完了',
};

function NewThemeModal({
  onSave,
  onClose,
}: {
  onSave: (t: Pick<InquiryTheme, 'title' | 'question' | 'description'>) => void;
  onClose: () => void;
}) {
  const [title, setTitle] = useState('');
  const [question, setQuestion] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  function handleSave() {
    if (!title.trim())    { setError('タイトルを入力してください'); return; }
    if (!question.trim()) { setError('核心的な問いを入力してください'); return; }
    onSave({ title: title.trim(), question: question.trim(), description: description.trim() });
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-title">新しい探究テーマ</div>
        {error && <div className="alert" style={{ background: 'var(--c-danger-bg)', color: 'var(--c-danger)' }}>{error}</div>}
        <div className="field">
          <label className="field-label required">テーマ名</label>
          <input className="field-input" value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="例: 深い集中とは何か" />
        </div>
        <div className="field">
          <label className="field-label required">核心的な問い</label>
          <textarea className="field-textarea" value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="例: 自分が「ゾーン」に入るための条件は何か？" />
          <div className="field-hint">このテーマで最も探りたい根本的な問い</div>
        </div>
        <div className="field" style={{ marginBottom: 0 }}>
          <label className="field-label">説明・背景</label>
          <textarea className="field-textarea" value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="なぜこのテーマを探究するのか" />
        </div>
        <div className="modal-actions">
          <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleSave}>作成</button>
          <button className="btn btn-ghost" onClick={onClose}>キャンセル</button>
        </div>
      </div>
    </div>
  );
}

export default function ThemeListView({ data, updateData, onOpen }: SharedProps & { onOpen: (id: string) => void }) {
  const [filter, setFilter] = useState<StatusFilter>('all');
  const [showModal, setShowModal] = useState(false);

  const filtered = data.themes
    .filter(t => filter === 'all' || t.status === filter)
    .sort((a, b) => {
      const order = { active: 0, paused: 1, completed: 2 };
      return order[a.status] - order[b.status] || b.updatedAt.localeCompare(a.updatedAt);
    });

  function createTheme(fields: Pick<InquiryTheme, 'title' | 'question' | 'description'>) {
    const n = now();
    const theme: InquiryTheme = {
      id: genId(),
      ...fields,
      status: 'active',
      notes: [],
      createdAt: n,
      updatedAt: n,
    };
    updateData(d => ({ ...d, themes: [...d.themes, theme] }));
    setShowModal(false);
  }

  const FILTERS: { value: StatusFilter; label: string }[] = [
    { value: 'all',       label: '全て' },
    { value: 'active',    label: '進行中' },
    { value: 'paused',    label: '停止中' },
    { value: 'completed', label: '完了' },
  ];

  return (
    <div>
      <div className="section-header">
        <div className="section-title">🔍 探究テーマ</div>
        <button className="btn btn-primary btn-sm" onClick={() => setShowModal(true)}>＋ 新規</button>
      </div>

      <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap' }}>
        {FILTERS.map(f => (
          <button
            key={f.value}
            className={`status-btn ${filter === f.value ? 'active-doing' : ''}`}
            onClick={() => setFilter(f.value)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">🔍</div>
          <div className="empty-text">
            {data.themes.length === 0
              ? 'テーマがまだありません\n「＋ 新規」で作成してください'
              : 'このフィルターに一致するテーマがありません'}
          </div>
        </div>
      ) : (
        filtered.map(theme => (
          <div key={theme.id} className="theme-card" onClick={() => onOpen(theme.id)}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
              <div className="theme-card-title">{theme.title}</div>
              <span className={`badge badge-${theme.status}`}>{STATUS_LABELS[theme.status]}</span>
            </div>
            <div className="theme-card-q">{theme.question}</div>
            <div className="theme-card-meta">
              <span>📝 {theme.notes.length} ノート</span>
              <span>·</span>
              <span>{new Date(theme.updatedAt).toLocaleDateString('ja-JP')}</span>
            </div>
          </div>
        ))
      )}

      {showModal && (
        <NewThemeModal onSave={createTheme} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}

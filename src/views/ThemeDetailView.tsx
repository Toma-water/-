import { useState } from 'react';
import type { SharedProps } from '../App';
import type { InquiryTheme, InquiryNote } from '../types';
import { genId, now, todayDate } from '../utils';

const STATUS_OPTIONS: { value: InquiryTheme['status']; label: string }[] = [
  { value: 'active',    label: '進行中' },
  { value: 'paused',    label: '一時停止' },
  { value: 'completed', label: '完了' },
];

export default function ThemeDetailView({
  data, updateData, themeId, onBack,
}: SharedProps & { themeId: string; onBack: () => void }) {
  const themeRaw = data.themes.find(t => t.id === themeId);

  const [editMode, setEditMode] = useState(false);
  const [title, setTitle] = useState(themeRaw?.title ?? '');
  const [question, setQuestion] = useState(themeRaw?.question ?? '');
  const [description, setDescription] = useState(themeRaw?.description ?? '');
  const [noteText, setNoteText] = useState('');
  const [addingNote, setAddingNote] = useState(false);
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [completionInsight, setCompletionInsight] = useState('');
  const [insightError, setInsightError] = useState(false);

  if (!themeRaw) {
    return (
      <div>
        <button className="back-btn" onClick={onBack}>← 一覧に戻る</button>
        <div className="empty"><div className="empty-text">テーマが見つかりません</div></div>
      </div>
    );
  }

  // 早期returnの後なので theme は確実に存在する（クロージャ内でも型が確定）
  const theme: InquiryTheme = themeRaw;

  function updateTheme(patch: Partial<InquiryTheme>) {
    updateData(d => ({
      ...d,
      themes: d.themes.map(t =>
        t.id === themeId ? { ...t, ...patch, updatedAt: now() } : t,
      ),
    }));
  }

  function saveEdit() {
    if (!title.trim()) return;
    updateTheme({ title: title.trim(), question: question.trim(), description: description.trim() });
    setEditMode(false);
  }

  function addNote() {
    if (!noteText.trim()) return;
    const note: InquiryNote = {
      id: genId(),
      content: noteText.trim(),
      relatedTaskIds: [],
      date: todayDate(),
      createdAt: now(),
    };
    updateTheme({ notes: [note, ...theme.notes] });
    setNoteText('');
    setAddingNote(false);
  }

  function deleteNote(noteId: string) {
    if (!confirm('このノートを削除しますか？')) return;
    updateTheme({ notes: theme.notes.filter(n => n.id !== noteId) });
  }

  function handleStatusChange(value: InquiryTheme['status']) {
    if (value === 'completed' && theme.status !== 'completed') {
      setCompletionInsight('');
      setInsightError(false);
      setShowCompletionModal(true);
    } else {
      updateTheme({ status: value, ...(value !== 'completed' ? { completionInsight: undefined } : {}) });
    }
  }

  function confirmCompletion() {
    if (!completionInsight.trim()) {
      setInsightError(true);
      return;
    }
    updateTheme({ status: 'completed', completionInsight: completionInsight.trim() });
    setShowCompletionModal(false);
  }

  function deleteTheme() {
    if (!confirm(`「${theme.title}」を削除しますか？この操作は元に戻せません。`)) return;
    updateData(d => ({ ...d, themes: d.themes.filter(t => t.id !== themeId) }));
    onBack();
  }

  return (
    <div>
      <button className="back-btn" onClick={onBack}>← 一覧に戻る</button>

      {/* Header */}
      <div className="card">
        {editMode ? (
          <>
            <div className="field">
              <label className="field-label required">テーマ名</label>
              <input className="field-input" value={title} onChange={e => setTitle(e.target.value)} />
            </div>
            <div className="field">
              <label className="field-label required">核心的な問い</label>
              <textarea className="field-textarea" value={question}
                onChange={e => setQuestion(e.target.value)} />
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label className="field-label">説明・背景</label>
              <textarea className="field-textarea" value={description}
                onChange={e => setDescription(e.target.value)} />
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <button className="btn btn-primary btn-sm" onClick={saveEdit}>保存</button>
              <button className="btn btn-ghost btn-sm" onClick={() => {
                setTitle(theme.title); setQuestion(theme.question);
                setDescription(theme.description); setEditMode(false);
              }}>キャンセル</button>
            </div>
          </>
        ) : (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
              <div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{theme.title}</div>
                <div style={{ fontSize: '.8rem', color: 'var(--c-text3)', marginTop: 2 }}>
                  {new Date(theme.createdAt).toLocaleDateString('ja-JP')} 作成
                </div>
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => setEditMode(true)}>編集</button>
            </div>
            <div style={{ marginTop: 12 }}>
              <div className="field-label">核心的な問い</div>
              <div style={{ marginTop: 4, fontStyle: 'italic', color: 'var(--c-text)' }}>
                「{theme.question}」
              </div>
            </div>
            {theme.description && (
              <div style={{ marginTop: 10 }}>
                <div className="field-label">背景</div>
                <div style={{ marginTop: 4, fontSize: '.88rem', color: 'var(--c-text2)' }}>
                  {theme.description}
                </div>
              </div>
            )}
          </>
        )}

        {/* Status */}
        {!editMode && (
          <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--c-border)' }}>
            <div className="field-label" style={{ marginBottom: 6 }}>ステータス</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {STATUS_OPTIONS.map(s => (
                <button
                  key={s.value}
                  className={`status-btn ${theme.status === s.value ? `active-${s.value === 'active' ? 'done' : s.value === 'paused' ? 'partial' : 'doing'}` : ''}`}
                  onClick={() => handleStatusChange(s.value)}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Completion insight */}
      {theme.status === 'completed' && theme.completionInsight && (
        <div className="card" style={{ borderLeft: '3px solid var(--c-primary)', background: 'var(--c-primary-bg, #eff6ff)' }}>
          <div className="field-label" style={{ marginBottom: 6 }}>💡 腑に落ちた考え</div>
          <div style={{ fontSize: '.92rem', color: 'var(--c-text)', whiteSpace: 'pre-wrap' }}>
            {theme.completionInsight}
          </div>
        </div>
      )}

      {/* Notes */}
      <div className="section-header" style={{ marginTop: 4 }}>
        <div className="section-title">ノート ({theme.notes.length})</div>
        <button className="btn btn-primary btn-sm" onClick={() => setAddingNote(v => !v)}>
          {addingNote ? '✕' : '＋ 追加'}
        </button>
      </div>

      {addingNote && (
        <div className="card" style={{ marginBottom: 12 }}>
          <div className="field">
            <label className="field-label">ノート内容</label>
            <textarea
              className="field-textarea"
              value={noteText}
              onChange={e => setNoteText(e.target.value)}
              placeholder="気づき、観察、疑問、アイデア…"
              autoFocus
            />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary btn-sm" onClick={addNote}>保存</button>
            <button className="btn btn-ghost btn-sm" onClick={() => { setNoteText(''); setAddingNote(false); }}>
              キャンセル
            </button>
          </div>
        </div>
      )}

      {theme.notes.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">📝</div>
          <div className="empty-text">ノートがまだありません</div>
        </div>
      ) : (
        theme.notes.map(note => (
          <div key={note.id} className="note-item">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div className="note-date">
                {new Date(note.date + 'T00:00:00').toLocaleDateString('ja-JP')}
              </div>
              <button
                style={{ background: 'none', border: 'none', color: 'var(--c-text3)', fontSize: '.8rem', cursor: 'pointer' }}
                onClick={() => deleteNote(note.id)}
              >
                ✕
              </button>
            </div>
            <div className="note-text">{note.content}</div>
          </div>
        ))
      )}

      {/* Danger zone */}
      <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--c-border)' }}>
        <button className="btn btn-ghost btn-sm" style={{ color: 'var(--c-danger)', borderColor: 'var(--c-danger)' }}
          onClick={deleteTheme}>
          このテーマを削除
        </button>
      </div>

      {/* Completion modal */}
      {showCompletionModal && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setShowCompletionModal(false)}>
          <div className="modal">
            <div className="modal-title">テーマを完了にする</div>
            <div style={{ fontSize: '.88rem', color: 'var(--c-text2)', marginBottom: 16 }}>
              「{theme.title}」の探究を通じて得た気づきを記録します。
            </div>
            <div className="field">
              <label className="field-label required">腑に落ちた考えは何か</label>
              <textarea
                className="field-textarea"
                value={completionInsight}
                onChange={e => { setCompletionInsight(e.target.value); setInsightError(false); }}
                placeholder="この探究で最終的に理解・納得できたことを書いてください"
                rows={5}
                autoFocus
                style={insightError ? { borderColor: 'var(--c-danger)' } : {}}
              />
              {insightError && (
                <div style={{ color: 'var(--c-danger)', fontSize: '.82rem', marginTop: 4 }}>
                  入力してください
                </div>
              )}
            </div>
            <div className="modal-actions">
              <button className="btn btn-primary" style={{ flex: 1 }} onClick={confirmCompletion}>
                完了にする
              </button>
              <button className="btn btn-ghost" onClick={() => setShowCompletionModal(false)}>
                キャンセル
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

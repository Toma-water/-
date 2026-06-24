import type { SharedProps } from '../App';
import { formatDate } from '../utils';
import { collectActiveTasks, progressPct } from '../tasks';

type Props = SharedProps & {
  onGoMorning: () => void;
  onGoEvening: () => void;
  onGoThemes: () => void;
};

export default function TodayView({ data, today, onGoMorning, onGoEvening, onGoThemes }: Props) {
  const dayLog = data.days[today];
  const plan   = dayLog?.morningPlan;
  const review = dayLog?.eveningReview;

  const tasks = collectActiveTasks(data, today).map(v => v.task);
  const doneCount = tasks.filter(t => t.status === 'done').length;
  const partialCount = tasks.filter(t => t.status === 'partial').length;
  const pct = progressPct(tasks);

  const activeThemes = data.themes.filter(t => t.status === 'active');

  return (
    <div>
      <div className="date-heading">{formatDate(today)}</div>

      {/* 朝のプラン */}
      <div className="summary-card">
        <div className="summary-icon">📝</div>
        <div className="summary-body">
          <div className="summary-label">朝のプラン</div>
          {(plan || tasks.length > 0) ? (
            <>
              <div className="summary-main">{plan?.theme || (tasks.length > 0 ? '今日のタスク' : '（テーマ未設定）')}</div>
              <div className="summary-sub">
                タスク {doneCount}/{tasks.length} 完了
                {partialCount > 0 && <span style={{ color: 'var(--c-text3)' }}>（部分 {partialCount}）</span>}
                {tasks.length > 0 && (
                  <span style={{ marginLeft: 8, color: pct === 100 ? 'var(--c-success)' : undefined }}>
                    {pct}%
                  </span>
                )}
              </div>
              {tasks.length > 0 && (
                <div className="progress-bar" style={{ marginTop: 8 }}>
                  <div className="progress-fill" style={{ width: `${pct}%` }} />
                </div>
              )}
            </>
          ) : (
            <div className="summary-main" style={{ color: 'var(--c-text3)' }}>まだ作成されていません</div>
          )}
          <button className="summary-action" onClick={onGoMorning}>
            {plan ? 'プランを確認・編集 →' : '今日のプランを作成 →'}
          </button>
        </div>
      </div>

      {/* 夜のレビュー */}
      <div className="summary-card">
        <div className="summary-icon">🌙</div>
        <div className="summary-body">
          <div className="summary-label">夜のレビュー</div>
          {review ? (
            <>
              <div className="summary-main" style={{ color: 'var(--c-success)' }}>✓ 完了</div>
              {review.insight && (
                <div className="summary-sub">気づき: {review.insight.slice(0, 60)}{review.insight.length > 60 ? '…' : ''}</div>
              )}
            </>
          ) : (
            <div className="summary-main" style={{ color: 'var(--c-text3)' }}>まだ記録されていません</div>
          )}
          <button className="summary-action" onClick={onGoEvening}>
            {review ? 'レビューを確認 →' : '今日を振り返る →'}
          </button>
        </div>
      </div>

      {/* 探究テーマ */}
      <div className="summary-card">
        <div className="summary-icon">🔍</div>
        <div className="summary-body">
          <div className="summary-label">探究テーマ</div>
          {activeThemes.length > 0 ? (
            <>
              <div className="summary-main">{activeThemes[0].title}</div>
              {activeThemes.length > 1 && (
                <div className="summary-sub">他 {activeThemes.length - 1} テーマが進行中</div>
              )}
            </>
          ) : (
            <div className="summary-main" style={{ color: 'var(--c-text3)' }}>テーマがありません</div>
          )}
          <button className="summary-action" onClick={onGoThemes}>
            テーマ一覧を見る →
          </button>
        </div>
      </div>
    </div>
  );
}

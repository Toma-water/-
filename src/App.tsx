import { useState, useCallback, Suspense, lazy } from 'react';
import type { AppData } from './types';
import { loadData, saveData } from './storage';
import { todayDate } from './utils';

const TodayView      = lazy(() => import('./views/TodayView'));
const MorningPlanView= lazy(() => import('./views/MorningPlanView'));
const EveningReviewView = lazy(() => import('./views/EveningReviewView'));
const ThemeListView  = lazy(() => import('./views/ThemeListView'));
const ThemeDetailView= lazy(() => import('./views/ThemeDetailView'));
const HistoryView    = lazy(() => import('./views/HistoryView'));

export type ViewName = 'today' | 'morning' | 'evening' | 'themes' | 'theme-detail' | 'history';

export type SharedProps = {
  data: AppData;
  updateData: (updater: (d: AppData) => AppData) => void;
  today: string;
};

function Loading() {
  return <div className="loading">読み込み中…</div>;
}

export default function App() {
  const [data, setData] = useState<AppData>(() => loadData());
  const [view, setView] = useState<ViewName>('today');
  const [selectedThemeId, setSelectedThemeId] = useState<string | null>(null);

  const updateData = useCallback((updater: (d: AppData) => AppData) => {
    setData(prev => {
      const next = updater(prev);
      saveData(next);
      return next;
    });
  }, []);

  const today = todayDate();
  const shared: SharedProps = { data, updateData, today };

  const NAV = [
    { id: 'today'   as ViewName, label: '今日',   icon: '☀️' },
    { id: 'morning' as ViewName, label: '朝プラン', icon: '📝' },
    { id: 'evening' as ViewName, label: '夜レビュー', icon: '🌙' },
    { id: 'themes'  as ViewName, label: 'テーマ',  icon: '🔍' },
    { id: 'history' as ViewName, label: '履歴',    icon: '📅' },
  ];

  const isThemeSection = view === 'themes' || view === 'theme-detail';

  return (
    <div className="app">
      <header className="app-header">
        <span className="app-title">Daily Inquiry Log</span>
      </header>

      <main className="app-main">
        <Suspense fallback={<Loading />}>
          {view === 'today' && (
            <TodayView
              {...shared}
              onGoMorning={() => setView('morning')}
              onGoEvening={() => setView('evening')}
              onGoThemes={() => setView('themes')}
            />
          )}
          {view === 'morning' && <MorningPlanView {...shared} />}
          {view === 'evening' && <EveningReviewView {...shared} />}
          {view === 'themes' && (
            <ThemeListView
              {...shared}
              onOpen={(id) => { setSelectedThemeId(id); setView('theme-detail'); }}
            />
          )}
          {view === 'theme-detail' && selectedThemeId && (
            <ThemeDetailView
              {...shared}
              themeId={selectedThemeId}
              onBack={() => setView('themes')}
            />
          )}
          {view === 'history' && <HistoryView {...shared} />}
        </Suspense>
      </main>

      <nav className="bottom-nav">
        {NAV.map(item => (
          <button
            key={item.id}
            className={`nav-item ${(item.id === 'themes' && isThemeSection) || view === item.id ? 'active' : ''}`}
            onClick={() => {
              if (item.id === 'themes' && view === 'theme-detail') setView('themes');
              else setView(item.id);
            }}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}

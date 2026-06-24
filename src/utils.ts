export function genId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

export function todayDate(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function now(): string {
  return new Date().toISOString();
}

const WEEKDAYS = ['日', '月', '火', '水', '木', '金', '土'];

export function formatDate(date: string): string {
  const d = new Date(date + 'T00:00:00');
  const m = d.getMonth() + 1;
  const day = d.getDate();
  const w = WEEKDAYS[d.getDay()];
  return `${m}月${day}日（${w}）`;
}

export function formatDateShort(date: string): string {
  const d = new Date(date + 'T00:00:00');
  const m = d.getMonth() + 1;
  const day = d.getDate();
  const w = WEEKDAYS[d.getDay()];
  return `${m}/${day}（${w}）`;
}

// fromStr から dateStr までの残り日数（同日=0、過去=マイナス）
export function daysUntil(dateStr: string, fromStr: string): number {
  const from = new Date(fromStr + 'T00:00:00').getTime();
  const to = new Date(dateStr + 'T00:00:00').getTime();
  return Math.round((to - from) / 86400000);
}

// 残り日数の表示ラベル（例: あと3日 / 今日まで / 2日超過）
export function dueRemainLabel(dateStr: string, fromStr: string): string {
  const n = daysUntil(dateStr, fromStr);
  if (n > 0) return `あと${n}日`;
  if (n === 0) return '今日まで';
  return `${-n}日超過`;
}

export function pastDates(n: number): string[] {
  const result: string[] = [];
  for (let i = 0; i < n; i++) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const s = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    result.push(s);
  }
  return result;
}

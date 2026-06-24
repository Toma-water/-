import type { AppData, Task, TaskStatus } from './types';
import { now } from './utils';

// 「まだ開いている（持ち越し対象）」とみなすステータス
const OPEN_STATUSES: TaskStatus[] = ['todo', 'doing', 'partial'];
// 「終わった系」（リスト下に沈める）
const FINISHED_STATUSES: TaskStatus[] = ['done', 'skipped', 'cancelled'];

export type VisibleTask = {
  task: Task;
  ownerDay: string;   // 実際にこのタスクが保存されている日
  carried: boolean;   // 過去日からの持ち越しかどうか
};

// 期限が未設定なら「持ち主の日（基本は今日）」を実質期限とする
export function effectiveDue(task: Task, ownerDay: string): string {
  return task.dueDate ?? ownerDay;
}

// その日に表示すべきタスク（今日のタスク＋過去日からの未完了の持ち越し）を集計し、並べ替える
export function collectActiveTasks(data: AppData, today: string): VisibleTask[] {
  const out: VisibleTask[] = [];
  const seen = new Set<string>();

  // ① 今日のタスク（全ステータス）
  for (const task of data.days[today]?.morningPlan?.tasks ?? []) {
    out.push({ task, ownerDay: today, carried: false });
    seen.add(task.id);
  }

  // ② 過去日の未完了タスク＝持ち越し
  for (const [day, log] of Object.entries(data.days)) {
    if (day >= today) continue;
    for (const task of log.morningPlan?.tasks ?? []) {
      if (seen.has(task.id)) continue;
      if (!OPEN_STATUSES.includes(task.status)) continue;
      out.push({ task, ownerDay: day, carried: true });
      seen.add(task.id);
    }
  }

  // 並べ替え: 終わった系は下 → 期限の近い順（今日/超過が上、先の期限ほど下）→ 作成順
  out.sort((a, b) => {
    const af = FINISHED_STATUSES.includes(a.task.status) ? 1 : 0;
    const bf = FINISHED_STATUSES.includes(b.task.status) ? 1 : 0;
    if (af !== bf) return af - bf;
    const ad = effectiveDue(a.task, a.ownerDay);
    const bd = effectiveDue(b.task, b.ownerDay);
    if (ad !== bd) return ad < bd ? -1 : 1;
    return a.task.createdAt < b.task.createdAt ? -1 : 1;
  });

  return out;
}

// タスクがどの日にあっても探して更新する
export function updateTaskAnywhere(data: AppData, taskId: string, patch: Partial<Task>): AppData {
  const days = { ...data.days };
  for (const [day, log] of Object.entries(days)) {
    const plan = log.morningPlan;
    if (!plan) continue;
    const idx = plan.tasks.findIndex(t => t.id === taskId);
    if (idx === -1) continue;
    const tasks = plan.tasks.slice();
    tasks[idx] = { ...tasks[idx], ...patch, updatedAt: now() };
    days[day] = { ...log, morningPlan: { ...plan, tasks, updatedAt: now() } };
    break;
  }
  return { ...data, days };
}

// タスクがどの日にあっても探して削除する
export function removeTaskAnywhere(data: AppData, taskId: string): AppData {
  const days = { ...data.days };
  for (const [day, log] of Object.entries(days)) {
    const plan = log.morningPlan;
    if (!plan) continue;
    if (!plan.tasks.some(t => t.id === taskId)) continue;
    days[day] = {
      ...log,
      morningPlan: { ...plan, tasks: plan.tasks.filter(t => t.id !== taskId), updatedAt: now() },
    };
    break;
  }
  return { ...data, days };
}

// 達成率: 完了=1.0、部分完了=0.5、それ以外=0
export function progressPct(tasks: Task[]): number {
  if (tasks.length === 0) return 0;
  const score = tasks.reduce(
    (s, t) => s + (t.status === 'done' ? 1 : t.status === 'partial' ? 0.5 : 0),
    0,
  );
  return Math.round((score / tasks.length) * 100);
}

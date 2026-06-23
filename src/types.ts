export type TaskStatus = 'todo' | 'doing' | 'done' | 'partial' | 'skipped' | 'cancelled';

export type Task = {
  id: string;
  action: string;               // やること
  completionCondition: string;  // 完了条件
  firstAction: string;          // 最初の一手
  reason?: string;
  estimatedMinutes?: number;
  status: TaskStatus;
  actualProgress?: string;
  blockedReason?: string;
  nextAction?: string;
  inquiryIds: string[];
  createdAt: string;
  updatedAt: string;
};

export type MorningPlan = {
  id: string;
  date: string;       // YYYY-MM-DD
  theme: string;
  intention: string;
  tasks: Task[];
  createdAt: string;
  updatedAt: string;
};

export type EveningReview = {
  id: string;
  date: string;
  whatWentWell: string;
  whatDidntWork: string;
  insight: string;
  gratitude: string;
  tomorrowFocus: string;
  createdAt: string;
  updatedAt: string;
};

export type DayLog = {
  date: string;
  morningPlan?: MorningPlan;
  eveningReview?: EveningReview;
};

export type InquiryNote = {
  id: string;
  content: string;
  relatedTaskIds: string[];
  date: string;
  createdAt: string;
};

export type InquiryTheme = {
  id: string;
  title: string;
  question: string;    // 核心的な問い
  description: string;
  status: 'active' | 'paused' | 'completed';
  completionInsight?: string;  // 完了時の腑に落ちた考え
  notes: InquiryNote[];
  createdAt: string;
  updatedAt: string;
};

export type AppData = {
  version: 1;
  days: Record<string, DayLog>;
  themes: InquiryTheme[];
};

# タスク管理アプリ「DayPilot」実装仕様書

> **このドキュメントはAIコーディングエージェント(Claude for VS Code / Codex)に渡して実装させるための仕様書です。**
> 上位の設計思想は `docs/task-app-design.md` を参照。本書だけで実装可能なように、型・画面・ロジック・受け入れ条件をすべて具体化しています。

---

## 0. エージェントへの指示(最初に読むこと)

- この仕様書に書かれた**型名・ストレージキー・ファイル構成は変更しない**こと(拡張は可)。
- 実装は **§12 のフェーズ順**に進め、各フェーズの「受け入れ条件」を満たしてから次に進むこと。
- 判断に迷う細部(余白、文言の微調整など)は仕様の設計原則(§1)に沿って自律的に決めてよい。
- UIテキストはすべて**日本語**。
- 外部UIライブラリは使わない(React + 素のCSS)。依存は最小限に保つ。

---

## 1. プロダクト概要

**DayPilot** — 「次の一手」を常に1つだけ提示する個人用タスク管理アプリ。

設計原則(実装判断に迷ったらこれに従う):
1. 常に「次の一手」が1つだけ表示されている。選択肢を並べない。
2. 完了条件のないタスクは登録できない。
3. 計画は崩れる前提。復帰はボタン1つ。自責メッセージは一切出さない。
4. 効率性 = 成果ポイント ÷ 実績時間。時間の長さではなく成果で評価する。
5. 入力の入口はInboxひとつ。仕分けはアプリとAIの仕事。

---

## 2. 技術スタック

| 項目 | 指定 |
|---|---|
| フレームワーク | React 18 + TypeScript 5 |
| ビルド | Vite(`npm create vite@latest daypilot -- --template react-ts`) |
| 状態管理 | React state + Context(Redux等は使わない) |
| 永続化 | localStorage(§6のラッパー経由でのみアクセス) |
| ルーティング | ライブラリ不使用。`currentView` state による画面切替 |
| スタイル | 素のCSS(`src/styles.css` 1ファイル)。CSS変数でテーマ定義 |
| AI | Google Gemini API(fetch直叩き、SDK不使用)。§10参照 |
| テスト | Vitest(ロジック層のみ。UIテストは不要) |

---

## 3. ディレクトリ構成

```
daypilot/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── src/
    ├── main.tsx              // エントリポイント
    ├── App.tsx               // アプリシェル・画面切替・Context提供
    ├── styles.css            // 全スタイル
    ├── types.ts              // §5の型定義(全型をここに集約)
    ├── storage.ts            // §6のストレージ層
    ├── logic/
    │   ├── efficiency.ts     // 効率スコア計算
    │   ├── srs.ts            // 間隔反復ロジック
    │   ├── scheduler.ts      // 締切逆算配置・バッファ挿入・翌日再配置
    │   ├── pomodoro.ts       // ポモドーロ分割
    │   └── fallback.ts       // AI不通時のルールベース処理
    ├── ai/
    │   ├── client.ts         // Gemini APIクライアント(§10.2)
    │   ├── prompts.ts        // プロンプトテンプレート(§10.4)
    │   └── schemas.ts        // レスポンスJSONスキーマ(§10.3)
    ├── components/
    │   ├── TaskCard.tsx
    │   ├── Timer.tsx
    │   ├── ProgressRing.tsx  // 成果ポイントの円形ゲージ
    │   └── TabBar.tsx
    └── views/
        ├── MorningLauncherView.tsx
        ├── TodayView.tsx
        ├── RecoveryModal.tsx
        ├── CalendarView.tsx
        ├── StudyView.tsx
        ├── InboxView.tsx
        ├── EveningCloseView.tsx
        └── SettingsView.tsx
```

---

## 4. 画面遷移

```
起動時判定:
  - 当日の DayPlan が存在し firstTaskId 設定済み & 未開始 → MorningLauncherView
  - それ以外 → TodayView

TabBar(下部固定): [今日] [カレンダー] [学習] [Inbox] [設定]
EveningCloseView: TodayView右上の[今日を閉じる]ボタン、または20:30以降にバナー表示から遷移
RecoveryModal: TodayView常設の[プランが崩れた]ボタンから開くモーダル
```

---

## 5. データモデル(`src/types.ts`)

```typescript
export type TaskStatus = 'inbox' | 'todo' | 'doing' | 'done' | 'dropped';
export type OutcomePoints = 1 | 2 | 3 | 5;

export interface Task {
  id: string;                 // crypto.randomUUID()
  title: string;
  purpose?: string;
  doneCriteria: string;       // 必須。空文字での保存はバリデーションエラー
  firstStep: string;          // 必須。「2分以内に着手できる物理的動作」
  steps?: string[];
  estimateMin: number;        // 5〜480
  actualMin?: number;
  outcomePoints: OutcomePoints;
  deadline?: string;          // 'YYYY-MM-DD'
  scheduledDate?: string;     // 'YYYY-MM-DD'
  scheduledTime?: string;     // 'HH:mm'
  bufferMin?: number;
  status: TaskStatus;
  tags: string[];
  subjectId?: string;
  createdAt: string;          // ISO 8601
  completedAt?: string;
}

export interface Subject {
  id: string;
  name: string;
  weeklyTargetMin: number;
  weakPoints: WeakPoint[];
}

export interface WeakPoint {
  id: string;
  text: string;
  createdAt: string;
  resolvedAt?: string;
}

export interface ReviewItem {
  id: string;
  subjectId: string;
  content: string;
  lastReviewedAt: string;
  intervalDays: 1 | 3 | 7 | 14 | 30;
  nextReviewAt: string;       // 'YYYY-MM-DD'
}

export type InboxKind = 'memo' | 'idea' | 'decision' | 'resource' | 'task-candidate';

export interface InboxItem {
  id: string;
  text: string;
  kind?: InboxKind;
  createdAt: string;
  processedAt?: string;
  linkedTaskId?: string;
}

export interface DayPlan {
  date: string;               // 'YYYY-MM-DD'(主キー)
  topThree: string[];         // Task.id 最大3件
  firstTaskId: string | null;
  startedAt?: string;         // 朝ランチャーで[開始]を押した時刻
  recoveryCount: number;
  review?: DayReview;
}

export interface DayReview {
  didWell: string;
  stuck: string;
  tomorrowFirstStep: string;
  efficiencyScore: number;
  closedAt: string;
}

export interface Settings {
  geminiApiKey: string;       // 空文字 = AI無効(全機能ルールベースで動作)
  geminiModel: string;        // デフォルト 'gemini-2.5-flash'。設定画面で変更可
  dayStartHour: number;       // デフォルト 6
  eveningCloseHour: number;   // デフォルト 20.5(=20:30)
  pomodoroWorkMin: number;    // デフォルト 25
  pomodoroBreakMin: number;   // デフォルト 5
}

export interface AppData {
  schemaVersion: 1;
  tasks: Task[];
  subjects: Subject[];
  reviewItems: ReviewItem[];
  inbox: InboxItem[];
  dayPlans: DayPlan[];
  settings: Settings;
}
```

---

## 6. ストレージ層(`src/storage.ts`)

- localStorage キー: **`daypilot.v1`**(AppData全体をJSONで1キーに保存)
- 公開API:

```typescript
export function loadData(): AppData;          // 無ければデフォルト値で初期化して返す
export function saveData(data: AppData): void;
export function exportJson(): string;         // バックアップ用(設定画面からDL)
export function importJson(json: string): void;
```

- `loadData` は `schemaVersion` を検査し、不明バージョンなら例外ではなく**バックアップキー(`daypilot.backup`)に退避してデフォルト初期化**する。
- 書き込みはすべて `saveData` 経由。コンポーネントから直接 `localStorage` を触らない。
- App.tsx で `AppData` をContextに載せ、更新関数 `update(fn: (d: AppData) => AppData)` を提供する(更新→保存→再レンダを一箇所に集約)。

---

## 7. 画面仕様

### 7.1 MorningLauncherView(朝ランチャー)

**目的:** 起床直後、迷いゼロで最初のタスクを開始させる。

**表示:**
- 画面中央に大きく: 今日の最初のタスクの `firstStep`(例:「机に問題集とノートを開く」)
- その下に小さく: タスク名・完了条件・見積時間
- ボタン2つのみ:
  - **[開始する]**(プライマリ・特大)→ 該当タスクを `doing` に、`DayPlan.startedAt` を記録し、TodayViewへ
  - **[今日は無理そう]** → RecoveryModal を「縮小モード」で開く
- 他のナビゲーション(TabBar)は**表示しない**。

**エッジケース:**
- `firstTaskId` が null(前夜に未設定)の場合:
  - AI有効時 → §10.4-C「朝のプラン生成」を呼び、Top3+最初の一手の提案を表示 → [これでいく]で確定
  - AI無効時 → `deadline` が近い順のtodoタスク上位3件を機械的にTop3として提案

**受け入れ条件:**
- [ ] 前夜に一手を設定済み → 起動時にこの画面が出て、開始まで**タップ1回**
- [ ] [開始する]後、同日に再度この画面は表示されない

### 7.2 TodayView(今日ビュー)

**目的:** 日中の実行専用画面。

**レイアウト(上から):**
1. **NOWカード**: `doing` のタスク1件。タスク名/完了条件/経過タイマー(Timer.tsx)/[完了][中断]ボタン
   - `estimateMin >= 45` のタスクは `pomodoro.ts` により「25分作業+5分休憩」のセグメント表示。休憩中は「休憩中 残りmm:ss」を表示
2. **NEXTカード(小)**: 次のタスク1件(決定ロジック: Top3の未完了先頭 → なければ今日scheduled分の先頭)
3. **Top3チェックリスト**: 3件のタイトル+完了チェック
4. **今日の成果**: ProgressRing(獲得成果ポイント合計)+ 完了件数
5. 常設フッターボタン: **[プランが崩れた]**(RecoveryModalを開く)/ **[今日を閉じる]**(EveningCloseViewへ)

**挙動:**
- [完了] → `status: 'done'`、`completedAt` 記録、`actualMin` = タイマー実測(分、四捨五入)。NEXTが自動でNOWに繰り上がる(確認ダイアログなし)。学習タスク(`tags`に`study`)完了時は「復習リストに入れる?」を1タップYes/Noで表示(§7.5)
- NOWが無くNEXTも無い → 「今日のプランは完了。お疲れさま」+[今日を閉じる]への導線
- タスク追加UIはこの画面に**置かない**(Inboxへ誘導するテキストリンクのみ)

**受け入れ条件:**
- [ ] 完了操作からNEXT繰り上がりまで自動(追加タップ不要)
- [ ] タイマーはタブを閉じて再度開いても継続している(開始時刻をstateでなく永続化して差分計算)

### 7.3 RecoveryModal(復帰モーダル)

**目的:** 崩れた瞬間に、責めずに、続きを1案だけ示す。

**挙動:**
1. 開くと「大丈夫、立て直そう」とだけ表示(自責を誘う文言・絵文字の泣き顔等は禁止)
2. 残り可処分時間を選択(30分/1時間/2時間/自由入力)
3. AI有効時 → §10.4-D を呼び、縮小プラン1案を表示。AI無効時 → `fallback.ts`: 「Top3未完了の最上位1件を、見積の半分の時間でやる」案を生成
4. **[このプランでいく]** → 提示タスク以外の今日分は `scheduler.ts` が翌日以降に自動再配置(メッセージ:「残りは明日に配置済み」)。`recoveryCount++`
5. [やっぱり続ける] → 何も変えず閉じる

**受け入れ条件:**
- [ ] 提示されるプランは常に**1案のみ**(比較選択させない)
- [ ] 再配置されたタスクに「失敗」「未達」等のラベルが付かない

### 7.4 CalendarView(カレンダー)

**目的:** 締切管理と「いつやるか」の自動配置。

**表示:**
- 上段: 週ビュー(7列)。各日に scheduledDate が一致するタスクをチップ表示。deadline 当日のタスクは赤枠
- 下段: 「今後7日の締切」リスト(deadline昇順)
- 月ビューは実装しない(P5以降)

**タスク登録フォーム(この画面とInboxから開ける):**
- 入力: タイトル(必須)/締切(任意)/科目(任意)/メモ
- 保存時にAI有効なら §10.4-A「タスク分解」を呼び、`doneCriteria / firstStep / steps / estimateMin / outcomePoints / bufferMin` を自動補完 → ユーザーが確認・修正して確定
- AI無効なら同項目を手入力(doneCriteria と firstStep は必須バリデーション)
- deadline 設定時、`scheduler.ts` が作業日を逆算提案(§9.3)。バッファは `bufferMin` として本体の前に表示

**受け入れ条件:**
- [ ] doneCriteria か firstStep が空のままでは保存ボタンが押せない
- [ ] 締切を入れると scheduledDate が自動提案される(手動変更可)

### 7.5 StudyView(学習)

**目的:** 復習の自動化・弱点の可視化・科目配分。

**セクション:**
1. **今日の復習**: `nextReviewAt <= 今日` の ReviewItem 一覧。各項目に[できた][あやしい]ボタン
   - できた → 間隔を次段階へ(1→3→7→14→30)、`nextReviewAt` 更新
   - あやしい → 間隔を1日にリセット
2. **弱点リスト**: 科目ごとの `weakPoints`(未解決のみ)。1行追加フォーム+[解決した]ボタン
3. **科目配分**: 科目ごとに「今週の実績分(studyタグのactualMin合計)/週目標」の横棒グラフ。差分が大きい順に並べる
4. **効率スコア**: 今日・今週の `efficiency.ts` 計算結果を数値+直近14日の折れ線(SVG手描きで可)

**受け入れ条件:**
- [ ] TodayViewで学習タスク完了→Yes選択 → ReviewItemが作られ、翌日の「今日の復習」に出る
- [ ] 復習アイテムは毎朝、当日分が自動でTodayViewのNEXT候補にも合流する(topThreeの後ろ)

### 7.6 InboxView(Inbox)

**目的:** 何でも1行で放り込める唯一の入口。

**表示:**
- 最上部: 1行入力欄+[追加](Enterでも追加)。追加時は分類しない
- 未処理リスト(processedAt無し)/処理済みは折りたたみ
- 各項目メニュー: [タスクにする](登録フォームへ引き継ぎ)/[決定ログへ]/[資料]/[削除]
- **決定ログタブ**: `kind: 'decision'` を日付降順で一覧、テキスト検索付き

**受け入れ条件:**
- [ ] 入力→追加が1秒以内・1操作で完了する(分類等を聞かない)

### 7.7 EveningCloseView(夜のクローズ)

**目的:** 5分で「今日を締めて明日を予約する」。5ステップのウィザード形式。

1. **今日の結果**(表示のみ): 完了タスク/獲得成果ポイント/効率スコア/recoveryCount(「立て直し◯回」と肯定的に表示)
2. **1行振り返り**: didWell / stuck 各1入力欄
3. **Inbox仕分け**: 未処理アイテムを1件ずつカード表示。AI有効なら §10.4-E の一括分類結果を事前取得し、提案kindとタスク候補をプリセット → [承認][修正][削除]。AI無効なら手動で4分類ボタン
4. **明日の最初の一手(必須・スキップ不可)**: 明日のタスク候補(明日scheduled+期限近い順)から1件選択、または新規作成。AI有効なら §10.4-F が候補3つを提案。選択したタスクを明日の `DayPlan.firstTaskId` に設定し、Top3も同時に確定
5. **明日の準備チェック**: 明日deadline/scheduledのタスクから持ち物・提出物(`kind:'resource'`のリンク含む)を自動リスト化 → チェックして完了

完了で `DayReview.closedAt` 記録+「今日はクローズ済み」バッジをTodayViewに表示。

**受け入れ条件:**
- [ ] ステップ4を飛ばして完了する経路が存在しない
- [ ] クローズ完了の翌朝、MorningLauncherViewに選んだ一手が表示される

### 7.8 SettingsView(設定)

- Gemini APIキー入力(パスワード型・localStorageにのみ保存)/モデル名/各時刻・ポモドーロ設定(§5 Settings)
- [接続テスト]ボタン: 固定の軽いプロンプトを投げて成否表示
- データのエクスポート/インポート(JSONファイル)
- 「AIなしでも全機能が動きます」の注記を表示

---

## 8. コンポーネント仕様(要点のみ)

- **Timer.tsx**: `startedAtIso` を受け取り経過を mm:ss 表示。1秒間隔更新。開始時刻は永続化データ由来(リロード耐性)
- **ProgressRing.tsx**: SVG円弧。`value / max` を受け取る。アニメーション付き(CSS transition)
- **TaskCard.tsx**: NOW用(大)/NEXT・リスト用(小)の2バリアント
- **TabBar.tsx**: 5タブ。現在ビューをハイライト

---

## 9. ビジネスロジック仕様(`src/logic/`)— すべて純関数+Vitestテスト必須

### 9.1 efficiency.ts
```
efficiencyScore(tasks: Task[]): number
  = Σ(done かつ対象日のoutcomePoints) ÷ (Σ(actualMin) / 60)
  actualMin合計が0なら0を返す。小数1位まで。
```

### 9.2 srs.ts
```
nextInterval(current: 1|3|7|14|30, ok: boolean): 1|3|7|14|30
  ok=true → 次段階(30はそのまま30) / ok=false → 1
dueToday(items: ReviewItem[], today: string): ReviewItem[]
```

### 9.3 scheduler.ts
```
backSchedule(task: Task, today: string): string
  // 締切からの逆算: estimateMin<=60 → deadline前日 /
  // <=180 → 2日前から / それ以上 → 3日前から。過去日になる場合はtoday。
suggestBuffer(task: Task): number
  // tagsに 'errand' | 'submit' | 'outing' を含む → 15、それ以外 0
rescheduleToTomorrow(taskIds: string[], data: AppData): AppData
  // scheduledDateを翌日に。翌日が過密(合計estimate>300分)なら翌々日へ
```

### 9.4 pomodoro.ts
```
splitSegments(estimateMin, workMin=25, breakMin=5):
  Array<{type:'work'|'break', min:number}>
  // estimateMin < 45 → [{work, estimateMin}] のみ
```

### 9.5 fallback.ts(AI無効・失敗時)
```
fallbackDecompose(title): {doneCriteria:'', firstStep:'', estimateMin:30, outcomePoints:2}
  // 空を返してフォームで手入力させる(嘘の完了条件を自動生成しない)
fallbackMorningPlan(data): {topThree, firstTaskId}   // deadline昇順→createdAt昇順で3件
fallbackRecovery(data, remainMin): {taskId, shrunkEstimate} // Top3未完了先頭、見積半分
fallbackClassify(item): InboxKind  // URL含む→resource / 「〜する」で終わる→task-candidate / それ以外memo
```

---

## 10. AI統合仕様(`src/ai/`)

### 10.1 方針
- プロバイダ: **Google Gemini API**(無料枠内で運用。ユーザーが自分のキーを設定画面から入力)
- SDKは使わず `fetch`。エンドポイント:
  `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={apiKey}`
- すべての呼び出しで `generationConfig.responseMimeType: "application/json"` と `responseSchema` を指定し、**構造化JSONのみ**を受け取る
- タイムアウト15秒。失敗(ネットワーク/429/パース失敗)時は**必ず `fallback.ts` に切り替え、エラーでUIを止めない**(トースト「AIが使えないため簡易モードで動作中」を1回表示)

### 10.2 client.ts
```typescript
export async function generateJson<T>(opts: {
  systemPrompt: string;
  userPrompt: string;
  schema: object;          // §10.3のスキーマ
  settings: Settings;
}): Promise<T>;             // 失敗時は例外を投げる(呼び出し側でfallback)
```
- リクエストボディ: `{ system_instruction: {parts:[{text}]}, contents: [{role:'user', parts:[{text}]}], generationConfig: { responseMimeType, responseSchema, temperature: 0.4 } }`
- 同一入力のメモ化: `(機能名 + userPrompt)` のハッシュをキーに直近50件を localStorage(`daypilot.aicache`)にキャッシュ

### 10.3 schemas.ts — 機能別レスポンススキーマ(Gemini responseSchema形式)

例: タスク分解(A)
```json
{
  "type": "OBJECT",
  "properties": {
    "title":        {"type": "STRING"},
    "doneCriteria": {"type": "STRING"},
    "firstStep":    {"type": "STRING"},
    "steps":        {"type": "ARRAY", "items": {"type": "STRING"}},
    "estimateMin":  {"type": "INTEGER"},
    "outcomePoints":{"type": "INTEGER"},
    "bufferMin":    {"type": "INTEGER"}
  },
  "required": ["title", "doneCriteria", "firstStep", "estimateMin", "outcomePoints"]
}
```
(B〜Fも同様に §10.4 の出力欄に対応するスキーマを定義すること)

### 10.4 prompts.ts — プロンプト仕様

**共通システムプロンプト(全機能に前置):**
```
あなたは実行支援アシスタント。原則:
- 完了条件は必ず「数値」または「観測可能な状態」で書く(例:「4ページ解いて丸付けまで完了」)
- 「最初の一手」は2分以内に着手できる物理的動作にする(例:「机に問題集を開く」)
- 効率性=一定時間内の成果。成果に直結しない工程は手順から削る
- 移動・準備・休憩が必要なタスクはバッファ時間を見積に含める
- 出力は指定JSONのみ。励ましや前置きは書かない
```

| ID | 機能 | userPromptに含める入力 | 出力(スキーマ対応) |
|---|---|---|---|
| A | タスク分解 | 生テキスト、あれば締切・科目 | title, doneCriteria, firstStep, steps[], estimateMin, outcomePoints(1/2/3/5), bufferMin |
| B | 効率化手順 | タスク全項目+持ち時間 | steps[](3〜5個、各1行)、cutSuggestion(削れる工程の説明) |
| C | 朝プラン生成 | 今日のtodo一覧(id,title,deadline,estimate)+可処分時間 | topThreeIds[], firstTaskId, reason(1行) |
| D | 復帰プラン | 未完了Top3+残り分数 | taskId, shrunkEstimateMin, shrunkCriteria(縮小した完了条件), postponedIds[] |
| E | Inbox一括分類 | 未処理item配列(id,text) | items[]: {id, kind, taskCandidate?: Aと同形} |
| F | 振り返り→明日の一手 | 今日の完了/未完了、didWell、stuck、明日の候補タスク | candidates[]: {taskId or newTask(Aと同形), reason(1行)} 最大3件 |
| G | 週次学習配分 | 科目別 実績/目標、弱点リスト | allocations[]: {subjectId, nextWeekTargetMin, focusWeakPointIds[]} |

**呼び出しタイミング:** A=タスク保存時 / B=タスク詳細の[効率化]ボタン / C=朝ランチャーでfirstTask未設定時 / D=RecoveryModal / E・F=夜クローズ(Eは1回のバッチ) / G=StudyViewの[週次見直し]ボタン。

---

## 11. スタイル指針

- モバイルファースト(375px基準)。max-width 560px 中央寄せ。デスクトップでもスマホ幅レイアウトのままで良い
- CSS変数: `--bg`(#0f172a系ダーク基調)/ `--card` / `--accent`(1色のみ、例 #38bdf8)/ `--danger` は締切表示のみに使用
- フォント: system-ui。NOWカードのfirstStepは24px以上
- `prefers-color-scheme` 対応は不要(ダーク固定で可)
- アニメーションは「タスク完了時のポイント加算」と「NEXT繰り上がり」の2箇所のみ(過剰演出禁止)

---

## 12. 実装フェーズと受け入れ条件

**フェーズ1: 基盤 + 実行ループ(最優先)**
- types.ts / storage.ts / App.tsx / TabBar / TodayView / タスク登録フォーム(AI無しの手入力経路)/ EveningCloseView(ステップ1,2,4のみ)/ MorningLauncherView
- ✅ 条件: 「夜に一手を選ぶ→朝1タップで開始→完了でNEXT繰り上がり→夜閉じる」が通しで動く。`npm run build` と `tsc --noEmit` が通る

**フェーズ2: ロジック層**
- logic/ 全ファイル+Vitestテスト(各関数、正常系+境界)
- ✅ 条件: `npx vitest run` 全パス。効率スコアがTodayView/EveningCloseに表示される

**フェーズ3: AI統合**
- ai/ 全ファイル+SettingsView+機能A,C,D,E,F の組み込み(B,Gは後回し可)
- ✅ 条件: キー未設定でも全画面が動作(fallback経由)。キー設定時、タスク分解が自動補完される。接続テストボタンが機能する

**フェーズ4: カレンダー/学習/Inbox完成**
- CalendarView / StudyView / InboxView / RecoveryModal / 逆算配置・SRS・弱点・決定ログ
- ✅ 条件: §7.4〜7.6の受け入れ条件全て

**フェーズ5: 仕上げ**
- ポモドーロ表示 / ProgressRingアニメーション / エクスポート・インポート / (任意)PWA manifest+アイコン
- ✅ 条件: Lighthouse PWAインストール可能(任意)。全受け入れ条件の再確認

---

## 13. 動作確認シナリオ(実装完了の定義)

1. 初回起動 → TodayViewが空で表示され、エラーが出ない
2. Inboxに「数学勉強する」と入れ、タスク化 →(AI有効なら)完了条件と最初の一手が自動補完される
3. 締切付きタスクを登録 → カレンダーに逆算配置される
4. 夜クローズを完走 → 翌朝(日付変更後)MorningLauncherに一手が出る
5. [プランが崩れた] → 縮小プラン1案 → 承認 → 残タスクが翌日へ移動
6. 学習タスク完了 → 復習登録 → 翌日「今日の復習」に出現
7. APIキーを消す → 全機能がfallbackで動き続ける
8. `daypilot.v1` を書き出し → 削除 → インポートで復元できる

---

## 14. やらないこと(スコープ外)

- ユーザー認証・サーバ・クラウド同期(localStorageのみ)
- 複数人共有・コラボ機能
- 月カレンダー、ドラッグ&ドロップでの予定移動
- ネイティブアプリ化(PWAまで)
- AIとの自由チャットUI(AIは構造化出力の裏方に徹する)

---

## 付録: エージェントに渡すプロンプト例

```
docs/implementation-spec.md を読み、フェーズ1から実装してください。
- 仕様書の型名・ストレージキー・ファイル構成は変更しないこと
- 各フェーズの受け入れ条件を満たしたら、満たした証拠(実行結果)を示してから次のフェーズへ進むこと
- 不明点は仕様書§1の設計原則に沿って自律的に判断すること
```

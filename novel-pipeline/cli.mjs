#!/usr/bin/env node
// 小説生成パイプライン CLI
//
// 使い方:
//   node novel-pipeline/cli.mjs bible [--dry-run] [--force]
//   node novel-pipeline/cli.mjs scene <番号> [--review-stop] [--resume] [--check] [--dry-run] [--no-summary]
//
// 必要な環境変数: ANTHROPIC_API_KEY (--dry-run のときは不要)

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import Anthropic from "@anthropic-ai/sdk";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_MODEL = "claude-opus-4-8";

// ---------- ファイル入出力 ----------

function read(rel) {
  const p = path.join(ROOT, rel);
  if (!fs.existsSync(p)) {
    fail(`ファイルが見つかりません: novel-pipeline/${rel}`);
  }
  return fs.readFileSync(p, "utf8");
}

function readOptional(rel, fallback) {
  const p = path.join(ROOT, rel);
  return fs.existsSync(p) ? fs.readFileSync(p, "utf8") : fallback;
}

function write(rel, content) {
  const p = path.join(ROOT, rel);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, content);
  console.log(`  保存: novel-pipeline/${rel}`);
}

function exists(rel) {
  return fs.existsSync(path.join(ROOT, rel));
}

function fail(msg) {
  console.error(`\nエラー: ${msg}`);
  process.exit(1);
}

// テンプレートの {{KEY}} を実際の資料で置き換える
function fill(template, vars) {
  return template.replace(/\{\{(\w+)\}\}/g, (m, key) => {
    if (!(key in vars)) fail(`テンプレートの ${m} に対応する資料がありません`);
    return vars[key];
  });
}

// ---------- JSONスキーマ(構造化出力用) ----------

const INNER_SCHEMA = {
  type: "object",
  additionalProperties: false,
  properties: {
    scene: { type: "integer" },
    pov_character: { type: "string" },
    characters: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        properties: {
          name: { type: "string" },
          surface_emotion: { type: "string" },
          hidden_emotion: { type: "string" },
          internal_conflict: { type: "string" },
          motivation: { type: "string" },
          body_language: { type: "string" },
        },
        required: [
          "name", "surface_emotion", "hidden_emotion",
          "internal_conflict", "motivation", "body_language",
        ],
      },
    },
    what_to_convey: { type: "string" },
    emotional_arc: { type: "string" },
    reader_feeling: { type: "string" },
    foreshadowing: { type: "array", items: { type: "string" } },
  },
  required: [
    "scene", "pov_character", "characters", "what_to_convey",
    "emotional_arc", "reader_feeling", "foreshadowing",
  ],
};

const PLAN_SCHEMA = {
  type: "object",
  additionalProperties: false,
  properties: {
    scene: { type: "integer" },
    pov: { type: "string" },
    tone: { type: "string" },
    show_vs_tell: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        properties: {
          target: { type: "string" },
          method: { type: "string", enum: ["show", "tell"] },
          direction: { type: "string" },
        },
        required: ["target", "method", "direction"],
      },
    },
    beats: { type: "array", items: { type: "string" } },
    dialogue_ratio: { type: "string" },
    sentence_rhythm: { type: "string" },
    motifs: { type: "array", items: { type: "string" } },
    opening_line_idea: { type: "string" },
    closing_line_idea: { type: "string" },
    avoid: { type: "array", items: { type: "string" } },
  },
  required: [
    "scene", "pov", "tone", "show_vs_tell", "beats", "dialogue_ratio",
    "sentence_rhythm", "motifs", "opening_line_idea", "closing_line_idea", "avoid",
  ],
};

// ---------- API呼び出し ----------

function makeClient() {
  if (!process.env.ANTHROPIC_API_KEY) {
    fail(
      "環境変数 ANTHROPIC_API_KEY が設定されていません。\n" +
      "  export ANTHROPIC_API_KEY=sk-ant-...  を実行してから再度お試しください。\n" +
      "  (APIを呼ばずにプロンプトだけ確認するには --dry-run を付けてください)"
    );
  }
  return new Anthropic();
}

function handleApiError(err) {
  if (err instanceof Anthropic.AuthenticationError) {
    fail("APIキーが無効です。ANTHROPIC_API_KEY を確認してください。");
  } else if (err instanceof Anthropic.RateLimitError) {
    fail("レート制限に達しました。少し待ってから再実行してください。");
  } else if (err instanceof Anthropic.APIError) {
    fail(`APIエラー (${err.status}): ${err.message}`);
  }
  throw err;
}

// JSONを返す段階(構造化出力を使用。パース失敗時は1回だけリトライ)
async function jsonStage(client, model, prompt, schema, label) {
  for (let attempt = 1; attempt <= 2; attempt++) {
    console.log(`\n[${label}] 生成中… (${model})`);
    let response;
    try {
      response = await client.messages.create({
        model,
        max_tokens: 16000,
        thinking: { type: "adaptive" },
        output_config: { format: { type: "json_schema", schema } },
        messages: [{ role: "user", content: prompt }],
      });
    } catch (err) {
      handleApiError(err);
    }
    const text = response.content
      .filter((b) => b.type === "text")
      .map((b) => b.text)
      .join("");
    try {
      return JSON.parse(text);
    } catch {
      if (attempt === 2) fail(`[${label}] JSONの解析に2回失敗しました。`);
      console.log(`[${label}] JSON解析に失敗。リトライします…`);
    }
  }
}

// 本文などのテキストを返す段階(ストリーミングで進捗を表示)
async function textStage(client, model, prompt, label) {
  console.log(`\n[${label}] 生成中… (${model})\n`);
  try {
    const stream = client.messages.stream({
      model,
      max_tokens: 32000,
      thinking: { type: "adaptive" },
      messages: [{ role: "user", content: prompt }],
    });
    stream.on("text", (delta) => process.stdout.write(delta));
    const message = await stream.finalMessage();
    process.stdout.write("\n");
    return message.content
      .filter((b) => b.type === "text")
      .map((b) => b.text)
      .join("");
  } catch (err) {
    handleApiError(err);
  }
}

// ---------- コマンド: bible ----------

async function cmdBible(opts) {
  const events = read("events/scenes.md");
  const prompt = fill(read("templates/bible.md"), { EVENTS_ALL: events });

  if (opts.dryRun) {
    write("output/prompt_bible.md", prompt);
    console.log(
      "\n--dry-run: 組み立てたプロンプトを保存しました。" +
      "\n中身をコピーして別のチャットに貼れば、同じ処理を手動で再現できます。"
    );
    return;
  }

  if (!opts.force && (exists("story_bible.md") || exists("characters.md"))) {
    fail(
      "story_bible.md または characters.md が既に存在します。\n" +
      "  上書きする場合は --force を付けてください。"
    );
  }

  const client = makeClient();
  const out = await textStage(client, opts.model, prompt, "設定資料の生成");

  const bibleMatch = out.match(/===\s*STORY_BIBLE\s*===([\s\S]*?)===\s*CHARACTERS\s*===/);
  const charsMatch = out.match(/===\s*CHARACTERS\s*===([\s\S]*)$/);
  if (!bibleMatch || !charsMatch) {
    write("output/bible_raw.md", out);
    fail("出力の区切り線が見つかりませんでした。output/bible_raw.md を確認して手動で分割してください。");
  }
  write("story_bible.md", bibleMatch[1].trim() + "\n");
  write("characters.md", charsMatch[1].trim() + "\n");
  console.log(
    "\n完了。story_bible.md と characters.md の【要確認】【提案】を確認・編集してから、" +
    "\nscene コマンドに進んでください。"
  );
}

// ---------- コマンド: scene ----------

async function cmdScene(n, opts) {
  const outDir = `output/scene_${n}`;
  const eventFile = `events/scene_${n}.md`;

  if (!exists("story_bible.md") || !exists("characters.md")) {
    fail(
      "story_bible.md / characters.md がまだありません。\n" +
      "  先に設定資料を生成してください:  node novel-pipeline/cli.mjs bible"
    );
  }

  // 資料の読み込み
  const event = read(eventFile);
  const bible = read("story_bible.md");
  const chars = read("characters.md");
  const summary = readOptional("summary.md", "(まだありません — 物語の冒頭)");
  const style = readOptional(
    "style_sample.md",
    "和風ファンタジー。三人称一元視点。硬すぎない現代的な文体。"
  );

  const baseVars = {
    SCENE_NUMBER: String(n),
    EVENT: event,
    STORY_BIBLE: bible,
    CHARACTERS: chars,
    SUMMARY: summary,
    STYLE_SAMPLE: style,
  };

  // --dry-run: 揃っている資料の範囲でプロンプトを組み立てて保存するだけ
  if (opts.dryRun) {
    write(`${outDir}/prompt_01_inner.md`, fill(read("templates/inner_analysis.md"), baseVars));
    if (exists(`${outDir}/01_inner.json`)) {
      const innerJson = read(`${outDir}/01_inner.json`);
      write(`${outDir}/prompt_02_plan.md`,
        fill(read("templates/expression_plan.md"), { ...baseVars, INNER_JSON: innerJson }));
      if (exists(`${outDir}/02_plan.json`)) {
        const planJson = read(`${outDir}/02_plan.json`);
        write(`${outDir}/prompt_03_prose.md`,
          fill(read("templates/prose.md"), { ...baseVars, INNER_JSON: innerJson, PLAN_JSON: planJson }));
        if (exists(`${outDir}/03_prose.md`)) {
          write(`${outDir}/prompt_04_review.md`,
            fill(read("templates/review.md"), {
              ...baseVars, INNER_JSON: innerJson, PLAN_JSON: planJson,
              PROSE: read(`${outDir}/03_prose.md`),
            }));
        }
      }
    }
    console.log(
      "\n--dry-run: 組み立てたプロンプトを保存しました。" +
      "\n中身をコピーして別のチャットに貼れば、同じ処理を手動で再現できます。" +
      "\n(前の段階の出力ファイルがあるほど、後の段階のプロンプトも組み立てられます)"
    );
    return;
  }

  const client = makeClient();

  // 段階1: 内面分析
  let inner;
  if (opts.resume && exists(`${outDir}/01_inner.json`)) {
    console.log(`\n[内面分析] 既存の ${outDir}/01_inner.json を使用(--resume)`);
    try {
      inner = JSON.parse(read(`${outDir}/01_inner.json`));
    } catch {
      fail(`${outDir}/01_inner.json のJSONが壊れています。編集内容を確認してください。`);
    }
  } else {
    const prompt = fill(read("templates/inner_analysis.md"), baseVars);
    inner = await jsonStage(client, opts.model, prompt, INNER_SCHEMA, "内面分析");
    write(`${outDir}/01_inner.json`, JSON.stringify(inner, null, 2));
  }

  if (opts.reviewStop) {
    console.log(
      `\n--review-stop: ここで一時停止します。` +
      `\n${outDir}/01_inner.json を確認・編集してから、次で再開してください:` +
      `\n  node novel-pipeline/cli.mjs scene ${n} --resume`
    );
    return;
  }

  const innerJson = JSON.stringify(inner, null, 2);

  // 段階2: 表現設計
  let plan;
  if (opts.resume && exists(`${outDir}/02_plan.json`)) {
    console.log(`\n[表現設計] 既存の ${outDir}/02_plan.json を使用(--resume)`);
    try {
      plan = JSON.parse(read(`${outDir}/02_plan.json`));
    } catch {
      fail(`${outDir}/02_plan.json のJSONが壊れています。編集内容を確認してください。`);
    }
  } else {
    const prompt = fill(read("templates/expression_plan.md"), { ...baseVars, INNER_JSON: innerJson });
    plan = await jsonStage(client, opts.model, prompt, PLAN_SCHEMA, "表現設計");
    write(`${outDir}/02_plan.json`, JSON.stringify(plan, null, 2));
  }

  const planJson = JSON.stringify(plan, null, 2);

  // 段階3: 本文生成
  const prosePrompt = fill(read("templates/prose.md"), {
    ...baseVars, INNER_JSON: innerJson, PLAN_JSON: planJson,
  });
  const prose = await textStage(client, opts.model, prosePrompt, "本文生成");
  write(`${outDir}/03_prose.md`, prose);

  // オプション: 推敲チェック
  if (opts.check) {
    const reviewPrompt = fill(read("templates/review.md"), {
      ...baseVars, INNER_JSON: innerJson, PLAN_JSON: planJson, PROSE: prose,
    });
    const review = await textStage(client, opts.model, reviewPrompt, "推敲チェック");
    write(`${outDir}/04_review.md`, review);
  }

  // あらすじの更新(次のシーンの資料になる)
  if (!opts.noSummary) {
    const sumPrompt = fill(read("templates/summary_update.md"), {
      SCENE_NUMBER: String(n), PROSE: prose,
    });
    const sceneSummary = await textStage(client, opts.model, sumPrompt, "あらすじ更新");
    const current = readOptional("summary.md", "");
    write("summary.md", `${current.trimEnd()}\n\n## シーン${n}\n\n${sceneSummary.trim()}\n`);
  }

  console.log(`\n完了。本文: novel-pipeline/${outDir}/03_prose.md`);
}

// ---------- エントリポイント ----------

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    "dry-run": { type: "boolean", default: false },
    "review-stop": { type: "boolean", default: false },
    resume: { type: "boolean", default: false },
    check: { type: "boolean", default: false },
    "no-summary": { type: "boolean", default: false },
    force: { type: "boolean", default: false },
    model: { type: "string", default: DEFAULT_MODEL },
  },
});

const opts = {
  dryRun: values["dry-run"],
  reviewStop: values["review-stop"],
  resume: values.resume,
  check: values.check,
  noSummary: values["no-summary"],
  force: values.force,
  model: values.model,
};

const [command, arg] = positionals;

if (command === "bible") {
  await cmdBible(opts);
} else if (command === "scene") {
  const n = Number(arg);
  if (!Number.isInteger(n) || n < 1) fail("シーン番号を指定してください。例: node novel-pipeline/cli.mjs scene 1");
  await cmdScene(n, opts);
} else {
  console.log(`小説生成パイプライン

使い方:
  node novel-pipeline/cli.mjs bible                 設定資料(story_bible.md / characters.md)を生成
  node novel-pipeline/cli.mjs scene <番号>          シーンを生成(内面分析 → 表現設計 → 本文)

オプション:
  --dry-run       APIを呼ばず、組み立てたプロンプトだけ保存(別チャットに貼って手動再現できる)
  --review-stop   内面分析のあとで一時停止(JSONを確認・編集してから --resume で再開)
  --resume        既存の出力ファイルがある段階をスキップして続きから実行
  --check         本文生成後に推敲チェックも実行
  --no-summary    summary.md への追記をしない
  --force         bible: 既存の story_bible.md / characters.md を上書き
  --model <id>    使用モデル(既定: ${DEFAULT_MODEL})

例:
  node novel-pipeline/cli.mjs scene 1 --review-stop   # 分析まで実行して止める
  node novel-pipeline/cli.mjs scene 1 --resume --check # 編集後、続きから本文+チェックまで
`);
}

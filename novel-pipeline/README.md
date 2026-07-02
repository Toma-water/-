# 小説生成パイプライン

「出来事を書く → 心情の推定 → 表現の設計 → 本文化」を自動化するツールとプロンプト集。

```
出来事(自分で書く)
  → ① 設定資料の生成(最初に1回: story_bible.md / characters.md)
  → ② 内面分析(シーンごと・JSON)     ← ここで人間が確認・修正できる
  → ③ 表現設計(シーンごと・JSON)
  → ④ 本文生成
  → ⑤ 推敲チェック(オプション)
```

## 事前準備(自分のPCで1回だけ)

1. Node.js 18以上をインストール
2. このリポジトリをclone(またはpull)して、ブランチを切り替える
3. リポジトリのフォルダで `npm install` を実行
4. AnthropicのAPIキーを取得し、環境変数に設定:
   - Mac/Linux: `export ANTHROPIC_API_KEY=sk-ant-...`
   - Windows(PowerShell): `$env:ANTHROPIC_API_KEY="sk-ant-..."`

## 使い方

すべてリポジトリのルートフォルダで実行します。

### ステップ1: 設定資料を作る(最初に1回)

```
node novel-pipeline/cli.mjs bible
```

`events/scenes.md`(出来事集)から `story_bible.md` と `characters.md` が生成されます。
生成されたファイルを開き、**【要確認】の質問に答え、【提案】を採用/修正**してください。
名前などを確定させるほど、以降の生成が安定します。

### ステップ2: シーンを生成する

おすすめは「分析まで実行 → 確認 → 続きを実行」の2段階:

```
node novel-pipeline/cli.mjs scene 1 --review-stop
```

→ `output/scene_1/01_inner.json`(内面分析)ができて止まります。
中身を読んで、意図と違うところを直接編集してください
(例: `"hidden_emotion": "悔しさ"` → `"諦め"`)。ここが作品の芯になります。

```
node novel-pipeline/cli.mjs scene 1 --resume --check
```

→ 表現設計 → 本文生成 → 推敲チェックまで実行されます。

一気に全部やる場合は `node novel-pipeline/cli.mjs scene 1 --check` だけでOK。

### 出力ファイル

| ファイル | 中身 |
|---|---|
| `output/scene_N/01_inner.json` | 内面分析(感情・伝えたいこと) |
| `output/scene_N/02_plan.json` | 表現設計(視点・show/tell・ビート) |
| `output/scene_N/03_prose.md` | **本文** |
| `output/scene_N/04_review.md` | 推敲チェック(--check時) |
| `summary.md` | あらすじ(シーンを生成するたび自動追記。次のシーンの資料になる) |

### オプション一覧

`node novel-pipeline/cli.mjs` を引数なしで実行するとヘルプが出ます。

## 別のチャットで手動再現する方法

APIを使わず、ChatGPT・Claude・Codexなど任意のチャットで同じ処理を再現できます。

- **方法A(組み立て済みプロンプトを使う)**: `--dry-run` を付けて実行すると、
  資料を埋め込み済みのプロンプトが `output/` に保存されます。
  それをそのままチャットに貼るだけです。
  ```
  node novel-pipeline/cli.mjs bible --dry-run
  node novel-pipeline/cli.mjs scene 1 --dry-run
  ```
  (前の段階の出力ファイルがあるほど、後の段階のプロンプトも組み立てられます)

- **方法B(手動用プロンプトを使う)**: `prompts/01〜05` は人間がコピペで使う前提の
  プロンプトです。指示に従って資料を貼り込んでチャットに送ってください。

## ファイル構成

| ファイル | 役割 |
|---|---|
| `cli.mjs` | パイプライン本体(CLIツール) |
| `events/scenes.md` | 出来事集(全シーンまとめ) |
| `events/scene_1.md` 〜 `scene_7.md` | シーンごとの出来事(CLIが読む) |
| `templates/*.md` | CLIが使うプロンプト(`{{...}}` を資料で置換して送信) |
| `prompts/01〜05_*.md` | 手動チャット用のプロンプト |
| `story_bible.md` / `characters.md` | 設定資料(bibleコマンドで生成→自分で編集) |
| `style_sample.md` | 文体見本(自分の文章を貼ると文体が寄る) |
| `summary.md` | これまでのあらすじ(自動追記) |

## コツ

- **②の内面分析(01_inner.json)は必ず自分で確認・修正してから先へ進む。**
  「かわいそうな子として描かない」等の軸はテンプレートに入れてあるが、
  シーンごとの機微は人間にしか決められない。
- 毎回同じ修正をしていると気づいたら、`templates/` の該当プロンプトに
  ルールとして書き足す(コード変更は不要。次回から反映される)。
- 新しいシーン(8以降)を書くときは `events/scene_8.md` を作って
  `node novel-pipeline/cli.mjs scene 8` を実行するだけ。

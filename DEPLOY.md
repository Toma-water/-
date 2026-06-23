# スマホで使うための公開リンクの作り方

このアプリは **Cloudflare Pages** または **Vercel** で公開できます。
どちらも **リポジトリは非公開のまま**、無料で永続的なリンクが作れます。
GitHubにpushすると自動で更新されます。

> ⚠️ データはブラウザ（デバイス）ごとに保存されます。PCとスマホでデータは共有されません。
> 移したいときは「履歴」画面のJSONエクスポート/インポートを使ってください。

---

## おすすめ: Cloudflare Pages（無料・簡単）

1. https://dash.cloudflare.com/ にアクセスしてサインアップ / ログイン
2. 左メニュー **「Workers & Pages」** → **「Create」** → **「Pages」** タブ
   → **「Connect to Git」**
3. GitHub と連携し、リポジトリ **`Toma-water/-`** を選択
4. ビルド設定を以下のとおり入力:
   - **Production branch**: `claude/nice-feynman-ayq4yd`
     （または main にマージ済みなら `main`）
   - **Framework preset**: `None`（または Vite）
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
5. **「Save and Deploy」** をクリック
6. 数十秒後、`https://〇〇.pages.dev` という公開リンクが発行されます
   → スマホのブラウザでそのリンクを開けばOK！

スマホのホーム画面に追加すると、アプリのように使えます
（Safari/Chrome の「共有」→「ホーム画面に追加」）。

---

## 別案: Vercel

1. https://vercel.com/ にサインアップ / ログイン（GitHubアカウントでログイン推奨）
2. **「Add New...」** → **「Project」**
3. リポジトリ **`Toma-water/-`** を **Import**
4. 設定は `vercel.json` に書いてあるので基本そのままでOK:
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Production Branch を `claude/nice-feynman-ayq4yd` に変更
     （Settings → Git → Production Branch）
5. **「Deploy」** をクリック
6. `https://〇〇.vercel.app` という公開リンクが発行されます

---

## 更新方法

このリポジトリに変更を push するだけで、自動で再ビルド＆公開されます。
（私が変更を push したときも自動反映されます）

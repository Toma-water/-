/**
 * 小説執筆用 Claude サイドバー for Google ドキュメント
 *
 * Googleドキュメントに「Claude」メニューを追加し、
 * 選択範囲のリライト・講評・続きの執筆をドキュメント内で完結させる。
 *
 * 設定資料ドキュメントを指定しておくと、毎回それを文脈として読み込むので
 * 「主人公の姉って誰だっけ」が起きない。
 */

var API_URL = 'https://api.anthropic.com/v1/messages';
var ANTHROPIC_VERSION = '2023-06-01';
var DEFAULT_MODEL = 'claude-opus-5';

// UrlFetchApp はストリーミングできず、応答を待ち切れないと失敗するので
// 対話用途では max_tokens と effort を control する。
var MAX_TOKENS = 8000;
var SETTINGS_DOC_LIMIT = 60000;  // 設定資料から読み込む最大文字数
var BODY_LIMIT = 120000;         // 本文から読み込む最大文字数

// ---------------------------------------------------------------- メニュー

function onOpen() {
  DocumentApp.getUi()
    .createMenu('Claude')
    .addItem('サイドバーを開く', 'showSidebar')
    .addSeparator()
    .addItem('APIキーを設定', 'promptApiKey')
    .addItem('設定資料ドキュメントを指定', 'promptSettingsDoc')
    .addItem('現在の設定を確認', 'showConfig')
    .addToUi();
}

function onInstall() {
  onOpen();
}

function showSidebar() {
  var html = HtmlService.createHtmlOutputFromFile('Sidebar')
    .setTitle('Claude');
  DocumentApp.getUi().showSidebar(html);
}

// ---------------------------------------------------------------- 設定

function props_() {
  return PropertiesService.getUserProperties();
}

function promptApiKey() {
  var ui = DocumentApp.getUi();
  var res = ui.prompt(
    'Anthropic APIキー',
    'console.anthropic.com で発行したキー（sk-ant- で始まる）を貼り付けてください。\n' +
    'キーはこのドキュメントではなく、あなたのアカウントに紐づく非公開領域に保存されます。',
    ui.ButtonSet.OK_CANCEL);
  if (res.getSelectedButton() !== ui.Button.OK) return;
  var key = res.getResponseText().trim();
  if (!key) return;
  props_().setProperty('ANTHROPIC_API_KEY', key);
  ui.alert('保存しました。');
}

function promptSettingsDoc() {
  var ui = DocumentApp.getUi();
  var res = ui.prompt(
    '設定資料ドキュメント',
    '世界観・人物設定をまとめたGoogleドキュメントのURL（またはID）を貼ってください。\n' +
    '毎回の相談で自動的に文脈として読み込まれます。空欄で解除。',
    ui.ButtonSet.OK_CANCEL);
  if (res.getSelectedButton() !== ui.Button.OK) return;
  var raw = res.getResponseText().trim();
  if (!raw) {
    props_().deleteProperty('SETTINGS_DOC_ID');
    ui.alert('設定資料の指定を解除しました。');
    return;
  }
  var id = extractDocId_(raw);
  try {
    var title = DocumentApp.openById(id).getName();
    props_().setProperty('SETTINGS_DOC_ID', id);
    ui.alert('設定資料として「' + title + '」を登録しました。');
  } catch (e) {
    ui.alert('開けませんでした。URLかIDを確認してください。\n' + e.message);
  }
}

function showConfig() {
  var p = props_();
  var key = p.getProperty('ANTHROPIC_API_KEY');
  var docId = p.getProperty('SETTINGS_DOC_ID');
  var settingsName = '(未設定)';
  if (docId) {
    try { settingsName = DocumentApp.openById(docId).getName(); }
    catch (e) { settingsName = '(開けません: ' + docId + ')'; }
  }
  DocumentApp.getUi().alert(
    'APIキー: ' + (key ? '設定済み (' + key.slice(0, 11) + '…)' : '未設定') + '\n' +
    'モデル: ' + (p.getProperty('CLAUDE_MODEL') || DEFAULT_MODEL) + '\n' +
    '設定資料: ' + settingsName);
}

function extractDocId_(raw) {
  var m = raw.match(/\/document\/d\/([a-zA-Z0-9_-]+)/);
  return m ? m[1] : raw;
}

/** サイドバー起動時の状態確認 */
function getStatus() {
  var p = props_();
  var docId = p.getProperty('SETTINGS_DOC_ID');
  var settingsName = null;
  if (docId) {
    try { settingsName = DocumentApp.openById(docId).getName(); } catch (e) {}
  }
  return {
    hasKey: !!p.getProperty('ANTHROPIC_API_KEY'),
    model: p.getProperty('CLAUDE_MODEL') || DEFAULT_MODEL,
    settingsName: settingsName
  };
}

// ---------------------------------------------------------------- 本文の読み書き

/** 選択範囲のテキストを返す。未選択なら空文字。 */
function getSelectionText_() {
  var sel = DocumentApp.getActiveDocument().getSelection();
  if (!sel) return '';
  var out = [];
  var els = sel.getRangeElements();
  for (var i = 0; i < els.length; i++) {
    var re = els[i];
    var el = re.getElement();
    if (!el.editAsText) continue;
    var text = el.asText().getText();
    out.push(re.isPartial()
      ? text.substring(re.getStartOffset(), re.getEndOffsetInclusive() + 1)
      : text);
  }
  return out.join('\n');
}

function getSelectionInfo() {
  var t = getSelectionText_();
  return { hasSelection: !!t, length: t.length, preview: t.slice(0, 80) };
}

/**
 * 選択範囲を newText で置き換える。
 * 複数段落にまたがる場合、先頭の段落に新しい本文を入れ、残りの段落は削除する。
 */
function replaceSelection(newText) {
  var doc = DocumentApp.getActiveDocument();
  var sel = doc.getSelection();
  if (!sel) throw new Error('置き換えたい範囲を選択してから実行してください。');

  var els = sel.getRangeElements();

  // 末尾側から処理する（先に消すと先頭要素のオフセットが狂わないため）
  for (var i = els.length - 1; i >= 0; i--) {
    var re = els[i];
    var el = re.getElement();
    if (!el.editAsText) continue;
    var t = el.editAsText();

    if (re.isPartial()) {
      t.deleteText(re.getStartOffset(), re.getEndOffsetInclusive());
      if (i === 0) t.insertText(re.getStartOffset(), newText);
    } else {
      if (i > 0) {
        // 完全に選択された途中の段落は丸ごと消す
        try { el.removeFromParent(); continue; } catch (e) { /* 消せない場合は下へ */ }
      }
      var len = t.getText().length;
      if (len > 0) t.deleteText(0, len - 1);
      if (i === 0) t.insertText(0, newText);
    }
  }
  return true;
}

/** カーソル位置（または本文末尾）に挿入する。 */
function insertAtCursor(text) {
  var doc = DocumentApp.getActiveDocument();
  var cursor = doc.getCursor();
  if (cursor) {
    var el = cursor.insertText(text);
    if (el) return true;
  }
  doc.getBody().appendParagraph(text);
  return true;
}

// ---------------------------------------------------------------- Claude 呼び出し

var ROLE_PROMPT =
  'あなたは日本語のライトノベルを担当する編集者兼共作者です。作者の相談相手として振る舞ってください。\n' +
  '\n' +
  '守ること:\n' +
  '- 作者の文体・語り手の人称・作品の温度感を尊重する。勝手に整えない。\n' +
  '- 指摘するときは「どこが」「なぜ」弱いのかを具体的に言う。褒めるだけの感想は要らない。\n' +
  '- リライトを頼まれたら、前置きも解説も付けず、本文だけを出力する。かぎ括弧や地の文の記法は原文に合わせる。\n' +
  '- 講評を頼まれたら本文は書き直さず、指摘だけを返す。\n' +
  '- 設定資料が与えられている場合、固有名詞・年齢・時系列の矛盾があれば必ず指摘する。\n' +
  '- 分からないことを推測で埋めない。作者に確認すべき点は質問として挙げる。';

var MODE_PROMPT = {
  rewrite:  '【依頼】選択範囲を書き直してください。出力は書き直した本文のみ。説明・前置き・締めの言葉は一切書かないこと。',
  critique: '【依頼】選択範囲を講評してください。本文の書き直しはしないこと。弱い箇所を具体的に指摘し、直す方向性だけ示してください。',
  continue: '【依頼】選択範囲（またはカーソル直前）に続く本文を書いてください。出力は本文のみ。説明・前置きは書かないこと。',
  chat:     '【依頼】以下の相談に答えてください。'
};

/** サイドバーから呼ばれるメイン関数 */
function ask(mode, instruction) {
  var p = props_();
  var key = p.getProperty('ANTHROPIC_API_KEY');
  if (!key) throw new Error('APIキーが未設定です。メニューの「Claude ▸ APIキーを設定」から登録してください。');

  var doc = DocumentApp.getActiveDocument();
  var selection = getSelectionText_();
  var body = doc.getBody().getText();

  if ((mode === 'rewrite' || mode === 'critique') && !selection) {
    throw new Error('本文を選択してから実行してください。');
  }

  // --- system: 役割 + 設定資料（毎回同じなのでキャッシュが効く）
  var system = ROLE_PROMPT;
  var settings = readSettingsDoc_();
  if (settings) {
    system += '\n\n----- 作品の設定資料（正典。ここと矛盾する記述は指摘すること） -----\n' + settings;
  }

  // --- user: 本文 + 選択範囲 + 指示
  var parts = [];
  parts.push('----- 執筆中の原稿（ドキュメント「' + doc.getName() + '」全文） -----');
  parts.push(truncate_(body, BODY_LIMIT));
  if (selection) {
    parts.push('\n----- いま選択している箇所 -----');
    parts.push(selection);
  }
  parts.push('\n' + (MODE_PROMPT[mode] || MODE_PROMPT.chat));
  if (instruction) parts.push('\n【作者からの指示】\n' + instruction);

  var effort = (mode === 'critique') ? 'medium' : 'low';

  var payload = {
    model: p.getProperty('CLAUDE_MODEL') || DEFAULT_MODEL,
    max_tokens: MAX_TOKENS,
    output_config: { effort: effort },
    system: [{ type: 'text', text: system, cache_control: { type: 'ephemeral' } }],
    messages: [{ role: 'user', content: parts.join('\n') }]
  };

  var res = UrlFetchApp.fetch(API_URL, {
    method: 'post',
    contentType: 'application/json',
    headers: { 'x-api-key': key, 'anthropic-version': ANTHROPIC_VERSION },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  var code = res.getResponseCode();
  var raw = res.getContentText();
  var data;
  try { data = JSON.parse(raw); }
  catch (e) { throw new Error('応答を解釈できませんでした (HTTP ' + code + ')'); }

  if (code === 401) throw new Error('APIキーが拒否されました。キーを確認してください。');
  if (code === 429) throw new Error('レート制限です。少し待ってからもう一度。');
  if (code !== 200) {
    throw new Error('APIエラー ' + code + ': ' + ((data.error && data.error.message) || raw.slice(0, 300)));
  }
  if (data.stop_reason === 'refusal') {
    throw new Error('この内容には応答できないと判断されました。表現を変えて試してください。');
  }

  var text = (data.content || [])
    .filter(function (b) { return b.type === 'text'; })
    .map(function (b) { return b.text; })
    .join('');

  return {
    text: text,
    truncated: data.stop_reason === 'max_tokens',
    usage: data.usage || null
  };
}

function readSettingsDoc_() {
  var id = props_().getProperty('SETTINGS_DOC_ID');
  if (!id) return null;
  try {
    return truncate_(DocumentApp.openById(id).getBody().getText(), SETTINGS_DOC_LIMIT);
  } catch (e) {
    return null;
  }
}

function truncate_(s, limit) {
  if (!s) return '';
  return s.length <= limit ? s : s.slice(0, limit) + '\n…（以下省略）';
}

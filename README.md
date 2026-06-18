# PairRadioListening（ペア・ラジオ・リスニング）

講演動画などで、1人で聞きつつAIと学びや思考の壁打ちができるプロダクトです。

## 1. 目的

### 開発の背景と価値

* 講義・講演を1人で聞いている時に感想や疑問が湧いてきても、誰かと共有して壁打ちするのは難しいという課題があります。
* 課題を解決するために、単なる文字起こしと要約だけではなく「学びをより楽しく、思考をより深くする壁打ち相手」を届けます。
* 1人だけでも、AIとの雑談や議論を通じて、学びを「自分ごと」として深く落とし込める体験を提供します。

## 2. コア機能

講義・講演を1人で視聴しながら、タイムライン上でユーザーとAIがリアクションし、学びを深める壁打ち体験を提供する。

### 発話内容の文字起こし
* AmiVoice により発話内容を書き起こし、文字起こし画面に表示する機能
* 講義・講演の発話内容の把握、聞き逃した部分を遡り、AIと壁打ちできるようにするため

### タイムラインへの投稿
* 視聴しているユーザーが、感想や学び、疑問などを書き殴って投稿する機能
* 感想や学び、疑問を曖昧でも投稿することで、思考の外化を促せるようにするため
  
### AIとの壁打ち
* 講義・講演の発話内容やユーザーの投稿に応じて、AIがタイムライン上でリアクションする機能
* ユーザーに「学びを楽しく、思考を深くする壁打ち相手」を、講義・講演の進行に同期して届けるため

## 3. 構成

### エンティティ層
* `domain/entities`: システムの中心にある最も安定したルールを定義
* `domain/value_object`: 属性によって定義される不変なオブジェクトを定義
* `domain/services`: 複数の値オブジェクトやエンティティに跨ぐドメインロジックを定義
* 仕様: [docs/spec/domain.md](docs/spec/domain.md)

### アプリケーション層
* `application/use_cases`: 1 操作単位のユースケースを定義
* `application/dtos`: 各ユースケースの Request / Response を定義
* `application/ports`: 永続化・外部サービスとの Outbound Port（Protocol）を定義
* `application/errors`: ユースケースが返す標準エラーを定義
* * 仕様: [docs/spec/application.md](docs/spec/application.md)

### インターフェイスアダプター層
* `interface_adapters/controllers`: 外部入力の検証・変換とユースケース呼び出し（Command / Query refresh）
* `interface_adapters/presenters`: Query レスポンスの ViewModel 反映（Humble Object）
* `interface_adapters/mappers`: 表示用 ViewModel への変換（テスト可能な純粋変換）
* `interface_adapters/view_models`: UI が bind する表示専用状態
* `interface_adapters/orchestrators`: 非同期 AI 生成 UC の起動と対話パネル refresh
* `interface_adapters/events` / `interface_adapters/outcomes`: Controller の入出力 DTO
* `interface_adapters/ports`: ViewModel 更新先・バックグラウンドタスク等の Protocol
* `interface_adapters/presentation`: 時刻ラベル・エラー文言などの表示定数
* 仕様: [docs/spec/interface.md](docs/spec/interface.md)

### フレームワーク&ドライバー層
* `framework/`: FastAPI（HTTP API・Composition root・AmiVoice WebSocket Bridge 等）
* `infrastructure/`: リポジトリ・LLM 等の Outbound ドライバ（MVP は in-memory + LLM アダプタ）
* `frontend/`: Vue 3 + TypeScript + Vite（SPA。Python パッケージ外）
* 仕様: [docs/spec/framework.md](docs/spec/framework.md)、[AmiVoice](docs/spec/framework_amivoice.md)、[LLM（Gemini）](docs/spec/framework_llm.md)
* **AI 壁打ち:** ユーザー投稿時のみ。LLM には投稿時点の **1 分前までの書き起こし（最大 15 区間）** と返信先を渡す（`framework_llm.md` §3）
* **MVP 運用:** ローカル 1 人・**localhost のみ**（API をインターネット公開しない）。音声は VB-Cable 経由で YouTube / Zoom 等からキャプチャ

## 4. 技術スタック

### バックエンド
* Python 3.13.1
* FastAPI

#### ローカル起動（バックエンド API）

1. 依存のインストール（プロジェクトルート）:

```bash
uv sync
```

2. 秘密情報の設定（**localhost のみ**で利用。`.env` はコミットしない）:

```bash
cp .env.example .env
# .env を編集: Phase1c AMIVOICE_API_KEY、Phase3 以降 GEMINI_API_KEY 等
```

**Phase1c — ライブ文字起こし（VB-Cable → AmiVoice）**

| 項目 | 内容 |
|------|------|
| 必須 | `.env` に `AMIVOICE_API_KEY`（[AmiVoice マイページ](https://docs.amivoice.com/) の API キー） |
| 任意 | `AMIVOICE_PROXY_SERVER_NAME`（社内プロキシ必須時。Wrp 形式 `user:password@proxyhost:port`） |
| 任意 | `AUDIO_CAPTURE_DEVICE`（省略時 **VB-Cable** / **CABLE Output** 等を自動探索） |
| 任意 | `AMIVOICE_GRAMMAR_FILE_NAMES`（接続エンジン。省略時 `-a2-ja-general`） |
| 任意 | `AMIVOICE_WS_URL`（省略時 `wss://acp-api.amivoice.com/v1/`。末尾 `/` 必須） |
| 任意 | `AMIVOICE_RECEIVE_TIMEOUT_MS`（受信タイムアウト ms。`0` で無効、既定 `0`） |
| 任意 | `AMIVOICE_SPEAKER_DISPLAY_NAME`（文字起こし行の話者表示名。既定: 講師） |

AmiVoice 接続は公式 **Wrp** クライアントを `third_party/amivoice_wrp` に vendor して利用します（`websocket-client` 自前実装は廃止）。

**OS 音声設定（macOS 例）**

1. [VB-Audio Virtual Cable](https://vb-audio.com/Cable/) をインストールする
2. システム設定 → サウンド → 出力を **VB-Audio Virtual Cable (Input)** にする（YouTube / Zoom 等の再生音がケーブルへ入る）
3. PairRadioListening は **VB-Cable**（macOS）または **CABLE Output**（Windows）などのキャプチャ端子から PCM を読み取る

`AMIVOICE_API_KEY` が **未設定** のときはライブ WS・キャプチャは起動せず、開発用の `POST /internal/amivoice/utterances` のみ利用可能です。

**手動受入（Phase1c）**

1. 上記のとおり VB-Cable と `.env` を設定する（社内プロキシ必須なら `AMIVOICE_PROXY_SERVER_NAME` も設定）
2. バックエンド・フロントエンドを起動する
3. 別ウィンドウで YouTube 講義動画などを再生する（出力先は VB-Cable Input）
4. フロントで **講義開始** → 数秒〜数十秒以内に左パネル（文字起こし）に発話が追加されること
5. サーバログに Wrp の connect / feedDataResume 成功、`resultFinalized` 受信が出ること
6. **講義終了** で AmiVoice セッションが閉じること

3. API サーバー起動:

```bash
uv run uvicorn framework.bootstrap:app --host 127.0.0.1 --port 8000
```

**AmiVoice の切り分けログ:** `.env` に `AMIVOICE_DEBUG=1` を入れると `framework.amivoice` 配下が DEBUG 出力されます（接続・PCM 送信・`resultFinalized`・`record_utterance`）。API キー本体はログに出しません。

`GET http://127.0.0.1:8000/health` が `{"status":"ok"}` を返せば Phase0 基盤は起動できている。

### フロントエンド
* Vue 3 + TypeScript + Vite

#### ローカル起動

```
source .venv/bin/activate
cd frontend
pnpm install
pnpm dev
```

ブラウザで `http://localhost:5173` を開く。デフォルトで FastAPI（`http://127.0.0.1:8000`）へ接続し、講義開始後に文字起こし・対話パネルをポーリング更新する。開発時にモック表示のみ試す場合は画面上の「バックエンド API 接続」をオフにする。

#### テスト（Phase1c）

```bash
uv run pytest -m "phase1c and not integration" -v   # CI 相当（Wrp 単体・Fake キャプチャ）
uv run pytest -m phase1c -v                         # integration 含む（実キー・VB-Cable は任意）
```

**Phase2 — タイムライン投稿**

| 項目 | 内容 |
|------|------|
| 前提 | Phase1 と同様にバックエンド・フロント起動。講義 `active` 中 |
| スコープ | ユーザー投稿 → 対話パネルに自分の行（話者・本文・時刻ラベル）。`latest_anchor_ms` による anchor 自動設定 |
| スコープ外 | `reply_target` UI 選択、投稿編集・削除 |

**手動受入（Phase2）**

1. バックエンド・フロントエンドを起動する
2. **講義開始** → 文字起こしが 1 件以上あること（AmiVoice または `POST /internal/amivoice/utterances`）
3. 感想を入力して **投稿** → 右パネル（対話）に自分の行が表示され、本文の下に時刻ラベルが右寄せで出ること
4. 文字起こし 0 件の間は投稿ボタンが無効であること
5. **講義終了** 後は投稿できないこと

#### テスト（Phase2）

```bash
uv run pytest -m phase2 -v
```

**Phase3 — AI との壁打ち**

| 項目 | 内容 |
|------|------|
| 必須 | `.env` に `LLM_API_KEY` または `GEMINI_API_KEY`（[Google AI Studio](https://aistudio.google.com/) の API キー） |
| 任意 | `LLM_MODEL`（省略時 `gemini-3.1-flash-lite`） |
| 任意 | `LLM_RPM_LIMIT` / `LLM_RPD_LIMIT`（省略時 15 / 500） |
| 前提 | Phase2 と同様にバックエンド・フロント起動。講義 `active` 中 |
| スコープ | ユーザー投稿成功後、非同期で AI `reaction` が 1 件生成され対話パネルに表示。`reference_quote_label` でユーザー投稿を参照 |
| スコープ外 | 講師発話トリガーの AI 生成、`reply_target` UI 選択（Phase4） |

**手動受入（Phase3）**

1. `.env` に LLM API キーを設定し、バックエンド・フロントエンドを起動する
2. **講義開始** → 文字起こしが 1 件以上あること
3. 感想を **投稿** → 直後は対話パネルにユーザー行のみ表示されること
4. 数秒以内に AI 行が追加され、ユーザー投稿への `reference_quote_label` が表示されること
5. 文字起こし（`record_utterance`）のみでは AI 行が増えないこと

#### テスト（Phase3）

```bash
uv run pytest -m phase3 -v
```

**社内プロキシ環境:** AmiVoice 接続は Wrp の `setProxyServerName` に `.env` の `AMIVOICE_PROXY_SERVER_NAME`（`user:password@proxyhost:port`）を渡します。`HTTP_PROXY` からの自動合成は行いません。

### インフラ
* 未決定

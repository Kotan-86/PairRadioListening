# フレームワーク&ドライバー層仕様

<!-- 関連: docs/spec/domain.md, docs/spec/application.md, docs/spec/interface.md, docs/spec/framework_amivoice.md, docs/spec/framework_llm.md -->

PairRadioListening のフレームワーク&ドライバー層（FastAPI・外部 API ドライバ・Composition root・フロントエンド SPA）の仕様を定義する。ビジネスルールは `domain.md`、ユースケース契約は `application.md`、入力変換・表示契約は `interface.md` に従う。

**命名（Python）:** 識別子は **snake_case** で表記する。HTTP JSON も snake_case とし、フロントエンド TypeScript の型定義はこれに合わせる。

## 1. 概要

- 最も外側の層として、外界（ブラウザ UI・AmiVoice・LLM・永続化）とのやり取りを担う
- バックエンドの HTTP 軸は **FastAPI**。フロントエンドは **別プロセス・別言語**（**Vue 3 + TypeScript + Vite**）とする
- Inbound は HTTP ルートまたは AmiVoice Bridge（プロセス内）から `interface.md` の Port / event を呼び出す。Outbound は `application.md` の Port および Domain の `LlmAnalyzerProtocol` を実装する
- **Composition root** がユースケース・Controller・Presenter・ドライバを組み立て、API キー等の秘密情報はここでのみ読み込む

### 1.1 設計原則

| 原則 | 内容 |
|------|------|
| 最外層 | ユーザーインターフェイス（Web API・SPA）、データベース／リポジトリ、外部サービス（AmiVoice・LLM）、将来のファイル入出力を本層で接続する |
| 依存関係ルール | 依存の向きは **外→内**。Framework は `interface_adapters` / `application` / `infrastructure` を呼ぶ。内側は Framework の型・ルート・SDK を import しない |
| 交換可能性 | 具体技術（FastAPI、Vue、AmiVoice、LLM ベンダー、in-memory ↔ DB）は差し替え可能。契約は Port・HTTP JSON・`interface.md` の event / outcome / ViewModel に置く |

**Why（Interface 層の内側に置かない）:** HTTP ステータス・CORS・SDK・環境変数はビジネス関心事ではなく、技術詳細であるため。

### 1.2 MVP 技術選定

| 領域 | 採用 | 配置（概念） |
|------|------|-------------|
| HTTP API・Composition root | **FastAPI**（Python 3.13） | `framework/` |
| SPA | **Vue 3 + TypeScript + Vite** | `frontend/`（リポジトリ直下。Python パッケージ外） |
| 永続化（MVP） | 既存 `infrastructure/repositories`（in-memory） | `infrastructure/` |
| 音声認識 | **AmiVoice**（WebSocket クライアント） | `framework/`（`framework_amivoice.md`） |
| LLM | **Gemini 3.1 Flash-Lite**（`framework_llm.md`） | Outbound ドライバ |

**スタイル（フロント）:** CSS は **最小**とする。Tailwind 等は任意（採用しても Discord 的なコンポーネントライブラリは使わない）。UI フレームワークは Vue 3 + TypeScript + Vite に限定する。

### 1.3 UI 方針（MVP）

| 項目 | 内容 |
|------|------|
| レイアウト | **2 カラム**：文字起こしパネル｜対話パネル。下部に講義操作・投稿フォーム |
| 対話表示 | **フラットリスト**（`interface.md` §1.3・§7.4）。スレッドツリー・リッチエディタ・Discord 的な作り込みは **不要** |
| データ源 | フロントは `transcript_view_model` / `dialogue_view_model` の JSON のみ bind（§7） |
| 更新 | MVP は **ポーリング**（例: 2〜3 秒間隔で GET refresh）。WebSocket / SSE は将来 |

**Why:** コア価値は壁打ち体験であり、UI の装飾より Interface / Application の正しさを優先するため。

### 1.4 秘密情報と設定

| 項目 | 内容 |
|------|------|
| 読み込み場所 | Composition root 起動時のみ（`.env` ・環境変数） |
| 例 | `AMIVOICE_API_KEY`、`GEMINI_API_KEY` / `LLM_API_KEY`、`LLM_MODEL`（`framework_llm.md` §6.3） |
| 禁止 | リポジトリへのコミット、フロントエンドへの埋め込み、Domain / Application / Interface 層での参照 |
| 失敗時 | キー未設定で外部ドライバが使えない場合、起動時または初回呼び出しで明確に失敗させる（サイレント無効化しない） |

### 1.5 プロダクト前提（MVP）

| ID | 内容 |
|----|------|
| 0-1 | **ローカル 1 人**利用。アプリは **インターネット公開しない**（API 料金リスク回避）。ソースは GitHub 公開可 |
| 0-2 | 音声源は **YouTube / Zoom PC アプリ** 等の再生音声（**VB-Cable** 経由でキャプチャ） |
| 0-3 | 講義動画は別ウィンドウで再生。**`lecture_time_anchor` は utterance 時間軸と同期**（動画 `currentTime` 自動連動は MVP 不要） |
| 0-4 | MVP は **オンライン必須**（AmiVoice・LLM） |
| 0-5 | 1 講義 **30〜60 分** |

**Why:** デプロイ形態と音声経路を Framework 層の境界条件として固定し、Webhook 公開やマルチテナントを MVP から除外するため。

## 2. コンポーネント一覧（MVP）

### 2.1 Inbound ドライバ一覧

| 名前 | 外界 | 接続先（Interface） | 詳細 |
|------|------|---------------------|------|
| `http_api_router` | ブラウザ（Vue SPA） | 各 Port を呼ぶ HTTP ハンドラ | §4 |
| `amivoice_streaming_bridge` | AmiVoice API（WS）・VB-Cable | `transcription_port.on_utterance` | `framework_amivoice.md` |
| `amivoice_utterance_http_handler`（任意） | 手動テスト | 同上 | §4.3・§6.1 |

### 2.2 Outbound ドライバ一覧

| 名前 | 外界 | 実装する Port / Protocol | 詳細 |
|------|------|------------------------|------|
| `in_memory_lecture_repository` | メモリ | `LectureRepository` | 既存 `infrastructure/` |
| `in_memory_reaction_repository` | メモリ | `ReactionRepository` | 既存 `infrastructure/` |
| `gemini_llm_analyzer_driver` | Gemini API | `LlmAnalyzerProtocol` | `framework_llm.md` §6.1 |
| `gemini_reaction_text_generator` | Gemini API | `ReactionTextGeneratorPort` | `framework_llm.md` §6.2 |
| `llm_rate_limiter` | （内部） | — | `framework_llm.md` §5.2 |
| `background_task_scheduler` | プロセス内スレッド等 | `background_task_port`（`interface.md` §8） | §6.4 |

### 2.3 HTTP API 一覧（MVP）

| メソッド | パス | Interface 経路 | レスポンス |
|--------|------|----------------|------------|
| `POST` | `/api/lectures/start` | `lecture_session_port.start` | `start_lecture_outcome` JSON |
| `POST` | `/api/lectures/{lecture_id}/end` | `lecture_session_port.end` | `end_lecture_outcome` JSON |
| `POST` | `/api/lectures/{lecture_id}/reactions` | `user_reaction_port.on_submit` | `post_user_reaction_outcome` JSON |
| `GET` | `/api/lectures/{lecture_id}/transcript` | `transcript_view_port.refresh` | `transcript_view_model` JSON |
| `GET` | `/api/lectures/{lecture_id}/dialogue` | `dialogue_view_port.refresh` | `dialogue_view_model` JSON |
| `POST` | `/internal/amivoice/utterances`（任意） | `transcription_port.on_utterance` | `record_utterance_outcome` JSON（手動テスト用） |

**備考:** `generate_ai_*` 用の公開 HTTP エンドポイントは **持たない**（`interface.md` §2.1）。AI 生成は Orchestrator 経由の内部 UC のみ。

**AmiVoice 主経路:** `amivoice_streaming_bridge` がプロセス内で `transcription_port` を呼ぶ（`framework_amivoice.md`）。上記 internal POST は **必須ではない**。

### 2.4 フロントエンド（Vue）一覧

| コンポーネント | 責務 | 詳細 |
|---------------|------|------|
| `App.vue` | 2 カラムレイアウト・講義状態 | §7 |
| `TranscriptPanel` | `transcript_view_model` の bind | §7.2 |
| `DialoguePanel` | `dialogue_view_model` の bind | §7.2 |
| `LectureControls` | 開始・終了 API 呼び出し | §4.1・§4.2 |
| `ReactionForm` | 投稿 API 呼び出し | §4.4 |
| `apiClient` | FastAPI への fetch ラッパ | §7.1 |
| `pollingService` | 講義中の transcript / dialogue GET | §7.3 |

### 2.5 Composition root

| 名前 | 責務 | 詳細 |
|------|------|------|
| `create_app` / `bootstrap` | FastAPI アプリ生成・DI 配線・ルータ登録 | §5 |

## 3. HTTP API 共通規約

### 3.1 Command：`Outcome` → HTTP

| `success` | HTTP ステータス（MVP） |
|-----------|------------------------|
| `true` | `200`（または `201`：`start` のみ） |
| `false` | `error_kind` に応じて 4xx / 5xx（下表） |

| `error_kind`（例） | HTTP |
|--------------------|------|
| `invalid_request` | `400` |
| `lecture_not_found` | `404` |
| `lecture_closed` / `lecture_already_closed` | `409` |
| `timeline_not_established` / `reply_target_not_found` | `409` または `400` |
| `invalid_persona_profiles` | `400` |
| `persistence_failed` / 外部サービス失敗 | `503` |

レスポンスボディは対応する `*_outcome` JSON とする（`interface.md` §3.3）。**本文テキストは含めない**。

### 3.2 Query：ViewModel JSON

| 項目 | 内容 |
|------|------|
| 成功 | `200`。ボディは `transcript_view_model` または `dialogue_view_model`（`interface.md` §7） |
| refresh 失敗 | `present_error` 済み ViewModel を返す：`lines=[]`、`error_message` 非空（§7.2） |
| スキーマ | OpenAPI（FastAPI 自動生成）でフロント TypeScript 型と同期する |

### 3.3 CORS と静的ファイル

| 項目 | MVP |
|------|-----|
| CORS | Vue 開発サーバー（Vite 既定オリジン）から FastAPI への呼び出しを許可 |
| 本番 | 同一オリジン配信（FastAPI が `frontend` ビルド成果物を配信）またはリバースプロキシで統一 |

### 3.4 セッションと `lecture_id`

| 項目 | 内容 |
|------|------|
| 講義 ID | `start_lecture` 成功後の `lecture_id` をフロントが保持し、以降のパスに付与する |
| 認証 | MVP では **なし**（単一ユーザー・**localhost のみ**でバインド） |
| 公開 | **インターネット向けに API を公開しない**（§1.5 0-1） |

## 4. HTTP API 詳細

### 4.1 `POST /api/lectures/start`

<!-- 仕様: docs/spec/interface.md#start_lecture_controller -->

* 意図: 講義セッションを開始する
* ハンドラ: `start_lecture_form_event` を組み立て → `lecture_session_port.start`

#### リクエストボディ

| フィールド | 型 | 必須 | 説明 |
|------------|-----|------|------|
| `persona_profiles` | 配列 | ○ | MVP では **1 件**（`application.md`） |
| `title` | 文字列 | × | 表示用タイトル |

#### レスポンス

`start_lecture_outcome`（`lecture_id` をフロントが保存）

---

### 4.2 `POST /api/lectures/{lecture_id}/end`

<!-- 仕様: docs/spec/interface.md#end_lecture_controller -->

* 意図: 講義を終了する
* 入力: パス `lecture_id` → `end_lecture_session_event`

#### レスポンス

`end_lecture_outcome`

---

### 4.3 `POST /internal/amivoice/utterances`（任意）

<!-- 仕様: docs/spec/interface.md#record_utterance_controller -->

* 意図: **手動テスト**用に `speech_recognition_utterance_event` 相当の JSON を注入し 1 発話を記録する
* 主経路: 本番の AmiVoice 連携は **`amivoice_streaming_bridge`**（`framework_amivoice.md`）。本エンドポイントは Bridge 未接続時の検証用
* ハンドラ: リクエストボディ → `speech_recognition_utterance_event` → `transcription_port.on_utterance`
* 認証: localhost のみバインド（§3.4）

#### レスポンス

`record_utterance_outcome`（AI 生成の成否は含めない）

**副作用:** なし（MVP では発話記録は文字起こしのみ。AI はユーザー投稿時のみ `framework_llm.md` §2）。

---

### 4.4 `POST /api/lectures/{lecture_id}/reactions`

<!-- 仕様: docs/spec/interface.md#post_user_reaction_controller -->

* 意図: ユーザー投稿を記録する

#### リクエストボディ

| フィールド | 型 | 必須 | 説明 |
|------------|-----|------|------|
| `reaction_text` | 文字列 | ○ | 投稿本文 |
| `lecture_time_anchor` | 整数（ms） | ○ | 投稿時点の講義時間軸 |
| `speaker_display_name` | 文字列 | ○ | 表示名 |
| `reply_target` | オブジェクト | × | 省略時は UC が直近 `utterance` を使用 |

#### レスポンス

`post_user_reaction_outcome`

---

### 4.5 `GET /api/lectures/{lecture_id}/transcript`

<!-- 仕様: docs/spec/interface.md#refresh_transcript_controller -->

* 意図: 文字起こしパネル用 ViewModel を返す
* ハンドラ: `transcript_view_port.refresh` → 最新 `transcript_view_model` JSON

---

### 4.6 `GET /api/lectures/{lecture_id}/dialogue`

<!-- 仕様: docs/spec/interface.md#refresh_dialogue_controller -->

* 意図: 対話パネル用 ViewModel を返す
* ハンドラ: `dialogue_view_port.refresh` → 最新 `dialogue_view_model` JSON

## 5. Composition root 詳細

### 5.1 責務

1. 設定（環境変数）の読み込み
2. Outbound ドライバの生成（リポジトリ・LLM・スケジューラ）
3. Domain サービス（`LecturerReactionGenerator` 等）への `LlmAnalyzer` 注入
4. Application ユースケースの生成
5. Interface 層（Controller・Presenter・Orchestrator）の生成と Port 実装の接続
6. FastAPI ルータへの登録

### 5.2 配線（概念）

```
create_app()
  → repositories (in_memory)
  → gemini_llm_*_driver, llm_rate_limiter（framework_llm.md）
  → use_cases(...)
  → controllers(..., orchestrator=...)
  → amivoice_streaming_bridge(transcription_port, audio_capture_source)
  → http_api_router(deps)
  → FastAPI include_router
  → start_lecture / end_lecture 成功時に Bridge セッション同期（framework_amivoice.md §4.2）
```

**禁止:** ルートハンドラ内での `UseCase()` の `new`。`execute` 以外のビジネス分岐。

### 5.3 `ViewModelStore` の HTTP 実装

| 項目 | 内容 |
|------|------|
| 方式 | 講義 ID ごとに最新 ViewModel を保持するインメモリ Store、または refresh 都度 GET ハンドラ内で組み立て |
| `GET` | Store のスナップショットを JSON 化して返す（Presenter の `present` / `present_error` 後） |

## 6. Outbound / Inbound ドライバ詳細

### 6.1 AmiVoice 連携

* 意図: リアルタイム音声認識結果を `speech_recognition_utterance_event` に変換し `transcription_port` に渡す
* 主実装: **`amivoice_streaming_bridge`**（WebSocket クライアント・VB-Cable キャプチャ）— 詳細は **`framework_amivoice.md`**
* 任意: **`amivoice_utterance_http_handler`** — §4.3 の internal POST。AmiVoice 公式 Webhook をインターネット公開する構成は **採用しない**（§1.5 0-1）
* 責務外: 書き起こしテキストのビジネス解釈（Application）

**備考:** Bridge も HTTP 注入も、Interface への入口は同一 `speech_recognition_utterance_event` 形式に揃える。

### 6.2 LLM 連携

* 意図: ユーザー投稿への壁打ち AI を Gemini で生成する
* 詳細: **`framework_llm.md`**（モデル・クォータ・トリガー・**講義コンテキスト**・レート制限）
* MVP トリガー: **`post_user_reaction` 成功後のみ**（講師発話では LLM を呼ばない）
* MVP コンテキスト: 投稿 `lecture_time_anchor` の **1 分前〜 anchor** の `utterance`（**最大 15 区間**）+ 返信先（`framework_llm.md` §3）

### 6.3 `background_task_scheduler`

* 意図: `ai_reaction_orchestrator` から渡された callable を非同期実行する
* MVP テスト: `interface_adapters` の即時実行スケジューラと差し替え可能
* 本番: スレッドプールまたは `asyncio.create_task`（How は実装時）

## 7. フロントエンド詳細（Vue 3 + TypeScript + Vite）

### 7.1 設計原則

| 原則 | 内容 |
|------|------|
| 表示専用 | `interface.md` §7.1 に従い、フォーマット・`reply_target` 解釈・エラー文言生成は **行わない** |
| API のみ | バックエンドは FastAPI JSON のみ。API キーは持たない |
| 型 | TypeScript の型は OpenAPI または手書きで ViewModel JSON と一致（snake_case） |

### 7.2 画面構成（MVP）

```
┌─────────────────────────┬─────────────────────────┐
│ TranscriptPanel         │ DialoguePanel           │
│ error_message（あれば）│ error_message（あれば） │
│ lines[] 時刻・話者・本文 │ lines[] 話者・本文      │
│                         │  reference_time_label   │
│                         │  reference_quote_label  │
└─────────────────────────┴─────────────────────────┘
[LectureControls: 開始 / 終了]  [ReactionForm]
```

| 領域 | bind するフィールド |
|------|---------------------|
| 文字起こし行 | `time_label`, `speaker_label`, `body` |
| 対話行 | `speaker_label`, `body`, `reference_time_label`, `reference_quote_label`（空は非表示） |
| パネルエラー | `error_message` が非空なら表示し `lines` は空 |

**対話行レイアウト（MVP）:** 表示順は **話者 → 本文 → `reference_time_label`**。`reference_time_label` は本文の下・右寄せ。`reference_quote_label` は AI 行用（Phase3）で現状どおり。

**`ReactionForm`（MVP）:** `transcript_view_model.latest_anchor_ms` を `lecture_time_anchor` として POST する。ms 手入力 UI は持たない。`latest_anchor_ms === 0`（utterance 未確立）の間は投稿ボタンを無効にする。

**投稿成功後:** `GET .../dialogue` を **1 回** 実行し対話パネルを更新する（§7.3 ポーリングに加え、投稿直後の即時反映を明記）。

### 7.3 ポーリング

| 状態 | 動作 |
|------|------|
| 講義 `active` | `GET .../transcript` と `GET .../dialogue` を間隔実行 |
| 講義未開始 / 終了後 | ポーリング停止 |

投稿・発話記録直後の即時反映は、ポーリング 1 回または手動 refresh で足りる（MVP）。ユーザー投稿直後は上記のとおり `GET .../dialogue` を 1 回追加する。

**Post-MVP:** `reference_time_label` クリックで文字起こしパネルを該当時刻へスクロール（Phase2 では表示のみ）。

### 7.4 受入基準（フロント）

1. Vue コンポーネント内に `reply_target` や `dialogue_sequence` のビジネス分岐がない
2. 表示文言はすべて API から受け取った文字列をそのまま表示する
3. 講義開始成功後のみ `lecture_id` 付き API を呼ぶ
4. 講義中、文字起こしリスト末尾付近にいる状態で新規行が追加されたとき、手動スクロールなしで最新行が表示領域内に入る
5. 講義中、対話リスト末尾付近にいる状態で新規行が追加されたとき（投稿直後の refresh またはポーリング更新を含む）、手動スクロールなしで最新行が表示領域内に入る。過去ログを上方向へスクロールして読んでいる間は位置を動かさない

## 8. 受入基準（Framework 横断）

1. 全 HTTP ハンドラは `interface_adapters` の Port / Controller 経由で UC を呼ぶ（UC をハンドラから直接呼ばない）
2. `application` / `domain` / `interface_adapters` が `framework` を import しない
3. API キーがリポジトリにコミットされていない
4. Command API は `Outcome` のみ返し、AI 本文は返さない
5. Query API は `interface.md` §7 の ViewModel JSON のみ返す
6. ユーザー投稿成功時のみ Orchestrator 経由で `generate_ai_replies_for_user_reaction` が非同期起動する（`framework_llm.md` §2）
7. `record_utterance` 成功だけでは LLM を呼ばない
8. AmiVoice セッションは `start_lecture` / `end_lecture` と同期する（`framework_amivoice.md` §4.2）
9. FastAPI は localhost のみで待ち受け、インターネット公開しない（§1.5 0-1）
10. LLM 呼び出しは `llm_rate_limiter` で RPM / RPD を守る（`framework_llm.md` §5）
11. LLM 講義コンテキストは `framework_llm.md` §3・§8.2 に従う
12. フロントは Vue 3 + TypeScript + Vite で、Discord 的 UI コンポーネントに依存しない

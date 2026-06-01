# インターフェイスアダプター層仕様

<!-- 関連: docs/spec/domain.md, docs/spec/application.md -->

PairRadioListening のインターフェイスアダプター層（Controller / Presenter / ViewModel / Orchestrator）の仕様を定義する。ビジネスルールは `domain.md`、ユースケース契約は `application.md` に従う。

**命名:** 識別子は **snake_case** で表記する。

## 1. 概要

- 外部（UI・音声認識）と Application ユースケースの間に立ち、入力変換・表示整形・非同期 UC 連鎖を担う
- Controller は `Request` 変換と UC 呼び出し。Presenter は `Response` の ViewModel 化。`generate_ai_*` は Orchestrator が非同期起動（`application.md` §1）
- 表示用読み取りは **`get_transcript`** と **`get_dialogue`** の 2 経路（`domain.md` §1.1）
- 各 Controller の `execute` 相当は 1 操作あたり UC を 1 回呼び、戻りは Interface 層の **Outcome** に変換する

### 1.1 設計原則

| 原則 | 内容 |
|------|------|
| 依存関係ルール | Controller / Presenter / Orchestrator は Application 層（および Interface の Port）にのみ依存する。Application 層は Interface 層を知らない |
| 単一責任 | Controller は外部入力の検証・変換と UC 呼び出し。Presenter は Response / Error の表示用整形 |
| インターフェイス分離 | 操作ごとに Port を分離する（例: `transcription_port`, `user_reaction_port`, `transcript_view_port`, `dialogue_view_port`） |

### 1.2 表示の二分割（MVP）

| 画面領域 | Query UC | Presenter | ViewModel |
|----------|----------|-----------|-----------|
| 文字起こしパネル | `get_transcript` | `transcript_presenter` | `transcript_view_model` |
| 対話パネル（ユーザー・AI） | `get_dialogue` | `dialogue_presenter` | `dialogue_view_model` |

**Why:** 文字起こしと対話は非同期に更新される。データ源を分け、各パネルが独立して refresh する（`domain.md` §1.1）。

Command の Response に本文テキストは含めない。表示更新は上記 Query → Presenter → ViewModel の経路で行う。

### 1.3 対話パネルの表示規則（MVP）

`dialogue_presenter` は `GetDialogueResponse` を `dialogue_view_model` に変換する。

| `reply_target` | 返信参照の表示（ViewModel では §7.4 の 2 ラベルに分解） |
|----------------|---------------|
| `utterance` | `reference_time_label` に講義時刻（`time_range` 由来）。UI は所定スロットに bind（§1.3 の「左上等」は View テンプレートの責務） |
| `reaction` | `reference_quote_label` に **話者表示名 + テキスト抜粋** のみ（時刻ラベルは出さない） |

対話リストは **フラット** とする。スレッドツリー用の ViewModel は持たない（`domain.md` §4.3）。

## 2. コンポーネント一覧（MVP）

### 2.1 Controller 一覧

| 名前 | 種別 | 対応 UC | 入口 Port | トリガー |
|------|------|---------|-----------|----------|
| `start_lecture_controller` | Command | `start_lecture` | `lecture_session_port.start` | 文字起こし開始 |
| `end_lecture_controller` | Command | `end_lecture` | `lecture_session_port.end` | 音声認識停止 |
| `record_utterance_controller` | Command | `record_utterance` | `transcription_port.on_utterance` | 音声認識結果（1 発話） |
| `post_user_reaction_controller` | Command | `post_user_reaction` | `user_reaction_port.on_submit` | ユーザーがタイムラインに投稿 |
| `refresh_transcript_controller` | Query（refresh） | `get_transcript` | `transcript_view_port.refresh` | 文字起こし表示・更新 |
| `refresh_dialogue_controller` | Query（refresh） | `get_dialogue` | `dialogue_view_port.refresh` | 対話表示・更新 |

**備考:** `generate_ai_reactions_for_utterance` / `generate_ai_replies_for_user_reaction` に対応する Controller は **持たない**（`ai_reaction_orchestrator` が担う。§2.5）。

### 2.2 Presenter 一覧

| 名前 | 入力 | 出力 ViewModel | 呼び出し元 | 詳細 |
|------|------|----------------|------------|------|
| `transcript_presenter` | `GetTranscriptResponse` | `transcript_view_model` | `refresh_transcript_controller` | §6 |
| `dialogue_presenter` | `GetDialogueResponse` + 参照コンテキスト | `dialogue_view_model` | `refresh_dialogue_controller` | §6 |

**備考:** 表示規則の骨子は §1.2・§1.3。Presenter 契約は §6、ViewModel 契約は §7。

### 2.3 ViewModel 一覧

| 名前 | 画面領域 | 更新経路 | 詳細 |
|------|----------|----------|------|
| `transcript_view_model` | 文字起こしパネル | `transcript_presenter` | §7 |
| `dialogue_view_model` | 対話パネル | `dialogue_presenter` | §7 |

### 2.4 Port 一覧（Inbound）

| 名前 | 操作 | Controller | 説明 |
|------|------|------------|------|
| `lecture_session_port` | `start` | `start_lecture_controller` | 講義セッション開始 |
| `lecture_session_port` | `end` | `end_lecture_controller` | 講義セッション終了 |
| `transcription_port` | `on_utterance` | `record_utterance_controller` | 音声認識結果受け口 |
| `user_reaction_port` | `on_submit` | `post_user_reaction_controller` | ユーザー投稿受け口 |
| `transcript_view_port` | `refresh` | `refresh_transcript_controller` | 文字起こしパネル更新 |
| `dialogue_view_port` | `refresh` | `refresh_dialogue_controller` | 対話パネル更新 |

### 2.5 Orchestrator 一覧

| 名前 | 起動契機 | 非同期 UC | 詳細 |
|------|----------|-----------|------|
| `ai_reaction_orchestrator` | `record_utterance` 成功後 | `generate_ai_reactions_for_utterance` | §8 |
| `ai_reaction_orchestrator` | `post_user_reaction` 成功後 | `generate_ai_replies_for_user_reaction` | §8 |

**Why（Orchestrator を Controller から分離）:** Controller の単一責任（入力変換）を保ちつつ、`application.md` §1 の非同期 UC 起動を担うため。

## 3. Controller 共通規約

本節は §4 の **全 Controller** に共通する契約を定義する。

### 3.1 責務

| やること | やらないこと |
|----------|--------------|
| 外部入力 DTO の Interface 層形式検証 | ドメインエンティティの生成・永続化の直接実行 |
| Application `Request` への変換 | UseCase の `new`（常に注入された `execute` を呼ぶ） |
| `execute(request)` の 1 回呼び出し | `generate_ai_*` の同期実行（Orchestrator に委譲） |
| `Result` を **Outcome**（Interface 層 DTO）に変換して返す | Application 層の `Error` を HTTP 等に変換（Framework 層） |

### 3.2 Command Controller と Query Controller

| 種別 | 対応 UC | Presenter | Orchestrator | 典型 Outcome |
|------|---------|-----------|--------------|--------------|
| Command | `start_lecture`, `record_utterance`, `post_user_reaction`, `end_lecture` | 呼ばない | 成功時に委譲する場合あり | ID のみ。本文テキストなし |
| Query（refresh） | `get_transcript`, `get_dialogue` | **呼ぶ** | 呼ばない | ViewModel 更新の成否 |

**Why:** Command の Response は識別子のみ（`application.md`）。表示本文は Query → Presenter 経路に限定する（§1.2）。

### 3.3 Outcome の共通形

Command 系 Outcome は次のフィールドを持つ（Query refresh は各 Controller 詳細）。

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `success` | 真偽値 | ○ | UC の `Result` が `Ok` か |
| `error_kind` | 文字列 | 失敗時 ○ | 失敗種別の識別子（例: `lecture_not_found`）。Framework 層が HTTP 等にマップする |

成功時に Outcome が持つ ID フィールドは Controller ごとに §4 で定義する。

### 3.4 `Result` の解釈

| UC の `Result` | Controller の扱い |
|----------------|-------------------|
| `Ok(response)` | `success=true`。Response の識別子フィールドを Outcome に写す |
| `Err(error)` | `success=false`。`error` の型に応じて `error_kind` を設定する（対応は `application.md` §4.6） |

Controller は `error` の詳細属性を Outcome に含めてもよいが、**必須**なのは `error_kind` のみとする（MVP）。

### 3.5 Controller と Orchestrator の分担

| コンポーネント | 起動契機 | 呼ぶ UC |
|----------------|----------|---------|
| `record_utterance_controller` | 音声認識 1 発話 | `record_utterance` →（成功）`ai_reaction_orchestrator.on_utterance_recorded` |
| `post_user_reaction_controller` | ユーザー投稿 | `post_user_reaction` →（成功）`ai_reaction_orchestrator.on_user_reaction_posted` |
| `start_lecture_controller` / `end_lecture_controller` | セッション開始・終了 | 各 1 UC のみ。Orchestrator は呼ばない |
| `refresh_*_controller` | 表示 refresh | 対応 Query UC + Presenter |

## 4. Controller 詳細

### start_lecture_controller

<!-- 仕様: docs/spec/application.md#start_lecture -->

* 意図: UI の講義開始操作を `StartLectureRequest` に変換し、講義セッションを開始する
* 入口: `lecture_session_port.start`
* 入力: `start_lecture_form_event`
* 出力: `start_lecture_outcome`

#### 外部入力：`start_lecture_form_event`

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `persona_profiles` | `ai_persona_profile` の配列 | ○ | 参加 AI ペルソナ。**MVP ではちょうど 1 件** |
| `title` | 文字列 | × | 講義の表示用タイトル |

#### 責務

1. `start_lecture_form_event` の形式検証（`persona_profiles` が **ちょうど 1 件**、各要素の必須属性）
2. `StartLectureRequest` への変換
3. 注入された `start_lecture_use_case.execute(request)` の呼び出し
4. `start_lecture_outcome` の組み立て

#### 責務外

- `lecture_id` の生成（UC）
- 文字起こし・対話の表示
- Orchestrator の呼び出し

#### 依存性注入

| 依存 | 用途 |
|------|------|
| `_use_case` | `start_lecture` |

#### 変換：`start_lecture_form_event` → `StartLectureRequest`

| 入力（event） | 出力（request） |
|--------------|----------------|
| `persona_profiles` | `persona_profiles` |
| `title` | `title`（省略時は request に含めない） |

#### `start_lecture_outcome`

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `success` | 真偽値 | ○ | §3.3 |
| `lecture_id` | 文字列 | 成功時 ○ | `StartLectureResponse.lecture_id` |
| `error_kind` | 文字列 | 失敗時 ○ | 例: `invalid_persona_profiles`, `persistence_failed` |

#### 検証の分担

| 検証 | 担当 |
|------|------|
| 配列長が 1・各ペルソナの必須属性 | Controller |
| `lecture` 生成・永続化 | UC |

#### 処理フロー

```
UI → lecture_session_port.start → start_lecture_controller → start_lecture_use_case
```

---

### end_lecture_controller

<!-- 仕様: docs/spec/application.md#end_lecture -->

* 意図: 講義終了操作を `EndLectureRequest` に変換し、セッションを閉じる
* 入口: `lecture_session_port.end`
* 入力: `end_lecture_session_event`
* 出力: `end_lecture_outcome`

#### 外部入力：`end_lecture_session_event`

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | 文字列 | ○ | 終了対象の講義 |

#### 責務

1. 形式検証 → `EndLectureRequest` 変換 → UC 呼び出し → Outcome 組み立て

#### 責務外

- `lecture.status` の遷移（UC）
- 進行中 `generate_ai_*` のキャンセル（MVP 未定義）

#### 依存性注入

| 依存 | 用途 |
|------|------|
| `_use_case` | `end_lecture` |

#### 変換

| 入力（event） | 出力（request） |
|--------------|----------------|
| `lecture_id` | `lecture_id` |

#### `end_lecture_outcome`

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `success` | 真偽値 | ○ | §3.3 |
| `lecture_id` | 文字列 | 成功時 ○ | |
| `ended_at` | 整数（ms） | 成功時 ○ | `EndLectureResponse.ended_at` |
| `error_kind` | 文字列 | 失敗時 ○ | 例: `lecture_not_found`, `lecture_already_closed` |

---

### record_utterance_controller

<!-- 仕様: docs/spec/application.md#record_utterance -->

* 意図: 音声認識 1 発話を `RecordUtteranceRequest` に変換し `utterance` を記録する
* 入口: `transcription_port.on_utterance`
* 入力: `speech_recognition_utterance_event`
* 出力: `record_utterance_outcome`

#### 経路上のコンポーネント

| コンポーネント | 層 | 役割 |
|---------------|-----|------|
| 音声認識エンジン | Framework & Drivers | 1 発話区間の認識結果を外部イベントとして送出 |
| `speech_recognition_utterance_event` | Interface（入力 DTO） | エンジン固有形式を Interface 層内に閉じ込める |
| `transcription_port` | Interface（Protocol） | 音声認識結果受け口 |
| `record_utterance_controller` | Interface | イベント変換と UC 呼び出し |
| `record_utterance_use_case` | Application | `utterance` 記録 |
| `ai_reaction_orchestrator` | Interface | 成功後に `generate_ai_reactions_for_utterance` を非同期起動 |

#### 外部入力：`speech_recognition_utterance_event`

本 DTO は **ドメインの `utterance` エンティティではない**。

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | 文字列 | ○ | 記録先講義 |
| `utterance_id` | 文字列 | ○ | 音声認識インフラが付与した発話 ID |
| `start_ms` | 整数 | ○ | 発話開始位置（講義タイムライン相対 ms） |
| `end_ms` | 整数 | ○ | 発話終了位置 |
| `transcript` | 文字列 | ○ | 書き起こしテキスト |
| `speaker_display_name` | 文字列 | ○ | 講師の表示名 |

#### Port 操作

| 操作 | 入力 | 出力 |
|------|------|------|
| `on_utterance` | `speech_recognition_utterance_event` | `record_utterance_outcome` |

#### 責務

1. `speech_recognition_utterance_event` の形式検証
2. `RecordUtteranceRequest` への変換
3. `record_utterance_use_case.execute(request)` の呼び出し
4. `record_utterance_outcome` の組み立て
5. 成功時、`ai_reaction_orchestrator.on_utterance_recorded(response)` への委譲

#### 責務外

- ドメインエンティティの生成・永続化の直接実行
- 文字起こし・対話の表示（各 `*_view_port.refresh`）
- `generate_ai_reactions_for_utterance` の成否を Outcome に含める

#### 依存性注入

| 依存 | 用途 |
|------|------|
| `_use_case` | `record_utterance` |
| `_orchestrator` | AI リアクション非同期起動 |

#### 変換：`speech_recognition_utterance_event` → `RecordUtteranceRequest`

| 入力（event） | 出力（request） |
|--------------|----------------|
| `lecture_id` | `lecture_id` |
| `utterance_id` | `utterance_id` |
| `start_ms`, `end_ms` | `time_range` |
| `transcript` | `speech_text` |
| `speaker_display_name` | `speaker`（`role=lecturer`） |

#### `record_utterance_outcome`

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `success` | 真偽値 | ○ | §3.3 |
| `utterance_id` | 文字列 | 成功時 ○ | 記録された発話 ID |
| `lecture_id` | 文字列 | 成功時 ○ | 記録先講義 ID |
| `error_kind` | 文字列 | 失敗時 ○ | 失敗の種別識別子 |

#### 検証の分担

| 検証 | 担当 |
|------|------|
| 必須フィールド・`start_ms` ≤ `end_ms` | Controller |
| 講義状態・永続化 | UC |

#### 処理フロー

```
音声認識エンジン → transcription_port.on_utterance
  → record_utterance_controller → record_utterance_use_case
  →（成功）ai_reaction_orchestrator → generate_ai_reactions_for_utterance（非同期）
```

`generate_ai_*` 成功後、UI は `dialogue_view_port.refresh` で対話を更新。文字起こしは `transcript_view_port.refresh`。

#### 表示との関係

* `RecordUtteranceResponse` に `speech_text` は含めない
* 文字起こしは **`get_transcript`**、AI 本文は **`get_dialogue`**
* 本 Controller は Presenter を呼ばない

---

### post_user_reaction_controller

<!-- 仕様: docs/spec/application.md#post_user_reaction -->

* 意図: ユーザー投稿を `PostUserReactionRequest` に変換し `reaction` を記録する
* 入口: `user_reaction_port.on_submit`
* 入力: `user_reaction_submitted_event`
* 出力: `post_user_reaction_outcome`

#### 外部入力：`user_reaction_submitted_event`

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | 文字列 | ○ | 投稿先講義 |
| `reaction_text` | 文字列 | ○ | ユーザー入力テキスト |
| `lecture_time_anchor` | 整数（ms） | ○ | 投稿時点の講義時間軸上の位置 |
| `speaker_display_name` | 文字列 | ○ | 対話表示名（`speaker.role=user`） |
| `reply_target` | `reply_target` | × | 省略時は UC が直近 `utterance` を解決 |

**UI 契約（MVP）:**

| ユーザー操作 | `reply_target` |
|--------------|----------------|
| 通常投稿（講師発話へのコメント） | 省略（直近 `utterance`） |
| 対話上の AI / ユーザー行を選んで返信 | `kind=reaction`, 対象 `reaction_id` |

#### 責務

1. 形式検証 → `PostUserReactionRequest` 変換 → UC 呼び出し → Outcome 組み立て
2. 成功時、`ai_reaction_orchestrator.on_user_reaction_posted(response)` への委譲

#### 責務外

- 直近 `utterance` の解決・`dialogue_sequence` 採番（UC）
- 対話表示・`generate_ai_replies_for_user_reaction` の成否を Outcome に含める

#### 依存性注入

| 依存 | 用途 |
|------|------|
| `_use_case` | `post_user_reaction` |
| `_orchestrator` | AI 返信の非同期起動 |

#### 変換：`user_reaction_submitted_event` → `PostUserReactionRequest`

| 入力（event） | 出力（request） |
|--------------|----------------|
| `lecture_id` | `lecture_id` |
| `reaction_text` | `reaction_text` |
| `reply_target` | `reply_target`（省略時は request に含めない） |
| `lecture_time_anchor` | `lecture_time_anchor` |
| `speaker_display_name` | `speaker_display_name` |

#### `post_user_reaction_outcome`

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `success` | 真偽値 | ○ | §3.3 |
| `reaction_id` | 文字列 | 成功時 ○ | ユーザー `reaction` の ID |
| `lecture_id` | 文字列 | 成功時 ○ | |
| `error_kind` | 文字列 | 失敗時 ○ | 例: `timeline_not_established`, `reply_target_not_found` |

#### 検証の分担

| 検証 | 担当 |
|------|------|
| 必須フィールド・`reaction_text` 非空 | Controller |
| タイムライン確立・参照存在・採番・永続化 | UC |

#### 処理フロー

```
UI → user_reaction_port.on_submit → post_user_reaction_controller → post_user_reaction_use_case
  →（成功）ai_reaction_orchestrator → generate_ai_replies_for_user_reaction（非同期）
  →（任意）dialogue_view_port.refresh
```

成功直後の UI は **楽観表示** してもよい。確定表示は `get_dialogue` の refresh に合わせる。

---

### refresh_transcript_controller

<!-- 仕様: docs/spec/application.md#get_transcript -->

* 意図: 文字起こしパネル用に `get_transcript` を呼び、Presenter で ViewModel を更新する
* 入口: `transcript_view_port.refresh`
* 入力: `transcript_refresh_request`
* 出力: `transcript_refresh_outcome`

#### 入力：`transcript_refresh_request`

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | 文字列 | ○ | 表示対象の講義 |

#### 責務

1. `GetTranscriptRequest` 変換 → UC 呼び出し
2. `Ok` 時、`transcript_presenter.present(response)` で `transcript_view_model` を更新（§7.3）
3. `Err` 時、`transcript_presenter.present_error(error)` で **前回内容を残さず** 空リスト + 整形済みエラー文を載せる（§7.2）
4. `transcript_refresh_outcome` の組み立て

#### 依存性注入

| 依存 | 用途 |
|------|------|
| `_use_case` | `get_transcript` |
| `_presenter` | Response → `transcript_view_model` |

#### `transcript_refresh_outcome`

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `success` | 真偽値 | ○ | §3.3 |
| `item_count` | 整数 | 成功時 ○ | 反映した `utterance` 件数 |
| `error_kind` | 文字列 | 失敗時 ○ | |

#### 起動契機（MVP）

| 契機 | 例 |
|------|-----|
| 講義開始後の初回表示 | UI |
| `record_utterance` 成功後 | ポーリング / コールバック連携 |
| 手動更新 | UI |

---

### refresh_dialogue_controller

<!-- 仕様: docs/spec/application.md#get_dialogue -->

* 意図: 対話パネル用に `get_dialogue` を呼び、Presenter で ViewModel を更新する
* 入口: `dialogue_view_port.refresh`
* 入力: `dialogue_refresh_request`
* 出力: `dialogue_refresh_outcome`

#### 入力：`dialogue_refresh_request`

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | 文字列 | ○ | 表示対象の講義 |

#### 責務

1. `GetDialogueRequest` 変換 → `get_dialogue` 呼び出し
2. `get_dialogue` が `Err` のとき `dialogue_presenter.present_error(error)`（§7.2）し、手順 3〜4 は行わない
3. 同一 refresh 内で `get_transcript` を呼び、`dialogue_presentation_context` を組み立てる（§6.5）
4. `get_transcript` が `Err` のとき `present_error`（§7.2）し、`present` は呼ばない
5. 上記がともに `Ok` のとき、`dialogue_presenter.present(response, context)` で `dialogue_view_model` を更新
6. `dialogue_refresh_outcome` の組み立て

#### 依存性注入

| 依存 | 用途 |
|------|------|
| `_dialogue_use_case` | `get_dialogue` |
| `_transcript_use_case` | `get_transcript`（`dialogue_presentation_context` 用） |
| `_presenter` | Response + context → `dialogue_view_model` |

#### `dialogue_refresh_outcome`

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `success` | 真偽値 | ○ | §3.3 |
| `item_count` | 整数 | 成功時 ○ | 反映した `reaction` 件数 |
| `error_kind` | 文字列 | 失敗時 ○ | |

#### 起動契機（MVP）

| 契機 | 例 |
|------|-----|
| 対話パネル初回表示 | UI |
| `post_user_reaction` 成功後 | UI / Port 連携 |
| `generate_ai_*` 完了後 | Orchestrator → `dialogue_view_port.refresh` |
| ポーリング | UI |

#### 受入基準（本 Controller）

1. `get_dialogue` 成功時、`get_transcript` が 1 回呼ばれ context が組み立てられる
2. `get_dialogue` または `get_transcript` が失敗した場合、`present` は呼ばれ、`present_error` で ViewModel の `lines` が空かつ `error_message` が非空になる

## 5. 受入基準

### 5.1 Controller（横断）

1. 各 Controller は対応 UC の `execute` を **1 リクエストあたり 1 回** 呼ぶ
2. UseCase を Controller 内で `new` しない（コンストラクタ注入のみ）
3. Command Controller は Presenter を呼ばない（§3.2）
4. `record_utterance` / `post_user_reaction` 成功時、Orchestrator がそれぞれ対応する `generate_ai_*` を非同期起動する
5. `refresh_*_controller` は UC 成功時のみ Presenter を呼ぶ
6. Application 層が Interface 層の型を import しない
7. `generate_ai_*` 用の Controller は存在しない

### 5.2 `record_utterance_controller`（音声認識経路）

1. 有効なイベントで、注入された UC の `execute` が 1 回呼ばれる
2. 成功時 Orchestrator が `generate_ai_reactions_for_utterance` を非同期起動する

## 6. Presenter 詳細

<!-- 関連: docs/spec/application.md#get_transcript, #get_dialogue -->

Presenter は Application の Query `Response` を、UI が bind する **ViewModel** に変換する。MVP では **Humble Object** パターンを用い、表示整形の大半をテスト可能な **ViewModel Mapper** に分離する。

### 6.1 設計方針（Humble Object）

| コンポーネント | 役割 | テスト容易性 |
|---------------|------|--------------|
| `*_presenter`（Humble） | Mapper を呼び、結果を ViewModel 更新先に反映する | ViewModel 更新先をテストダブル化 |
| `*_view_model_mapper`（Testable） | `Response` → 表示用行モデルへの変換（§1.3 等のプレゼンテーション規則） | 純粋入力で単体テスト |
| `*_view_model` | View が読む表示専用状態 | Presenter 経由で置換 |

**Why（Humble Object を採用する）:**

- View を表示専用のシンプルなものに保つ（フォーマット・条件分岐は View に書かない）
- プレゼンテーションロジックのテストを容易にする（Mapper の単体テスト）
- ビジネスルールを「表示」の関心事から切り離す（採番・妥当性は UC / ドメイン。見せ方は Interface）
- 複数の UI アダプター間で Mapper を共有できる（Web / CLI 等で Presenter の Humble 部分だけ差し替え）

**責務外（Presenter / Mapper 共通）:**

- 状態の永続化・UC の呼び出し（`refresh_*_controller`）
- ドメイン不変条件の判定（Application / Domain）
- エクスポート用ログ整形（`domain.md` の Export コンテキスト。別契約）

**依存:** Presenter / Mapper は Application の `Response` / DTO 型のみに依存する。Domain エンティティを直接組み立てない。

### 6.2 Presenter 共通契約

| 項目 | 内容 |
|------|------|
| 入口メソッド | `present(...)`（名前は実装で統一） |
| 呼び出し元 | 対応する `refresh_*_controller` のみ（Command Controller からは呼ばない） |
| 成功時 | `present(...)` で ViewModel を全体置換（§7.2） |
| 失敗時（refresh） | `present_error(error)` で空リスト + 整形済み `error_message` に全体置換（§7.2）。**前回の成功内容を残さない** |
| Command 失敗時 | Presenter は呼ばれない。UI は `Outcome` を参照（§3.2） |
| ViewModel 更新 | 1 回の `present` / `present_error` で対象 ViewModel を **全体置換** する（差分マージは MVP では行わない） |
| 並び順 | UC `Response.items` の順序を維持する（再ソートしない） |

### 6.3 ViewModel の定義

`transcript_view_model` / `dialogue_view_model` のフィールド契約・設計原則は **§7** に定義する。

### 6.4 `transcript_presenter`

* 意図: `GetTranscriptResponse` を `transcript_view_model` に変換する
* 入力: `GetTranscriptResponse`
* 出力: 更新された `transcript_view_model`（更新先は注入）

#### 責務（Humble）

1. `present`: Mapper で成功 ViewModel を組み立て、更新先に反映する
2. `present_error`: Mapper で失敗 ViewModel（§7.2）を組み立て、更新先に反映する

#### `transcript_view_model_mapper`（Testable）

| 変換 | 規則 |
|------|------|
| `TranscriptItem` → `transcript_line_view` | `utterance_id`, `speech_text`→`body`, `speaker`→`speaker_label` を写す |
| `time_label` | 当該 `time_range` から Presentation 定数に従い生成する |
| 並び | `response.items` の順序を維持 |

#### 依存性注入

| 依存 | 用途 |
|------|------|
| `_mapper` | `GetTranscriptResponse` → `transcript_view_model` |
| `_view_model` | 表示状態の更新先（Store / Port） |

---

### 6.5 `dialogue_presenter`

<!-- 仕様: docs/spec/domain.md#4.3 対話 UI モデル / §1.3 -->

* 意図: `GetDialogueResponse` を `dialogue_view_model` に変換する
* 入力: `GetDialogueResponse`, `dialogue_presentation_context`
* 出力: 更新された `dialogue_view_model`

#### `dialogue_presentation_context`

`get_dialogue` の `Response` だけでは足りない表示情報を、Controller が assemble して渡す。

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `utterance_times` | `utterance_id` → `time_range` の対応 | ○ | `reply_target=utterance` の講義時刻ラベル用 |
| `reaction_snippets` | `reaction_id` → `{ speaker_label, excerpt }` の対応 | ○ | `reply_target=reaction` の名前＋抜粋用 |

**組み立て責務:** `refresh_dialogue_controller` が、同一 refresh 内で得た `GetTranscriptResponse` から `utterance_times` を構築する。`reaction_snippets` は当該 refresh の `GetDialogueResponse.items` から構築してよい（自己参照・過去行参照に足る）。

#### 責務（Humble）

1. `present`: `dialogue_view_model_mapper.to_view_model(response, context)` を呼び、更新先に反映する
2. `present_error`: 失敗 ViewModel（§7.2）を組み立て、更新先に反映する

#### `dialogue_view_model_mapper`（Testable）

| `reply_target` | `reference_time_label` | `reference_quote_label` |
|--------------|------------------------|-------------------------|
| `utterance` | 講義時刻ラベル（非空） | 空 |
| `reaction` | 空 | 話者名 + 区切り + 抜粋（非空） |

| 規則 | 内容 |
|------|------|
| 相互排他 | 各行で `reference_time_label` と `reference_quote_label` は **同時に非空にしない**（§7.5） |
| 講義時刻ラベル | 参照先 `utterance` の `time_range` から生成。具体書式は Presentation 定数 |
| 名前＋抜粋 | 講義時刻ラベルは **含めない**（§1.3） |
| 抜粋長 | 元テキストが Presentation 定数の最大長を超える場合、末尾を省略表示する（具体長は Mapper のテストで固定） |
| 参照欠落 | 両ラベルを空とする（クラッシュしない） |
| 並び | `response.items` の順序を維持。`dialogue_sequence` は ViewModel に載せない（§7.5） |
| スレッド | 親子ツリー用フィールドは持たない（§1.3） |

#### 依存性注入

| 依存 | 用途 |
|------|------|
| `_mapper` | `GetDialogueResponse` + context → `dialogue_view_model` |
| `_view_model` | 表示状態の更新先 |

---

### 6.7 受入基準（Presenter）

#### 横断

1. Command Controller から Presenter が呼ばれない
2. Mapper は Framework / 永続化 / UC に依存しない
3. 1 回の `present` / `present_error` で ViewModel が全体置換される
4. `present_error` は §7.2 の失敗状態を満たす
5. Application 層が ViewModel / Mapper の型を import しない

#### `transcript_view_model_mapper`

1. `items` の件数と `lines` の件数が一致する
2. 各 `lines[i].utterance_id` が `items[i].utterance_id` と一致する
3. 各 `body` が対応する `speech_text` と一致する

#### `dialogue_view_model_mapper`

1. `items` の件数と `lines` の件数が一致する
2. `reply_target=utterance` の行で、`utterance_times` に存在する ID なら `reference_time_label` が非空かつ `reference_quote_label` が空
3. `reply_target=reaction` の行で、`reference_time_label` が空かつ `reference_quote_label` が非空
4. 任意の行で `reference_time_label` と `reference_quote_label` がともに非空にならない
5. `reply_target=reaction` の行の `reference_quote_label` に、講義時刻形式のサブストリングを含めない（時刻ラベル混在禁止）
6. 参照キーが context に無い行で、Mapper が例外を投げない
7. 各行に `dialogue_sequence` フィールドを持たない

## 7. ViewModel 詳細

<!-- 関連: §6 Presenter / Mapper、docs/spec/application.md#get_transcript, #get_dialogue -->

View は **ViewModel のみ** を bind する。フォーマット・`reply_target` の解釈・エラー文言の生成は Presenter 配下の Mapper が担う（§6.1）。

### 7.1 設計原則

| 原則 | 内容 |
|------|------|
| プリミティブのみ | フィールドは文字列・整数・真偽値・それらの配列、および **プリミティブだけを持つ行レコード** に限定する。`time_range`・`reply_target`・ドメインエンティティは載せない |
| 事前フォーマット | 画面に出す文言（時刻ラベル・話者名・本文・引用・エラー文）はすべて Mapper が生成済みとする |
| 表示メカニズムを ViewModel で表現しない | `reply_target` 種別や「左上等」のレイアウト指示は載せない。対話の返信参照は **2 つの任意ラベル** で表す（§7.5） |
| 表示に必要なデータのみ | 並び順は `lines` 配列の順序で表す。`dialogue_sequence` は ViewModel に含めない |

**Why:**

- フォーマットロジックを View から排除し、Presenter / Mapper に集約する
- ドメイン概念は Application `Response` 上にのみ現れ、ViewModel では表示用文字列に変換済みとする
- refresh 成功・失敗のどちらも View が bind する状態を ViewModel で統一する（§7.2）
- Interface 固有の見せ方を Application / Domain から分離したまま保つ

**View の責務（MVP）:** 各フィールドを所定の UI スロットに bind する。空文字列のラベルスロットは非表示としてよい。並べ替え・`error_kind` の解釈・日時計算は行わない。

### 7.2 パネル共通：`error_message` と refresh 失敗

`transcript_view_model` と `dialogue_view_model` は、次のパネル状態フィールドを共有する。

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `error_message` | 文字列 | ○ | ユーザー向けエラー表示文。成功時は **空文字列** |

| 状態 | `lines` | `error_message` |
|------|---------|-----------------|
| refresh 成功（`present`） | UC 由来の行を載せる | 空 |
| refresh 失敗（`present_error`） | **空配列** | `application.md` §4 の `Error` から Mapper が生成した整形済み文言（非空） |

**Why（前回内容を出さない）:** 失敗時に古い成功データが残ると、ユーザーが誤って正しい内容と判断するため。Outcome（`success` / `error_kind`）は Controller の戻り値として併用してよいが、**パネル表示の単一の真実の源は ViewModel** とする。

**`present_error`:** 各 `*_presenter` が `Application` の `Error` を受け取り、`*_view_model_mapper.to_error_view_model(lecture_id, error)` で上記失敗状態を組み立て、ViewModel 更新先に全体置換する。`error_kind` から文言への対応は Mapper の Presentation 定数とする。

### 7.3 `transcript_view_model`

文字起こしパネル用。

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | 文字列 | ○ | 表示中の講義 |
| `lines` | `transcript_line_view` の配列 | ○ | 上から下へ表示順（`get_transcript` の `items` 順と一致） |
| `error_message` | 文字列 | ○ | §7.2 |

#### `transcript_line_view`

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `utterance_id` | 文字列 | ○ | 発話 ID（リスト `key`・将来の横断参照用。画面に表示しなくてよい） |
| `time_label` | 文字列 | ○ | 講義時間軸の表示用ラベル |
| `speaker_label` | 文字列 | ○ | 講師の表示名 |
| `body` | 文字列 | ○ | 書き起こし本文 |

### 7.4 `dialogue_view_model`

対話パネル用。リストは **フラット**（§1.3）。

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | 文字列 | ○ | 表示中の講義 |
| `lines` | `dialogue_line_view` の配列 | ○ | 上から下へ表示順（`get_dialogue` の `items` 順 = `dialogue_sequence` 昇順と一致） |
| `error_message` | 文字列 | ○ | §7.2 |

#### `dialogue_line_view`

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `reaction_id` | 文字列 | ○ | リアクション ID（リスト `key`・将来の返信選択用。画面に表示しなくてよい） |
| `speaker_label` | 文字列 | ○ | 話者表示名 |
| `body` | 文字列 | ○ | リアクション本文 |
| `reference_time_label` | 文字列 | ○ | 返信参照の講義時刻ラベル。不要時は **空文字列** |
| `reference_quote_label` | 文字列 | ○ | 返信参照の「話者名 + 抜粋」。不要時は **空文字列** |

**Why（2 ラベル）:** `reply_target` 種別を View が知らずに、§1.3 の 2 パターンを表現するため。View は 2 つのラベルスロットに bind し、空のスロットを非表示にする。

**`dialogue_sequence` を ViewModel に含めない理由:** 表示順は `lines` の配列順で足りる。ID の重複表現を避け、表示に不要なドメイン順序 ID を View に漏らさないため。

#### 返信参照ラベルの対応（§1.3）

| `reply_target`（Mapper 入力側） | `reference_time_label` | `reference_quote_label` |
|------------------------------|------------------------|-------------------------|
| `utterance` | 非空 | 空 |
| `reaction` | 空 | 非空（話者名 + 抜粋。時刻は含めない） |
| 参照解決不能 | 空 | 空 |

### 7.5 受入基準（ViewModel）

#### 横断

1. 全フィールドが §7.1 のプリミティブ制約を満たす
2. refresh 成功時、`error_message` は空であり `lines` は 1 件以上あり得る
3. refresh 失敗時、`lines` は空配列であり `error_message` は非空
4. 失敗後の ViewModel に、直前の成功時の `lines` 内容が残らない

#### `dialogue_line_view`

1. 任意の行で `reference_time_label` と `reference_quote_label` がともに非空でない
2. `dialogue_sequence` フィールドを持たない

## 8. Orchestrator 詳細

<!-- 関連: docs/spec/application.md §1, #generate_ai_reactions_for_utterance, #generate_ai_replies_for_user_reaction -->

Orchestrator は **複数 Application UC の起動順序と非同期委譲** を担う Interface 層コンポーネントである。ビジネスルール・永続化・本文生成は Application / Domain に委ね、Orchestrator は `Request` 組み立てと UC 呼び出しの編成のみ行う。

MVP では `ai_reaction_orchestrator` の 1 種のみを定義する。

### 8.1 設計方針

| 原則 | 内容 |
|------|------|
| 依存関係ルール | Orchestrator は Application 層の UseCase（と Interface 層の Port）にのみ依存する。Application は Orchestrator を知らない |
| Controller との分離 | 外部入力の変換は Controller。`generate_ai_*` の起動は Orchestrator（§3.1, §3.5） |
| 単一責任 | 契機となった Command の `Response` から後続 UC を起動する。入力 DTO 変換・表示整形は行わない |
| 非同期 | `generate_ai_*` は **呼び出し元 Controller の Outcome 返却をブロックしない**（`application.md` §1） |
| 失敗の局所化 | `generate_ai_*` の失敗は、契機となった `record_utterance` / `post_user_reaction` を **ロールバックしない**（`application.md` 各 UC 備考） |
| 表示経路 | AI 本文は `GenerateAi*Response` に載せず、成功後は **`dialogue_view_port.refresh`** で `get_dialogue` → Presenter（§1.2, §7） |

**Why（専用 Controller を置かない）:** `generate_ai_*` は外部（UI・音声認識）から直接触られない後続処理であり、入口は常に他 Command の成功後であるため。

**責務外:**

- ドメインエンティティの生成ロジック（UC）
- 文字起こしパネルの更新（`transcript_view_port` は Orchestrator から呼ばない。発話記録後の更新は別経路）
- `generate_ai_*` の成否を、契機 Command の **Outcome** に含める
- AI 専用 Presenter（MVP では不要。対話本文は `dialogue_presenter` が担当）
- 講義終了後の進行中タスクのキャンセル（MVP 未定義。失敗は UC の `LectureClosed` 等で扱う）

### 8.2 `ai_reaction_orchestrator`

<!-- 仕様: docs/spec/application.md#generate_ai_reactions_for_utterance / #generate_ai_replies_for_user_reaction -->

* 意図: Command 成功後に、対応する `generate_ai_*` UC を非同期起動し、完了後に対話パネルを refresh する
* 呼び出し元: `record_utterance_controller` / `post_user_reaction_controller`（成功時のみ）

#### 公開操作

| 操作 | 入力 | 起動 UC |
|------|------|---------|
| `on_utterance_recorded` | `RecordUtteranceResponse` | `generate_ai_reactions_for_utterance` |
| `on_user_reaction_posted` | `PostUserReactionResponse` | `generate_ai_replies_for_user_reaction` |

いずれも **同期で return しない**（非同期スケジュールのみ）。戻り値は MVP では定義しない（void 相当）。

#### 責務

1. 入力 `Response` から対応する `GenerateAi*Request` を組み立てる
2. 注入された `generate_ai_*_use_case.execute(request)` を **非同期** に 1 回スケジュールする
3. UC が `Ok` のとき、注入された `dialogue_view_port.refresh` を当該 `lecture_id` で呼ぶ
4. UC が `Err` のとき、契機 Command の Outcome / ViewModel を **変更しない**（§8.1）

#### 責務外

- `RecordUtteranceRequest` / `PostUserReactionRequest` の変換（Controller）
- `generate_ai_*` 失敗時の `dialogue_presenter.present_error`（AI 失敗はユーザー投稿・発話記録の成功を否定しない。対話パネルのエラー表示は **refresh UC 失敗時のみ** §7.2）
- 同一契機での `generate_ai_*` の重複起動の抑止（MVP では Controller が 1 回だけ委譲する前提）

#### 変換：`RecordUtteranceResponse` → `GenerateAiReactionsForUtteranceRequest`

| 入力（response） | 出力（request） |
|-----------------|----------------|
| `lecture_id` | `lecture_id` |
| `utterance_id` | `utterance_id` |

#### 変換：`PostUserReactionResponse` → `GenerateAiRepliesForUserReactionRequest`

| 入力（response） | 出力（request） |
|-----------------|----------------|
| `lecture_id` | `lecture_id` |
| `reaction_id` | `reaction_id` |

#### 依存性注入

| 依存 | 用途 |
|------|------|
| `_generate_for_utterance_use_case` | `generate_ai_reactions_for_utterance` |
| `_generate_for_user_reaction_use_case` | `generate_ai_replies_for_user_reaction` |
| `_dialogue_view_port` | AI 生成成功後の対話 refresh |
| `_task_scheduler`（概念） | 非同期実行の委譲（実装は Framework 層。Orchestrator は Protocol のみ依存） |

**備考:** `_task_scheduler` は Interface 層の Outbound Port（例: `background_task_port.schedule(fn)`）として定義してよい。具体（スレッド・asyncio・キュー）は Framework が提供する。

#### 処理フロー（utterance 契機）

```
record_utterance_controller（成功）
  → ai_reaction_orchestrator.on_utterance_recorded(response)
  →（非同期）generate_ai_reactions_for_utterance_use_case.execute(request)
  → Ok: dialogue_view_port.refresh({ lecture_id })
  → Err: 何もしない（ログ等は Framework 任意）
```

#### 処理フロー（ユーザー投稿契機）

```
post_user_reaction_controller（成功）
  → ai_reaction_orchestrator.on_user_reaction_posted(response)
  →（非同期）generate_ai_replies_for_user_reaction_use_case.execute(request)
  → Ok: dialogue_view_port.refresh({ lecture_id })
  → Err: 何もしない
```

**並行:** 複数の `on_utterance_recorded` / `on_user_reaction_posted` は連続してスケジュールされうる。完了順は `dialogue_sequence` 採番に反映される（`domain.md` / `application.md`）。

#### 表示との関係

| タイミング | 対話パネル |
|------------|------------|
| Command 成功直後 | Controller は Presenter を呼ばない。UI の楽観表示は任意（§4 `post_user_reaction`） |
| `generate_ai_*` 成功後 | `dialogue_view_port.refresh` → `get_dialogue` → `dialogue_presenter.present` |
| `generate_ai_*` 失敗後 | refresh しない（MVP）。ユーザー投稿・発話記録は画面に残る |

文字起こしパネルは、発話記録後 **`transcript_view_port.refresh`** を別経路（UI ポーリング等）で更新する。Orchestrator は呼ばない。

### 8.3 受入基準（Orchestrator）

#### `ai_reaction_orchestrator`

1. `on_utterance_recorded` で `generate_ai_reactions_for_utterance` の `execute` が 1 回スケジュールされる
2. `on_user_reaction_posted` で `generate_ai_replies_for_user_reaction` の `execute` が 1 回スケジュールされる
3. スケジュールは `record_utterance_controller` / `post_user_reaction_controller` の Outcome 返却をブロックしない
4. UC `Ok` 時のみ `dialogue_view_port.refresh` が 1 回呼ばれる
5. UC `Err` 時、契機 Command の Outcome と当該パネルの ViewModel（成功済み内容）を Orchestrator が上書きしない
6. Orchestrator が Domain エンティティを直接生成しない
7. Application 層が Orchestrator の型を import しない

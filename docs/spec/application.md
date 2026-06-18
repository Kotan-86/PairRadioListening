# アプリケーション層仕様

## 1. 概要
- ユースケース（1操作単位）を定義する
  - 考え方: ユーザーが操作する際に、ドメインエンティティをどのように作る・足す・読む・組み合わせるかを1操作で考える
- ビジネスルールは、`domain.md` に従う
- 文字起こし・ユーザー投稿・AI 投稿は並行して発生する。各 Command UC は単独で完結する
- **MVP:** `generate_ai_*` は **`post_user_reaction` 成功後** のみ、別 UC として非同期起動する（`framework_llm.md` §2）。`record_utterance` 成功では AI を起動しない
- 表示用の読み取りは **2 つの Query** に分ける: `get_transcript`（`utterance` のみ）と `get_dialogue`（`reaction` のみ。`dialogue_sequence` 昇順）。詳細は `domain.md` §1.1
- 各ユースケースの execute は Result[Response, Error] を返す。仕様の「失敗時」は Error の種別として定義する。HTTP 等への変換はアダプター層の責務とする（詳細は §4.0）

## 2. ユースケース一覧（MVP）

| 名前 | 種別 | 関連コンテキスト | トリガー |
|------|------|------------------|----------|
| `start_lecture` | Command | 講義記録 | 文字起こし開始 |
| `record_utterance` | Command | 講義記録 | 音声認識結果（1発話）が届いたとき |
| `post_user_reaction` | Command | タイムライン対話 | ユーザーがタイムラインに投稿したとき |
| `generate_ai_reactions_for_utterance` | Command | タイムライン対話 | （**MVP スコープ外**）将来: 新しい `utterance` 記録後 |
| `generate_ai_replies_for_user_reaction` | Command | タイムライン対話 | ユーザー `reaction` 投稿後 |
| `get_transcript` | Query | 講義記録 | 文字起こし表示・更新 |
| `get_dialogue` | Query | タイムライン対話 | 対話（ユーザー・AI）表示・更新 |
| `end_lecture` | Command | 講義記録 | 音声認識停止 |

**移行メモ:** 旧 `get_timeline`（`utterance` と `reaction` の統合 Query）は廃止し、`get_transcript` と `get_dialogue` に置き換える。

## 3. ユースケース詳細

### start_lecture

* 意図: 講義タイムラインを開始せず、講義セッション（`lecture`）を新規に用意する
* トリガー: 文字起こし開始を実行したとき
  * 入口: `StartLectureUseCase.execute(request: StartLectureRequest)`
  * 入力: `StartLectureRequest`（下表）
* 戻り値: `StartLectureResponse`（下表）

#### StartLectureRequest

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `persona_profiles` | `ai_persona_profile` の配列 | ○ | 参加 AI ペルソナ。**MVP ではちょうど 1 件**。属性は `domain.md` §5 に従う |
| `title` | 文字列 | × | 講義の表示用タイトル |

**備考:**
- 本 Request は HTTP ボディそのものではない。UI アダプターが画面入力から変換して渡す。
- `lecture.id` は Request に含めない（本ユースケースが生成する）。

#### StartLectureResponse

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | `lecture.id` | ○ | 永続化された講義の ID。以降の `record_utterance` 等で使用する |

#### 手順

1. `StartLectureRequest` を形式検証する（`persona_profiles` が **ちょうど 1 件**、各要素が有効）
2. `lecture` を生成する
3. `lecture` を永続化する
4. `StartLectureResponse` を返す

#### 成功時

* 戻り値: `StartLectureResponse`
* 事後条件:
  * `lecture` が永続化されている
  * `lecture.status` が `active` である
  * `persona_profiles` が `lecture` に紐づいている
  * `started_at` は null（タイムライン未確立）
  * `utterance` は 0 件
  * `ended_at` は 0
  * `next_dialogue_sequence` は 0

#### 失敗時

* `persona_profiles` が不正（0 件・2 件以上・要素不正） → `lecture` は作成・永続化されない
* 永続化に失敗 → 呼び出し元に失敗を返す（`lecture` は利用可能な状態にならない）

### record_utterance

* 意図: 音声認識結果を `utterance` として `lecture` に記録する
* トリガー: 音声認識結果（1発話区間）が届いたとき
  * 入口: `RecordUtteranceUseCase.execute(request: RecordUtteranceRequest)`
  * 入力: `RecordUtteranceRequest`
* 戻り値: `RecordUtteranceResponse`

#### RecordUtteranceRequest

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | `lecture.id` | ○ | 記録先の講義。`start_lecture` 成功後に得た ID |
| `utterance_id` | 文字列 | ○ | 音声認識インフラが付与した発話 ID（`utterance.id`） |
| `time_range` | `time_range` | ○ | 発話区間。`start_ms` / `end_ms`（講義タイムライン相対 ms） |
| `speech_text` | `speech_text` | ○ | 書き起こしテキスト |
| `speaker` | `speaker`（講義記録側） | ○ | `role` は `lecturer` 固定 |

#### RecordUtteranceResponse

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `utterance_id` | `utterance.id` | ○ | 記録された発話の ID。Request の `utterance_id` と同一 |
| `lecture_id` | `lecture.id` | ○ | 記録先の講義 ID。Request の `lecture_id` と同一 |

**備考:**
- 1 本目の発話で講義タイムライン原点が確立されたかどうかは Response には含めない。必要なら `lecture` の `started_at` を別途取得する。

#### 手順
1. 入力を形式検証する
2. `lecture` を取得する
3. 1本目なら `started_at` を確立し、`time_range` を原点基準に正規化する
4. `utterance` を生成または同一 id で更新する
5. `lecture.add_utterance` し、永続化する
6. `RecordUtteranceResponse` を返す

#### 成功時

* 戻り値: `RecordUtteranceResponse`
* 事後条件:
  * `utterance` が `lecture` に永続化されている

#### 失敗時

* 入力不正 → 永続化しない
* `lecture` が存在しない → `utterance` を追加しない
* 講義が終了済み → `utterance` を追加しない
* 永続化失敗 → 利用可能な状態として返さない

### post_user_reaction

<!-- 仕様: docs/spec/domain.md#reaction（集約ルート） -->

* 意図: ユーザーが入力したテキストを `reaction` として `lecture` に記録する
* トリガー: ユーザーがタイムラインに投稿したとき
  * 入口: `PostUserReactionUseCase.execute(request: PostUserReactionRequest)`
  * 入力: `PostUserReactionRequest`（下表）
* 戻り値: `PostUserReactionResponse`（下表）

**備考:**
- 本 UC は AI 返信を含まない。成功後、`generate_ai_replies_for_user_reaction` を **別 UC として非同期起動** する（§1 概要）。
- 講義タイムライン未確立（`started_at` が null、または `utterance` が 0 件）の間は投稿不可。

#### PostUserReactionRequest

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | `lecture.id` | ○ | 投稿先の講義 |
| `reaction_text` | `reaction_text` | ○ | ユーザー入力テキスト |
| `reply_target` | `reply_target` | × | 直接の返信先。省略時は当該講義の **直近** `utterance` を用いる（`domain.md` §4.2） |
| `lecture_time_anchor` | `lecture_time_anchor` | ○ | 投稿時点の講義時間軸上の位置 |
| `speaker_display_name` | 文字列 | ○ | 対話ストリーム表示名。`speaker.role` は `user` 固定 |

**備考（`reply_target`）:** Interface 層は通常、ユーザーが AI 行を選んだときのみ `reaction` を指定する。それ以外は省略し、UC が直近 `utterance` を解決する。

#### PostUserReactionResponse

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `reaction_id` | `reaction.id` | ○ | 永続化されたユーザー `reaction` の ID |
| `lecture_id` | `lecture.id` | ○ | 投稿先の講義 ID |

#### 手順

1. `PostUserReactionRequest` を形式検証する
2. `lecture` を取得する（存在しなければ失敗）
3. 講義が終了済みでないこと、`started_at` が確立済みであることを確認する
4. `reply_target` が省略されていれば、当該講義の直近 `utterance` を返信先とする（`utterance` が 0 件なら失敗）
5. `reply_target` の参照先が同一 `lecture_id` 内に存在することを確認する
6. `lecture` から `dialogue_sequence` を採番する
7. `reaction` を生成する（`speaker.role` は `user`、`audio_data` は未設定）
8. `reaction` を永続化し、`lecture` の `next_dialogue_sequence` を更新する
9. `PostUserReactionResponse` を返す

#### 成功時

* 戻り値: `PostUserReactionResponse`
* 事後条件:
  * ユーザー `reaction` が永続化されている
  * `lecture_time_anchor` と `reply_target` が欠落なく保持されている

#### 失敗時

* 入力不正 → 永続化しない
* `lecture` が存在しない → 投稿しない
* 講義が終了済み → 投稿しない
* タイムライン未確立 → 投稿しない
* `reply_target` の参照先が存在しない → 投稿しない
* 永続化失敗 → 利用可能な状態として返さない

### generate_ai_reactions_for_utterance

<!-- 仕様: docs/spec/domain.md#lecturer_reaction_generator, docs/spec/framework_llm.md#2.2 -->

* 意図: 新規 `utterance` に対し、AI ペルソナ（MVP では 1 件）の `reaction` を 1 件生成して永続化する
* トリガー: **MVP では起動しない**（将来: `record_utterance` 成功後に非同期起動）
  * 入口: `GenerateAiReactionsForUtteranceUseCase.execute(request: GenerateAiReactionsForUtteranceRequest)`
  * 入力: `GenerateAiReactionsForUtteranceRequest`（下表）
* 戻り値: `GenerateAiReactionsForUtteranceResponse`（下表）

**備考:**
- `record_utterance` の同一 `execute` 内に含めない（§1 概要）。
- 本 UC の失敗は `record_utterance` をロールバックしない。
- ドメインサービスは方針決定まで。本文テキスト生成は `ReactionTextGeneratorPort`（アプリケーション層ポート）経由。

#### GenerateAiReactionsForUtteranceRequest

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | `lecture.id` | ○ | 対象講義 |
| `utterance_id` | `utterance.id` | ○ | リアクションの契機となった発話 |

#### GenerateAiReactionsForUtteranceResponse

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | `lecture.id` | ○ | 対象講義 ID |
| `utterance_id` | `utterance.id` | ○ | 契機となった発話 ID |
| `reaction_id` | `reaction.id` | ○ | 生成・永続化された AI `reaction` の ID |

#### 手順

1. `GenerateAiReactionsForUtteranceRequest` を形式検証する
2. `lecture` と対象 `utterance` を取得する（いずれか不存在なら失敗）
3. 講義が終了済みでないことを確認する
4. `lecturer_reaction_generator` でリアクション方針を決定する
5. `ReactionTextGeneratorPort` で方針に基づき本文を生成する
6. `lecture` から `dialogue_sequence` を採番する
7. AI `reaction` を 1 件生成する（`reply_target` は当該 `utterance`、`speaker.role` は `ai`）
8. `reaction` を永続化し、`lecture` の `next_dialogue_sequence` を更新する
9. `GenerateAiReactionsForUtteranceResponse` を返す

#### 成功時

* 戻り値: `GenerateAiReactionsForUtteranceResponse`
* 事後条件:
  * AI `reaction` が 1 件永続化されている
  * 当該 `reaction` の `reply_target` は当該 `utterance` を指す
  * `dialogue_sequence` は採番順（生成完了順）を反映している

#### 失敗時

* 入力不正 → AI `reaction` を永続化しない
* `lecture` または `utterance` が存在しない → 処理しない
* 講義が終了済み → 処理しない
* 方針決定・本文生成・永続化のいずれかが失敗 → 当該 UC は失敗として返す（部分成功は許容しない）

### generate_ai_replies_for_user_reaction

<!-- 仕様: docs/spec/domain.md#user_reaction_responder -->

* 意図: ユーザー `reaction` に対し、AI ペルソナ（MVP では 1 件）の返信 `reaction` を 1 件生成して永続化する
* トリガー: `post_user_reaction` 成功後（インターフェイスアダプター等が **非同期** に起動）
  * 入口: `GenerateAiRepliesForUserReactionUseCase.execute(request: GenerateAiRepliesForUserReactionRequest)`
  * 入力: `GenerateAiRepliesForUserReactionRequest`（下表）
* 戻り値: `GenerateAiRepliesForUserReactionResponse`（下表）

**備考:**
- `post_user_reaction` の同一 `execute` 内に含めない（§1 概要）。
- 本 UC の失敗は `post_user_reaction` をロールバックしない。
- `user_reaction_responder` で `reply_target` の種別に応じた返信方針を決定し、本文は `ReactionTextGeneratorPort` 経由。`user_reaction_analyzer` は MVP では使用しない。
- 講義の書き起こし片は **`lecture_llm_context`**（下表）として組み立て、方針決定・本文生成の **両方**に渡す（`framework_llm.md` §3）。

#### GenerateAiRepliesForUserReactionRequest

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | `lecture.id` | ○ | 対象講義 |
| `reaction_id` | `reaction.id` | ○ | 返信契機となったユーザー `reaction` の ID |

#### GenerateAiRepliesForUserReactionResponse

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | `lecture.id` | ○ | 対象講義 ID |
| `user_reaction_id` | `reaction.id` | ○ | 契機となったユーザー `reaction` ID |
| `reaction_id` | `reaction.id` | ○ | 生成・永続化された AI 返信 `reaction` の ID |

#### `lecture_llm_context`（講義 LLM コンテキスト）

`framework_llm.md` §3.1 に従い、当該 UC 内で組み立てる（永続化しない）。

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `anchor_ms` | 整数 | ○ | 対象ユーザー `reaction` の `lecture_time_anchor`（`t0`） |
| `utterance_excerpts` | 配列 | ○ | 窓内 `utterance`（最大 15 件）。空配列可 |

**`utterance_excerpt` 要素:**

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `utterance_id` | `utterance.id` | ○ | 発話 ID |
| `start_ms` | 整数 | ○ | 区間開始 |
| `end_ms` | 整数 | ○ | 区間終了 |
| `speech_text` | `speech_text` | ○ | 書き起こし |

**選定規則:**

1. `t0` = 対象ユーザー `reaction` の `lecture_time_anchor`
2. 候補 = 当該 `lecture` の `utterance` のうち、`time_range` が **`[t0 - 60_000, t0]`** と重なるもの
3. 候補が **16 件以上** のとき、`time_range.end_ms` の降順で先頭 15 件を残す
4. `utterance_excerpts` は `start_ms` **昇順**

#### `reply_target_focus`（返信先の明示）

`framework_llm.md` §3.2。`reply_target` を解決した結果（永続化しない）。

| `reply_target` 種別 | 内容 |
|---------------------|------|
| `utterance` | 参照 `utterance` の `speech_text` + `start_ms` / `end_ms` |
| `reaction` | 参照 AI `reaction` の `reaction_text` + `speaker.display_name` |

#### 手順

1. `GenerateAiRepliesForUserReactionRequest` を形式検証する
2. `lecture` と対象ユーザー `reaction` を取得する（いずれか不存在、またはユーザー投稿でなければ失敗）
3. 講義が終了済みでないことを確認する
4. `lecture_llm_context` を組み立てる（§上表）
5. `reply_target` を解決し `reply_target_focus` を組み立てる（§上表。`utterance` 不存在・`reaction` 不存在なら失敗）
6. `user_reaction_responder` で返信方針を決定する（`lecture_llm_context`・`reply_target_focus` を渡す）
7. `ReactionTextGeneratorPort` で方針に基づき本文を生成する（同一コンテキストを渡す）
8. `lecture` から `dialogue_sequence` を採番する
9. AI `reaction` を 1 件生成する（`reply_target` は当該ユーザー `reaction`、`speaker.role` は `ai`）
10. `reaction` を永続化し、`lecture` の `next_dialogue_sequence` を更新する
11. `GenerateAiRepliesForUserReactionResponse` を返す

#### 成功時

* 戻り値: `GenerateAiRepliesForUserReactionResponse`
* 事後条件:
  * AI 返信 `reaction` が 1 件永続化されている
  * 当該 `reaction` の `reply_target` は当該ユーザー `reaction` を指す

#### 失敗時

* 入力不正 → AI 返信を永続化しない
* `lecture` またはユーザー `reaction` が存在しない → 処理しない
* 対象 `reaction` がユーザー投稿でない → 処理しない
* 講義が終了済み → 処理しない
* 方針決定・本文生成・永続化のいずれかが失敗 → 当該 UC は失敗として返す（部分成功は許容しない）

### get_transcript

<!-- 仕様: docs/spec/domain.md#1.1 読み取りビュー -->

* 意図: 文字起こしストリーム用に、当該講義の `utterance` を講義時間軸の昇順で取得する
* トリガー: 文字起こしパネルの表示・更新（音声認識の進行に伴うポーリング等）
  * 入口: `GetTranscriptUseCase.execute(request: GetTranscriptRequest)`
  * 入力: `GetTranscriptRequest`（下表）
* 戻り値: `GetTranscriptResponse`（下表）

**備考:**
- 本 UC は状態を変更しない（Query）。
- `reaction` は含めない。

#### GetTranscriptRequest

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | `lecture.id` | ○ | 取得対象の講義 |

#### GetTranscriptResponse

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | `lecture.id` | ○ | 対象講義 ID |
| `items` | `TranscriptItem` の配列 | ○ | `time_range.start_ms` 昇順 |

#### TranscriptItem

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `utterance_id` | `utterance.id` | ○ | 発話 ID |
| `time_range` | `time_range` | ○ | 発話区間 |
| `speech_text` | `speech_text` | ○ | 書き起こし |
| `speaker` | `speaker`（講義記録側） | ○ | 講師 |

#### 手順

1. `GetTranscriptRequest` を形式検証する
2. `lecture` を取得する（存在しなければ失敗）
3. 当該 `lecture` の `utterance` 一覧を `TranscriptItem` に変換し、`time_range.start_ms` 昇順で並べる
4. `GetTranscriptResponse` を返す

#### 成功時

* 戻り値: `GetTranscriptResponse`
* 事後条件:
  * `items` は `time_range.start_ms` の昇順である

#### 失敗時

* 入力不正 → 返却しない
* `lecture` が存在しない → 返却しない

### get_dialogue

<!-- 仕様: docs/spec/domain.md#1.1 読み取りビュー / #4.3 対話 UI モデル -->

* 意図: 対話ストリーム用に、当該講義の `reaction`（ユーザー・AI）を `dialogue_sequence` 昇順で取得する
* トリガー: 対話パネルの表示・更新（投稿・AI 生成完了後のポーリング等）
  * 入口: `GetDialogueUseCase.execute(request: GetDialogueRequest)`
  * 入力: `GetDialogueRequest`（下表）
* 戻り値: `GetDialogueResponse`（下表）

**備考:**
- 本 UC は状態を変更しない（Query）。
- `utterance` は含めない。並び順は **`dialogue_sequence` 昇順のみ**（`lecture_time_anchor` は並びに使わない）。

#### GetDialogueRequest

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | `lecture.id` | ○ | 取得対象の講義 |

#### GetDialogueResponse

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | `lecture.id` | ○ | 対象講義 ID |
| `items` | `DialogueItem` の配列 | ○ | `dialogue_sequence` 昇順 |

#### DialogueItem

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `reaction_id` | `reaction.id` | ○ | リアクション ID |
| `dialogue_sequence` | 整数 | ○ | 対話ストリーム上の順序 |
| `reaction_text` | `reaction_text` | ○ | テキスト |
| `speaker` | `speaker`（対話側） | ○ | `user` または `ai` |
| `reply_target` | `reply_target` | ○ | 直接の返信先 |
| `lecture_time_anchor` | `lecture_time_anchor` | ○ | 時間錨 |

**備考（表示）:** `reply_target` が `utterance` のとき、Interface 層は参照先 `utterance` の `time_range` から講義時刻ラベルを表示する（`domain.md` §4.3）。`reply_target` が `reaction` のときは話者名と抜粋のみ。

#### 手順

1. `GetDialogueRequest` を形式検証する
2. `lecture` を取得する（存在しなければ失敗）
3. 当該 `lecture` の `reaction` 一覧を取得する
4. 各項目を `DialogueItem` に変換し、`dialogue_sequence` 昇順で並べる
5. `GetDialogueResponse` を返す

#### 成功時

* 戻り値: `GetDialogueResponse`
* 事後条件:
  * `items` は `dialogue_sequence` の昇順である
  * 各 `reaction` が欠落なく含まれる

#### 失敗時

* 入力不正 → 返却しない
* `lecture` が存在しない → 返却しない

### end_lecture

<!-- 仕様: docs/spec/domain.md#lecture（集約ルート） -->

* 意図: 音声認識停止をもって講義セッションを終了し、以降の書き込みを拒否できる状態にする
* トリガー: 音声認識を停止したとき
  * 入口: `EndLectureUseCase.execute(request: EndLectureRequest)`
  * 入力: `EndLectureRequest`（下表）
* 戻り値: `EndLectureResponse`（下表）

**備考:**
- 外部動画（YouTube 等）の停止は本 UC の範囲外。
- `lecture.status` を `closed` に遷移させる（`domain.md` §3.1 `lecture`）。
- `ended_at` は最後に確定した `utterance` の `time_range.end_ms` と一致させる（`record_utterance` により更新済みの値を確定する）。`utterance` が 0 件の場合は 0 のまま。
- 講義の途中停止・再開は MVP では扱わない。

#### EndLectureRequest

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | `lecture.id` | ○ | 終了対象の講義 |

#### EndLectureResponse

| フィールド | 型（概念） | 必須 | 説明 |
|------------|-----------|------|------|
| `lecture_id` | `lecture.id` | ○ | 終了した講義 ID |
| `ended_at` | 整数（ms） | ○ | 確定した講義タイムライン終端位置 |

#### 手順

1. `EndLectureRequest` を形式検証する
2. `lecture` を取得する（存在しなければ失敗）
3. 既に終了済みでないことを確認する
4. `ended_at` を最後に確定した `utterance` の `time_range.end_ms` で確定する（`utterance` 0 件なら 0）
5. `lecture.status` を `closed` に遷移させる
6. 永続化する
7. `EndLectureResponse` を返す

#### 成功時

* 戻り値: `EndLectureResponse`
* 事後条件:
  * `lecture.status` が `closed` である
  * `ended_at` が確定されている
  * 以降 `record_utterance` / `post_user_reaction` / `generate_ai_*` は失敗する

#### 失敗時

* 入力不正 → 終了処理しない
* `lecture` が存在しない → 終了処理しない
* 既に終了済み → 終了処理しない（二重終了を許容しない）
* 永続化失敗 → 利用可能な終了状態として返さない

## 4. アプリケーションエラー

各ユースケースの「失敗時」は、本節の標準エラークラスに対応する。各ユースケースの `execute` は `Result[Response, XxxError]` を返す。HTTP 等への変換はアダプター層の責務とする。

**命名:** エラークラス名は PascalCase、属性名は snake_case。実装は `application/errors/` に置く。

**方針:**

- 複数ユースケースで同じ意味の失敗は **1 クラス** に統一する
- ドメイン層の不変条件違反（`ValueError` 等）はユースケース内で捕捉し、本節のエラーに **変換** して返す
- `except Exception` による catch-all は行わない

### 実装方針

#### モジュール構成

| パス | 責務 |
|------|------|
| `application/result.py` | `Ok` / `Err` / `Result` を定義する。成功値またはエラーをカプセル化する **コンテナのみ**。Request・Response・HTTP 等の入出力は持たない |
| `application/errors/` | §4.1〜4.4 の標準エラークラス（dataclass）を定義する |
| `application/use_cases/` | 各 UC の `execute(request) -> Result[Response, XxxError]` を実装する |

**Why:** `Result`（機械）と `Error`（意味）を分離し、エラー定義の再利用と UC 実装の見通しを保つため。

#### ユースケース内の入出力

| 位置 | 役割 |
|------|------|
| **入力** | `execute(request: XxxRequest)` の `request` のみ。アダプターが外部形式から変換して渡す |
| **成功** | 処理の最後で `return Ok(XxxResponse(...))` |
| **失敗（主経路）** | 仕様の「失敗時」に該当する分岐で `return Err(...)`。例外を投げない |
| **失敗（変換）** | ドメインの `ValueError` 等、またはポート境界の **特定** 例外のみ `except` で捕捉し `return Err(...)` に変換する |

想定内の失敗（例: `lecture` 不存在、終了済み、入力不正）を **例外 + except** で制御しない。`except` は境界変換に限定する。

#### 層ごとの Error / Result の扱い

| 層 | 方針 |
|----|------|
| **ドメイン** | 不変条件違反は `ValueError` 等で raise してよい。ApplicationError や HTTP は知らない |
| **アプリケーション（UC）** | 戻り値は常に `Result[Response, XxxError]`。§4.5 の union に含まれるエラーのみ `Err` で返す |
| **ポート（Outbound）** | 永続化・LLM 等は `Result` を返すか、実装内で捕捉して UC が解釈可能な失敗に変換する |
| **アダプター** | UC の `Result` のみを解釈し HTTP 等に変換する。`except Exception` は使わない |

#### Result の API（概念）

- `Ok(value)` … 成功
- `Err(error)` … 失敗
- `is_ok()` / `is_err()` … 分岐用（プロジェクト内で名称を統一する）

#### テスト

- **Arrange:** `XxxRequest` を組み立てる（必要ならリポジトリ等をテストダブル化）
- **Act:** `use_case.execute(request)` を呼ぶ
- **Assert（成功）:** `result.is_ok()` および `result.value` の内容
- **Assert（失敗）:** `result.is_err()` および `isinstance(result.error, 期待するエラークラス)`。§4.6 の対応表に沿って代表ケースを網羅する

#### 禁止事項

- `except Exception` による catch-all
- UC 内で HTTP ステータスコードや外部 API の詳細を `Err` に含める（アダプター層の責務）
- 想定内失敗を raise して UC 外に漏らす（UC の `Result` で完結させる）

### 共通エラー

| クラス名 | 意味 | 属性（例） | 主な発生 UC |
|----------|------|------------|-------------|
| `InvalidRequest` | Request の形式・必須項目が不正 | `use_case`, `field`（任意）, `reason`（任意） | 全 UC |
| `PersistenceFailed` | リポジトリの保存・読込が失敗 | `use_case`, `operation`（`save` / `load`）, `resource` | Command 系、`get_transcript`, `get_dialogue` |
| `LectureNotFound` | 指定 `lecture_id` の講義が存在しない | `lecture_id` | `start_lecture` 以外の全 UC |
| `LectureClosed` | 講義が `closed` のため書き込み不可 | `lecture_id` | `record_utterance`, `post_user_reaction`, `generate_ai_*` |
| `LectureAlreadyClosed` | 既に `closed` の講義を再度終了しようとした | `lecture_id` | `end_lecture` |

### 講義記録コンテキスト

| クラス名 | 意味 | 属性（例） | 発生 UC |
|----------|------|------------|---------|
| `InvalidPersonaProfiles` | `persona_profiles` が 0 件・2 件以上、または要素が不正 | `reason`（任意） | `start_lecture` |
| `UtteranceNotFound` | 指定 `utterance` が当該講義内に存在しない | `lecture_id`, `utterance_id` | `generate_ai_reactions_for_utterance` |

### タイムライン対話コンテキスト

| クラス名 | 意味 | 属性（例） | 発生 UC |
|----------|------|------------|---------|
| `TimelineNotEstablished` | タイムライン未確立（`started_at` 未確立）のため投稿不可 | `lecture_id` | `post_user_reaction` |
| `ReplyTargetNotFound` | `reply_target` の参照先が同一講義内に存在しない | `lecture_id`, `reply_target_kind`, `reply_target_id` | `post_user_reaction` |
| `ReactionNotFound` | 指定 `reaction` が当該講義内に存在しない | `lecture_id`, `reaction_id` | `generate_ai_replies_for_user_reaction` |
| `InvalidUserReaction` | 対象 `reaction` がユーザー投稿ではない | `lecture_id`, `reaction_id` | `generate_ai_replies_for_user_reaction` |

### AI 生成・外部サービス

| クラス名 | 意味 | 属性（例） | 発生 UC |
|----------|------|------------|---------|
| `AiPolicyGenerationFailed` | ドメインサービスによる方針決定が失敗 | `lecture_id`, `trigger`（`utterance` / `user_reaction`）, `source_id` | `generate_ai_*` |
| `AiTextGenerationFailed` | LLM ポートによる本文生成が失敗 | `lecture_id`, `trigger`, `source_id` | `generate_ai_*` |

**Why（`LectureClosed` と `LectureAlreadyClosed` の分離）:** いずれも `status == closed` だが、書き込み拒否と終了操作の二重実行は呼び出し側の扱いが異なるため、クラスを分ける。

### ユースケース別 Error 型

各 UC の `XxxError` は、以下の union とする。

| UC | `XxxError`（union メンバー） |
|----|------------------------------|
| `start_lecture` | `InvalidRequest`, `InvalidPersonaProfiles`, `PersistenceFailed` |
| `record_utterance` | `InvalidRequest`, `LectureNotFound`, `LectureClosed`, `PersistenceFailed` |
| `post_user_reaction` | `InvalidRequest`, `LectureNotFound`, `LectureClosed`, `TimelineNotEstablished`, `ReplyTargetNotFound`, `PersistenceFailed` |
| `generate_ai_reactions_for_utterance` | `InvalidRequest`, `LectureNotFound`, `LectureClosed`, `UtteranceNotFound`, `AiPolicyGenerationFailed`, `AiTextGenerationFailed`, `PersistenceFailed` |
| `generate_ai_replies_for_user_reaction` | `InvalidRequest`, `LectureNotFound`, `LectureClosed`, `ReactionNotFound`, `InvalidUserReaction`, `AiPolicyGenerationFailed`, `AiTextGenerationFailed`, `PersistenceFailed` |
| `get_transcript` | `InvalidRequest`, `LectureNotFound`, `PersistenceFailed` |
| `get_dialogue` | `InvalidRequest`, `LectureNotFound`, `PersistenceFailed` |
| `end_lecture` | `InvalidRequest`, `LectureNotFound`, `LectureAlreadyClosed`, `PersistenceFailed` |

### ユースケース「失敗時」とエラーの対応

| UC | 仕様の失敗条件 | エラークラス |
|----|----------------|--------------|
| `start_lecture` | `persona_profiles` が不正 | `InvalidPersonaProfiles` |
| | 永続化に失敗 | `PersistenceFailed` |
| `record_utterance` | 入力不正 | `InvalidRequest` |
| | `lecture` が存在しない | `LectureNotFound` |
| | 講義が終了済み | `LectureClosed` |
| | 永続化に失敗 | `PersistenceFailed` |
| `post_user_reaction` | 入力不正 | `InvalidRequest` |
| | `lecture` が存在しない | `LectureNotFound` |
| | 講義が終了済み | `LectureClosed` |
| | タイムライン未確立（直近 `utterance` を解決できない） | `TimelineNotEstablished` |
| | `reply_target` の参照先が存在しない | `ReplyTargetNotFound` |
| | 永続化に失敗 | `PersistenceFailed` |
| `generate_ai_reactions_for_utterance` | 入力不正 | `InvalidRequest` |
| | `lecture` が存在しない | `LectureNotFound` |
| | `utterance` が存在しない | `UtteranceNotFound` |
| | 講義が終了済み | `LectureClosed` |
| | 方針決定が失敗 | `AiPolicyGenerationFailed` |
| | 本文生成が失敗 | `AiTextGenerationFailed` |
| | 永続化に失敗 | `PersistenceFailed` |
| `generate_ai_replies_for_user_reaction` | 入力不正 | `InvalidRequest` |
| | `lecture` が存在しない | `LectureNotFound` |
| | ユーザー `reaction` が存在しない | `ReactionNotFound` |
| | 対象がユーザー投稿でない | `InvalidUserReaction` |
| | 講義が終了済み | `LectureClosed` |
| | 方針決定が失敗 | `AiPolicyGenerationFailed` |
| | 本文生成が失敗 | `AiTextGenerationFailed` |
| | 永続化に失敗 | `PersistenceFailed` |
| `get_transcript` | 入力不正 | `InvalidRequest` |
| | `lecture` が存在しない | `LectureNotFound` |
| | 読込に失敗 | `PersistenceFailed` |
| `get_dialogue` | 入力不正 | `InvalidRequest` |
| | `lecture` が存在しない | `LectureNotFound` |
| | 読込に失敗 | `PersistenceFailed` |
| `end_lecture` | 入力不正 | `InvalidRequest` |
| | `lecture` が存在しない | `LectureNotFound` |
| | 既に終了済み | `LectureAlreadyClosed` |
| | 永続化に失敗 | `PersistenceFailed` |

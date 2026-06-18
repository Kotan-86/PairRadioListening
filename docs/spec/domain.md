# ドメインモデル

<!-- 仕様: README.md#2-コア機能 -->

PairRadioListening のドメイン境界・用語・不変条件を定義する。実装詳細（API、LLM プロンプト、AmiVoice 接続手順）は本書に含めない。

**命名:** 属性名・値オブジェクト名・ドメインサービス名などの識別子は **snake_case** で表記する。エンティティの同一性は `id` で表し、コンテキストをまたぐ参照は `lecture.id` / `utterance.id` 等の ID 値のみとする。

## 1. 概要

本プロダクトのドメインは、**講義上の事実（講師発話）** と **タイムライン上の解釈（ユーザー・AI のリアクション）** を分離し、両者を講義時間軸で結び付ける。

| 概念 | 役割 |
|------|------|
| 事実 | 講師が話した内容とその時間区間 |
| 解釈 | ユーザー・AI が事実や他の発言に対して行うリアクション |
| 時間錨 | 解釈が「講義のいつごろ」に属するかを保証する参照（`lecture_time_anchor`） |
| 対話時系列 | 対話ストリーム上の並び順を保証する単調 ID（`dialogue_sequence`） |

**Why（事実と解釈の表示分離）:** 文字起こしは講義時間軸の `utterance` ストリーム、ユーザーと AI のやり取りは `reaction` の対話ストリームとして **別画面** に表示する。両者は `reply_target` と `lecture_time_anchor` で横断参照する。

### 1.1 読み取りビュー（MVP）

| ビュー | 含むもの | 並び順 |
|--------|---------|--------|
| 文字起こしストリーム | `utterance` のみ | `time_range.start_ms` 昇順 |
| 対話ストリーム | `reaction`（`speaker.role` が `user` または `ai`）のみ | `dialogue_sequence` 昇順 |

**Why（`dialogue_sequence`）:** 連投を含む対話の表示順を講義時間軸と切り離し、投稿・生成の完了順を保証するため。並びに `lecture_time_anchor` は使わない。

---

## 2. 境界づけられたコンテキスト

**3 コンテキスト + 共有構成** に整理した。

```
┌─────────────────────┐     utterance.id / time_range      ┌─────────────────────┐
│  講義記録            │  ────────────────────────────────► │  タイムライン対話     │
│  (Lecture Recording)│                                   │ (Timeline Dialogue) │
│                     │                                   │                     │
│  lecture            │     lecture.id + 読み取り          │  reaction           │
│  utterance          │ ◄──────────────────────────────── │  + domain services  │
└─────────────────────┘                                   └──────────┬──────────┘
         │                                                              │
         │ 読み取り                                                      │ 読み取り
         ▼                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  エクスポート (Export) — lecture_log_formatter                                 │
└─────────────────────────────────────────────────────────────────────────────┘

         ┌──────────────────────┐
         │  共有構成 (Shared)    │  ← ai_persona_profile（全コンテキストから参照）
         └──────────────────────┘
```

### 2.1 講義記録コンテキスト (Lecture Recording)

音声認識インフラ（AmiVoice 等）から届く **事実** を時系列に記録するコンテキスト。

### 2.2 タイムライン対話コンテキスト (Timeline Dialogue)

タイムライン上の **解釈**（ユーザー投稿・AI リアクション）と、生成するドメインサービスを扱うコンテキスト。

### 2.3 エクスポートコンテキスト (Export)

講義終了後に事実と解釈を **読み取り専用** で結合し、外部向け成果物に整形する領域。状態を変更しない。

### 2.4 共有構成 (Shared Configuration)

`ai_persona_profile` は講義開始時に確定する **不変の設定値** として、タイムライン対話のドメインサービスから参照する。

---

## 3. 講義記録コンテキスト

### 3.1 集約

#### lecture（集約ルート）

講義・講演の単位。属性が変化しても永続 ID により同一性を保ち、当該講義に属するすべての `utterance` を時系列で包括する。

| 属性 | 説明 |
|-----|------|
| `id` | システム内の永続 ID |
| `title` | 表示用タイトル（任意） |
| `started_at` | 講義タイムラインの原点（0 ms）※ただし、lectureが成立した時点では未確立 |
| `ended_at` | 最後に確定した発話の終了位置（講義タイムライン上の ms） |
| `status` | 講義セッションのライフサイクル状態。`active`（進行中）または `closed`（終了） |
| `persona_profiles` | 参加 AI ペルソナの設定（MVP では `ai_persona_profile` **1 件のみ**。開始時に確定） |
| `next_dialogue_sequence` | 次に採番する `dialogue_sequence` の値（整数。初期値 0） |

**Why（`status`）:** `ended_at` はタイムライン上の終端位置であり、セッション終了（以降の書き込み拒否）と同一ではない。音声認識停止時に `end_lecture`（`application.md`）で `closed` へ遷移し、進行中のみ `utterance` / `reaction` の追加を許可するため。

**不変条件（`lecture`）:**

- 生成時（`start_lecture` 相当）の `status` は `active`
- `status` が `closed` の `lecture` に `utterance` または `reaction` を追加してはならない
- `status` が `closed` へ遷移するとき、`ended_at` は最後に確定した `utterance` の `time_range.end_ms` と一致する（`utterance` が 0 件なら 0）
- MVP では `closed` から `active` への再開は許容しない
- `persona_profiles` は **ちょうど 1 件** である（MVP）
- `reaction` を 1 件追加するたびに `next_dialogue_sequence` を 1 増やし、その増加前の値を当該 `reaction.dialogue_sequence` に付与する
- 同一 `lecture` 内の `dialogue_sequence` は重複しない

#### utterance（エンティティ）

講師のひと繋ぎの発言（一呼吸分）。音声認識インフラから付与された ID が `utterance.id` になる。

| 属性 | 説明 |
|-----|------|
| `id` | 外部音声認識から付与される ID |
| `time_range` | 発話区間（`time_range` 値オブジェクト）,  start_ms / end_ms は 講義タイムライン（lecture.started_at = 0）上の相対ミリ秒|
| `speech_text` | 書き起こし内容（`speech_text` 値オブジェクト） |
| `speaker` | 発言者（`speaker` 値オブジェクト。講師固定） |

**不変条件:**

- `utterance` は常に `lecture` 経由でだけ生成・保持し、`lecture_id` は持たない
- 同一 `utterance.id` の更新は、同一 `utterance` として扱う（新規作成しない）
- `lecture` の `started_at` が1本目の `utterance` が来たら確立する
- `time_range` の開始時刻 ≤ 終了時刻

### 3.2 値オブジェクト

#### time_range

発話区間の開始・終了時刻（ミリ秒等）。講義の特定時間帯をあてにして遡るために使用する。

#### speech_text

講師セリフの書き起こし文字列を保持する。

#### speaker（講義記録側）

| 属性 | 説明 |
|------|------|
| `role` | `lecturer` 固定 |
| `display_name` | 表示名 |

---

## 4. タイムライン対話コンテキスト

### 4.1 集約

#### reaction（集約ルート）

講師発話・ユーザー・AI への反応（テキスト。将来は音声付き）を表す。1 リアクションにシステム内一意 ID を 1 つ付与し、スレッド返信や音声データの有無などの状態変化を管理する。

| 属性（例） | 説明 |
|------------|------|
| `id` | システム内の永続 ID |
| `lecture_id` | 所属講義への参照（`lecture.id` の値） |
| `speaker` | 発言者（`speaker` 値オブジェクト） |
| `reply_target` | 直接の返信先（`reply_target` 値オブジェクト） |
| `lecture_time_anchor` | 講義時間軸上の位置（`lecture_time_anchor` 値オブジェクト） |
| `reaction_text` | テキスト内容（`reaction_text` 値オブジェクト） |
| `audio_data` | 音声データ（`audio_data` 値オブジェクト。初期実装では空を許容） |
| `dialogue_sequence` | 対話ストリーム上の順序（`lecture` が採番する単調増加の整数） |

**不変条件:**

- `reaction` は必ず 1 つの `lecture` に属する
- `lecture_time_anchor` と `dialogue_sequence` はいずれも必須
- `lecture_time_anchor` は、直接の返信先が別の `reaction` でも、講義のどの時間帯かを失わない
- `reply_target` が `utterance` の場合、参照先 `utterance.id` は同一 `lecture.id` 内に存在する
- `reply_target` が `reaction` の場合、参照先 `reaction.id` は同一 `lecture.id` 内に存在する
- ユーザー投稿の `speaker.role` は `user`、AI 生成の `speaker.role` は `ai`

### 4.2 値オブジェクト

#### reply_target

リアクションの **直接の** 返信先。

| 種別 | 保持する ID |
|------|-------------|
| `utterance` | `utterance.id` |
| `reaction` | `reaction.id` |

**MVP における `reply_target` の付け方:**

| 投稿者 | 状況 | `reply_target` |
|--------|------|----------------|
| ユーザー | 講師発話・いまの区間への反応（デフォルト） | 当該講義の **直近** `utterance` |
| ユーザー | 特定の AI 発言への返信（UI で選択） | 当該 `reaction`（`speaker.role` が `ai`） |
| AI | 新規 `utterance` への反応 | 当該 `utterance` |
| AI | ユーザー `reaction` への返信 | 当該ユーザー `reaction` |

**Why（デフォルト直近 `utterance`）:** 投稿時に返信先を選ばない操作を許しつつ、`reply_target` 必須の不変条件を満たすため（未指定時は Application 層または Interface 層が直近 `utterance` を解決する。詳細は `application.md` §3 `post_user_reaction`）。

#### lecture_time_anchor

リアクション発生時点で進行していた講師発話の時間情報。`time_range` または `utterance.id` + `time_range` で表現する。

#### reaction_text

ユーザー入力または AI 生成のテキスト。音声入出力時も、最終的な書き起こし／生成テキストをここに保持する。

#### audio_data

音声ファイルの保存先 URL や形式メタデータ。MVP では空（未設定）を許容する。

#### speaker（対話側）

| 属性 | 説明 |
|------|------|
| `role` | `user` / `ai` / `lecturer`（講師発話を `reaction` として載せる場合は将来検討） |
| `display_name` | 表示名 |
| `persona_id` | AI の場合のみ。`ai_persona_profile.id` の値 |

### 4.3 対話 UI モデル（MVP）

- 対話ストリームは **単一のフラットなリスト** とする。子スレッド用の集約やスレッド ID は持たない。
- 各 `reaction` は `reply_target` により **直接の返信先 1 件** を参照する。UI は返信参照（プレビュー）を表示してよい。
- **表示規則（Interface 層。`interface.md` 参照）:**
  - `reply_target` が `utterance` のとき: 当該 `utterance.time_range` に基づく **講義時刻** をメッセージ左上等に表示し、文字起こしパネルとの横断参照とする。
  - `reply_target` が `reaction` のとき: 返信参照は **話者表示名 + テキスト抜粋** のみとする（講義時刻ラベルは出さない）。

**Why:** Discord 的なフラットチャットと、文字起こしパネルとの役割分離を両立するため。

### 4.4 ドメインサービス

ドメインサービスは **方針・判定結果** を返す。本文テキストの生成は含めない。

#### user_reaction_analyzer

**MVP スコープ外。** ユーザー投稿の意図分類・感情トーン解析は行わない。

#### timeline_atmosphere_assessor

**MVP スコープ外。** 盛り上がり度の算出は行わない。

#### lecturer_reaction_generator

新規 `utterance`（事実）を受け取り、AI ペルソナ（MVP では 1 件）がリアクションするための **方針** を決定する。

**入力:** `utterance`、`ai_persona_profile`（講義に紐づく 1 件）  
**出力:** リアクション生成方針（テキスト生成そのものは含まない）

#### user_reaction_responder

対象ユーザー `reaction` と講義の書き起こし片・返信先に基づき、AI ペルソナ（MVP では 1 件）の **返信方針** を決定する。ユーザー投稿の解析は行わない。

**入力:**

| 入力 | 説明 |
|------|------|
| 対象 `reaction`（ユーザー投稿） | 壁打ちの主題 |
| `ai_persona_profile` | 講義に紐づく 1 件 |
| `lecture_llm_context` | `application.md` `generate_ai_replies_for_user_reaction` で組み立て。`lecture_time_anchor` の **1 分前〜 anchor** の `utterance`（最大 15 区間）。詳細は `framework_llm.md` §3.1 |
| `reply_target_focus` | ユーザーが向けた返信先の明示（`utterance` 本文+時刻、または AI `reaction` 抜粋）。`framework_llm.md` §3.2 |

**出力:** 返信方針（テキスト生成そのものは含まない）

**Why（解析の省略）:** MVP では質問／感想の分類や `user_reaction_analyzer` を用いず、講義コンテキストと `reply_target` に基づく方針決定で足りるため。

**Why（1 分・15 区間）:** ユーザーは「そこまで聞いた講義」に反応する。全文は渡さず、トークンとクォータ内に収める（`framework_llm.md` §3.1）。

---

## 5. 共有構成

### ai_persona_profile（値オブジェクト）

AI ペルソナのカスタマイズ設定。講義開始時に確定し、セッション中は不変として扱う。

| 属性 | 説明 |
|------|------|
| `id` | ペルソナの識別子 |
| `display_name` | タイムライン表示名 |
| `persona_prompt` | ユーザーが自由記述するペルソナ原稿（テキスト） |
| `voice_id` | 将来の音声合成用。MVP では未設定可 |

**Why:** AI ペルソナ設定を、対話ロジックから参照可能な不変データとして保持するため。

**MVP:** 講義あたり `ai_persona_profile` は **1 件のみ** とする。複数ペルソナは将来拡張とする。

---

## 6. エクスポートコンテキスト

### lecture_log_formatter（ドメインサービス）

講義終了時に、事実（`utterance`）と解釈（`reaction`）の依存関係を時系列で整理し、Markdown または JSON 形式の構造化ログに整形する。

**入力:** `lecture.id`（および関連 `utterance`・`reaction` の読み取り結果）  
**出力:** 構造化ログ（形式は呼び出し側が指定）

**不変条件:**

- 出力に含まれるすべての `reaction` は、対応する `lecture_time_anchor`、`dialogue_sequence`、`reply_target` を欠落なく含む
- 本サービスはドメイン状態を変更しない（読み取り専用）

**MVP スコープ:** 初期リリースでは実装対象外とする。README §2 のコア機能（視聴中の壁打ち）を優先する。

---

## 7. コンテキスト間の参照ルール

| 参照元 | 参照先 | 方式 |
|--------|--------|------|
| タイムライン対話 | 講義記録 | ID 参照のみ（`lecture.id`, `utterance.id`）。エンティティの内包・複製はしない |
| タイムライン対話 | 共有構成 | `ai_persona_profile.id` 経由で `ai_persona_profile` を参照 |
| エクスポート | 講義記録・タイムライン対話 | 読み取り専用 |

---

## 8. コア機能との対応

| README §2 | ドメイン |
|-----------|----------|
| 3.1 発話内容の文字起こし | 講義記録: `utterance`, `speech_text`, `time_range`（文字起こしストリームは講義時間軸順） |
| 3.2 タイムラインへの投稿 | タイムライン対話: `reaction`（ユーザー、`reply_target`, `lecture_time_anchor`, `dialogue_sequence`） |
| 3.3 AI との壁打ち | タイムライン対話: `reaction`（AI）、対話ストリーム、`§4.4` のドメインサービス（MVP 範囲） |

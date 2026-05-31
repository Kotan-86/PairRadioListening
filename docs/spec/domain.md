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
| 時間錨 | 解釈が「講義のいつごろ」に属するかを保証する参照 |

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
| `persona_profiles` | 参加 AI ペルソナの設定一覧（`ai_persona_profile` の集合。開始時に確定） |

**Why（`status`）:** `ended_at` はタイムライン上の終端位置であり、セッション終了（以降の書き込み拒否）と同一ではない。音声認識停止時に `end_lecture`（`application.md`）で `closed` へ遷移し、進行中のみ `utterance` / `reaction` の追加を許可するため。

**不変条件（`lecture`）:**

- 生成時（`start_lecture` 相当）の `status` は `active`
- `status` が `closed` の `lecture` に `utterance` または `reaction` を追加してはならない
- `status` が `closed` へ遷移するとき、`ended_at` は最後に確定した `utterance` の `time_range.end_ms` と一致する（`utterance` が 0 件なら 0）
- MVP では `closed` から `active` への再開は許容しない

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
| `created_at` | 投稿・生成時間（講義タイムライン上） |

**不変条件:**

- `reaction` は必ず 1 つの `lecture` に属する
- `lecture_time_anchor` は必須（直接の返信先がスレッドでも、講義のどの時間帯かを失わない）
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

### 4.3 ドメインサービス

ドメインサービスは **方針・判定結果** を返す。

#### user_reaction_analyzer

ユーザーが投稿した `reaction_text` を解析し、意図（技術的質問・共感・悩みの吐露等）と感情トーンを分類する。

**入力:** `reaction_text`  
**出力:** 意図ラベル、感情トーン（ドメイン定義の列挙）

#### timeline_atmosphere_assessor

直近の講師発話ペースと、タイムライン上の `reaction` 投稿頻度から、現在の盛り上がり度合いを算出する。

**入力:** 直近 `utterance` 一覧、`reaction` 一覧（時間窓付き）  
**出力:** 盛り上がり度（ドメイン定義の段階またはスコア）

#### lecturer_reaction_generator

新規 `utterance`（事実）を受け取り、各 AI ペルソナがリアクションを生成するための **方針** を決定する。方針には「事実の要約切り口」と「自分ごと化の例示角度」を含む。

**入力:** `utterance`、`ai_persona_profile`、任意で `timeline_atmosphere_assessor` の結果  
**出力:** ペルソナごとのリアクション生成方針（テキスト生成そのものは含まない）

#### user_reaction_responder

`user_reaction_analyzer` の結果を受け取り、各 AI ペルソナがスレッド返信する **方針**（トーン・返信意図・参照すべき事実）を決定する。

**入力:** 対象 `reaction`、`ai_persona_profile`、解析結果、任意で盛り上がり度  
**出力:** ペルソナごとの返信方針（テキスト生成そのものは含まない）

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

**Why:** 複数 AI ペルソナの参加設定を、対話ロジックから参照可能な不変データとして保持するため。

---

## 6. エクスポートコンテキスト

### lecture_log_formatter（ドメインサービス）

講義終了時に、事実（`utterance`）と解釈（`reaction`）の依存関係を時系列で整理し、Markdown または JSON 形式の構造化ログに整形する。

**入力:** `lecture.id`（および関連 `utterance`・`reaction` の読み取り結果）  
**出力:** 構造化ログ（形式は呼び出し側が指定）

**不変条件:**

- 出力に含まれるすべての `reaction` は、対応する `lecture_time_anchor` と `reply_target` を欠落なく含む
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
| 3.1 発話内容の文字起こし | 講義記録: `utterance`, `speech_text`, `time_range` |
| 3.2 タイムラインへの投稿 | タイムライン対話: `reaction`（ユーザー、`reply_target`, `lecture_time_anchor`） |
| 3.3 AI との壁打ち | タイムライン対話: `reaction`（AI）、§4.3 のドメインサービス群 |

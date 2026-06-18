# LLM 連携仕様（Framework & Drivers）

<!-- 関連: docs/spec/framework.md, docs/spec/application.md, docs/spec/interface.md#8.2, docs/spec/domain.md -->

PairRadioListening が **Google Gemini API**（AI Studio）で壁打ち用 AI `reaction` を生成する仕様を定義する。

**Why（独立した章）:** モデル・クォータ・レート制限・プロンプト境界は外界（LLM）固有の詳細であり、`framework.md` の HTTP 契約とは分離するため。

**命名（Python）:** 識別子は **snake_case**。環境変数名は実装時に `framework/settings` で定義する。

## 1. 概要

| 項目 | MVP |
|------|-----|
| プロバイダ | **Google AI Studio**（Gemini API） |
| モデル | **Gemini 3.1 Flash-Lite**（コンソールで確認した model ID を `LLM_MODEL` に設定） |
| 用途 | `generate_ai_replies_for_user_reaction` の方針決定・本文生成 |
| 価値の中心 | **ユーザーの投稿への壁打ち**。講師発話への自動 AI リアクションは **MVP では行わない** |

### 1.1 プロダクト前提との関係

| 参照 | 内容 |
|------|------|
| `framework.md` §1.5 0-1 | ローカル 1 人・API をインターネット公開しない |
| `framework.md` §1.5 0-4 | オンライン必須（AmiVoice・LLM） |
| `application.md` | UC 契約・`LlmAnalyzerProtocol` / `ReactionTextGeneratorPort` |

### 1.2 設計原則

| 原則 | 内容 |
|------|------|
| 内側への境界 | Application / Domain は Gemini SDK を知らない。Port / Protocol のみ |
| トリガー | MVP では **`post_user_reaction` 成功後** のみ LLM を呼ぶ（§2） |
| 失敗の局所化 | LLM 失敗は `post_user_reaction` をロールバックしない（`interface.md` §8.1） |
| クォータ遵守 | Framework が RPM / RPD をカウントし、超過時は新規呼び出しを **スキップ**（§5） |

## 2. AI 生成のトリガー（MVP）

### 2.1 起動する経路

| 契機 | Orchestrator | Application UC | LLM |
|------|--------------|----------------|-----|
| `post_user_reaction` 成功 | `on_user_reaction_posted` | `generate_ai_replies_for_user_reaction` | **呼ぶ** |
| `record_utterance` 成功 | **呼ばない** | — | **呼ばない** |

**Why（発話トリガーを外す）:** コア価値はユーザーが書き殴った思考の壁打ちであり、講師発話ごとの AI はクォータ消費が大きく体験もノイズになりやすいため。

### 2.2 MVP スコープ外（将来）

| 項目 | 内容 |
|------|------|
| `generate_ai_reactions_for_utterance` | Application 層に UC 定義は残す。**MVP では Orchestrator から起動しない** |
| `on_utterance_recorded` | Interface Orchestrator の操作として **定義しない**（将来追加可） |
| 手動「AI に聞く」 | 将来の HTTP / UI。MVP では未提供 |

### 2.3 処理フロー

```
post_user_reaction_controller（成功）
  → ai_reaction_orchestrator.on_user_reaction_posted(response)
  →（非同期）generate_ai_replies_for_user_reaction
      → user_reaction_responder（LlmAnalyzerProtocol）
      → ReactionTextGeneratorPort
  → Ok: dialogue_view_port.refresh
```

`record_utterance` は文字起こし（`get_transcript`）のみ更新。対話パネルはユーザー投稿・AI 返信後に refresh する。

## 3. 講義 LLM コンテキスト（MVP）

ユーザー投稿への壁打ち返信では、LLM に **講義の書き起こし片** と **ユーザー投稿・返信先** を渡す（`application.md` `generate_ai_replies_for_user_reaction` で組み立て、本節は境界条件）。

### 3.1 講義コンテキスト（`utterance` ストリーム）

| 項目 | 内容 |
|------|------|
| 基準時刻 `t0` | 対象ユーザー `reaction` の `lecture_time_anchor`（講義タイムライン相対 ms） |
| 時間窓 | **`[t0 - 60_000, t0]`**（投稿時点の **1 分前から `t0` まで**。`t0` **より後**の `utterance` は含めない） |
| 含める `utterance` | `time_range` が上記窓と **1 ms でも重なる**もの |
| 件数上限 | **最大 15 区間**。超過時は **`time_range.end_ms` が新しい方から 15 件**を残し、`start_ms` 昇順で並べる |
| 窓内 0 件 | UC は失敗しない（講義コンテキスト空で続行） |
| 各要素 | `start_ms` / `end_ms`（または表示用時刻ラベル）+ `speech_text` |

**Why（1 分・後ろなし）:** リアクションは「そこまで聞いた講義」への解釈であり、投稿時点より未来の講師発話はユーザーの聞取範囲に含まれないため。

**Why（15 区間上限）:** 発話が細かい講義でも TPM とプロンプト長を抑え、Gemini 無料枠内に収めるため。

**含めない（MVP）:** 講義全文タイムライン、全 `utterance` 履歴、対話ストリームの過去 `reaction`（将来拡張可）。

### 3.2 返信先（ユーザーの焦点）

MVP では LLM トリガーは **ユーザー投稿のみ**。`reply_target` は **ユーザーが講義のどこ／どの AI 行に向けて書いたか** を示す（講師発話への AI 自発反応ではない）。

| `reply_target` | LLM に必ず含めるもの |
|----------------|----------------------|
| `utterance` | 解決済み `utterance` の `speech_text` + 時刻。1 分窓に含まれていても **返信先として明示**してよい |
| `reaction` | 参照先 AI `reaction` の本文抜粋 + `speaker.display_name`。§3.1 の講義コンテキストは **別枠**で付与 |

### 3.3 LLM 入力の全体像（MVP）

| ブロック | 内容 |
|----------|------|
| ペルソナ | `ai_persona_profile` |
| 講義コンテキスト | §3.1 |
| ユーザー投稿 | `reaction_text` |
| 返信先 | §3.2 |

方針決定（`LlmAnalyzerProtocol`）と本文生成（`ReactionTextGeneratorPort`）の **両方**に、上記ブロックを渡す（How で 1 API 統合は将来可）。

## 4. モデルとクォータ

コンソールで確認済みの **Gemini 3.1 Flash-Lite** 無料枠（プロジェクト依存。変更時は本節を更新する）。

| 制限 | 値 | 仕様上の扱い |
|------|-----|--------------|
| **RPM** | 15 / 分 | `llm_rate_limiter` が 1 分窓で API 呼び出し回数を制限 |
| **TPM** | 250,000 / 分 | 入力トークン合計の監視（MVP は概算または API エラー時バックオフで足りる前提） |
| **RPD** | 500 / 日 | 日次カウンタ。超過時は §5.3 |

### 4.1 1 回の壁打ちあたりの消費

`generate_ai_replies_for_user_reaction` は Application 上 **2 段**（方針 LLM + 本文 LLM）とする（`application.md`）。

| 項目 | 目安 |
|------|------|
| API 呼び出し / ユーザー投稿 1 回 | **2 リクエスト** |
| 実効 RPD（投稿回数） | 500 ÷ 2 ≈ **250 投稿/日** 上限 |
| 実効 RPM（投稿回数） | 15 ÷ 2 ≈ **7 投稿/分** 上限 |

**Why（2 段を維持）:** Domain の方針決定と本文生成の責務分離を Application 契約で保つ。ドライバ内で 1 回の API に統合する最適化は **How**（将来可）。

### 4.2 講義あたりの余裕

30〜60 分の講義でユーザーが **10〜30 回** 投稿する想定では、RPD・RPM ともに **通常は十分** である。

## 5. Framework コンポーネント

### 5.1 一覧（MVP）

| 名前 | 実装する Port / Protocol | 詳細 |
|------|-------------------------|------|
| `gemini_llm_analyzer_driver` | `LlmAnalyzerProtocol` | §6.1 |
| `gemini_reaction_text_generator` | `ReactionTextGeneratorPort` | §6.2 |
| `llm_rate_limiter` | （Framework 内部） | §5.2 |
| `llm_client`（概念） | Gemini SDK ラッパ | API キー・model ID・429 処理 |

### 5.2 `llm_rate_limiter`

* 意図: クォータ超過による 429 と意図しない課金リスクを抑える
* 責務:
  1. 各 `generateContent`（または同等）呼び出し前に **許可判定**
  2. 分次カウント（RPM≤15）・日次カウント（RPD≤500）
  3. 超過時は **呼び出さず** `AiPolicyGenerationFailed` / `AiTextGenerationFailed` 相当で UC に返す（またはドライバが Port 契約に沿った失敗を返す）

**安全マージン（推奨）:** 実装時は上限の 1 未満（例: RPM 14、RPD 480）で止めてもよい。

### 5.3 超過・429 時

| 状況 | 動作 |
|------|------|
| レートリミッタで拒否 | 当該 `generate_ai_*` を失敗。ユーザー `reaction` は存続 |
| API 429 | 指数バックオフ **最大 1 回** リトライ（MVP）。仍失敗なら UC 失敗 |
| 日次上限到達 | 以降の LLM 呼び出しをスキップ。UI 文言は将来（MVP はログのみ可） |

## 6. Outbound ドライバ詳細

### 6.1 `gemini_llm_analyzer_driver`

* 意図: `LlmAnalyzerProtocol` を実装し、`user_reaction_responder` 用の **構造化方針** を返す
* MVP で使用: **`user_reaction_responder` のみ**
* 入力: §3.3 のブロック（Application が組み立てた講義コンテキスト・返信先を含む）

### 6.2 `gemini_reaction_text_generator`

* 意図: `ReactionTextGeneratorPort` を実装し、方針に基づく AI `reaction` **本文** を返す
* 入力: §3.3 と同一（方針 JSON を追加）
* 出力: 短い壁打ち文（具体トークン上限は実装時。目安 512 トークン以内）

### 6.3 設定

| 変数（例） | 内容 |
|------------|------|
| `GEMINI_API_KEY` または `LLM_API_KEY` | AI Studio API キー |
| `LLM_MODEL` | コンソールの model ID（例: `gemini-3.1-flash-lite`） |
| `LLM_RPM_LIMIT` | 省略時 15 |
| `LLM_RPD_LIMIT` | 省略時 500 |

**禁止:** リポジトリへのコミット、フロントエンドへの埋め込み（`framework.md` §1.4）。

## 7. 秘密情報・ネットワーク

| 項目 | MVP |
|------|-----|
| 呼び出し先 | Google Generative Language API（HTTPS） |
| 実行場所 | バックエンド（Composition root）のみ |
| データ | ユーザー投稿・参照先発話・ペルソナが送信される。Google のデータポリシーに従う |

## 8. 受入基準

### 8.1 トリガー

1. `record_utterance` 成功だけでは LLM API が **呼ばれない**
2. `post_user_reaction` 成功後、非同期で `generate_ai_replies_for_user_reaction` が 1 回スケジュールされる
3. 上記成功後、`dialogue_view_port.refresh` が 1 回呼ばれる（`interface.md` §8）

### 8.2 講義コンテキスト

1. 講義コンテキストの `t0` は対象ユーザー `reaction` の `lecture_time_anchor` と一致する
2. 含まれる `utterance` は `time_range` が `[t0 - 60_000, t0]` と重なるもののみである
3. `time_range.start_ms > t0` の `utterance` は含まれない
4. 候補が 16 件以上のとき、結果は **15 件**である（新しい `end_ms` 優先）
5. 結果は `start_ms` 昇順である
6. `reply_target` が `utterance` のとき、返信先 `speech_text` が LLM 入力に含まれる
7. `reply_target` が `reaction` のとき、参照先 AI 本文抜粋が LLM 入力に含まれる

### 8.3 クォータ

1. 分次 15 回を超える API 呼び出しは同一分内に実行されない（または失敗として扱う）
2. 日次 500 回を超える呼び出しは同日に実行されない（または失敗として扱う）
3. レート制限の状態はプロセス内で保持する（MVP。再起動でリセット可）

### 8.4 依存関係

1. `domain` / `application` / `interface_adapters` が Gemini SDK を import しない
2. API キーがリポジトリに含まれない

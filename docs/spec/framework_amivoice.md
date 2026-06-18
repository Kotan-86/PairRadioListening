# AmiVoice 連携仕様（Framework & Drivers）

<!-- 関連: docs/spec/framework.md, docs/spec/interface.md#record_utterance_controller, AmiVoice API 公式ドキュメント -->

PairRadioListening が **AmiVoice API** の WebSocket インターフェースでリアルタイム音声認識を行い、結果を `speech_recognition_utterance_event` として Interface 層に渡す仕様を定義する。

**Why（独立した章）:** 接続方式・ペイロード・音声フォーマットは外界（AmiVoice）固有の詳細であり、`framework.md` の自前 HTTP 契約とは分離するため。

**命名（Python）:** 識別子は **snake_case**。AmiVoice 応答 JSON のフィールド名（`starttime`, `utteranceid` 等）は **ベンダー形式のまま** パースし、変換後のみ snake_case とする。

## 1. 概要

- **製品:** AmiVoice API（WebSocket インターフェース）
- **役割:** ローカル PC 上の再生音声（YouTube / Zoom PC アプリ等）を VB-Cable 経由でキャプチャし、AmiVoice にストリーム送信する。発話区間ごとの確定結果を `transcription_port.on_utterance` に渡す
- **MVP:** 途中結果（partial）は扱わず、**発話区間確定 1 件 = 1 回** `record_utterance` 相当の処理とする
- **公開範囲:** アプリは **localhost のみ**（インターネット向けに AmiVoice Webhook を開かない）。ソースコードは GitHub 公開可（API キーはコミットしない）

### 1.1 プロダクト前提（音声経路）

| 項目 | 内容 |
|------|------|
| 利用者 | ローカル 1 人 |
| 音声源 | YouTube / Zoom **PC アプリ** 等の音声トラック |
| キャプチャ | OS **既定出力を VB-Cable**（仮想オーディオデバイス） |
| 講義動画 | ブラウザ / Zoom で **別ウィンドウ再生**。本アプリは文字起こし・対話のみ |
| `lecture_time_anchor` | **講義タイムライン（utterance 軸）** と同期（動画 `currentTime` との自動連動は MVP 不要） |
| ネットワーク | MVP は **オンライン必須**（AmiVoice・LLM） |
| 講義長 | 30〜60 分 / 回 |

### 1.2 設計原則

| 原則 | 内容 |
|------|------|
| クライアント | 本システムが AmiVoice **WebSocket クライアント**として接続する（自前が WS サーバになる必要はない） |
| 内側への境界 | Interface には `speech_recognition_utterance_event` のみ渡す（`interface.md` §4 `record_utterance`） |
| 1 講義 = 1 セッション | `start_lecture` で AmiVoice セッション開始（`s`）、`end_lecture` で終了（`e`）。セッション内 ms は区間ごとに 0 基準でリセットされない（同一 `s`〜`e` 内の相対時間） |
| 交換可能性 | キャプチャデバイス（VB-Cable）や認識エンジン grammar（既定 `-a2-ja-general`）は `AMIVOICE_GRAMMAR_FILE_NAMES` で差し替え可能。Interface 契約は不変 |

## 2. コンポーネント一覧（MVP）

| 名前 | 層 | 責務 | 詳細 |
|------|-----|------|------|
| `amivoice_streaming_bridge` | Framework | WS 接続・PCM 送信・結果受信・event 変換 | §4 |
| `wrp_session` / `wrp_import` | Framework | 公式 Wrp クライアント（vendor）による 1 講義 = 1 セッション | §4.2 |
| `audio_capture_source` | Framework | VB-Cable 出力端子から PCM 読み取り | §4.3 |
| `transcription_port` | Interface | `on_utterance` | `interface.md` |
| `record_utterance_controller` | Interface | event → UC | `interface.md` |

**実装（How）:** AmiVoice 接続は [Wrp Python クライアント](https://github.com/advanced-media-inc/amivoice-api-client-library/tree/main/Wrp/python) を `third_party/amivoice_wrp` に vendor し、`WrpAmiVoiceSession` が `connect` → `feedDataResume` → `feedData` → `feedDataPause` → `disconnect` を担う。確定結果は Wrp の `resultFinalized` のみを Bridge へ渡す（`resultUpdated` は MVP では無視）。

**主経路:** `audio_capture_source` → `amivoice_streaming_bridge` → `transcription_port`（**プロセス内呼び出し**。HTTP 不要）

**任意（テスト）:** `POST /internal/amivoice/utterances`（`framework.md` §4.3）— 手動で event を注入する際のみ

## 3. 音声フォーマットとセッション開始

### 3.1 送信フォーマット（MVP）

AmiVoice API 公式に合わせ、以下を送る。

| 項目 | MVP 値 |
|------|--------|
| エンコーディング | Signed 16-bit PCM |
| エンディアン | リトルエンディアン |
| チャンネル | モノラル |
| サンプリングレート | **16 kHz** |
| 開始コマンド（例） | `s LSB16K -a2-ja-general` |

**Why（16 kHz）:** 公式 WebSocket 例（`LSB16K`）と一致させ、Bridge 実装を単純にするため。

**備考:** VB-Cable 側デバイスのネイティブレートが異なる場合、Bridge が **リサンプルして 16 kHz PCM** に揃えてから送る（How は実装時）。

### 3.2 時刻の意味

| 時刻 | 意味 |
|------|------|
| `results[0].starttime` / `endtime` | 当該 AmiVoice セッション（`s`〜`e`）内での **相対 ms**（音声先頭 = 0） |
| 講義タイムライン | 1 本目の確定 `utterance` 記録時に Application が `lecture.started_at` を確立（`application.md` `record_utterance`）。以降の `time_range` は講義原点基準 |

## 4. `amivoice_streaming_bridge` 詳細

<!-- 仕様: docs/spec/interface.md#record_utterance_controller -->

* 意図: AmiVoice WebSocket でリアルタイム認識し、発話区間確定ごとに文字起こしを記録する
* 起動: `start_lecture` 成功後にセッション開始。`end_lecture` でセッション終了

### 4.1 認証・設定

| 項目 | 内容 |
|------|------|
| 秘密情報 | `AMIVOICE_API_KEY`（環境変数。`framework/settings`） |
| プロキシ（任意） | `AMIVOICE_PROXY_SERVER_NAME` — Wrp `setProxyServerName` 形式 `user:password@proxyhost:port`。未設定時はプロキシなし |
| WebSocket URL（任意） | `AMIVOICE_WS_URL`（末尾 `/` 必須。省略時 `wss://acp-api.amivoice.com/v1/`） |
| 接続エンジン（任意） | `AMIVOICE_GRAMMAR_FILE_NAMES`（省略時 `-a2-ja-general`。Wrp `setGrammarFileNames`） |
| 読み込み | Composition root のみ |
| 話者表示名 | `speaker_display_name` 設定値（例: 講師名）。MVP では AmiVoice 話者分離に依存しない |

### 4.2 講義ライフサイクルとの同期

| アプリ操作 | Bridge の動作 |
|------------|---------------|
| `start_lecture` 成功 | Wrp `connect` → `feedDataResume`（内部で `s LSB16K -a2-ja-general` 相当）→ PCM ストリーム開始 |
| 講義中 | キャプチャ → `feedData`（送信ペースは `getWaitingResults` で調整）→ `resultFinalized` 受信ループ |
| `end_lecture` 成功 | `feedDataPause`（`e`）→ `disconnect`（発話ごとに pause しない） |

**Why:** ユーザー認識の「音声認識のスタート・終了」を、AmiVoice セッション境界と一致させるため。

### 4.3 音声キャプチャ（VB-Cable）

| 項目 | 内容 |
|------|------|
| 前提 | OS 既定出力が **VB-Cable Input** に向いている |
| 入力デバイス | **VB-Cable**（macOS）または **CABLE Output**（Windows）等のキャプチャ端子から PCM を読み取る。不一致時は `AUDIO_CAPTURE_DEVICE` で名前を指定 |
| 責務 | 16 kHz / 16-bit / mono に整形したバイト列を Bridge が AmiVoice へ送る |

### 4.4 AmiVoice 応答 JSON（発話区間ごと）

発話区間ごとに、概ね次の構造のメッセージが得られる（公式ドキュメント・ベンダー形式のフィールド名）。

```json
{
  "results": [
    {
      "starttime": 0,
      "endtime": 1200,
      "tokens": [],
      "confidence": 0.95,
      "tags": [],
      "rulename": "",
      "text": "書き起こし結果"
    }
  ],
  "text": "書き起こし結果",
  "code": "",
  "message": "",
  "utteranceid": "..."
}
```

| フィールド | MVP で使用 |
|------------|-----------|
| `text`（body ルート） | ○（成功判定・`transcript` の正） |
| `code` / `message` | ○（成功 / エラー判定） |
| `utteranceid` | ○ |
| `results[0].starttime` / `endtime` | ○ |
| `results[0].text` | ×（`body.text` を正とする） |
| `tokens` / `confidence` / `tags` / `rulename` | × |

### 4.5 認識成功の判定

AmiVoice から **発話区間ごとに 1 件** メッセージが届く前提で、ペイロード（以下 **body** — JSON ルート、または `body` キー配下のオブジェクト）を次で判定する。

| 条件 | 意味 |
|------|------|
| `body.code == ""` | エラーコードなし（リクエスト成功時は空文字） |
| `body.message == ""` | エラーメッセージなし（成功時は空文字） |
| `body.text != ""` | 書き起こし本文あり |

実装では、受信 JSON がルート直下に `code` / `message` / `text` を持つ場合はそれを body とみなす。ネスト `{ "body": { ... } }` の場合は `body` 直下を読む。

**partial:** MVP では **上記を満たす発話区間メッセージのみ** を UC に渡す。途中の仮更新は Interface / Application に渡さない。発話区間ごとに 1 回上記が来る前提とする。

### 4.6 エラー時

| 条件 | Bridge の動作 |
|------|---------------|
| `body.code != ""` または `body.message != ""` | `transcription_port` を呼ばない。ログに記録（任意で UI 通知は Framework） |
| `body.text == ""` | スキップ |
| `results` が空、または `starttime` / `endtime` が取得できない | スキップ（ログ） |

講義全体や AmiVoice セッションは、1 区間の失敗では **即停止しない**（可能なら継続）。

### 4.7 変換：AmiVoice 応答 → `speech_recognition_utterance_event`

| 入力（AmiVoice・成功時） | 出力（event） |
|--------------------------|---------------|
| （Bridge が保持） | `lecture_id` |
| `utteranceid` | `utterance_id` |
| `results[0].starttime` | `start_ms` |
| `results[0].endtime` | `end_ms` |
| `body.text`（ルートの `text`） | `transcript` |
| 設定値 | `speaker_display_name` |

### 4.8 処理フロー

```
start_lecture 成功
  → amivoice_streaming_bridge.start_session(lecture_id)
  → Wrp connect + feedDataResume
  → audio_capture_source から PCM 送信（ループ）

resultFinalized（発話区間ごと）
  → §4.5 成功判定
  → speech_recognition_utterance_event 組み立て
  → transcription_port.on_utterance(event)
  →（成功）record_utterance_controller → Orchestrator

end_lecture 成功
  → feedDataPause + disconnect
```

### 4.9 責務外

- `RecordUtteranceRequest` 以降の講義状態・永続化ロジック（Application）
- 文字起こし・対話の ViewModel 更新（`transcript_view_port` は別経路。発話記録後はフロントのポーリング等）
- LLM 呼び出し

## 5. 受入基準

### 5.1 `amivoice_streaming_bridge`

1. `start_lecture` 後に AmiVoice セッションが 1 本開始される
2. `end_lecture` 後にセッションが終了する
3. 成功応答（§4.5）に対し、`transcription_port.on_utterance` が **1 区間 1 回** 呼ばれる
4. `body.code` / `body.message` が非空の応答では `on_utterance` を呼ばない
5. `body.text` が空の応答では `on_utterance` を呼ばない
6. 変換後 event の `transcript` は `body.text` と一致する
7. `start_ms` / `end_ms` は `results[0].starttime` / `endtime` と一致する
8. `utterance_id` は `utteranceid` と一致する
9. Bridge が Domain エンティティを直接生成しない
10. 送信音声は 16 kHz / 16-bit PCM / mono である（テストでは送出バイト列を検証）

### 5.2 結合（任意）

1. `on_utterance` 成功後、文字起こし用 `utterance` が記録される。MVP では LLM / Orchestrator は起動しない（`framework_llm.md` §2）
2. 同一 `utteranceid` の再送時、Application が同一 `utterance_id` で更新する（`application.md` `record_utterance`）

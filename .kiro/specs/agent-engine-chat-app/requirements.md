# Requirements Document

## Project Description

このプロジェクトは、**Vertex AI Agent Engineを使ったステートフル対話アプリケーション**です。Memory BankとSessionsを活用して、ユーザーとの関係性を記憶し、シーンに応じた画像を生成する対話体験を提供します。

### 主な特徴

- AIキャラクターとテキストベースでの会話
- キャラクターの感情に応じた画像の動的生成（Gemini 3 Image使用）
- 会話履歴の管理と一貫性のある応答
- Agent Engineの記憶機構を活用
  - **Sessions**: 短期記憶（直近の会話文脈）
  - **Memory Bank**: 長期記憶（親密度、過去の重要な出来事）
- Vertex AI（Gemini API）を活用した高品質な対話と画像生成

### 画面構成

```
┌─────────────────────────────────┐
│  [キャラクター画像表示エリア]      │
│     (常に表示、表情・雰囲気変化)    │
├─────────────────────────────────┤
│  会話ログエリア                    │
│  キャラ: 「こんにちは!」           │
│  あなた: 「元気?」                │
│  キャラ: 「うん、元気だよ♪」       │
├─────────────────────────────────┤
│  [メッセージ入力欄] [送信ボタン]   │
└─────────────────────────────────┘
```

### 技術デモの焦点

このプロジェクトは、以下の技術要素のデモンストレーションを目的としています：

1. **Agent Engineの記憶機構**
   - Sessionsによる短期記憶管理
   - Memory Bankによる長期記憶管理
   - 記憶の使い分け設計

2. **構造化出力**
   - LLMからのJSON形式データ抽出
   - 感情・シーン情報の構造化

3. **画像生成統合**
   - Gemini 3 Imageとの連携
   - 対話に応じた動的画像生成
   - 画像生成トリガーの最適化

## 要件

### 要件1: キャラクター画像表示機能
**目的:** ユーザーとして、AIキャラクターの現在の感情状態を視覚的に理解できるようにするため、感情・シーンに応じた画像を表示したい

#### 受入基準
1. WHEN システムが起動された THEN Chat System SHALL キャラクター画像表示エリアにデフォルトの画像を表示する
2. WHEN AIキャラクターが会話応答を生成した THEN Chat System SHALL 感情カテゴリ・シーン・親密度の変化を判定する
3. IF 感情カテゴリが変化した（例: neutral→positive）またはシーンが変化した THEN Chat System SHALL 新しい画像を同期生成する
4. IF 感情カテゴリが同じ（例: happy→excited）かつシーン変化なしかつ親密度変化が±10未満 THEN Chat System SHALL 現在表示中の画像を維持する
5. IF 同一の感情×シーンの組み合わせが過去に生成済みである THEN Chat System SHALL キャッシュされた画像を返し、APIを呼ばない
6. WHILE 画像が生成中である THEN Chat System SHALL ローディング表示を行い、生成完了まで待機する
7. WHEN 画像生成が完了した THEN Chat System SHALL 新しい画像を表示する
8. IF 画像生成がエラーになった THEN Chat System SHALL 前回の画像を維持し、エラーログを記録する

### 要件2: 会話機能
**目的:** ユーザーとして、AIキャラクターと自然で一貫性のある会話を楽しむために、テキストベースで対話したい

#### 受入基準
1. WHEN ユーザーがメッセージを入力して送信ボタンを押した THEN Chat System SHALL メッセージを会話ログに追加し、Agent Engineにリクエストを送信する
2. WHEN Agent Engineから応答を受信した THEN Chat System SHALL キャラクターのメッセージとして会話ログに追加する
3. WHILE Agent Engineが応答を生成中である THE Chat System SHALL 送信ボタンを無効化し、ローディング状態を表示する
4. IF ユーザーが空のメッセージを送信しようとした THEN Chat System SHALL 送信を拒否し、エラーメッセージを表示する
5. WHEN 会話ログが更新された THEN Chat System SHALL 自動的に最新のメッセージまでスクロールする

### 要件3: 会話履歴管理（Sessions）
**目的:** ユーザーとして、過去の会話の文脈を維持した自然な対話を続けられるようにするため、直近の会話履歴を管理したい

#### 受入基準
1. WHEN ユーザーがメッセージを送信した THEN Chat System SHALL そのメッセージをSessionsに記録する
2. WHEN Agent Engineが応答を生成する THEN Chat System SHALL Sessionsから直近の会話文脈を取得して利用する
3. WHEN 会話が一定時間（例: 30分）継続していない THEN Chat System SHALL Sessionを終了し、新しいSessionを開始する
4. WHERE 会話履歴を保存する THE Chat System SHALL タイムスタンプとともに保存する

### 要件4: 長期記憶管理（Memory Bank）
**目的:** ユーザーとして、セッションをまたいで関係性や重要な情報を記憶してもらうため、長期記憶を管理したい

#### 受入基準
1. WHEN 会話中に重要な情報（ユーザーの好み、過去の出来事、親密度の変化）が発生した THEN Chat System SHALL その情報をMemory Bankに記録する
2. WHEN 新しいSessionが開始された THEN Chat System SHALL Memory Bankから関連情報を取得し、会話文脈に組み込む
3. WHEN ユーザーが過去の出来事に言及した THEN Chat System SHALL Memory Bankから該当情報を検索し、整合性のある応答を生成する
4. WHERE Memory Bankに情報を保存する THE Chat System SHALL カテゴリ（親密度、好み、出来事など）とともに保存する

### 要件5: 親密度システム
**目的:** ユーザーとして、対話を通じて関係性が発展していく体験を得るため、親密度レベルを管理したい

#### 受入基準
1. WHEN システムが初期化された THEN Chat System SHALL 親密度を0に設定する
2. WHEN ユーザーとキャラクターが対話した THEN Chat System SHALL LLMが会話内容に基づいてStructuredResponseのaffinity_levelを更新する（範囲: 0-100）
3. WHEN 会話ターンが完了した THEN Chat System SHALL ConversationServiceがFirestore（user_statesコレクション）にaffinity_levelを記録する
4. WHEN 新しいSessionが開始された THEN Chat System SHALL initialize_sessionツールがFirestoreから親密度を読み込み、シーンと感情をランダムに初期化する
5. WHEN Agent Engineが応答を生成する THEN Chat System SHALL コンテキストメッセージの親密度レベルに応じた応答トーンを使用する
6. WHERE 親密度が計算される THEN Chat System SHALL LLMがポジティブな会話で増加、ネガティブな会話で減少するロジックを判断し、ConversationServiceは前ターンの値とStructuredResponseの値を比較してFirestoreに保存する

### 要件6: 構造化出力（JSON）
**目的:** 開発者として、LLMの応答から必要な情報を確実に抽出するため、構造化されたJSON出力を得たい

#### 受入基準
1. WHEN Agent Engineが応答を生成する THEN Chat System SHALL 以下の構造でJSON形式の応答を要求する：
```json
{
  "dialogue": "セリフ部分",
  "narration": "情景描写部分",
  "emotion": "happy|sad|neutral|surprised|thoughtful|embarrassed|excited|angry",
  "scene": "indoor|outdoor|cafe|park|school|home",
  "affinity_level": 0
}
```
注: `needsImageUpdate` / `affinityChange` / `isImportantEvent` / `eventSummary` はAgent Engineのカスタムツールに移行済みのため含まない。画像生成トリガーはConversationServiceがプログラム的に判定する。
2. IF JSON出力のパースに失敗した THEN Chat System SHALL デフォルト値（emotion: neutral, scene: indoor, affinity_level: 0）を使用し、エラーログを記録する

### 要件7: 画像生成プロンプト構築
**目的:** 開発者として、適切な画像を生成するため、シーン・感情情報に基づいたプロンプトを構築したい

#### 受入基準
1. WHEN 画像生成が必要と判定された THEN Chat System SHALL 以下の情報を組み合わせてプロンプトを構築する：
   - キャラクターの外見設定
   - 現在の感情（emotion）
   - 現在のシーン（scene）
   - 雰囲気・トーン
2. WHEN プロンプトを生成する THEN Chat System SHALL Gemini 3 Image APIに適した形式で出力する
3. WHERE 画像が生成される THE Chat System SHALL 生成された画像を適切なファイル名で保存する

### 要件8: エラーハンドリング
**目的:** ユーザーとして、エラー発生時も適切なフィードバックを受け取り、アプリケーションを継続利用できるようにしたい

#### 受入基準
1. IF Agent Engine APIへの接続が失敗した THEN Chat System SHALL エラーメッセージを表示する
2. IF 画像生成APIへの接続が失敗した THEN Chat System SHALL 前回の画像を維持し、会話は継続可能にする
3. WHEN エラーが発生した THEN Chat System SHALL エラー内容をログに記録する

### 要件9: ユーザーインターフェース
**目的:** ユーザーとして、デモに必要な最小限の操作ができるUIを通じて対話したい

#### 受入基準
1. WHEN 画面が表示される THEN Chat System SHALL 画像表示エリア、会話ログ、メッセージ入力欄を表示する
2. WHEN ユーザーがメッセージを入力する THEN Chat System SHALL Enterキーで送信できるようにする
3. WHEN 会話ログが更新される THEN Chat System SHALL 最新メッセージまでスクロールする
4. WHEN システムが処理中である THEN Chat System SHALL ローディング表示を行う

## 非機能要件

### セキュリティ
- API キーは環境変数で管理
- 公開リポジトリに機密情報を含めない

### デモ用の制約
- フロントエンド: ローカル環境で動作
- バックエンド: Vertex AI Agent Engine（GCP）を使用
- 画像生成は同期処理（生成完了まで待機）
- エラーハンドリングは基本的なログ出力のみ
- UIは機能を示せる最小限のデザイン

## 技術スタック

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: Next.js 14+ (TypeScript)
- **AI Platform**: Vertex AI Agent Engine
  - Memory Bank
  - Sessions
- **Image Generation**: Gemini 3 Pro Image（`gemini-3-pro-image-preview`、globalエンドポイント）
- **Storage**: File-based（`data/images/` をFastAPI `/images/` エンドポイントで配信）
- **State**: Cloud Firestore（親密度の永続化）

## 段階的開発プラン

**Phase 1: Agent Engine基礎**
- 最小限のAgent実装
- Sessions基本機能

**Phase 2: Memory Bank統合**
- Memory Bankの実装
- 親密度システムの統合

**Phase 3: 画像生成機能**
- Gemini 3 Imageとの連携
- 画像生成トリガーの実装

**Phase 4: フロントエンド統合**
- 最小限のUI実装
- エンドツーエンドフローの確認

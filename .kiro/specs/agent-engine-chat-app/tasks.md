# 実装計画

## 凡例
- **(P)**: 同レベルの前タスクと並列実行可能
- **前提**: タスクグループ開始に必要な先行タスク

- [x] 0. GCPインフラのセットアップ（実装開始前に完了必須）

- [x] 0.1 必要なAPIの有効化と認証設定
  - 必要なGCP APIの有効化（Vertex AI API、Cloud Firestore API）
  - ADC（Application Default Credentials）でのローカル認証確認（`gcloud auth application-default login`）
  - ローカル実行のためService Account Keyは不要（ADCで完結）
  - _Requirements: 8.1_

- [x] 0.2 Agent Engine + Memory Bankのセットアップ
  - Agent Engine インスタンスの作成（us-central1）
  - Memory Bank の有効化
  - Agent Engine ID を取得して .env に記録
  - sandbox スクリプトで Agent Engine + Memory Bank への接続を確認
  - _Requirements: 3.1, 4.1_

- [x] 1. プロジェクト基盤のセットアップ

- [x] 1.1 バックエンド環境の構築
  - Python 3.11+ 仮想環境と依存パッケージ（FastAPI、uvicorn、google-adk、pydantic、python-dotenv、google-cloud-firestore）の設定
  - 必要な環境変数（GCPプロジェクトID、Vertex AIロケーション、Agent Engine ID）を定義した .env.example の作成
  - FastAPI アプリのエントリポイントと設定管理モジュールの骨格実装
  - データ保存用ディレクトリ（images、characters）の作成と .gitignore 設定（sessions はAgent Engineがクラウド管理するため不要）
  - サンプルキャラクター設定ファイル(data/characters/character.json)の作成(name, personality, appearance_prompt フィールド)
  - JSON構造化ログの設定（timestamp、level、service、error_type フィールド）
  - _Requirements: 8.1, 8.3_

- [x] 1.2 (P) フロントエンド環境の構築
  - Next.js 14+ TypeScript プロジェクトの初期化（App Router、strict mode）
  - Tailwind CSS の設定
  - shadcn/ui の初期化（Card、Button、Input、ScrollArea、Skeleton コンポーネントの追加）
  - バックエンドとの通信を担うAPIクライアントの基本骨格と環境変数設定
  - _Requirements: 9.1_

- [ ] 2. バックエンドデータモデルの定義

- [x] 2.1 会話・メッセージのデータモデル定義
  - 感情（happy/sad/neutral/surprised/thoughtful）、シーン（indoor/outdoor/cafe/park）、役割（user/agent）の列挙型定義
  - メッセージ送受信のリクエスト・レスポンスモデルをフィールド制約付きで定義
  - 対話応答の構造化データモデル（セリフ、情景描写、感情、シーン、画像更新フラグ、親密度変化量、重要イベントフラグ、イベントサマリー）の定義
  - 会話セッションとメッセージのデータ構造定義
  - _Requirements: 2.1, 2.2, 6.1_

- [x] 2.2 (P) 画像生成のデータモデル定義 (前提: 2.1)
  - タスク2.1で定義済みのEmotionおよびScene列挙型を使ったImageGenerationRequestモデルの定義（emotion, scene, affinity_levelフィールド、affinity_levelは0-100の制約付き）
  - data/characters/character.jsonの型安全なロードを可能にするCharacterConfigモデルの定義（name, personality, appearance_promptフィールド）
  - _Requirements: 7.1_

- [ ] 3. (P) ADKエージェントの実装と動作確認 (前提: 0.2, 2.1)

- [x] 3.1 ADKエージェントの初期化とシステムインストラクション構築
  - Memory Bankサービスの接続設定
  - モデル: gemini-3.1-pro-preview を使用
  - キャラクター設定・各フィールドの意味・応答ルールのみをシステムインストラクションに記述（JSON形式の説明は不要。response_schemaがAPI側で構造を強制するため、プロンプトへの重複記述は品質低下の原因となる）
  - StructuredResponseをmodel_json_schema()でdict変換してresponse_schemaに渡す設定（generate_content_configパラメータを使用）
  - 毎ターンのユーザーメッセージに現在の親密度・シーン・感情を付加するメッセージ構築ロジックの実装（動的状態はシステムプロンプトではなくメッセージに含める）
  - _Requirements: 5.5, 6.1_

- [ ] 3.2 構造化出力とSession管理の設定
  - 構造化レスポンススキーマを指定したJSON強制出力の設定
  - VertexAiSessionServiceでSessionを明示的に作成し、session_idをADK Runnerに渡すSession管理の実装
  - Memory Bankからの関連記憶を毎ターン自動取得するPreloadMemoryToolと、LLMが過去の出来事を能動的に検索するLoadMemoryToolの設定
  - after_agent_callbackは空実装(return Noneのみ。Memory Bank保存判定はConversationServiceが担う)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.2, 4.3, 6.1_

- [ ] 3.3 JSONパースとエラーハンドリングの実装
  - 構造化レスポンスのJSONパース処理
  - JSONパース失敗時のデフォルト値フォールバック（感情: neutral、シーン: indoor、画像更新フラグ: false、重要イベントフラグ: false）
  - エラーログ記録
  - _Requirements: 6.2, 8.3_

- [ ] 3.4 ChatAgent単体動作確認
  - エージェントを直接呼び出して構造化レスポンスが返却されることを確認
  - セリフ・感情・シーン・画像更新フラグ・親密度変化量・重要イベントフラグ・イベントサマリーの全フィールドが期待する型・値で返ること確認
  - 複数ターンの会話で同一Sessionが維持されていることを確認
  - 過去の出来事に言及する会話を送信し、LoadMemoryToolが能動的にMemory Bank検索を行うことを確認
  - JSONパース失敗時にデフォルト値でフォールバックされることを確認（不正な応答を模擬）
  - _Requirements: 3.1, 3.2, 6.1, 6.2_

- [ ] 4. (P) MemoryManagerの実装と動作確認 (前提: 0.2, 2.1)

- [ ] 4.1 Memory Bank書き込み機能の実装
  - 重要イベント(好み・出来事)をMemory Bankへ書き込む機能の実装
  - Memory Bank検索はChatAgentのLoadMemoryToolが担うため、MemoryManagerでの検索実装は不要
  - _Requirements: 4.1, 4.4_

- [ ] 4.2 親密度管理とセッション初期状態のロジック実装
  - セッション開始時にFirestore（user_statesコレクション）から親密度を1回だけ読み込みメモリにキャッシュ（デフォルト値: 0）
  - ターン中はキャッシュから取得（Firestoreへの毎ターン読み込みを回避）
  - 親密度更新処理（0-100範囲制限、キャッシュ更新 + Firestoreへの保存）
  - セッション開始時のシーン・感情のランダム生成（scene: 4種からランダム、emotion: neutral固定またはランダム）
  - _Requirements: 5.1, 5.3, 5.4_

- [ ] 4.3 MemoryManager単体動作確認
  - Memory Bankへの書き込みが正常に動作することを確認
  - 親密度がFirestoreに正しく読み書きされることを確認
  - セッション開始時にシーン・感情がランダム生成されることを確認
  - 親密度が0-100の範囲外になった場合にクランプされることを確認
  - _Requirements: 4.1, 4.4, 5.1, 5.3, 5.4_

- [ ] 5. (P) ImageGenerationServiceの実装と動作確認 (前提: 1.1, 2.2)

- [x] 5.1 画像生成プロンプト構築ロジックの実装
  - `data/characters/character.json` の `appearance_prompt` を読み込み、感情・シーンを組み合わせた最終プロンプトを生成（例: `{appearance_prompt}, happy expression, cafe background`）
  - 感情とシーンの英語プロンプト表現へのマッピングテーブルの実装
  - Gemini Image APIに適したプロンプト形式での出力
  - _Requirements: 7.1, 7.2_

- [x] 5.2 Gemini 3 Pro Image API連携と画像保存の実装
  - Vertex AI Gemini 3 Pro Image APIへの同期呼び出し
  - キャラクター外見の一貫性維持設定（appearance_promptをベースに使用）
  - 生成画像を感情・シーン・タイムスタンプを組み合わせた命名規則でローカル保存し、ファイルパスを返す
  - 生成失敗時のリトライ（1回）とエラーログ記録
  - _Requirements: 1.3, 1.7, 7.3, 8.3_

- [x] 5.3 ImageGenerationService単体動作確認
  - 感情とシーンの組み合わせを指定してプロンプトが期待通りに構築されることを確認
  - 画像生成APIを呼び出して画像が生成され、データディレクトリに保存されることを確認
  - 生成ファイル名が命名規則（感情_シーン_タイムスタンプ.png）に従っていることを確認
  - APIエラー時のリトライ動作を確認
  - _Requirements: 1.3, 7.1, 7.2, 7.3_

- [ ] 6. ConversationServiceの実装 (前提: 3, 4, 5)

- [ ] 6.1 会話ターンのオーケストレーション実装
  - メッセージ送信処理：エージェント実行 → 構造化応答取得 → 親密度計算 → 親密度更新 → Memory Bank書き込み判定の順次処理
  - 現在の親密度・シーン・感情をエージェントのメッセージコンテキストに渡す仕組みの実装
  - 親密度変化量に基づく親密度更新（0-100範囲制限）
  - 親密度変化量±10以上またはisImportantEvent=trueの場合にeventSummaryをMemory Bankへ非同期書き込み(重要イベントの保存判定はConversationServiceが一元的に担う)
  - 会話応答データの組み立てと返却（次ターン用にシーン・感情を更新）
  - _Requirements: 2.1, 2.2, 4.1, 5.2, 5.6_

- [ ] 6.2 画像生成トリガー判定とフォールバックの実装
  - needsImageUpdateフラグ + 感情カテゴリ変更・シーン変更・親密度閾値超過（±10）の複合検証ロジック（LLMの提案をバックエンドが最終判定）
  - 判定が真の場合に画像生成サービスを同期呼び出し
  - 画像生成失敗時に前回の画像URL（またはnull）を維持するフォールバック処理
  - _Requirements: 1.2, 1.3, 1.4, 1.7, 8.2_

- [ ] 7. FastAPIルーターの実装とバックエンドE2E確認 (前提: 6)

- [ ] 7.1 ConversationRouterの実装
  - メッセージ送信エンドポイント（リクエスト受信 → 会話サービス委譲 → レスポンス返却）
  - 会話履歴取得エンドポイント（セッションIDとlimitパラメータ対応）
  - 依存性注入による各サービスの組み立て
  - _Requirements: 2.1, 8.1_

- [ ] 7.2 エラーハンドリングとヘルスチェックの実装
  - Agent Engine障害時のHTTP 503エラーと適切なエラーメッセージの返却
  - ヘルスチェックエンドポイント（Agent Engine・Firestoreの接続状態確認）
  - フロントエンドからのリクエストを受け付けるためのCORS設定
  - _Requirements: 8.1, 8.3_

- [ ] 7.3 バックエンドAPIのE2E動作確認
  - メッセージ送信エンドポイントを呼び出し、会話1ターンが正常に完了することを確認
  - 会話応答の全フィールド（セリフ、感情、シーン、親密度レベル等）が返却されることを確認
  - isImportantEvent=trueとなる会話を送信し、Memory Bankに記録されることを確認
  - 画像更新が必要な会話を送信し、画像URLが返却されることを確認
  - ヘルスチェックエンドポイントでバックエンドの接続状態が正常であることを確認
  - 連続2〜3ターンの会話でSessionが維持されていることを確認
  - _Requirements: 2.1, 2.2, 1.3, 3.1, 3.2, 4.1, 8.1_

- [ ] 8. (P) フロントエンド型定義とChatContextの実装 (前提: 2.1)

- [ ] 8.1 TypeScript型定義の実装
  - 会話リクエスト・レスポンス、メッセージ、チャット状態、コンテキスト値のインターフェース定義
  - 各UIコンポーネントのProps型定義
  - 感情・シーンのLiteral Union型定義
  - _Requirements: 2.1, 6.1_

- [ ] 8.2 ChatContext状態管理の実装
  - useReducerによる状態管理（メッセージ一覧、現在の画像URL、ローディング状態、画像生成中フラグ、親密度、セッションID）
  - メッセージ送信処理：バックエンドAPI呼び出し → 状態更新（メッセージ追加・画像URL更新・親密度更新）
  - API障害時のエラー状態管理とローディング状態のリセット
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 9. UIコンポーネントの実装とフロントエンド疎通確認 (前提: 8)

- [ ] 9.1 (P) CharacterImageDisplayコンポーネントの実装
  - 画像URLを受け取り画像を表示するコンポーネント（shadcn/ui の Card を使用）
  - 画像生成中のスピナー/Skeleton表示（shadcn/ui の Skeleton を使用）
  - 初回表示用のデフォルト画像設定
  - _Requirements: 1.1, 1.5, 1.6, 9.4_

- [ ] 9.2 (P) ConversationLogコンポーネントの実装
  - shadcn/ui の ScrollArea で会話ログを囲んだスクロール可能な表示領域
  - ユーザーメッセージ（右寄せ）とキャラクターメッセージ（左寄せ）を区別した表示
  - セリフと情景描写のスタイル分け表示
  - 最新メッセージへの自動スクロール
  - _Requirements: 2.2, 2.5, 9.3_

- [ ] 9.3 (P) MessageInputコンポーネントの実装
  - shadcn/ui の Input + Button を使用したテキスト入力フォームと送信ボタン
  - Enterキー送信対応
  - 空メッセージ送信の拒否（フロントエンドバリデーション）
  - ローディング中の入力欄とボタンの無効化
  - _Requirements: 2.1, 2.3, 2.4, 9.2, 9.4_

- [ ] 9.4 ChatPageの組み立て
  - ChatProviderでラップしたChatPageコンポーネントの実装
  - CharacterImageDisplay、ConversationLog、MessageInputを縦レイアウトで配置
  - _Requirements: 9.1_

- [ ] 9.5 フロントエンドとバックエンドの疎通確認
  - ブラウザでメッセージを入力・送信し、キャラクターの応答が会話ログに表示されることを確認
  - メッセージ送信中にローディング状態（送信ボタン無効化・スピナー表示）が表示されることを確認
  - 空メッセージ送信時に送信が拒否されることを確認
  - 画像更新が発生した際にキャラクター画像表示が新しい画像に切り替わることを確認
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 1.5, 1.6, 9.4_

- [ ] 10. デモシナリオの通し確認 (前提: 7, 9)

- [ ] 10.1 Memory Bankを使った記憶の永続化シナリオ確認
  - 重要なイベント（isImportantEvent=true）となる会話を行い、Memory Bankに記録されることを確認
  - 親密度が閾値（±10）を超える会話を行い、Memory Bankに記録されることを確認
  - Sessionをリセットして新しいSessionを開始後、Memory Bankから過去の情報が復元されることを確認
  - 新Session開始時にシーン・感情がランダムに初期化され、親密度が引き継がれることを確認
  - デモ用シナリオ（親密度0→親密度30→Session切替→記憶復元）を通して実行
  - _Requirements: 3.3, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4_

- [ ] 10.2 画像生成を含む完全な会話フローの確認
  - 感情・シーン変化が生じる会話を複数ターン実行し、画像生成トリガーが正しく動作することを確認
  - 画像生成中のローディング表示→完了後の画像切り替えの一連の流れを確認
  - 画像生成を意図的に失敗させ、前回画像が維持されたまま会話が継続できることを確認
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 7.1, 7.2, 7.3_

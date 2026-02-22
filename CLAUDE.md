# AI Chat Game - Vertex AI Edition

Agent Engine × Gemini 3 Imageを使ったステートフル対話アプリケーション

## Project Context

このプロジェクトは、Google Cloud関連登壇でのデモ用に開発されています。

### セッション概要
- **タイトル**: Agent Engine × Gemini 3 Imageで作るステートフル対話アプリ
- **テーマ**: Vertex AI Agent Engineを使った恋愛シミュレーション型対話アプリの構築
- **技術要素**: Memory Bank（長期記憶）、Sessions（短期記憶）、Gemini 3 Pro Image（画像生成）

### 目的
- Vertex AI Agent Engineの記憶機構（Sessions / Memory Bank）の実践的な活用方法を示す
- LLMから構造化データを抽出する設計パターンの共有
- 画像生成を対話アプリに組み込む際の考え方の紹介

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **AI Platform**: Vertex AI Agent Engine
  - Memory Bank: 長期記憶（親密度、過去の重要な選択）
  - Sessions: 短期記憶（直近の会話文脈）
- **Image Generation**: Gemini 3 Pro Image (Imagen 3)
- **Storage**: File-based (JSON)

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript 5+
- **Styling**: Tailwind CSS
- **State Management**: React Context API / Zustand

### Infrastructure
- **Platform**: Google Cloud Platform
- **Services**: Vertex AI, Cloud Storage

## Development Guidelines

### Think in English, Respond in Japanese
- 思考プロセスは英語で行う
- ユーザーへの応答は日本語で生成する

### Security & Privacy
- **NEVER commit**: API keys, credentials, service account files
- **Use `.env`**: All sensitive configuration must be in environment variables
- **Public repository**: This is a public demo project - keep all content appropriate

### Code Quality
- Type hints for all Python functions
- TypeScript strict mode enabled
- Clear, descriptive variable and function names
- Comprehensive error handling

### Git Workflow
- Commit messages in English
- Meaningful commit messages describing what and why
- Small, focused commits

## Project Structure

```
ai-chat-game-vertex/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core configuration
│   │   ├── services/     # Business logic
│   │   │   ├── agent_engine.py    # Agent Engine integration
│   │   │   ├── memory_bank.py     # Long-term memory management
│   │   │   ├── session.py         # Short-term memory management
│   │   │   └── image.py           # Gemini 3 Image integration
│   │   ├── models/       # Data models
│   │   └── utils/        # Utilities
│   └── tests/
├── frontend/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # React components
│   ├── hooks/            # Custom hooks
│   ├── lib/              # Utilities and API clients
│   └── types/            # TypeScript type definitions
├── data/                 # Data storage (gitignored)
│   ├── characters/       # Character configurations
│   └── sessions/         # Session data
└── docs/                 # Documentation
    └── architecture.md   # Architecture decisions
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Cloud Project with Vertex AI enabled
- Service account with appropriate permissions

### Environment Setup
1. Copy `.env.example` to `.env`
2. Set required environment variables
3. Place service account JSON in project root (ensure it's in .gitignore)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Implementation Roadmap

### Week 1: Agent Engine Foundation
- [ ] Vertex AI Agent Engine setup
- [ ] Minimal agent implementation
- [ ] Sessions basic functionality

### Week 2: Memory System
- [ ] Memory Bank implementation
- [ ] Sessions + Memory Bank integration
- [ ] State management (affinity, context)

### Week 3: Conversation Logic + Image Generation
- [ ] Conversation flow implementation
- [ ] Structured output (JSON) from Gemini
- [ ] Gemini 3 Image integration
- [ ] Image generation triggers

### Week 4: Integration & Demo Preparation
- [ ] End-to-end testing
- [ ] Demo scenario creation
- [ ] Demo video recording (backup)
- [ ] Presentation slides

## References

### Vertex AI Agent Engine
- [Agent Engine Documentation](https://cloud.google.com/vertex-ai/docs/agent-engine)
- [Memory Bank Guide](https://cloud.google.com/vertex-ai/docs/agent-engine/memory-bank)
- [Sessions Guide](https://cloud.google.com/vertex-ai/docs/agent-engine/sessions)

### Gemini API
- [Gemini 3 Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)
- [Imagen 3 Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/image/overview)

## License

MIT License - This is a demonstration project for educational purposes.


# AI-DLC and Spec-Driven Development

Kiro-style Spec Driven Development implementation on AI-DLC (AI Development Life Cycle)

## Project Context

### Paths
- Steering: `.kiro/steering/`
- Specs: `.kiro/specs/`

### Steering vs Specification

**Steering** (`.kiro/steering/`) - Guide AI with project-wide rules and context
**Specs** (`.kiro/specs/`) - Formalize development process for individual features

### Active Specifications
- Check `.kiro/specs/` for active specifications
- Use `/kiro:spec-status [feature-name]` to check progress

## Development Guidelines
- Think in English, generate responses in Japanese. All Markdown content written to project files (e.g., requirements.md, design.md, tasks.md, research.md, validation reports) MUST be written in the target language configured for this specification (see spec.json.language).

## Minimal Workflow
- Phase 0 (optional): `/kiro:steering`, `/kiro:steering-custom`
- Phase 1 (Specification):
  - `/kiro:spec-init "description"`
  - `/kiro:spec-requirements {feature}`
  - `/kiro:validate-gap {feature}` (optional: for existing codebase)
  - `/kiro:spec-design {feature} [-y]`
  - `/kiro:validate-design {feature}` (optional: design review)
  - `/kiro:spec-tasks {feature} [-y]`
- Phase 2 (Implementation): `/kiro:spec-impl {feature} [tasks]`
  - `/kiro:validate-impl {feature}` (optional: after implementation)
- Progress check: `/kiro:spec-status {feature}` (use anytime)

## Development Rules
- 3-phase approval workflow: Requirements → Design → Tasks → Implementation
- Human review required each phase; use `-y` only for intentional fast-track
- Keep steering current and verify alignment with `/kiro:spec-status`
- Follow the user's instructions precisely, and within that scope act autonomously: gather the necessary context and complete the requested work end-to-end in this run, asking questions only when essential information is missing or the instructions are critically ambiguous.

## Steering Configuration
- Load entire `.kiro/steering/` as project memory
- Default files: `product.md`, `tech.md`, `structure.md`
- Custom files are supported (managed via `/kiro:steering-custom`)

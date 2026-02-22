# Research & Design Decisions

## Summary
- **Feature**: agent-engine-chat-app
- **Discovery Scope**: New Feature (Greenfield)
- **Key Findings**:
  - ADK (Agent Development Kit) provides code-first framework with built-in Memory Bank/Sessions integration
  - VertexAiMemoryBankService simplifies Memory Bank operations with PreloadMemory/LoadMemory tools
  - Structured output via JSON schema is natively supported in Gemini API with strict validation
  - FastAPI service layer architecture with dependency injection aligns with clean architecture principles
  - Gemini 3 Pro Image requires paid tier ($0.134 per 1K-2K image) and has no code execution support

## Research Log

### ADK (Agent Development Kit) vs google-cloud-aiplatform SDK

- **Context**: Need to choose between low-level SDK and high-level ADK framework for Agent Engine integration
- **Sources Consulted**:
  - [ADK Documentation](https://google.github.io/adk-docs/)
  - [ADK Python Guide](https://google.github.io/adk-docs/get-started/python/)
  - [ADK Memory Integration](https://google.github.io/adk-docs/sessions/memory/)
  - [ADK Memory Bank Quickstart](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/quickstart-adk)
- **Findings**:
  - **ADK**: Code-first framework designed for agent development, model-agnostic, deployment-agnostic
  - **VertexAiMemoryBankService**: Built-in Memory Bank wrapper with simplified interface
  - **PreloadMemory tool**: Automatically retrieves memory at each turn's beginning
  - **LoadMemory tool**: Agent decides when to retrieve memory contextually
  - **ADK Runner**: Automatically manages sessions, orchestrates memory operations
  - **Authentication**: Uses `gcloud auth application-default login` (ADC)
  - **Latest release**: January 22, 2026, bi-weekly release cadence
  - **Deployment**: Can deploy to Cloud Run or scale with Vertex AI Agent Engine
  - **Callback system**: `auto_save_session_to_memory_callback` for automatic memory generation
- **Implications**:
  - ADK simplifies Memory Bank/Sessions integration compared to raw SDK
  - Use VertexAiMemoryBankService instead of manual API calls
  - Leverage PreloadMemory tool for automatic context loading
  - ADK Runner handles session lifecycle automatically
  - Code-first approach aligns with FastAPI service layer architecture
  - No need to manually implement SessionService (ADK provides session management)

### Vertex AI Agent Engine Memory Bank & Sessions

- **Context**: Need to understand how to implement two-layer memory (short-term Sessions + long-term Memory Bank) for stateful conversation
- **Sources Consulted**:
  - [Memory Bank Overview](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/overview)
  - [Agent Engine Sessions](https://docs.cloud.google.com/agent-builder/agent-engine/overview)
  - [Generate Memories](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/generate-memories)
- **Findings**:
  - Memory Bank stores user-scoped long-term memories extracted from conversations
  - Each memory is a "self-contained piece of information" with scope isolation per user
  - Sessions maintain chronological sequence of messages and actions (SessionEvents)
  - Integration pattern: CreateSession → AppendEvent → GenerateMemories → RetrieveMemories
  - Asynchronous memory generation supported for background processing
  - Memory revisions track changes over time
  - Security concern: "memory poisoning" (false stored information) requires adversarial testing
- **Implications**:
  - Use Sessions for short-term context (5-10 recent turns)
  - Use Memory Bank for affinity level, user preferences, important events
  - Generate memories asynchronously after conversation turn completion
  - Implement user-scoped isolation via `scope.user` field

### Structured Output (JSON Schema)

- **Context**: Need to extract emotion, scene, affinity change, and image generation trigger from LLM response
- **Sources Consulted**:
  - [Structured Output Documentation](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/control-generated-output)
  - [Instructor Integration](https://python.useinstructor.com/integrations/vertex/)
  - [JSON Mode Best Practices](https://medium.com/google-cloud/how-to-consistently-output-json-with-the-gemini-api-using-controlled-generation-887220525ae0)
- **Findings**:
  - Native JSON schema support via `response_schema` field in generation config
  - Must use `response_mime_type: "application/json"` to enable structured output
  - **Critical**: Never duplicate schema in prompt (reduces output quality)
  - Use clear field names with `description` for model guidance
  - Set fields as `required` when context allows
  - Use `nullable: true` for optional fields to reduce hallucinations
  - Complex schemas may trigger `InvalidArgument: 400` errors
  - Supported schema fields: `anyOf`, `enum`, `format`, `items`, `maximum`, `minimum`, `nullable`, `properties`, `required`
  - `propertyOrdering` can enforce generation sequence
- **Implications**:
  - Define Pydantic models for ConversationResponse with emotion, scene, needsImageUpdate, affinityChange
  - Convert Pydantic to JSON schema for Gemini API
  - Use `nullable` for affinityChange (may not change every turn)
  - Keep schema simple to avoid complexity errors

### Gemini 3 Pro Image (Imagen 3)

- **Context**: Need to generate character images dynamically based on emotion and scene
- **Sources Consulted**:
  - [Gemini 3 Pro Image Documentation](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-pro-image)
  - [Nano Banana Pro Guide](https://blog.google/technology/developers/gemini-3-pro-image-developers/)
  - [Production Guidance](https://iamdgarcia.medium.com/master-gemini-3-pro-image-api-for-production-visuals-practical-guidance-for-engineers-cc816a90cb82)
- **Findings**:
  - Model ID: `gemini-3-pro-image-preview`
  - Pricing: $0.134 per 1K-2K image, $0.24 per 4K image (no free tier)
  - Max input tokens: 65,536; Max output tokens: 32,768
  - Supports: Grounding with Google Search, Thinking mode, System instructions
  - Does NOT support: Code execution, function calling, context caching
  - Requires billing enabled on GCP project
  - Authentication via Application Default Credentials (ADC) or service account
- **Implications**:
  - Budget consideration: Demo needs ~20-30 images max (cost: ~$4-5)
  - Use system instructions to define character appearance consistently
  - Leverage "Thinking mode" for complex prompt interpretation
  - Cannot use function calling to trigger image generation (must parse JSON response)
  - Generate synchronously to simplify demo (no async/SSE required)

### FastAPI Service Layer Architecture

- **Context**: Need to structure backend services for maintainability and testability
- **Sources Consulted**:
  - [FastAPI Clean Architecture](https://github.com/ivan-borovets/fastapi-clean-example)
  - [Production-Grade Architecture](https://blog.stackademic.com/building-a-production-grade-fastapi-backend-with-clean-layered-architecture-7e3ad6deb0bb)
  - [Service Layer Best Practices 2025](https://medium.com/@abhinav.dobhal/building-production-ready-fastapi-applications-with-service-layer-architecture-in-2025-f3af8a6ac563)
- **Findings**:
  - Layered architecture: Presentation → Application → Domain → Infrastructure
  - Service layer contains all business logic and transaction management
  - Controllers should be thin (input validation + routing only)
  - Dependency injection for testability (DB sessions, settings, external APIs)
  - One-directional dependency flow (higher layers depend on lower, not reverse)
  - 2025-2026 best practice: Service layer is essential, not optional
- **Implications**:
  - Structure: API routers (thin) → Service layer (business logic) → Models (data)
  - Services: AgentEngineService, MemoryBankService, SessionService, ImageGenerationService
  - Use FastAPI dependency injection for service instantiation
  - Keep router logic minimal (validation + service call + response mapping)

### Next.js 14 State Management for Chat

- **Context**: Need to manage conversation state, loading states, and image updates in frontend
- **Sources Consulted**:
  - [React Context in Next.js](https://vercel.com/kb/guide/react-context-state-management-nextjs)
  - [Chat History Management](https://dev.to/programmingcentral/mastering-chat-history-state-in-nextjs-the-ultimate-guide-to-building-persistent-ai-apps-maf)
  - [Real-time Chat Best Practices](https://makersden.io/blog/reactjs-for-real-time-chat-best-practices)
- **Findings**:
  - React Context API supported in Next.js 14 Client Components
  - Multiple contexts prevent re-render issues (separate auth, theme, chat state)
  - useReducer + Context API for complex state management
  - Server Actions as synchronization bridge for client-server state
  - Custom hooks (e.g., useChat()) prevent prop drilling
  - Performance: Split state into multiple contexts to avoid unnecessary re-renders
- **Implications**:
  - Create ChatContext for conversation state (messages, loading, current image)
  - Use useReducer for complex state transitions (sending message, receiving response, updating image)
  - Custom hook useChatContext() for component access
  - Keep image state separate from message state to prevent re-render cascade
  - Simplify with synchronous API calls (no WebSocket/SSE for 15-min demo)

### Authentication & Service Account

- **Context**: Need to authenticate FastAPI backend with Vertex AI services
- **Sources Consulted**:
  - [Vertex AI Authentication](https://docs.cloud.google.com/vertex-ai/docs/authentication)
  - [Service Account without gcloud](https://medium.com/@lilianli1922/authenticating-vertex-ai-gemini-api-calls-in-python-using-service-accounts-without-gcloud-cli-e17203995ff1)
  - [FastAPI Vertex AI Boilerplate](https://github.com/lablab-ai/Google-VertexAI-FastAPI)
- **Findings**:
  - Two methods: Application Default Credentials (ADC) or direct service account
  - ADC checks: GOOGLE_APPLICATION_CREDENTIALS env var → gcloud auth → Compute Engine metadata
  - Direct approach: `Credentials.from_service_account_file(path)` + `vertexai.init(credentials=...)`
  - Required IAM role: "Vertex AI User"
  - Service account JSON file must be excluded from git (.gitignore)
- **Implications**:
  - Use GOOGLE_APPLICATION_CREDENTIALS env var for flexibility
  - Fallback to direct service account file if ADC not available
  - Initialize vertexai at application startup (not per-request)
  - Store service account path in .env file
  - Add service_account.json to .gitignore

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| Clean Architecture (Layered) | Separate concerns into Presentation → Application → Domain → Infrastructure layers | Clear boundaries, testable, scalable | Requires more boilerplate for simple operations | Recommended by 2025-2026 best practices |
| MVC Pattern | Model-View-Controller with FastAPI routers as controllers | Familiar pattern, straightforward | Can lead to fat controllers if not disciplined | Simpler but less maintainable long-term |
| Service-Oriented | Business logic in dedicated service classes, thin controllers | Strong separation of concerns, dependency injection friendly | Requires careful service boundary definition | Aligns with FastAPI DI system |

**Selected Approach**: Service-Oriented with Layered Architecture principles
- API routers act as thin presentation layer
- Service layer contains business logic (agent interaction, memory management, image generation)
- Models define data structures (Pydantic)
- Clear service boundaries prevent coupling

## Design Decisions

### Decision: Synchronous Image Generation

- **Context**: Image generation can be synchronous (blocking) or asynchronous (SSE/WebSocket)
- **Alternatives Considered**:
  1. Synchronous blocking - Wait for image generation to complete before returning response
  2. Asynchronous with SSE - Stream image generation status updates to frontend
  3. Asynchronous with polling - Frontend polls for image completion status
- **Selected Approach**: Synchronous blocking for MVP
- **Rationale**:
  - 15-minute demo doesn't require production-grade UX
  - Simplifies frontend (no SSE/WebSocket handling)
  - Simplifies backend (no job queue, no status tracking)
  - Gemini 3 Pro Image generation is reasonably fast (5-15 seconds)
  - Loading indicator provides sufficient user feedback
- **Trade-offs**:
  - Benefits: Simpler implementation, fewer moving parts, easier debugging
  - Compromises: User must wait during generation, no partial updates, longer perceived latency
- **Follow-up**: Consider async implementation if demo receives positive feedback and productionization is desired

### Decision: Memory Bank Update Strategy

- **Context**: When to update Memory Bank with new conversation insights
- **Alternatives Considered**:
  1. After every turn - Update Memory Bank after each user-agent exchange
  2. Periodic batch - Update Memory Bank every N turns or on session end
  3. Threshold-based - Update only when significant events occur (affinity change, preferences mentioned)
- **Selected Approach**: Threshold-based updates
- **Rationale**:
  - Reduces API calls and costs (Memory Bank operations are billed)
  - Memory Bank is for long-term facts, not every conversational detail
  - Aligns with demo focus (showing memory persistence, not frequency)
  - Affinity level changes are natural triggers (0→30, 30→60, etc.)
- **Trade-offs**:
  - Benefits: Cost-efficient, focused memories, less noise
  - Compromises: May miss subtle preference changes, requires logic to detect "significant events"
- **Follow-up**: Define clear thresholds in configuration (e.g., affinity delta >= 10, explicit preference statements)

### Decision: JSON Schema vs Function Calling

- **Context**: How to extract structured data (emotion, scene, needsImageUpdate) from LLM response
- **Alternatives Considered**:
  1. JSON Schema with structured output - Define schema, get guaranteed JSON response
  2. Function calling - Define functions for metadata extraction
  3. Manual parsing - Extract via regex/string manipulation from unstructured text
- **Selected Approach**: JSON Schema with structured output
- **Rationale**:
  - Gemini 3 Pro Image doesn't support function calling (documented limitation)
  - JSON schema provides guaranteed structure without post-processing
  - Native Gemini API support reduces complexity
  - Better than manual parsing (fragile, error-prone)
- **Trade-offs**:
  - Benefits: Guaranteed structure, no parsing errors, simpler code
  - Compromises: Schema complexity limits (must keep simple), model must understand schema semantics
- **Follow-up**: Test schema with various conversation scenarios to ensure robust extraction

### Decision: Frontend State Management

- **Context**: How to manage conversation state, loading states, and UI updates in Next.js frontend
- **Alternatives Considered**:
  1. React Context API - Built-in React state management
  2. Zustand - Minimal state management library
  3. Redux Toolkit - Full-featured state management
- **Selected Approach**: React Context API
- **Rationale**:
  - Demo has limited state complexity (messages, loading, currentImage)
  - Context API is built-in (no additional dependencies)
  - Sufficient for single-page chat UI
  - Team familiarity (standard React pattern)
- **Trade-offs**:
  - Benefits: No external dependencies, simple API, adequate for scope
  - Compromises: Potential re-render issues if state grows (mitigated by splitting contexts)
- **Follow-up**: Monitor re-render performance; switch to Zustand if issues arise

## Risks & Mitigations

- **Risk 1: Memory Bank cost accumulation** — Proposed mitigation: Implement threshold-based updates, monitor API usage, set budget alerts
- **Risk 2: Image generation failures blocking conversation** — Proposed mitigation: Fallback to previous image, log error, allow conversation to continue
- **Risk 3: JSON schema complexity exceeding limits** — Proposed mitigation: Keep schema minimal (5-7 fields max), test with complex scenarios early
- **Risk 4: Session timeout during long pauses** — Proposed mitigation: Document 30-minute timeout in UI, provide "resume conversation" flow
- **Risk 5: Service account credential exposure** — Proposed mitigation: .gitignore for credentials, environment variables, clear documentation in README

## References

- [Vertex AI Agent Engine Memory Bank Overview](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/overview)
- [Structured Output Documentation](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/control-generated-output)
- [Gemini 3 Pro Image Documentation](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-pro-image)
- [FastAPI Clean Architecture Example](https://github.com/ivan-borovets/fastapi-clean-example)
- [Production-Grade FastAPI with Service Layer](https://blog.stackademic.com/building-a-production-grade-fastapi-backend-with-clean-layered-architecture-7e3ad6deb0bb)
- [React Context API in Next.js](https://vercel.com/kb/guide/react-context-state-management-nextjs)
- [Vertex AI Authentication](https://docs.cloud.google.com/vertex-ai/docs/authentication)

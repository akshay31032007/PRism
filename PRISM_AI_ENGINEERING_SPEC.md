
# PRISM_AI_ENGINEERING_SPEC.md

# PRism AI Engineering Specification
Version: 1.0

## 1. Project Vision
PRism AI is a production-grade autonomous Pull Request review platform built using a multi-agent architecture.
Its objective is to reduce manual review effort while improving security, code quality, architecture consistency,
test coverage, dependency health, and documentation quality.

## 2. Core Principles
- Python 3.12+
- LangGraph for orchestration
- LangChain for LLM abstraction
- Pydantic models everywhere
- Clean Architecture
- SOLID, DRY, KISS
- Type-safe, modular, extensible
- No hardcoded secrets
- All configuration through `.env`

## 3. Overall Architecture
GitHub Webhook
→ Repository Loader
→ Context Builder
→ Diff Parser
→ LangGraph Workflow
→ Parallel Agents
→ Risk Aggregator
→ PR Summary
→ Final Review Report

## 4. Required Frameworks
- LangGraph
- LangChain
- langchain-openai
- langchain-anthropic
- langchain-google-genai
- qdrant-client
- tree-sitter
- GitPython
- sentence-transformers
- pydantic
- pydantic-settings
- tenacity
- structlog
- pytest

## 5. LangGraph Workflow
Nodes:
1. Repository Loader
2. Repository Context Builder
3. Diff Parser
4. Security Agent
5. Code Quality Agent
6. Architecture Agent
7. Documentation Agent
8. Test Coverage Agent
9. Dependency Agent
10. Repository QA Agent (RAG)
11. Risk Aggregation Node
12. PR Summary Node

Requirements:
- Parallel execution where possible
- Shared GraphState
- Retry support
- Checkpointing
- Human-in-the-loop ready
- Streaming capable

## 6. GraphState
Contains:
- RepositoryContext
- PullRequestContext
- ParsedDiff
- RepositoryTree
- ChangedFiles
- GitMetadata
- AgentResults
- TokenUsage
- ExecutionTime
- FinalRiskScore

Every node:
GraphState -> GraphState

## 7. AI Agent Specifications

### 7.1 Security Agent
Responsibilities:
- SQLi
- XSS
- CSRF
- SSRF
- Command Injection
- Path Traversal
- Hardcoded Secrets
- Auth/AuthZ
- OWASP Top 10
Output:
Severity, Confidence, Reasoning, Suggested Fix, File, Lines

### 7.2 Code Quality Agent
Checks:
- SOLID
- Clean Code
- Code Smells
- Complexity
- Dead Code
- Duplication
- Naming
- Refactoring suggestions

### 7.3 Architecture Agent
Checks:
- Layers
- Circular dependencies
- Coupling
- Cohesion
- Scalability
- Design patterns

### 7.4 Documentation Agent
Checks:
README, comments, API docs, docstrings, PR description consistency.

### 7.5 Test Coverage Agent
Checks:
- Missing tests
- Edge cases
- Unit & Integration tests
- Coverage gaps

### 7.6 Dependency Agent
Checks:
requirements.txt, package.json, pom.xml, Cargo.toml, go.mod
Finds:
- CVEs
- License issues
- Outdated packages
- Conflicts

### 7.7 Repository QA Agent
RAG Pipeline:
Repository → Chunking → Embeddings → Qdrant → Retriever → LLM
Must defend against prompt injection and repository poisoning.

### 7.8 PR Summary Agent
Produces:
- Executive Summary
- Strengths
- Weaknesses
- Risks
- Merge Recommendation
- Review Order

## 8. Shared Components
- BaseAgent
- AgentResult
- Issue
- PromptManager
- LLM Wrapper
- Embedding Wrapper
- Vector Store Wrapper
- Config Loader
- Logger
- Retry Handler
- JSON Validator
- Metrics
- Cache

## 9. LLM Layer
Support:
- OpenAI
- Anthropic
- Gemini
- Groq
- OpenRouter
- Azure OpenAI
- Ollama

Provider selected via environment variable only.

## 10. Embeddings
Support:
- OpenAI
- Voyage
- Jina
- Sentence Transformers

## 11. Vector Databases
Support:
- Qdrant
- Chroma
- FAISS

## 12. AST Analysis
Use Tree-sitter before invoking LLM reasoning.
Avoid regex-only analysis.

## 13. Reliability
Implement:
- Retry
- Exponential Backoff
- Circuit Breaker
- Timeouts
- Structured Logging
- Graceful Failure
- Caching

## 14. Security
- Never execute repository code
- Never expose secrets
- Sanitize inputs
- Protect against prompt injection
- Protect against RAG poisoning

## 15. Configuration
Create:
- .env.example
- config.py
- settings.py

Required variables:
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
OPENROUTER_API_KEY=
GROQ_API_KEY=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
VOYAGE_API_KEY=
JINA_API_KEY=
GITHUB_TOKEN=
GITHUB_APP_ID=
GITHUB_PRIVATE_KEY=
GITHUB_WEBHOOK_SECRET=
QDRANT_URL=
QDRANT_API_KEY=
POSTGRES_URL=
REDIS_URL=
LANGSMITH_API_KEY=
SENTRY_DSN=
DEFAULT_LLM_PROVIDER=
DEFAULT_EMBEDDING_PROVIDER=
DEFAULT_VECTOR_DB=

## 16. Folder Structure
Recommend:
ai/
├── agents/
├── graph/
├── prompts/
├── llm/
├── rag/
├── embeddings/
├── parsers/
├── models/
├── tools/
├── utils/
└── tests/

## 17. Testing
- Unit Tests
- Integration Tests
- Mock LLM Tests
- Regression Tests
Target coverage: 90%+

## 18. Delivery Strategy
Implement incrementally:
1. Folder structure
2. Shared models
3. Config
4. LangGraph workflow
5. BaseAgent
6. Security Agent
7. Code Quality Agent
8. Architecture Agent
9. Documentation Agent
10. Test Coverage Agent
11. Dependency Agent
12. Repository QA Agent
13. Risk Aggregator
14. PR Summary Agent
15. Tests
16. Documentation

## Final Validation
Before marking any task complete:
- Run formatting
- Run Ruff
- Run MyPy
- Run Pytest
- Verify JSON schema
- Verify graph execution
- Verify .env loading
- Verify provider switching
- Verify retries and logging

---

# Final Instruction

**Codex will review your entire work.**

The implementation must be production-ready, modular, fully documented, free of placeholder code, and follow this specification exactly.

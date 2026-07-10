$dirs = @(
"frontend/app/(auth)/login",
"frontend/app/(auth)/callback",
"frontend/app/dashboard",
"frontend/app/repositories",
"frontend/app/pull-request",
"frontend/app/reports",
"frontend/app/settings",
"frontend/app/api",
"frontend/components/ui",
"frontend/components/layout",
"frontend/components/dashboard",
"frontend/components/repository",
"frontend/components/pull-request",
"frontend/components/graphs",
"frontend/components/chat",
"frontend/components/editor",
"frontend/components/common",
"frontend/hooks",
"frontend/lib",
"frontend/services",
"frontend/store",
"frontend/types",
"frontend/utils",
"frontend/public",

"backend/api",
"backend/services",
"backend/database",
"backend/schemas",
"backend/utils",

"ai/orchestrator",
"ai/agents",
"ai/prompts",
"ai/llm",

"rag",

"ml/datasets",
"ml/models",

"scanners",

"docs",

"tests/frontend",
"tests/backend",
"tests/ai",
"tests/integration"
)

foreach($dir in $dirs){
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

$files = @(
"README.md",
".gitignore",
".env.example",

"frontend/app/globals.css",
"frontend/app/layout.tsx",
"frontend/app/loading.tsx",
"frontend/app/error.tsx",
"frontend/app/page.tsx",
"frontend/middleware.ts",
"frontend/next.config.ts",
"frontend/tailwind.config.ts",
"frontend/tsconfig.json",
"frontend/package.json",

"backend/api/auth.py",
"backend/api/github.py",
"backend/api/repository.py",
"backend/api/pull_request.py",
"backend/api/analysis.py",
"backend/api/reports.py",
"backend/api/health.py",

"backend/services/github_service.py",
"backend/services/analysis_service.py",
"backend/services/report_service.py",
"backend/services/rag_service.py",
"backend/services/prediction_service.py",

"backend/database/connection.py",
"backend/database/models.py",
"backend/database/crud.py",

"backend/config.py",
"backend/dependencies.py",
"backend/main.py",
"backend/requirements.txt",
"backend/.env",

"ai/orchestrator/graph.py",
"ai/orchestrator/workflow.py",
"ai/orchestrator/state.py",
"ai/orchestrator/router.py",

"ai/agents/repository_context_agent.py",
"ai/agents/security_agent.py",
"ai/agents/code_quality_agent.py",
"ai/agents/architecture_agent.py",
"ai/agents/performance_agent.py",
"ai/agents/testing_agent.py",
"ai/agents/documentation_agent.py",
"ai/agents/merge_recommendation_agent.py",

"ai/prompts/security.md",
"ai/prompts/quality.md",
"ai/prompts/architecture.md",
"ai/prompts/performance.md",
"ai/prompts/testing.md",
"ai/prompts/documentation.md",
"ai/prompts/merge.md",
"ai/prompts/report.md",

"ai/llm/openai.py",
"ai/llm/gemini.py",
"ai/llm/embeddings.py",
"ai/llm/llm_factory.py",

"ai/utils.py",

"rag/loader.py",
"rag/parser.py",
"rag/chunker.py",
"rag/embeddings.py",
"rag/vector_store.py",
"rag/retriever.py",
"rag/indexer.py",

"ml/preprocessing.py",
"ml/feature_engineering.py",
"ml/train_merge_risk.py",
"ml/train_risk_score.py",
"ml/predict.py",
"ml/evaluate.py",

"scanners/codeql.py",
"scanners/semgrep.py",
"scanners/trivy.py",
"scanners/gitleaks.py",

"docs/architecture.md",
"docs/api.md",
"docs/ai-agents.md",
"docs/setup.md"
)

foreach($file in $files){
    New-Item -ItemType File -Force -Path $file | Out-Null
}

Write-Host ""
Write-Host "✅ PRism-AI folder structure created successfully!"
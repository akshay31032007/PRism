"""PRism AI Agents — all agent classes in one import."""

from .security_agent          import SecurityAgent
from .code_quality_agent      import CodeQualityAgent
from .architecture_agent      import ArchitectureAgent
from .documentation_agent     import DocumentationAgent
from .testing_agent           import TestingAgent
from .performance_agent       import PerformanceAgent
from .repository_context_agent import DependencyAgent
from .merge_recommendation_agent import MergeRecommendationAgent

__all__ = [
    "SecurityAgent",
    "CodeQualityAgent",
    "ArchitectureAgent",
    "DocumentationAgent",
    "TestingAgent",
    "PerformanceAgent",
    "DependencyAgent",
    "MergeRecommendationAgent",
]

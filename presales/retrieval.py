import re
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field
from .models import Source


def tokens(text):
    normalized = re.sub(r"\s+", "", text.casefold())
    return set(normalized[i:i + 2] for i in range(len(normalized) - 1))


class EvidenceRetriever(BaseRetriever):
    """透明的词项/字符检索；访问过滤在打分之前执行，不是语义向量检索。"""
    records: list[Source]
    role: str
    deployment: str
    capability: str
    k: int = Field(default=8, ge=1)

    def _get_relevant_documents(self, query, *, run_manager):
        candidates = [r for r in self.records
                      if (r.access == "sales" or self.role == "reviewer")
                      and self.deployment in r.deployment
                      and r.capability == self.capability]
        query_tokens = tokens(query)
        ranked = sorted(candidates, key=lambda r: (
            len(query_tokens & tokens(r.title + r.content)) / max(len(query_tokens), 1),
            r.updated_at), reverse=True)
        return [Document(page_content=r.content, metadata=r.model_dump())
                for r in ranked[:self.k]]

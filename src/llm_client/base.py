"""Abstract LLM client interface.

Defines the `LLMClient` abstract base class and a small convenience
method `analyze_many` for batch analysis. Implementations should
provide `analyze_article` which returns an `ArticleAnalysis`.
"""

from abc import ABC, abstractmethod
from typing import List
from src.core.models import Article, ArticleAnalysis
import logging
from src.logging_utils import trace

logger = logging.getLogger(__name__)

class LLMClient(ABC):
    @trace
    @abstractmethod
    def analyze_article(self, article: Article) -> ArticleAnalysis:
        """
        - function: analyze_article
        - logic: Perform an LLM-based analysis for a single `Article` and map
                 the response to the `ArticleAnalysis` dataclass. Concrete
                 subclasses implement the call to a specific LLM provider.
        """
        pass

    @trace
    def analyze_many(self, articles: List[Article]) -> List[ArticleAnalysis]:
        """
        - function: analyze_many
        - logic: Convenience wrapper that sequentially calls `analyze_article`
                 for each item and returns the resulting list. Useful for
                 simple batching in tests or small datasets.
        """
        return [self.analyze_article(a) for a in articles]

if __name__ == "__main__":
    # tiny smoke test
    from dataclasses import asdict
    from src.core.models import Entity

    dummy_article = Article(
        id="test-1",
        title="Dummy title",
        body="This is a fake article body.",
        section=None,
        publication=None,
        url="http://example.com",
        raw={},
    )

    class DummyLLM(LLMClient):
        def analyze_article(self, article: Article) -> ArticleAnalysis:
            return ArticleAnalysis(
                article_id=article.id,
                sentiment=0.0,
                summary="Stub summary",
                key_entities=[Entity(text="Example", type="OTHER", salience=0.5)],
                topics=["stub"],
                confidence=1.0,
                raw_llm_response={"note": "stub"},
            )

    client = DummyLLM()
    res = client.analyze_article(dummy_article)
    logger.info("analysis=%s", asdict(res))

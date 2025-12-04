from abc import ABC, abstractmethod
from typing import List
from src.core.models import Article, ArticleAnalysis

class LLMClient(ABC):
    @abstractmethod
    def analyze_article(self, article: Article) -> ArticleAnalysis:
        pass

    def analyze_many(self, articles: List[Article]) -> List[ArticleAnalysis]:
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
    print(asdict(res))

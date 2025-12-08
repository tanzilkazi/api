from dataclasses import dataclass
from typing import List, Any, Dict
import logging
from src.logging_utils import trace

logger = logging.getLogger(__name__)


@dataclass
class Article:
    id: str
    title: str
    body: str
    section: str | None
    publication: str | None
    url: str
    raw: Dict[str, Any]


@dataclass
class Entity:
    text: str
    type: str
    salience: float


@dataclass
class ArticleAnalysis:
    article_id: str
    sentiment: float
    summary: str
    key_entities: List[Entity]
    topics: List[str]
    confidence: float
    raw_llm_response: Dict[str, Any]


@trace
def article_from_guardian(item: dict) -> Article:
    fields = item.get("fields", {})
    return Article(
        id=item["id"],
        title=fields.get("headline", item.get("webTitle", "")),
        body=fields.get("bodyText", ""),
        section=item.get("sectionName"),
        publication=fields.get("publication"),
        url=item.get("webUrl", ""),
        raw=item,
    )

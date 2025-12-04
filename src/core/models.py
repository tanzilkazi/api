from dataclasses import dataclass
from typing import List, Optional, Any, Dict

@dataclass
class Article:
    id: str
    title: str
    body: str
    section: Optional[str]
    publication: Optional[str]
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

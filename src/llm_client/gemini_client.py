# src/llm_client/gemini_client.py

import json
from dataclasses import asdict
from google import genai
from src.core.models import Article, ArticleAnalysis, Entity
from src.llm_client.base import LLMClient
from src.config import get_env

class GeminiLLMClient(LLMClient):
    """
    For now: returns a deterministic stub result.
    Later: plug in real OpenAI call in _call_llm().
    """
    def __init__(self) -> None:
        self.client = genai.Client(api_key=get_env("GEMINI_API_KEY", required=True))
        self.model = "gemini-2.5-flash"
        
    def analyze_article(self, article: Article) -> ArticleAnalysis:
        prompt = self._build_prompt(article)
        raw = self._call_llm(prompt)  # currently stubbed
        #TODO: parse response
        return self._parse_response(article.id, raw)

    def _build_prompt(self, article: Article) -> str:
        # This is where you define what you *ask* the LLM.
        # Even though we're stubbing now, keep it realistic.
        return f"""
        You are analysing a news article.

        Title: {article.title}
        Body (truncated to first 1000 chars):
        {article.body[:1000]}

        Return ONLY valid JSON with this structure:
        {{
          "sentiment": float between -1 and 1,
          "summary": string <= 3 sentences,
          "key_entities": [
            {{"text": string, "type": string, "salience": float between 0 and 1}}
          ],
          "topics": [string, ...],
          "confidence": float between 0 and 1
        }}
        """

    def _call_llm(self, prompt: str) -> dict:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                max_output_tokens=1000,
                temperature=0.0,
                top_p=1.0,
                response_mime_type="application/json"
            )
            
        )
        content = json.loads(response.text)
        # response = self.client.chat.completions.create(
        #     model=self.model,
        #     response_format={"type": "json_object"},
        #     messages=[
        #         {
        #             "role": "system",
        #             "content": "You are a news analysis engine that ONLY outputs JSON.",
        #         },
        #         {"role": "user", "content": prompt},
        #     ],
        # )
        # content = response.choices[0].message.content
        return content

    def _parse_response(self, article_id: str, data: dict) -> ArticleAnalysis:
        # Defensive parsing with defaults so a slightly wrong response won't crash everything.
        sentiment = float(data.get("sentiment", 0.0))
        summary = str(data.get("summary", "")).strip()
        topics_raw = data.get("topics") or []
        topics = [str(t) for t in topics_raw]

        entities_raw = data.get("key_entities") or []
        entities = []
        for e in entities_raw:
            try:
                entities.append(
                    Entity(
                        text=str(e.get("text", "")),
                        type=str(e.get("type", "UNKNOWN")),
                        salience=float(e.get("salience", 0.0)),
                    )
                )
            except Exception:
                # Skip malformed entity
                continue

        confidence = float(data.get("confidence", 0.0))

        return ArticleAnalysis(
            article_id=article_id,
            sentiment=sentiment,
            summary=summary,
            key_entities=entities,
            topics=topics,
            confidence=confidence,
            raw_llm_response=data,
        )


if __name__ == "__main__":
    # quick test of the stub
    dummy_article = Article(
        id="test-2",
        title="Climate change is accelerating",
        body="Scientists warn that global temperatures continue to rise...",
        section="Environment",
        publication="The Guardian",
        url="https://example.com/article",
        raw={},
    )

    client = GeminiLLMClient()
    analysis = client.analyze_article(dummy_article)
    print(analysis)

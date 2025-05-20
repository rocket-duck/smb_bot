import logging
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict, Any
from bot.config.links import LINKS

logger = logging.getLogger(__name__)

class ParseMessageService:
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
        # Лениво инициализируем модель (чтобы не тянуть при старте)
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        return self._model

    def find_links(self, raw_keyword: str) -> List[Tuple[str, str]]:
        """
        Основной entrypoint для поиска: чистим, фильтруем, семантически ищем,
        возвращаем до трёх (name, url).
        """
        keyword = self._sanitize(raw_keyword)
        if self._should_skip(keyword):
            logger.debug(f"Пропускаем запрос на статус: {keyword}")
            return []

        raw_results: List[Tuple[str, str, float]] = []
        self._recursive_search(LINKS, keyword, raw_results)
        # сортируем по score и отбрасываем ниже threshold
        filtered = [(k, u) for k, u, s in sorted(raw_results, key=lambda x: x[2], reverse=True)
                    if s >= self.threshold][:3]
        if not filtered:
            logger.debug("Совпадений не найдено для «%s»", keyword)
        return filtered

    def _sanitize(self, text: str) -> str:
        # экранируем HTML, вырезаем < >, не печатные символы и всё, кроме базовых
        from html import escape
        cleaned = escape(text)
        cleaned = re.sub(r'[<>]', '', cleaned)
        cleaned = re.sub(r'[\x00-\x1F\x7F]', '', cleaned)
        cleaned = re.sub(r'[^\w\s\?\!\.,\-]', '', cleaned)
        return cleaned.strip().lower()

    def _should_skip(self, kw: str) -> bool:
        # выносим логику отбрасывания «статусных» запросов
        if "не работает" in kw or "умер" in kw or "мерт" in kw or "жива" in kw:
            return True
        if re.search(r"\bработает\b", kw) and "как" not in kw:
            return True
        return False

    def _recursive_search(
        self,
        data: Dict[str, Any],
        keyword: str,
        results: List[Tuple[str, str, float]],
        parent: str = ""
    ) -> None:
        """
        Recursively traverse LINKS structure, matching by regex and semantic similarity.
        """
        for key, value in data.items():
            full_name = f"{parent} > {key}" if parent else key
            if isinstance(value, dict):
                # Leaf section with url and optional regex
                if "url" in value:
                    url = value["url"]
                    # Regex-based matching
                    for pattern in value.get("regex", []):
                        if re.search(pattern, keyword, re.IGNORECASE):
                            results.append((full_name, url, 1.0))
                            break
                    # Semantic matching on section name
                    if self._semantic_match(keyword, key):
                        score = self._semantic_score(keyword, key)
                        results.append((full_name, url, score))
                # Recurse into subsections
                if "subsections" in value:
                    self._recursive_search(value["subsections"], keyword, results, full_name)

    def _semantic_score(self, query: str, text: str) -> float:
        """
        Compute semantic cosine similarity between query and text.
        """
        q_emb = self.model.encode(query, convert_to_numpy=True)
        t_emb = self.model.encode(text, convert_to_numpy=True)
        # Convert torch tensors to numpy
        if hasattr(q_emb, "cpu"):
            q_emb = q_emb.cpu().numpy()
        if hasattr(t_emb, "cpu"):
            t_emb = t_emb.cpu().numpy()
        sim = float((q_emb @ t_emb) / (np.linalg.norm(q_emb) * np.linalg.norm(t_emb)))
        return sim

    def _semantic_match(self, query: str, text: str, threshold: float = 0.7) -> bool:
        """
        Check if semantic similarity >= threshold.
        """
        return self._semantic_score(query, text) >= threshold

# Default instance for import
parse_message_service = ParseMessageService()
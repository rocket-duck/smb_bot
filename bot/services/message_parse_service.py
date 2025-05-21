import logging
import re
import inspect
import pymorphy2
import pickle
import asyncio
import numpy as np
import os
import importlib.resources as ilr
import os
try:
    import requests
except ImportError:
    requests = None

from functools import lru_cache
from symspellpy import SymSpell, Verbosity
from collections import OrderedDict
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict, Optional, Set

from bot.services.alias_service import extend_aliases
from bot.config.links import LINKS


# Ensure data directory exists for persistent storage
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
INDEX_PATH = DATA_DIR / "index.pkl"

DISLIKED_PATH = DATA_DIR / "disliked.pkl"
# Path for keyword-based disliked mapping
KEYWORD_DISLIKED_PATH = DATA_DIR / "keyword_disliked.pkl"
# Path for like counts persistence
LIKES_PATH = DATA_DIR / "likes.pkl"


# Monkey-patch for Python 3.13 compatibility: define getargspec wrapper matching legacy signature
if not hasattr(inspect, 'getargspec'):
    _orig_full = inspect.getfullargspec
    def getargspec(func):
        spec = _orig_full(func)
        return spec.args, spec.varargs, spec.varkw, spec.defaults
    inspect.getargspec = getargspec


logger = logging.getLogger(__name__)

class ParseMessageService:
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
        # Try loading prebuilt index from disk
        if INDEX_PATH.exists():
            try:
                data = pickle.load(open(INDEX_PATH, "rb"))
                (self._section_names, self._section_urls,
                 self._inverted_index, self._section_lemmas) = data
                self._index_ready = True
            except Exception:
                pass
        # Лениво инициализируем модель (чтобы не тянуть при старте)
        self._model: SentenceTransformer | None = None
        self._morph = pymorphy2.MorphAnalyzer()
        self._section_names: List[str] = []
        self._section_urls: List[str] = []
        self._section_lemmas: List[List[str]] = []
        self._inverted_index: Dict[str, set[int]] = {}
        self._index_ready = False
        # Global disliked keywords from legacy data
        self._global_disliked: Set[str] = set()
        # Track disliked keywords per chat
        self._disliked: Dict[int, Set[str]] = {}
        # Load persisted disliked mapping if available
        if DISLIKED_PATH.exists():
            try:
                data = pickle.load(open(DISLIKED_PATH, "rb"))
                # Legacy format was a set of keywords
                if isinstance(data, dict):
                    self._disliked = data
                elif isinstance(data, set):
                    self._global_disliked = data
            except Exception:
                pass
        # Load persisted keyword-disliked mapping if available
        self._keyword_disliked: Dict[int, Dict[str, Set[str]]] = {}
        if KEYWORD_DISLIKED_PATH.exists():
            try:
                self._keyword_disliked = pickle.load(open(KEYWORD_DISLIKED_PATH, "rb"))
            except Exception:
                pass
        # Load persisted like counts
        self._likes: Dict[str, int] = {}
        if LIKES_PATH.exists():
            try:
                self._likes = pickle.load(open(LIKES_PATH, "rb"))
            except Exception:
                pass
        # In-memory LRU cache for find_links
        self._cache = OrderedDict()
        self._cache_size = 128
        # Initialize SymSpell for Russian spell correction
        self._symspell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        # Load frequency dictionary: first try package resource, otherwise download
        dict_path = None
        try:
            # Attempt to locate bundled dictionary via importlib.resources
            try:
                pkg_dict_path = str(ilr.files("symspellpy").joinpath("frequency_dictionary_ru.txt"))
            except Exception:
                pkg_dict_path = None
            if pkg_dict_path and os.path.exists(pkg_dict_path):
                dict_path = pkg_dict_path
            elif requests:
                # Download Russian frequency dictionary from FrequencyWords repository
                dict_path = DATA_DIR / "frequency_dictionary_ru.txt"
                url = (
                    "https://raw.githubusercontent.com/hermitdave/"
                    "FrequencyWords/master/content/2016/ru/ru_50k.txt"
                )
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    with open(dict_path, "wb") as f:
                        f.write(response.content)
                    logger.info("Downloaded frequency dictionary to %s", dict_path)
                except Exception as ex:
                    logger.warning("Failed to download frequency dictionary: %s", ex)
                    dict_path = None
            if dict_path:
                self._symspell.load_dictionary(str(dict_path), term_index=0, count_index=1)
            else:
                logger.warning("Frequency dictionary not available; spell correction disabled")
        except Exception as e:
            logger.warning("Failed to initialize frequency dictionary: %s", e)

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            model_name = 'paraphrase-multilingual-mpnet-base-v2'
            device = 'cpu'
            cache_folder = str(DATA_DIR / "hf_models")
            self._model = SentenceTransformer(model_name, device=device, cache_folder=cache_folder)
        return self._model

    @lru_cache(maxsize=512)
    def _encode(self, text: str) -> np.ndarray:
        return self.model.encode(text, convert_to_numpy=True)

    def find_links(self, raw_keyword: str, context: Optional[List[str]] = None, chat_id: Optional[int] = None) -> List[Tuple[str, str]]:
        keyword = self._sanitize(raw_keyword)
        logger.info("Sanitized keyword: '%s'", keyword)
        if self._should_skip(keyword):
            logger.debug(f"Пропускаем запрос на статус: {keyword}")
            return []
        # Spell-correct the sanitized keyword
        suggestions = self._symspell.lookup(keyword, Verbosity.CLOSEST, max_edit_distance=2)
        if suggestions:
            keyword = suggestions[0].term
        # Check cache
        cache_key = (keyword, tuple(context) if context else None)
        if cache_key in self._cache:
            # Move to end and return cached
            result = self._cache.pop(cache_key)
            self._cache[cache_key] = result
            return result
        # Ensure index built synchronously to avoid threading issues
        if not getattr(self, "_index_ready", False):
            self._prepare_index()
            self._index_ready = True
        # Build full query including context if needed
        full_query = " ".join(context + [keyword]) if context else keyword
        logger.info("Full query for semantic search: '%s'", full_query)
        # Lemmatize query
        tokens = re.findall(r'\w+', keyword.lower())
        logger.info("Extracted tokens: %s", tokens)
        lemmas = [self._morph.parse(token)[0].normal_form for token in tokens]
        logger.info("Computed lemmas: %s", lemmas)
        # Collect candidate section indices
        counts: Dict[int, int] = {}
        for lemma in lemmas:
            for idx in self._inverted_index.get(lemma, []):
                logger.info("Matching lemma '%s' against section '%s' (index %d)", lemma, self._section_names[idx], idx)
                counts[idx] = counts.get(idx, 0) + 1
        if not counts:
            results: List[Tuple[str, str]] = []
            # Cache the result
            self._cache[cache_key] = results
            if len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)
            return results
        # Select top candidates by match count
        top_idxs = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
        # Semantic reranking using SentenceTransformer embeddings
        candidate_names = [self._section_names[idx] for idx, _ in top_idxs]
        # Compute embeddings for query and candidates
        q_emb = self._encode(full_query)
        cand_embs = np.vstack([self._encode(name) for name in candidate_names])
        # Normalize embeddings
        q_emb = q_emb / np.linalg.norm(q_emb) if np.linalg.norm(q_emb) > 0 else q_emb
        norms = np.linalg.norm(cand_embs, axis=1, keepdims=True)
        cand_embs = cand_embs / np.where(norms == 0, 1, norms)
        # Compute cosine similarities
        sim_scores = cand_embs.dot(q_emb)
        # Sort candidates by similarity
        reranked = sorted(zip(top_idxs, sim_scores), key=lambda x: x[1], reverse=True)
        # Return top 3 links
        results: List[Tuple[str, str]] = []
        for ((idx, _), _) in reranked[:3]:
            results.append((self._section_names[idx], self._section_urls[idx]))
        # Filter out links disliked for this chat and keyword
        if chat_id is not None:
            # URLs disliked under this keyword
            keyword_urls = self._keyword_disliked.get(chat_id, {}).get(keyword, set())
            # Legacy URL-level dislikes
            legacy_urls = self._disliked.get(chat_id, set())
            combined = keyword_urls.union(legacy_urls)
            results = [(n, u) for n, u in results if u not in combined]
            logger.info("Filtered disliked URLs for chat %s and keyword '%s': %s -> %s",
                        chat_id, keyword, combined, results)
            # Boost results by like count
            results.sort(key=lambda item: self._likes.get(item[1], 0), reverse=True)
            logger.info("Results reordered by likes: %s", [(u, self._likes.get(u, 0)) for _, u in results])
        logger.info(f"Query: {keyword}, Results: {results}")
        # Cache the result
        self._cache[cache_key] = results
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)
        return results

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

    def _prepare_index(self) -> None:
        # Extend aliases for all entries before indexing
        extend_aliases(LINKS)
        # Build lists from flat LINKS structure
        self._section_names.clear()
        self._section_urls.clear()
        self._section_lemmas.clear()
        self._inverted_index.clear()
        for entry in LINKS:
            full_name = entry["name"]
            self._section_names.append(full_name)
            self._section_urls.append(entry["url"])
        # Lemmatize and build inverted index
        for idx, name in enumerate(self._section_names):
            tokens = re.findall(r'\w+', name.lower())
            lemmas = [self._morph.parse(token)[0].normal_form for token in tokens]
            self._section_lemmas.append(lemmas)
            for lemma in lemmas:
                self._inverted_index.setdefault(lemma, set()).add(idx)
        # Persist index to disk for next startup
        try:
            pickle.dump(
                (self._section_names, self._section_urls, self._inverted_index, self._section_lemmas),
                open(INDEX_PATH, "wb")
            )
        except Exception:
            pass

    def register_dislike(self, chat_id: int, keyword: str, url: str) -> None:
        """
        Register URL-level dislike under specific query keyword
        """
        self._keyword_disliked.setdefault(chat_id, {}).setdefault(keyword, set()).add(url)
        logger.info("Registered dislike for url '%s' under keyword '%s' in chat %s",
                    url, keyword, chat_id)
        # Persist keyword-disliked mapping asynchronously
        loop = asyncio.get_event_loop()
        data = self._keyword_disliked
        loop.run_in_executor(None, lambda: pickle.dump(data, open(KEYWORD_DISLIKED_PATH, "wb")))

    def register_like(self, chat_id: int, url: str) -> None:
        """
        Increment like count for the given URL.
        """
        self._likes[url] = self._likes.get(url, 0) + 1
        logger.info("Registered like for url '%s'; total likes=%d", url, self._likes[url])
        # Persist likes asynchronously
        loop = asyncio.get_event_loop()
        data = self._likes
        loop.run_in_executor(None, lambda: pickle.dump(data, open(LIKES_PATH, "wb")))


parse_message_service = ParseMessageService()
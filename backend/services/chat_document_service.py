import asyncio
import re
from pathlib import Path
from typing import Any, Awaitable, Callable

from services.doc_parser import chunk_text, parse_document

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DOCS_DIR = DATA_DIR / "docs"
DOCUMENT_CATEGORIES = ("admin", "biz")
FALLBACK_SUPPORTED_EXTENSIONS = {".txt", ".md", ".doc", ".docx"}
COMPANY_INTRO_QUERY_MARKERS = ("介绍", "简介", "概况", "发展历程", "核心业务", "企业文化", "优势特色")
COMPANY_INTRO_SOURCE_BOOSTERS = ("简介", "概况", "企业文化", "发展历程", "核心业务")
COMPANY_DIRECTORY_SOURCE_MARKERS = ("分公司", "官方网站", "官网", "地址")
ASSISTANT_CAPABILITY_QUERY_MARKERS = (
    "你能做什么",
    "你会什么",
    "你能帮我做什么",
    "怎么用",
    "如何使用",
    "正确的使用",
    "用法",
    "功能",
    "操作说明",
    "使用指南",
    "自我介绍",
)
ASSISTANT_CAPABILITY_SOURCE_BOOSTERS = (
    "小易使用指南",
    "小易助手操作说明",
    "小易助手自我介绍",
    "小易助手赋能白皮书",
    "操作说明",
    "使用指南",
    "自我介绍",
    "赋能白皮书",
)
ADMIN_ROLE_LOOKUP_QUERY_MARKERS = (
    "职位",
    "职务",
    "岗位",
    "找谁",
    "对接",
    "负责人",
    "谁负责",
    "电话",
    "微信",
    "联系方式",
    "负责什么",
)
ADMIN_ROLE_DIRECTORY_SOURCE_BOOSTERS = (
    "行政部门岗位职责",
    "岗位职责",
    "人事类问题汇总",
)
PERSON_CONTACT_QUERY_MARKERS = ("电话", "微信", "联系方式", "职位", "职务", "岗位")
PHONE_NUMBER_PATTERN = re.compile(r"1\d{10}")
ASSISTANT_CAPABILITY_GENERIC_QUOTE_LINE = (
    "1. 智能报价查询 (Smart Quoting) 小易会基于系统内已接入并成功解析的最新报价表进行查询与对比。"
)
ASSISTANT_CAPABILITY_GENERIC_QUOTE_EXAMPLE = "“帮我查一下去美国的 FBA 海派，100kg，现在哪个渠道最便宜？”"


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _extract_person_name_from_query(query: str) -> str:
    normalized = _normalize_text(query)
    patterns = (
        r"([\u4e00-\u9fff]{2,4})(?=(?:电话|微信|联系方式))",
        r"([\u4e00-\u9fff]{2,4})(?=(?:是(?:什么)?(?:职位|职务|岗位)))",
        r"([\u4e00-\u9fff]{2,4})(?=(?:职位|职务|岗位))",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            return match.group(1)
    return ""


def _has_structured_contact_detail(content: str) -> bool:
    normalized = str(content or "")
    return any(marker in normalized for marker in ("电话：", "电话:", "微信：", "微信:", "联系方式")) or bool(
        PHONE_NUMBER_PATTERN.search(normalized)
    )


def _is_assistant_capability_query(query: str) -> bool:
    normalized_query = _normalize_text(query)
    return any(marker in normalized_query for marker in ASSISTANT_CAPABILITY_QUERY_MARKERS)


def _extract_query_terms(query: str) -> list[str]:
    normalized = _normalize_text(query)
    ascii_terms = re.findall(r"[A-Za-z0-9_]+", normalized.lower())
    chinese_terms = [
        token
        for token in re.split(r"[\s,.;:!?/\\|]+", normalized)
        if token and any("\u4e00" <= ch <= "\u9fff" for ch in token)
    ]
    chinese_ngrams = []
    for token in chinese_terms:
        condensed = "".join(ch for ch in token if "\u4e00" <= ch <= "\u9fff")
        if len(condensed) >= 2:
            chinese_ngrams.extend(condensed[index : index + 2] for index in range(len(condensed) - 1))
    return list(dict.fromkeys(ascii_terms + chinese_terms + chinese_ngrams))


def _iter_document_paths(docs_root: Path, category: str | None) -> list[tuple[Path, str | None]]:
    candidates: list[tuple[Path, str | None]] = []
    seen: set[tuple[str, str | None]] = set()

    if category in DOCUMENT_CATEGORIES:
        category_dir = docs_root / category
        if category_dir.exists():
            for path in sorted(category_dir.iterdir()):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in FALLBACK_SUPPORTED_EXTENSIONS:
                    continue
                key = (path.name, category)
                if key in seen:
                    continue
                seen.add(key)
                candidates.append((path, category))
        return candidates

    if docs_root.exists():
        for path in sorted(docs_root.iterdir()):
            if not path.is_file():
                continue
            if path.suffix.lower() not in FALLBACK_SUPPORTED_EXTENSIONS:
                continue
            key = (path.name, None)
            if key in seen:
                continue
            seen.add(key)
            candidates.append((path, None))

    for doc_category in DOCUMENT_CATEGORIES:
        category_dir = docs_root / doc_category
        if not category_dir.exists():
            continue
        for path in sorted(category_dir.iterdir()):
            if not path.is_file():
                continue
            if path.suffix.lower() not in FALLBACK_SUPPORTED_EXTENSIONS:
                continue
            key = (path.name, doc_category)
            if key in seen:
                continue
            seen.add(key)
            candidates.append((path, doc_category))

    return candidates


def _score_document_chunk(query_terms: list[str], source_name: str, content: str) -> int:
    source_haystack = source_name.lower()
    content_haystack = content.lower()
    score = 0
    for term in query_terms:
        if len(term) < 2:
            continue
        normalized_term = term.lower()
        source_hits = source_haystack.count(normalized_term)
        content_hits = content_haystack.count(normalized_term)
        if source_hits <= 0 and content_hits <= 0:
            continue
        score += source_hits * 4
        score += content_hits * 8
    return score


def _query_term_hit_count(query: str, source_name: str, content: str) -> int:
    haystack = f"{source_name} {content}".lower()
    terms = _extract_query_terms(query)
    return sum(1 for term in terms if term and term.lower() in haystack)


def _filter_supporting_documents(query: str, documents: list[dict]) -> list[dict]:
    if len(documents) <= 1:
        return documents

    best_distance = min(float(doc.get("distance", 1.0)) for doc in documents)
    hit_counts = [
        _query_term_hit_count(
            query,
            str((doc.get("metadata") or {}).get("source", "")),
            str(doc.get("document", "")),
        )
        for doc in documents
    ]
    best_hit_count = max(hit_counts, default=0)
    filtered_docs = []
    for doc, hit_count in zip(documents, hit_counts):
        metadata = doc.get("metadata") or {}
        source_name = str(metadata.get("source", ""))
        content = str(doc.get("document", ""))
        distance = float(doc.get("distance", 1.0))

        if best_hit_count > 0 and hit_count == 0:
            continue

        if hit_count > 0 or distance <= min(best_distance + 0.18, 0.45):
            filtered_docs.append(doc)

    return filtered_docs or documents[:1]


def _merge_document_candidates(query: str, primary_docs: list[dict], fallback_docs: list[dict]) -> list[dict]:
    primary_docs = list(primary_docs or [])
    fallback_docs = list(fallback_docs or [])
    if fallback_docs:
        best_primary_hits = max(
            (
                _query_term_hit_count(
                    query,
                    str((doc.get("metadata") or {}).get("source", "")),
                    str(doc.get("document", "")),
                )
                for doc in primary_docs
            ),
            default=0,
        )
        best_fallback_hits = max(
            (
                _query_term_hit_count(
                    query,
                    str((doc.get("metadata") or {}).get("source", "")),
                    str(doc.get("document", "")),
                )
                for doc in fallback_docs
            ),
            default=0,
        )
        if best_fallback_hits > best_primary_hits:
            return fallback_docs

    combined_docs = primary_docs + fallback_docs
    if len(combined_docs) <= 1:
        return combined_docs

    deduped_docs = []
    seen: set[tuple[str, str]] = set()
    for doc in combined_docs:
        metadata = doc.get("metadata") or {}
        dedupe_key = (str(metadata.get("source", "")), str(doc.get("document", "")))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped_docs.append(doc)

    return sorted(
        deduped_docs,
        key=lambda doc: (
            _query_term_hit_count(query, str((doc.get("metadata") or {}).get("source", "")), str(doc.get("document", ""))),
            -float(doc.get("distance", 1.0)),
        ),
        reverse=True,
    )


def _boost_company_intro_score(query: str, source_name: str, content: str, score: int) -> int:
    normalized_query = _normalize_text(query)
    if not any(marker in normalized_query for marker in COMPANY_INTRO_QUERY_MARKERS):
        return score

    if any(marker in source_name for marker in COMPANY_INTRO_SOURCE_BOOSTERS):
        score += 90
    if "公司概况" in content or "集团简介" in content:
        score += 30
    if any(marker in source_name for marker in COMPANY_DIRECTORY_SOURCE_MARKERS):
        score -= 45
    return score


def _boost_assistant_capability_score(query: str, source_name: str, content: str, score: int) -> int:
    if not _is_assistant_capability_query(query):
        return score

    if any(marker in source_name for marker in ASSISTANT_CAPABILITY_SOURCE_BOOSTERS):
        score += 120
    if "小易" in content and any(marker in content for marker in ("核心功能", "使用指南", "操作说明", "自我介绍")):
        score += 45
    return score


def _boost_admin_role_directory_score(query: str, source_name: str, content: str, score: int) -> int:
    normalized_query = _normalize_text(query)
    if not any(marker in normalized_query for marker in ADMIN_ROLE_LOOKUP_QUERY_MARKERS):
        return score

    person_name = _extract_person_name_from_query(query)
    content_hit_count = sum(
        1
        for term in _extract_query_terms(query)
        if len(term) >= 2 and term.lower() in content.lower()
    )

    if any(marker in source_name for marker in ADMIN_ROLE_DIRECTORY_SOURCE_BOOSTERS):
        score += 120
    if any(marker in content for marker in ("姓名", "职务", "岗位", "电话", "负责什么")):
        score += 45
    score += content_hit_count * 18
    if person_name:
        if person_name in content:
            score += 220
            if "姓名" in content:
                score += 60
        else:
            score -= 180
        if any(marker in normalized_query for marker in PERSON_CONTACT_QUERY_MARKERS):
            if _has_structured_contact_detail(content):
                score += 80
            else:
                score -= 180
        if not any(marker in content for marker in ("姓名", "职务", "岗位")) and not _has_structured_contact_detail(content):
            score -= 80
    return score


def _sanitize_assistant_capability_content(query: str, content: str) -> str:
    if not _is_assistant_capability_query(query):
        return content

    sanitized = str(content or "")
    sanitized = re.sub(
        r"1\.\s*智能报价查询\s*\(Smart Quoting\)\s*小易已经接入了多家主流国际物流渠道商（如：[^）]+）的最新报价表。",
        ASSISTANT_CAPABILITY_GENERIC_QUOTE_LINE,
        sanitized,
    )
    sanitized = re.sub(
        r"1\.\s*智能报价查询\s*\(Smart Quoting\)\s*小易已经接入了多家主流国际物流渠道商\([^)]*\)的最新报价表。",
        ASSISTANT_CAPABILITY_GENERIC_QUOTE_LINE,
        sanitized,
    )
    sanitized = re.sub(
        r"[“\"](?:金联|锦联|商翊|商壹|澳新|澳鑫|腾信|星野|易阳|亿阳)[^”\"\n]*最新[^”\"\n]*报价是多少？[”\"]",
        ASSISTANT_CAPABILITY_GENERIC_QUOTE_EXAMPLE,
        sanitized,
    )
    return sanitized


def _sanitize_documents_for_query(query: str, documents: list[dict]) -> list[dict]:
    if not documents:
        return documents

    sanitized_documents: list[dict] = []
    for doc in documents:
        sanitized_doc = dict(doc)
        sanitized_doc["metadata"] = dict(doc.get("metadata") or {})
        sanitized_doc["document"] = _sanitize_assistant_capability_content(
            query,
            str(doc.get("document", "")),
        )
        sanitized_documents.append(sanitized_doc)
    return sanitized_documents


async def search_documents_from_disk(
    query: str,
    category: str | None,
    top_k: int,
    *,
    docs_root: str | Path | None = None,
) -> list[dict]:
    docs_path = Path(docs_root) if docs_root is not None else DOCS_DIR
    if not docs_path.exists():
        return []

    query_terms = _extract_query_terms(query)
    if not query_terms:
        return []

    scored_chunks: list[dict] = []
    for file_path, file_category in _iter_document_paths(docs_path, category):
        try:
            text = await parse_document(str(file_path))
        except Exception:
            continue

        if not text.strip():
            continue

        for chunk in chunk_text(text):
            score = _score_document_chunk(query_terms, file_path.name, chunk)
            score = _boost_company_intro_score(query, file_path.name, chunk, score)
            score = _boost_assistant_capability_score(query, file_path.name, chunk, score)
            score = _boost_admin_role_directory_score(query, file_path.name, chunk, score)
            if score <= 0:
                continue
            scored_chunks.append(
                {
                    "score": score,
                    "distance": 1 / (1 + score),
                    "document": chunk,
                    "metadata": {
                        "source": file_path.name,
                        "category": file_category or category,
                    },
                }
            )

    scored_chunks.sort(key=lambda item: (-item["score"], item["distance"], item["metadata"]["source"]))
    deduped_chunks = []
    seen_chunks: set[tuple[str, str]] = set()
    for item in scored_chunks:
        dedupe_key = (item["metadata"]["source"], item["document"])
        if dedupe_key in seen_chunks:
            continue
        seen_chunks.add(dedupe_key)
        deduped_chunks.append(
            {
                "distance": item["distance"],
                "document": item["document"],
                "metadata": item["metadata"],
            }
        )
        if len(deduped_chunks) == top_k:
            break
    return deduped_chunks


async def retrieve_document_context(
    search_query: str,
    search_category: str,
    enable_rag: bool,
    top_k: int,
    *,
    get_embedding: Callable[[str], Awaitable[Any]] | None,
    search_documents: Callable[[Any, int, str | None], list[dict]] | None,
    rerank_documents: Callable[[str, list[dict]], list[dict]] | None,
    summarize_sources: Callable[[list[dict]], str],
    build_source_footer: Callable[[list[dict]], str],
    fallback_search_documents: Callable[[str, str | None, int], Awaitable[list[dict]]] | None = None,
) -> dict:
    result = {
        "context_text": "",
        "best_distance": 1.0,
        "similar_docs": [],
        "source_summary": "",
        "document_source_footer": "",
        "needs_realtime": True,
        "used_fallback": False,
    }

    if not enable_rag:
        return result

    similar_docs: list[dict] = []
    search_failed = False

    if get_embedding is not None and search_documents is not None and rerank_documents is not None:
        try:
            query_embedding = await get_embedding(search_query)
            similar_docs = await asyncio.to_thread(
                search_documents,
                query_embedding,
                top_k,
                search_category,
            )
            similar_docs = rerank_documents(search_query, similar_docs)
        except Exception:
            search_failed = True
            similar_docs = []

    should_try_fallback = (
        fallback_search_documents is not None
        and (
            not similar_docs
            or search_failed
        )
    )
    fallback_docs: list[dict] = []
    if should_try_fallback:
        fallback_docs = await fallback_search_documents(search_query, search_category, top_k)
        result["used_fallback"] = bool(fallback_docs)

    if fallback_docs:
        similar_docs = _merge_document_candidates(search_query, similar_docs, fallback_docs)

    similar_docs = _filter_supporting_documents(search_query, similar_docs)
    similar_docs = _sanitize_documents_for_query(search_query, similar_docs)
    result["similar_docs"] = similar_docs
    if not similar_docs:
        result["needs_realtime"] = not search_failed
        return result

    result["best_distance"] = similar_docs[0]["distance"]
    result["source_summary"] = summarize_sources(similar_docs)
    result["document_source_footer"] = build_source_footer(similar_docs)
    result["context_text"] = "".join(
        f"---\n[内部资料片段 {index + 1} | 来源: {doc['metadata'].get('source', '未知文档')}]\n{doc['document']}\n"
        for index, doc in enumerate(similar_docs)
    )
    result["needs_realtime"] = result["best_distance"] > 0.65
    return result

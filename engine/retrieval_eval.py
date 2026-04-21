import math
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple


class InMemoryVectorDB:
    """
    Vector DB tối giản dùng TF-IDF + cosine similarity.
    Dùng để benchmark retrieval khi chưa tích hợp DB production.
    """

    def __init__(self):
        self._idf: Dict[str, float] = {}
        self._doc_vectors: List[Tuple[str, Dict[str, float]]] = []

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\w+", (text or "").lower(), flags=re.UNICODE)

    @staticmethod
    def _normalize(vector: Dict[str, float]) -> Dict[str, float]:
        norm = math.sqrt(sum(v * v for v in vector.values()))
        if norm == 0:
            return {}
        return {term: value / norm for term, value in vector.items()}

    def build(self, docs: List[Dict[str, str]]) -> None:
        """
        docs: [{"id": "...", "text": "..."}]
        """
        if not docs:
            self._idf = {}
            self._doc_vectors = []
            return

        tokenized_docs = []
        doc_freq = Counter()
        for doc in docs:
            tokens = self._tokenize(doc["text"])
            term_freq = Counter(tokens)
            tokenized_docs.append((doc["id"], term_freq))
            for term in term_freq.keys():
                doc_freq[term] += 1

        total_docs = len(docs)
        self._idf = {
            term: math.log((1 + total_docs) / (1 + df)) + 1.0
            for term, df in doc_freq.items()
        }

        self._doc_vectors = []
        for doc_id, term_freq in tokenized_docs:
            vector = {term: count * self._idf.get(term, 0.0) for term, count in term_freq.items()}
            self._doc_vectors.append((doc_id, self._normalize(vector)))

    def search(self, query: str, top_k: int = 3) -> List[str]:
        if not self._doc_vectors:
            return []

        query_tf = Counter(self._tokenize(query))
        query_vector = {
            term: count * self._idf.get(term, 0.0) for term, count in query_tf.items()
        }
        query_vector = self._normalize(query_vector)
        if not query_vector:
            return []

        scored_docs = []
        for doc_id, doc_vector in self._doc_vectors:
            score = 0.0
            for term, q_val in query_vector.items():
                score += q_val * doc_vector.get(term, 0.0)
            scored_docs.append((score, doc_id))

        scored_docs.sort(key=lambda item: item[0], reverse=True)
        return [doc_id for _, doc_id in scored_docs[:top_k]]


class RetrievalEvaluator:
    def __init__(self, vector_db: Optional[InMemoryVectorDB] = None, top_k: int = 3):
        self.vector_db = vector_db or InMemoryVectorDB()
        self.top_k = top_k

    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3) -> float:
        """
        TODO: Tính toán xem ít nhất 1 trong expected_ids có nằm trong top_k của retrieved_ids không.
        """
        top_retrieved = retrieved_ids[:top_k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        """
        TODO: Tính Mean Reciprocal Rank.
        Tìm vị trí đầu tiên của một expected_id trong retrieved_ids.
        MRR = 1 / position (vị trí 1-indexed). Nếu không thấy thì là 0.
        """
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    async def evaluate_batch(self, dataset: List[Dict]) -> Dict:
        """
        Chạy eval cho toàn bộ bộ dữ liệu.
        Dataset cần có trường 'expected_retrieval_ids' và Agent trả về 'retrieved_ids'.
        """
        if not dataset:
            return {"avg_hit_rate": 0.0, "avg_mrr": 0.0, "total_cases": 0}

        docs_by_id: Dict[str, str] = {}
        for i, case in enumerate(dataset):
            metadata = case.get("metadata", {})
            source_doc = metadata.get("source_doc")
            expected_ids = case.get("expected_retrieval_ids", [])
            doc_id = source_doc or (expected_ids[0] if expected_ids else f"doc_{i}")
            context = case.get("context", "")

            if len(context) >= len(docs_by_id.get(doc_id, "")):
                docs_by_id[doc_id] = context

        docs = [{"id": doc_id, "text": text} for doc_id, text in docs_by_id.items()]
        self.vector_db.build(docs)

        total_hit_rate = 0.0
        total_mrr = 0.0
        evaluated = 0

        for case in dataset:
            expected_ids = case.get("expected_retrieval_ids", [])
            if not expected_ids:
                continue

            retrieved_ids = case.get("retrieved_ids")
            if not retrieved_ids:
                retrieved_ids = self.vector_db.search(case.get("question", ""), top_k=self.top_k)

            total_hit_rate += self.calculate_hit_rate(expected_ids, retrieved_ids, top_k=self.top_k)
            total_mrr += self.calculate_mrr(expected_ids, retrieved_ids)
            evaluated += 1

        if evaluated == 0:
            return {"avg_hit_rate": 0.0, "avg_mrr": 0.0, "total_cases": 0}

        return {
            "avg_hit_rate": total_hit_rate / evaluated,
            "avg_mrr": total_mrr / evaluated,
            "total_cases": evaluated,
        }

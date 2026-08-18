from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

import numpy as np
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class FAQMatcher:
    """FAQ retrieval engine using NLTK preprocessing + TF-IDF + cosine similarity."""

    FALLBACK = (
        "Sorry, I could not find an answer to that question. "
        "Please contact SecureBank customer support."
    )

    def __init__(self, faq_path: str | Path, threshold: float = 0.14):
        self.faq_path = Path(faq_path)
        self.threshold = threshold
        self.tokenizer = RegexpTokenizer(r"[A-Za-z0-9%$@.'-]+")
        self.stemmer = PorterStemmer()

        # Small built-in stopword set so Vercel does not need to download NLTK corpora.
        self.stop_words = {
            "a", "an", "the", "and", "or", "but", "to", "of", "for", "in", "on",
            "at", "by", "with", "from", "into", "is", "are", "was", "were", "be",
            "been", "being", "do", "does", "did", "can", "could", "would", "should",
            "i", "me", "my", "mine", "we", "our", "you", "your", "it", "this",
            "that", "these", "those", "please", "tell"
        }

        # Tiny synonym expansion improves common banking paraphrases while preserving
        # the required TF-IDF + cosine-similarity approach.
        self.synonyms = {
            "forgot": ["forget", "reset", "password"],
            "forgotten": ["forget", "reset", "password"],
            "stole": ["stolen", "lost", "theft"],
            "stolen": ["lost", "theft"],
            "missing": ["lost"],
            "cash": ["atm"],
            "withdraw": ["withdrawal", "atm"],
            "withdrawal": ["withdraw", "atm"],
            "transfer": ["send", "money"],
            "wire": ["transfer"],
            "charge": ["fee"],
            "fees": ["fee", "charge"],
            "refund": ["return", "money"],
            "fraud": ["unauthorized", "suspicious"],
            "scam": ["fraud", "suspicious"],
            "login": ["sign", "online", "banking"],
            "app": ["mobile", "banking"],
        }

        self.faqs: List[Dict] = json.loads(self.faq_path.read_text(encoding="utf-8"))

        # Match primarily against FAQ questions while including category words
        # for a little extra context.
        self.documents = [
            f"{faq['question']} {faq.get('category', '')}" for faq in self.faqs
        ]

        self.word_vectorizer = TfidfVectorizer(
            preprocessor=self.preprocess,
            tokenizer=str.split,
            token_pattern=None,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
        )
        self.word_matrix = self.word_vectorizer.fit_transform(self.documents)

        # Character n-grams help with short questions and small spelling variations.
        self.char_vectorizer = TfidfVectorizer(
            lowercase=True,
            analyzer="char_wb",
            ngram_range=(3, 5),
            sublinear_tf=True,
            min_df=1,
        )
        self.char_matrix = self.char_vectorizer.fit_transform(self.documents)

    def preprocess(self, text: str) -> str:
        text = text.lower().replace("’", "'")
        tokens = self.tokenizer.tokenize(text)

        normalized: List[str] = []
        for token in tokens:
            clean = token.strip(".'-")
            if not clean or clean in self.stop_words:
                continue

            expanded = [clean] + self.synonyms.get(clean, [])
            for word in expanded:
                # Keep numbers and symbols such as $500 readable.
                if re.fullmatch(r"[\d$%.]+", word):
                    normalized.append(word)
                else:
                    normalized.append(self.stemmer.stem(word))

        return " ".join(normalized)

    def top_matches(self, question: str, limit: int = 5) -> List[Dict]:
        """Return the most relevant FAQs, including their blended TF-IDF scores."""
        question = (question or "").strip()
        if not question:
            return []

        word_query = self.word_vectorizer.transform([question])
        char_query = self.char_vectorizer.transform([question])

        word_scores = cosine_similarity(word_query, self.word_matrix).flatten()
        char_scores = cosine_similarity(char_query, self.char_matrix).flatten()

        # Word similarity carries most of the score; character similarity provides
        # support for short or slightly misspelled questions.
        scores = (word_scores * 0.82) + (char_scores * 0.18)

        ranked_indexes = np.argsort(scores)[::-1][:max(1, limit)]
        return [
            {
                **self.faqs[int(index)],
                "score": round(float(scores[int(index)]), 3),
            }
            for index in ranked_indexes
        ]

    def match(self, question: str) -> Dict:
        question = (question or "").strip()
        if not question:
            return {
                "answer": "Please enter a question.",
                "matched": False,
                "confidence": 0.0,
                "matched_question": None,
                "category": None,
            }

        candidates = self.top_matches(question, limit=1)
        best_faq = candidates[0]
        best_score = best_faq["score"]

        if best_score < self.threshold:
            return {
                "answer": self.FALLBACK,
                "matched": False,
                "confidence": round(best_score, 3),
                "matched_question": None,
                "category": None,
            }

        return {
            "answer": best_faq["answer"],
            "matched": True,
            "confidence": round(best_score, 3),
            "matched_question": best_faq["question"],
            "category": best_faq.get("category"),
        }

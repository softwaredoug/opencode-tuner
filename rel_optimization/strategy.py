from cheat_at_search.strategy import SearchStrategy
from cheat_at_search.tokenizers import snowball_tokenizer
from searcharray import SearchArray
import numpy as np


class BM25Search(SearchStrategy):
    def __init__(self, corpus,
                 title_boost=9.3,
                 description_boost=4.1):
        super().__init__(corpus)
        self.index = corpus
        self.title_boost = title_boost
        self.description_boost = description_boost

        if 'title_snowball' not in self.index and 'title' in corpus:
            self.index['title_snowball'] = SearchArray.index(
                corpus['title'], snowball_tokenizer)
        if 'description_snowball' not in self.index and 'description' in corpus:
            self.index['description_snowball'] = SearchArray.index(
                corpus['description'], snowball_tokenizer)

    def search(self, query, k=10):
        """Dumb baseline lexical search"""
        tokenized = snowball_tokenizer(query)
        bm25_scores = np.zeros(len(self.index))
        for token in tokenized:
            bm25_scores += self.index['title_snowball'].array.score(token) * self.title_boost
            bm25_scores += self.index['description_snowball'].array.score(
                token) * self.description_boost
        top_k = np.argsort(-bm25_scores)[:k]
        scores = bm25_scores[top_k]
        return top_k, scores

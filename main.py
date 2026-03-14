from cheat_at_search.logger import log_to_stdout
from cheat_at_search.search import ndcgs, run_strategy
from cheat_at_search.wands_data import corpus, judgments
from rel_optimization.strategy import BM25Search


log_to_stdout(level="INFO")


def main():
    print("Hello from rel-optimization!")
    strategy = BM25Search(corpus)
    graded = run_strategy(strategy, judgments)
    per_query_ndcgs = ndcgs(graded)
    avg_ndcg = per_query_ndcgs.mean() if len(per_query_ndcgs) else 0
    print(f"Average NDCG: {avg_ndcg}")


if __name__ == "__main__":
    main()

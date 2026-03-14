from cheat_at_search.logger import log_to_stdout
from cheat_at_search.search import ndcgs, run_strategy
from cheat_at_search.wands_data import corpus, judgments
from rel_optimization.strategy import BM25Search


log_to_stdout(level="INFO")


def main():
    strategy = BM25Search(corpus)
    all_queries = judgments["query"].drop_duplicates()
    training_queries = all_queries.sample(200, random_state=42)
    remaining_queries = all_queries[~all_queries.isin(training_queries)]
    validation_queries = remaining_queries.sample(100, random_state=42)

    training_judgments = judgments[judgments["query"].isin(training_queries)]
    validation_judgments = judgments[judgments["query"].isin(validation_queries)]

    graded_training = run_strategy(strategy, training_judgments)
    training_ndcgs = ndcgs(graded_training)
    print("Training per-query NDCG:")
    for query, ndcg in training_ndcgs.items():
        print(f"{query}: {ndcg}")

    graded_validation = run_strategy(strategy, validation_judgments)
    validation_ndcgs = ndcgs(graded_validation)
    avg_validation_ndcg = validation_ndcgs.mean() if len(validation_ndcgs) else 0
    print(f"Validation Average NDCG: {avg_validation_ndcg}")


if __name__ == "__main__":
    main()

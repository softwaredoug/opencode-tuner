import argparse
import csv
import os

from cheat_at_search.logger import log_to_stdout
from cheat_at_search.search import ndcgs, run_strategy
from cheat_at_search.wands_data import corpus, judgments
from rel_optimization.new_strategy import NewSearch


log_to_stdout(level="INFO")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run ranking experiment and log NDCG results.",
        epilog=(
            'Example: python main.py --experiment-name "BM25 baseline" '
            '--experiment-description "Default parameters on WANDS"'
        ),
    )
    parser.add_argument(
        "--experiment-name",
        required=True,
        help="Short name for this run (required).",
    )
    parser.add_argument(
        "--experiment-description",
        required=True,
        help="Brief description of the experiment (required).",
    )
    return parser.parse_args()


def append_experiment_log(
    experiment_name, experiment_description, train_ndcg, test_ndcg
):
    file_path = "experiments.csv"
    needs_header = not os.path.exists(file_path) or os.path.getsize(file_path) == 0
    with open(file_path, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if needs_header:
            writer.writerow(
                [
                    "experiment_name",
                    "experiment_description",
                    "train_NDCG",
                    "test_NDCG",
                ]
            )
        writer.writerow(
            [
                experiment_name,
                experiment_description,
                f"{train_ndcg:.6f}",
                f"{test_ndcg:.6f}",
            ]
        )


def main():
    args = parse_args()
    strategy = NewSearch(corpus)
    all_queries = judgments["query"].drop_duplicates()
    training_queries = all_queries.sample(340, random_state=42)
    remaining_queries = all_queries[~all_queries.isin(training_queries)]
    validation_queries = remaining_queries.sample(140, random_state=42)

    training_judgments = judgments[judgments["query"].isin(training_queries)]
    validation_judgments = judgments[judgments["query"].isin(validation_queries)]

    graded_training = run_strategy(strategy, training_judgments)
    training_ndcgs = ndcgs(graded_training)
    print("Training per-query NDCG:")
    for query, ndcg in training_ndcgs.items():
        print(f"{query}: {ndcg}")
    avg_training_ndcg = training_ndcgs.mean() if len(training_ndcgs) else 0

    graded_validation = run_strategy(strategy, validation_judgments)
    validation_ndcgs = ndcgs(graded_validation)
    avg_validation_ndcg = validation_ndcgs.mean() if len(validation_ndcgs) else 0
    append_experiment_log(
        args.experiment_name,
        args.experiment_description,
        avg_training_ndcg,
        avg_validation_ndcg,
    )
    print(f"Validation Average NDCG: {avg_validation_ndcg}")


if __name__ == "__main__":
    main()

import argparse
import csv
import importlib.util
import os

from cheat_at_search.logger import log_to_stdout
from cheat_at_search.search import ndcgs, run_strategy
from cheat_at_search.wands_data import corpus, judgments


log_to_stdout(level="INFO")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run ranking experiment and log NDCG results.",
        epilog=(
            'Example: python main.py --experiment-description "Default parameters on WANDS" '
            '--test-module "rel_optimization/new_strategy.py"'
        ),
    )
    parser.add_argument(
        "--experiment-description",
        required=True,
        help="Brief description of the experiment (required).",
    )
    parser.add_argument(
        "--test-module",
        required=True,
        help="Path to a Python file that defines NewSearch (required).",
    )
    return parser.parse_args()


def load_test_module(test_module_path):
    if not os.path.exists(test_module_path):
        raise FileNotFoundError(
            f"Test module not found: {test_module_path}. "
            "Provide a valid path with --test-module."
        )
    spec = importlib.util.spec_from_file_location("test_module", test_module_path)
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Unable to load module from: {test_module_path}. "
            "Check that the file is a valid Python module."
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "NewSearch"):
        raise AttributeError(
            f"Module {test_module_path} does not export NewSearch. "
            "Define a NewSearch class and retry."
        )
    return module


def append_experiment_log(
    test_module_name, experiment_description, train_ndcg, test_ndcg
):
    file_path = os.path.join("rel_optimization", "experiments.csv")
    needs_header = not os.path.exists(file_path) or os.path.getsize(file_path) == 0
    with open(file_path, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if needs_header:
            writer.writerow(
                [
                    "test_module",
                    "experiment_description",
                    "train_NDCG",
                    "test_NDCG",
                ]
            )
        writer.writerow(
            [
                test_module_name,
                experiment_description,
                f"{train_ndcg:.6f}",
                f"{test_ndcg:.6f}",
            ]
        )


def main():
    args = parse_args()
    test_module = load_test_module(args.test_module)
    strategy = test_module.NewSearch(corpus)
    test_module_name = os.path.basename(args.test_module)
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
        test_module_name,
        args.experiment_description,
        avg_training_ndcg,
        avg_validation_ndcg,
    )
    print(f"Validation Average NDCG: {avg_validation_ndcg}")


if __name__ == "__main__":
    main()

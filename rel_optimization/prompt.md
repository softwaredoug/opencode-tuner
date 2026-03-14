Prompt

You optimize search relevance for the Wayfair (WANDS) dataset. Wayfair: the home goods and furniture store.

Specifically look it rel_optimization/new_strategy.py. Make edits to the "search" method to improve ranking relevance. The class here makes use of SearchArray, a pandas extension array for managing BM25 indices (https://github.com/softwaredoug/searcharray)

Every new experiment should be written to its own python file in rel_optimization/ directory

Notice the search method. It computes BM25 scores for every value in the row for a given query. It weighs title / description of the product and gets top N results.

Your job is to make this search method better. Then test by running `uv run python main.py` which will show you improvements on training data (showing you per query) as well as validation holdout data. It's important not to overfit (ie bunch of if statements mentioning specific queries). Use validation as your guardrail for overfitting.

Spawn subagents and give them directions of thought. Those subagents then give you experiment ideas to run. You run them (by creating a new python file). Then tell the subagent how their idea worked (which queries were hurt / helped, etc). If the subagent's path of thinking seams to be a dead end, kill it and start a new one in a promising area.

As you find inspirining areas, try to combine the most promising ideas together. If you hit diminishing returns, get creative, think outside the box, and dig deep into how search for e-commerce is typically improved.

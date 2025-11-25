## Evaluation Matrix (RAGAS)

This folder hosts lightweight scaffolding for running RAGAS-based evaluations against Paper.AI's Graph RAG service.

### Files
- `ragas_dataset.jsonl` – template dataset you can extend with real queries, retrieved contexts, and answers.
- `run_ragas_eval.py` – CLI helper that loads the JSONL dataset, builds a `ragas.EvaluationDataset`, and prints/saves metrics.

### Workflow
1. **Collect samples**
   - Export recent Paper.AI interactions: `question`, retrieved `contexts` (top-k passages), model `answer`, and human-labelled `ground_truth`.
   - Append each record as a JSON object (one per line) after the `_meta` entry inside `ragas_dataset.jsonl`.
2. **Install dependencies**
   - Activate your virtual environment and run `pip install ragas datasets tqdm langchain-google-genai`.
   - Export `GOOGLE_API_KEY` (Gemini) so the evaluator can call Gemini for LLM-based metrics.
3. **Run the evaluator**
   - Example: `python backend/Evalution_Matrix/run_ragas_eval.py --input-path backend/Evalution_Matrix/ragas_dataset.jsonl --output-path backend/Evalution_Matrix/ragas_results.json --llm-provider gemini --llm-model gemini-1.5-flash`.
   - The script builds a Gemini-backed evaluator via LangChain and prints/saves the aggregated metrics.

### Extending
- Populate dozens of samples for stable metrics.
- Add optional fields such as `ground_truth_contexts` or `document_ids` if you want to compute retrieval-specific metrics. The script can be extended to consume them.
- Store multiple JSONL snapshots (e.g., dated) to compare retriever/prompt/model variations over time.


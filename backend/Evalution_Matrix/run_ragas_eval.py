"""
Run RAGAS evaluation on Paper.AI outputs with Gemini-backed metrics.

Usage:
    python backend/Evalution_Matrix/run_ragas_eval.py \
        --input-path backend/Evalution_Matrix/ragas_dataset.jsonl \
        --output-path backend/Evalution_Matrix/ragas_results.json \
        --llm-provider gemini --llm-model gemini-1.5-flash

Requirements:
    pip install ragas datasets tqdm google-generativeai

LLM-backed metrics:
    Export `GOOGLE_API_KEY` (Gemini) before running so faithfulness and
    answer-relevancy scoring uses Gemini only.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable, Iterator, List, Optional

import google.generativeai as genai
from langchain_core.outputs import Generation, LLMResult
from ragas import EvaluationDataset, evaluate
from ragas.dataset_schema import SingleTurnSample
from ragas.llms import BaseRagasLLM
from ragas.embeddings import BaseRagasEmbedding


def load_jsonl(path: Path) -> Iterator[dict]:
    """Yield parsed JSON objects from a JSONL file."""
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            yield json.loads(stripped)


def build_samples(items: Iterable[dict]) -> List[SingleTurnSample]:
    """Convert JSON objects into RAGAS SingleTurnSample entries."""
    samples: List[SingleTurnSample] = []
    for item in items:
        if "_meta" in item:
            # Skip metadata/helper lines.
            continue
        question = item.get("question") or item.get("query")
        user_input = item.get("user_input") or question
        contexts = (
            item.get("retrieved_contexts")
            or item.get("contexts")
            or item.get("retrieved_passages")
            or []
        )
        answer = item.get("response") or item.get("answer") or item.get("prediction") or ""
        ground_truth = (
            item.get("reference")
            or item.get("ground_truth")
            or item.get("references")
            or ""
        )

        if not question or not contexts or not answer or not ground_truth:
            raise ValueError(
                "Each sample must include question, contexts, answer, and ground_truth."
            )

        samples.append(
            SingleTurnSample(
                user_input=user_input,
                retrieved_contexts=contexts,
                response=answer,
                reference=ground_truth,
            )
        )

    if not samples:
        raise ValueError("No valid samples found. Did you forget to add data?")

    return samples


class GeminiRagasLLM(BaseRagasLLM):
    """Minimal Gemini-backed evaluator for RAGAS metrics."""

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
    ):
        super().__init__()
        self.model_name = model
        self.temperature = temperature
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required.")
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(model)

    @staticmethod
    def _prompt_to_str(prompt) -> str:
        try:
            return prompt.to_string()
        except AttributeError:
            return str(prompt)

    @staticmethod
    def _response_text(response) -> str:
        if hasattr(response, "text") and response.text:
            return response.text
        candidates = getattr(response, "candidates", None)
        if candidates:
            parts: List[str] = []
            for candidate in candidates:
                if getattr(candidate, "content", None):
                    for part in getattr(candidate.content, "parts", []) or []:
                        text = getattr(part, "text", "")
                        if text:
                            parts.append(text)
            if parts:
                return "\n".join(parts)
        return ""

    def _to_llm_result(self, text: str) -> LLMResult:
        generation = Generation(
            text=text,
            generation_info={"finish_reason": "stop", "model": self.model_name},
        )
        return LLMResult(generations=[[generation]])

    def generate_text(
        self,
        prompt,
        n: int = 1,
        temperature: float = 0.01,
        stop: Optional[List[str]] = None,
        callbacks=None,
    ) -> LLMResult:
        _ = (n, stop, callbacks)
        prompt_str = self._prompt_to_str(prompt)
        response = self.client.generate_content(
            prompt_str,
            generation_config={"temperature": temperature or self.temperature},
        )
        text = self._response_text(response)
        return self._to_llm_result(text)

    async def agenerate_text(
        self,
        prompt,
        n: int = 1,
        temperature: Optional[float] = 0.01,
        stop: Optional[List[str]] = None,
        callbacks=None,
    ) -> LLMResult:
        _ = (n, stop, callbacks)
        prompt_str = self._prompt_to_str(prompt)
        response = await self.client.generate_content_async(
            prompt_str,
            generation_config={"temperature": temperature or self.temperature},
        )
        text = self._response_text(response)
        return self._to_llm_result(text)

    def is_finished(self, response: LLMResult) -> bool:
        """Check if the LLM response is finished."""
        # Gemini always finishes in a single response; we embed finish_reason in generation_info.
        for gen_list in response.generations:
            for gen in gen_list:
                info = getattr(gen, "generation_info", {}) or {}
                if info.get("finish_reason") not in ("stop", "STOP", None):
                    return False
        return True


class GeminiRagasEmbedding(BaseRagasEmbedding):
    """Gemini-backed embeddings for RAGAS metrics."""

    def __init__(
        self,
        model: str = "models/text-embedding-004",
        api_key: Optional[str] = None,
    ):
        self.model_name = model
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required.")
        genai.configure(api_key=self.api_key)

    def embed_text(self, text: str, **kwargs) -> List[float]:
        result = genai.embed_content(
            model=self.model_name,
            content=text,
            task_type="retrieval_document",
        )
        return result["embedding"]

    # Alias for RAGAS compatibility (some metrics call embed_query)
    def embed_query(self, text: str) -> List[float]:
        return self.embed_text(text)

    # Alias for RAGAS compatibility (some metrics call embed_documents)
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embed_texts(texts)

    async def aembed_text(self, text: str, **kwargs) -> List[float]:
        # google-generativeai doesn't have a native async embed; run sync in executor.
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.embed_text(text, **kwargs))


def build_embeddings(provider: Optional[str], model: Optional[str]):
    """Configure embeddings based on CLI hints."""
    if not provider:
        return None
    provider = provider.lower()
    if provider == "gemini":
        model_name = model or "models/text-embedding-004"
        return GeminiRagasEmbedding(model=model_name)
    raise ValueError(f"Unsupported embedding provider: {provider}")


def build_llm(provider: Optional[str], model: Optional[str]):
    """Configure an evaluation LLM based on CLI hints."""
    if not provider:
        return None

    provider = provider.lower()
    if provider == "gemini":
        model_name = model or "models/gemini-2.0-flash"
        # Ensure model name has models/ prefix for Gemini API
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
        return GeminiRagasLLM(model=model_name)

    raise ValueError(f"Unsupported llm provider: {provider}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation.")
    parser.add_argument("--input-path", required=True, help="Path to JSONL dataset.")
    parser.add_argument(
        "--output-path",
        default="ragas_results.json",
        help="Destination for metrics JSON.",
    )
    parser.add_argument(
        "--llm-provider",
        help="Optional: provider hint (openai, google, etc.). Currently informational.",
    )
    parser.add_argument(
        "--llm-model",
        help="Optional: model hint for LLM-based metrics (e.g., gpt-4o-mini).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_path)
    output_path = Path(args.output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_path}")

    print(f"Loading dataset from {input_path}")
    samples = build_samples(load_jsonl(input_path))
    dataset = EvaluationDataset(samples)

    llm = None
    embeddings = None
    if args.llm_provider:
        llm = build_llm(args.llm_provider, args.llm_model)
        embeddings = build_embeddings(args.llm_provider, None)
        print(f"Using custom LLM provider={args.llm_provider} model={args.llm_model}")
    else:
        print("No LLM provider specified; default RAGAS evaluator will be used.")

    print("Running RAGAS evaluation (this may invoke an LLM)...")
    result = evaluate(dataset, llm=llm, embeddings=embeddings)
    
    # Extract metrics from EvaluationResult
    # result._repr_dict contains metric_name -> mean_score
    # result._scores_dict contains metric_name -> list of per-sample scores
    if hasattr(result, "_repr_dict"):
        metrics = dict(result._repr_dict)
    elif hasattr(result, "scores") and result.scores:
        # Fallback: compute means from raw scores
        metrics = {}
        for key in result.scores[0].keys():
            vals = [s[key] for s in result.scores if s.get(key) is not None]
            metrics[key] = sum(vals) / len(vals) if vals else None
    else:
        metrics = {}
    
    print("Evaluation complete. Metrics:")
    print(json.dumps(metrics, indent=2))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved metrics to {output_path}")


if __name__ == "__main__":
    main()


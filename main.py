"""
Lab 18: Production RAG Pipeline — Main Entry Point
===================================================
Chạy toàn bộ pipeline: naive baseline → production → so sánh → report.

Usage:
    python main.py
"""

import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def main():
    print("=" * 60)
    print("LAB 18: PRODUCTION RAG PIPELINE")
    print("=" * 60)
    start = time.time()

    # Validate credentials before expensive indexing or repeated API calls.
    from config import OPENAI_API_KEY
    if not OPENAI_API_KEY:
        raise RuntimeError("Set OPENAI_API_KEY in .env to run real RAGAS evaluation")
    from openai import OpenAI
    try:
        OpenAI(api_key=OPENAI_API_KEY, timeout=15, max_retries=0).models.list()
    except Exception as exc:
        raise RuntimeError(f"OpenAI preflight failed ({type(exc).__name__}); check .env and connectivity") from None

    os.makedirs("reports", exist_ok=True)

    # Step 1: Basic Baseline
    print("\n📌 STEP 1: Running Basic RAG Baseline...")
    print("-" * 40)
    from naive_baseline import main as run_baseline
    run_baseline()

    with open("reports/naive_baseline_report.json", encoding="utf-8") as handle:
        baseline_report = json.load(handle)
    if baseline_report.get("status") != "completed":
        raise RuntimeError("Baseline RAGAS did not complete; inspect its report before comparing scores")

    # Step 2: Production Pipeline
    print("\n📌 STEP 2: Running Production Pipeline...")
    print("-" * 40)
    from src.pipeline import build_pipeline, evaluate_pipeline
    search, reranker = build_pipeline()
    prod_results = evaluate_pipeline(search, reranker)

    # Ensure reports are located in reports/
    for f in ["ragas_report.json", "naive_baseline_report.json"]:
        if os.path.exists(f):
            os.replace(f, f"reports/{f}")

    # Step 3: Comparison
    print("\n📌 STEP 3: Comparison")
    print("-" * 40)
    naive_path = "reports/naive_baseline_report.json"
    prod_path = "reports/ragas_report.json"

    if os.path.exists(naive_path) and os.path.exists(prod_path):
        with open(naive_path, encoding="utf-8") as f:
            naive = json.load(f)
        with open(prod_path, encoding="utf-8") as f:
            prod = json.load(f)

        if prod.get("status") != "completed":
            raise RuntimeError("Production RAGAS did not complete; scores are unavailable")
        print(f"\n{'Metric':<25} {'Basic':>8} {'Production':>12} {'Δ':>8}")
        print("-" * 55)
        for m in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
            n = naive.get("aggregate", {}).get(m, 0)
            p = prod.get("aggregate", {}).get(m, 0)
            d = p - n
            status = "✓" if p >= 0.75 else " "
            print(f"{status} {m:<23} {n:>8.4f} {p:>12.4f} {d:>+8.4f}")

    elapsed = time.time() - start
    print(f"\n⏱️  Total time: {elapsed:.1f}s")
    print("\n📋 Next steps:")
    print("  1. Điền analysis/failure_analysis.md")
    print("  2. Viết analysis/reflections/reflection_[HọTên].md")
    print("  3. Chạy: python check_lab.py")


if __name__ == "__main__":
    main()

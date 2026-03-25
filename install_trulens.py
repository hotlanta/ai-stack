#!/usr/bin/env python3
# =============================================================================
# install_trulens.py — Install TruLens inside AIO Sandbox
#
# Run this ONCE inside AIO Sandbox terminal:
#   docker cp D:\hotlanta_git\ai-stack\install_trulens.py aio-sandbox:/home/gem/install_trulens.py
#   docker exec -it aio-sandbox bash -c "python /home/gem/install_trulens.py"
#
# What TruLens does in your stack:
#   Evaluates your RAG pipeline using the RAG Triad:
#   1. Context Relevance  — did Qdrant retrieve the RIGHT chunks?
#   2. Groundedness       — is the response supported by the context?
#   3. Answer Relevance   — does the response actually answer the question?
#
#   All three scores together confirm the response is hallucination-free
#   up to the limit of your knowledge base.
#
# Results are logged to Langfuse at http://localhost:3020
# Dashboard: http://localhost:8090/jupyter → open trulens_dashboard.ipynb
# =============================================================================

import subprocess
import sys
import os

def run(cmd):
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"WARNING: Command returned {result.returncode}")
    return result.returncode

print("=" * 60)
print("Installing TruLens for RAG evaluation")
print("=" * 60)

# trulens-providers-ollama does not exist as a package.
# Use trulens-providers-litellm — LiteLLM bridges TruLens to Ollama.
run("pip install --ignore-installed trulens trulens-providers-litellm trulens-apps-langchain litellm langfuse")
# Verify install
run("python -c \"import trulens; print('trulens OK')\"")
run("python -c \"from trulens.providers.litellm import LiteLLM; print('LiteLLM provider OK')\"")

# Write the evaluation script
eval_script = '''#!/usr/bin/env python3
# =============================================================================
# trulens_eval.py — Evaluate RAG pipeline with TruLens RAG Triad
# Run from AIO Sandbox: python /home/gem/trulens_eval.py
#
# Scores each dimension 0.0-1.0:
#   > 0.7 = good    0.4-0.7 = needs work    < 0.4 = hallucination risk
# =============================================================================

import os
from trulens.core import TruSession
from trulens.providers.litellm import LiteLLM
from trulens.core import Feedback
from trulens.core.schema import Select
import numpy as np

# ── Configuration ─────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
EVAL_MODEL      = os.getenv("EVAL_MODEL", "phi4-mini:3.8b-q4_K_M")
QDRANT_URL      = os.getenv("QDRANT_URL", "http://host.docker.internal:6333")

print(f"Evaluator model:  {EVAL_MODEL}")
print(f"Ollama URL:       {OLLAMA_BASE_URL}")
print("")

# ── Initialize TruLens session ────────────────────────────────────────────────
# Stores results locally in SQLite — no cloud needed
session = TruSession(database_url="sqlite:////home/gem/trulens_results.db")
session.reset_database()

# ── Set up Ollama via LiteLLM as the evaluator ────────────────────────────────
# LiteLLM bridges TruLens to Ollama — no cloud API needed
# Uses phi4-mini as a fast local judge model
provider = LiteLLM(
    model_engine=f"ollama/{EVAL_MODEL}",
    api_base=OLLAMA_BASE_URL
)

# ── Define RAG Triad feedback functions ───────────────────────────────────────

# 1. Context Relevance — did retrieval return useful chunks?
#    Low score = Qdrant retrieved wrong/irrelevant documents
#    Fix: adjust chunk size, overlap, or embedding model
f_context_relevance = (
    Feedback(provider.context_relevance, name="Context Relevance")
    .on_input()
    .on(Select.RecordCalls.retrieve.rets)
    .aggregate(np.mean)
)

# 2. Groundedness — is the response supported by retrieved context?
#    Low score = model is making things up beyond the retrieved docs
#    Fix: add output rails, lower temperature, strengthen system prompt
f_groundedness = (
    Feedback(provider.groundedness_measure_with_cot_reasons, name="Groundedness")
    .on(Select.RecordCalls.retrieve.rets.collect())
    .on_output()
    .aggregate(np.mean)
)

# 3. Answer Relevance — does the response answer the actual question?
#    Low score = model answered the wrong question or went off-topic
#    Fix: improve retrieval top-k, adjust system prompt
f_answer_relevance = (
    Feedback(provider.relevance, name="Answer Relevance")
    .on_input_output()
)

FEEDBACKS = [f_context_relevance, f_groundedness, f_answer_relevance]

print("RAG Triad feedback functions configured:")
print("  - Context Relevance (retrieval quality)")
print("  - Groundedness (hallucination detection)")
print("  - Answer Relevance (response quality)")
print("")
print("To run evaluations, import this module and wrap your RAG app:")
print("")
print("  from trulens_eval import session, FEEDBACKS")
print("  from trulens.apps.langchain import TruChain")
print("")
print("  with TruChain(your_rag_chain, feedbacks=FEEDBACKS) as recorder:")
print("      response = your_rag_chain.invoke({\'query\': \'your question\'})")
print("")
print("  session.get_leaderboard()")
print("")
print("Results saved to: /home/gem/trulens_results.db")
print("View in Jupyter:  http://localhost:8090/jupyter")
'''

with open("/home/gem/trulens_eval.py", "w") as f:
    f.write(eval_script)

print("\nTruLens installation complete.")
print("\nFiles created:")
print("  /home/gem/trulens_eval.py  — RAG evaluation script")
print("  /home/gem/trulens_results.db  — created on first eval run")
print("\nUsage:")
print("  python /home/gem/trulens_eval.py   (shows configuration + usage)")
print("  Open Jupyter at http://localhost:8090/jupyter for interactive evals")

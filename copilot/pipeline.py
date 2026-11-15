"""The copilot: one problem in, one letter out.

predict.py and eval.py both call solve(), so whatever is here is exactly what
the official run measures. In order (ANSWER_MODE=prior in config.env, team addition):

1. copilot/dups.py, only if DUP_INDEX_FILES is set (off by default): if the same
   problem is already solved in M3Kang (another level or language), answer what
   is known.
2. copilot/prior.py: the most likely letter given the options, learned from
   M3Kang's training set.

The 0.8B model is not asked: its one-letter answer carries no information
(19.9% on validation once its letter bias is removed; docs/ARQUITECTURA.md).
ANSWER_MODE=llm is the organizers' baseline: the model's letter, with a grammar.
"""
import socket
import time
import urllib.error

from . import dups, prior
from .config import CONFIG
from .llm import URL, answer_letter

TIME_LIMIT = float(CONFIG["TIME_LIMIT_SECONDS"])
FALLBACK = CONFIG["FALLBACK_ANSWER"]
MODE = CONFIG.get("ANSWER_MODE", "llm")
MARGIN = 3.0  # seconds kept free for Python and for writing the answer


def solve(problem, index=None, k=0, exclude_id=None, image_b64=None, llm_url=URL,
          time_limit=TIME_LIMIT):
    """Return {"answer", "seconds", "status", ...} for one problem.

    index and k turn on retrieval: the k most similar solved problems are
    added to the prompt as examples. Each example costs reading time.
    image_b64 and llm_url send the problem image to a vision server.
    """
    start = time.perf_counter()
    result = {"answer": FALLBACK, "status": "ok", "prompt_tokens": 0, "retrieved": "", "examples": [],
              "source": "llm"}
    if MODE == "prior" and image_b64 is None and not (index is not None and k > 0):
        try:
            found = dups.default_index().match(problem, exclude_id=exclude_id)
            if found:
                result.update(answer=found[0], source="duplicate", retrieved=f"{found[3]}:{found[2]:.2f}")
            else:
                result.update(answer=prior.best(problem), source="prior")
        except Exception as error:  # never leave a problem without a letter
            result.update(answer=FALLBACK, source="fallback", status=f"error: {error}")
        result["seconds"] = round(time.perf_counter() - start, 2)
        return result
    try:
        examples = []
        if index is not None and k > 0:
            hits = index.search(problem, k=k, exclude_id=exclude_id)
            examples = [p for _score, p in hits]
            result["examples"] = hits
            result["retrieved"] = ";".join(f"{p['id']}:{s:.2f}" for s, p in hits)
        remaining = time_limit - (time.perf_counter() - start) - MARGIN
        letter, timings = answer_letter(problem, examples, timeout=max(remaining, 1.0),
                                        image_b64=image_b64, url=llm_url)
        result["answer"] = letter
        result["prompt_tokens"] = timings.get("prompt_n", 0)
    except (socket.timeout, TimeoutError):
        result["status"] = "timeout"
    except urllib.error.URLError as error:
        if isinstance(error.reason, (socket.timeout, TimeoutError)):
            result["status"] = "timeout"
        else:
            result["status"] = f"error: {error.reason}"
    result["seconds"] = round(time.perf_counter() - start, 2)
    return result

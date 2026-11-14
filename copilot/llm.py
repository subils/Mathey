"""Ask the small language model for one letter, A to E.

Optional letter calibration (team addition, off by default): the model picks D
and A far too often. If LETTER_BIAS_FILE in config.env points to a file written
by scripts/calibrate_letters.py, the letter is chosen as
argmax(logprob(letter) - bias(letter)) instead of the greedy letter. With the
setting empty, behaviour is exactly the organizers' baseline.
"""
import json
import math
import os

from .config import CONFIG, ROOT
from .client import post

URL = f"http://127.0.0.1:{CONFIG['LLM_PORT']}/v1/chat/completions"
LETTERS = "ABCDE"

# Keep the system prompt stable: llama-server caches the start of the prompt,
# so text that never changes is only read once.
SYSTEM = ("You solve multiple-choice math competition problems for school students. "
          "Read the problem and the options, then reply with the letter of the correct option.")


def format_problem(problem, sees_image=False):
    lines = [problem["text"].strip()]
    options = problem.get("options") or {}
    for letter in "ABCDE":
        if letter in options:
            lines.append(f"{letter}) {options[letter]}")
    if not options:
        lines.append("(The options are in the picture.)" if sees_image else
                     "(The options are in a picture that you can't see. Pick the most likely letter.)")
    return "\n".join(lines)


def build_messages(problem, examples=(), image_b64=None):
    """image_b64 is a PNG as base64 text. Only a server started with --mmproj can see it."""
    messages = [{"role": "system", "content": SYSTEM}]
    for ex in examples:  # solved problems retrieved with RAG, if any
        messages.append({"role": "user", "content": format_problem(ex) + "\nAnswer:"})
        messages.append({"role": "assistant", "content": ex["label"]})
    text = format_problem(problem, sees_image=bool(image_b64)) + "\nAnswer:"
    if image_b64:
        content = [{"type": "image_url", "image_url": {"url": "data:image/png;base64," + image_b64}},
                   {"type": "text", "text": text}]
    else:
        content = text
    messages.append({"role": "user", "content": content})
    return messages


def _load_bias():
    path = CONFIG.get("LETTER_BIAS_FILE", "")
    if not path:
        return None
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    try:
        with open(path) as f:
            bias = json.load(f).get("bias", {})
        return {k: float(v) for k, v in bias.items() if k in LETTERS} or None
    except (OSError, ValueError):
        return None


BIAS = _load_bias()


def letter_logprobs(response):
    """Log probability of each letter A-E among the top tokens llama-server returned.

    Reads the OpenAI-style `logprobs.content[0].top_logprobs` and, if absent, the
    native `completion_probabilities`. Letters not among the top tokens are missing.
    """
    scores = {}
    choice = response.get("choices", [{}])[0]
    content = ((choice.get("logprobs") or {}).get("content") or [{}])[0]
    for item in content.get("top_logprobs") or []:
        token = (item.get("token") or "").strip()
        if token in LETTERS and item.get("logprob") is not None:
            scores[token] = max(scores.get(token, -math.inf), float(item["logprob"]))
    if not scores:
        for prob in (response.get("completion_probabilities") or [{}])[0].get("probs", []) or []:
            token = (prob.get("tok_str") or "").strip()
            p = prob.get("prob")
            if token in LETTERS and p:
                scores[token] = max(scores.get(token, -math.inf), math.log(p))
    return scores


def answer_letter(problem, examples=(), timeout=60, image_b64=None, url=URL, want_logprobs=False):
    """Return (letter, timings). The grammar makes any other output impossible.

    With want_logprobs=True (calibration), timings also gets "letter_logprobs".
    """
    payload = {
        "messages": build_messages(problem, examples, image_b64),
        "grammar": "root ::= [A-E]",
        "max_tokens": 1,
        "temperature": 0,
        "seed": int(CONFIG["SEED"]),
        "cache_prompt": True,
    }
    if BIAS or want_logprobs:
        payload.update({"logprobs": True, "top_logprobs": 20, "n_probs": 20})
    response = post(url, payload, timeout=timeout)
    letter = response["choices"][0]["message"]["content"].strip()
    timings = response.get("timings", {})
    if BIAS or want_logprobs:
        scores = letter_logprobs(response)
        timings["letter_logprobs"] = scores
        if BIAS and len(scores) >= 2:
            letter = max(scores, key=lambda k: scores[k] - BIAS.get(k, 0.0))
    return letter, timings

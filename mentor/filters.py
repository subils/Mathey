"""El filtre: cap text que arribi a l'alumne pot revelar la resposta.

S'aplica a les pistes preparades (en construir el banc) i a tot el que escriu la
IA de la placa en directe. Si un text no el passa, no es mostra.

Regles (amb `context` = l'enunciat del problema):
- Esmentar la lletra correcta («opció B», «(B)», «B)») és filtració.
- Si la resposta és un sol número: és filtració que el text el contingui, tret
  que també surti a l'enunciat (un «6 fitxes» de l'enunciat no revela res).
- Si la resposta té diversos números (una data, una seqüència): és filtració que
  el text els contingui tots, tret que tots surtin a l'enunciat.
- Si la resposta és text (sense números): és filtració que el text la copiï.
"""
import re

_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def _numbers(text):
    """Números d'un text, normalitzats ("2 400" -> "2400", "1,5" -> "1.5")."""
    text = re.sub(r"(?<=\d)[   ](?=\d{3}\b)", "", text or "")
    return {n.replace(",", ".") for n in _NUMBER.findall(text)}


def leaks(text, correct_letter, correct_option, context=""):
    """Torna el motiu si `text` revela la resposta, o "" si és segur."""
    if not text:
        return ""
    letter = (correct_letter or "").upper()
    # Només lletra majúscula: "opció B", "resposta (B)", "(B)", "B)"
    if letter and re.search(
        rf"(\b([Oo]pci[óo]|[Rr]esposta|[Ll]letra|[Oo]ption|[Aa]nswer)\s*\(?{letter}\b)|(\({letter}\))|(\b{letter}\))",
        text,
    ):
        return f"esmenta la lletra correcta ({letter})"
    option = (correct_option or "").strip()
    option_numbers = _numbers(option)
    text_numbers = _numbers(text)
    context_numbers = _numbers(context)
    if len(option_numbers) == 1:
        found = (option_numbers & text_numbers) - context_numbers
        if found:
            return f"conté el valor correcte ({', '.join(sorted(found))})"
    elif option_numbers:
        if option_numbers <= text_numbers and not option_numbers <= context_numbers:
            return f"conté tots els números de la resposta ({', '.join(sorted(option_numbers))})"
    elif len(option) >= 4 and option.lower() in text.lower():
        return "conté el text de l'opció correcta"
    return ""


def new_numbers(text, *contexts):
    """Números de `text` que no surten en cap dels `contexts`.

    Per al problema propi de l'alumne no sabem la resposta, així que no podem
    comprovar si es filtra. El que sí podem comprovar és que la IA no afirmi
    resultats calculats per ella: tot número que escrigui ha de ser a l'enunciat
    o al dubte de l'alumne.
    """
    allowed = set()
    for context in contexts:
        allowed |= _numbers(context)
    return _numbers(text) - allowed


def is_question(text, max_words=30):
    """Per a la pregunta socràtica: una sola pregunta curta."""
    text = (text or "").strip()
    return bool(text) and "?" in text and len(text.split()) <= max_words

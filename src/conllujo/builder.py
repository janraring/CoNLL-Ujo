from copy import deepcopy
from typing import overload
import warnings
import regex as re

from .models import Document, Sentence, Token, Word


# ---------------------------------------------------------------------------
#     Abbreviation lists (lower-cased, without trailing dot)
# ---------------------------------------------------------------------------


ABBREVS: set[str] = {
    "dr",  # Doktor
    "ff",  # fortfolgende
    "nr",  # Nummer
    "st",  # sankt
    "ua",  # unter anderem
    "zb",  # zum Beispiel
    "abb",  # Abbildung
    "bzw",  # beziehungsweise
    "etc",  # et cetera
    "idr",  # in der regel
    "gem",  # Gemeinde
    "ggf",  # gegebenenfalls
    "mio",  # Million
    "mrd",  # Milliarde
    "stk",  # Stuck
    "str",  # Straße
    "tab",  # Tabelle
    "usw",  # und so weiter
    "vgl",  # vergleiche
    "vol",  # Volumen
    "bspw",  # beispielssweise
    "bzgl",  # bezüglich
    "evtl",  # eventuell
    "inkl",  # inklusive
    "prof",  # Professor
    "sek",  # Sekunde
    "min",  # Minute
    "std",  # Stunde
    "chr",  # Christus
    "jan",  # Januar
    "feb",  # Februar
    "mär",  # März
    "apr",  # April
    "jun",  # Juni
    "jul",  # Juli
    "aug",  # August
    "sep",  # September
    "okt",  # Oktober
    "nov",  # November
    "dez",  # Dezember
}


# ---------------------------------------------------------------------------
#     Character sets
# ---------------------------------------------------------------------------


# private-use characters as stand-ins; restored after masking
_C = "\ue002"  # colon
_D = "\ue003"  # dot
_E = "\ue004"  # ellipsis
_P = "\ue015"  # paragraph

# Opening, closing and terminal characters
_OPEN_CHARS = r'„‚»›"\'“‘(\[\{'  # Opening quotes/brackets
_CLOSE_CHARS = r'“‘«‹"\'”’)\]\}'  # Closing quotes/brackets
_TERM_CHARS = r".!?"  # Terminal characters

# Sequences of opening, closing and terminal characters
_OPEN = rf"[{_OPEN_CHARS}]*"
_CLOSE = rf"[{_CLOSE_CHARS}]*"
_TERM = rf"[{_TERM_CHARS}]+"

# Apostrophe characters: straight ' and typographic ' '
_APOS = r"['\u2018\u2019]"

# Characters that can *begin* a sentence
_SENT_INIT = (
    "["
    "A-Z"
    "\u00c0-\u00d6\u00d8-\u00de"  # Latin extended uppercase
    "0-9"  # digit-initial sentences
    f"{_OPEN_CHARS}"
    "]"
)

# "Word characters" for our purposes: Unicode letters, digits, underscore,
# plus the masked-dot placeholder so abbreviations survive intact.
_WORD_CHAR = rf"[\w{_D}-]"


# ---------------------------------------------------------------------------
#     Precompiled regexes
# ---------------------------------------------------------------------------


_BOUNDARY_RE = re.compile(
    rf"({_TERM})"  # one or more terminal punctuation chars
    rf"({_CLOSE})"  # optional closing quotes / brackets
    rf"(\s+)"  # whitespace / newlines
    rf"(?={_SENT_INIT})"  # lookahead: sentence-initial character
)

_PARA_BREAK_RE = re.compile(r"\n{2,}")

# ---------------------------------------------------------------------------
#     Core tokenizer regex
#
#     Priority (leftmost-longest wins via alternation order):
#
#     A) Word with apostrophe(s)   — kept whole, trailing space absorbed
#     B) Abbreviation + dot        — kept whole, trailing space absorbed
#     C) Plain word run            — no punctuation, trailing space absorbed
#     D) Any other single character (punctuation / whitespace already consumed
#        by A–C)                   — trailing space absorbed
#
#     The optional trailing-space group (\s*) at the end of every branch
#     is what makes the tokenisation lossless.
# ---------------------------------------------------------------------------
_TOKEN_RE = re.compile(
    rf"(?:{_WORD_CHAR}+(?:{_APOS}{_WORD_CHAR}+)+|{_WORD_CHAR}+|\S)\s*",
    re.UNICODE,
)

char_to_mask = {",": _C, ".": _D, "…": _E}
mask_to_char = {_C: ",", _D: ".", _E: "…", _P: "\n\n"}


# ---------------------------------------------------------------------------
#     Masking — replace non-boundary dots with a private-use placeholder
# ---------------------------------------------------------------------------


def _mask_dots(text: str) -> str:
    """Mask dots that are NOT sentence (and transitively not token) boundaries."""

    # Numbers: decimals and thousands separators  3.14  1.000.000
    text = re.sub(r"(?<=\d)\.(?=\d)", _D, text)

    # Ellipses: two or more dots, or the Unicode ellipsis character
    text = re.sub(
        r"\.{2,}|\u2026",  # TODO: the … isn't actually getting replaced here
        lambda m: m.group().replace(".", _D),
        text,
    )

    # Consecutive dotted initials without spaces: J.R.R.  U.S.A.
    # Pattern: (X. repeated 2+ times), optionally a final dot.
    # We mask ALL dots inside because no boundary can lie within.
    text = re.sub(
        r"\b(?:[A-Za-z]\.){2,}",  # TODO: Expand to all alphabetic characters
        lambda m: m.group().replace(".", _D),
        text,
    )

    # Abbreviations and single initials — scan token by token
    tokens = re.split(r"(\s+)", text)
    out = []
    for tok in tokens:
        if not tok.strip():
            out.append(tok)
            continue

        if tok.endswith("."):
            stem = tok.rstrip(".")
            # Strip leading open-punctuation before lookup
            word = stem.lstrip(f"{_OPEN_CHARS}").lower()
            # Collapse any remaining (already-masked) internal dots
            word_clean = word.replace(".", "").replace(_D, "")

            is_abbrev = (
                word_clean in ABBREVS
                # Single letter that isn't already handled by ABBREVS
                or (len(word_clean) == 1 and word_clean.isalpha())
            )
            if is_abbrev:
                tok = tok.replace(".", _D)
        out.append(tok)
    text = "".join(out)

    # Ordinal numbers: "1." "2." "(3.)" "§4."
    text = re.sub(
        # TODO: Currently only catches up to 4-digit ordinals
        r"(?<!\w)(§\s*)?\d{1,4}\.",
        lambda m: m.group().replace(".", _D),
        text,
    )

    return text


def _unmask(text: str) -> str:
    """Restore masked dots to real dots."""
    return text.replace(_D, ".")


# ---------------------------------------------------------------------------
# 0.  Sanitize text before doing any fancy processing
# ---------------------------------------------------------------------------


def sanitize(text: str) -> str:
    """Normalize whitespace in text while preserving paragraph breaks.

    Collapses runs of spaces into a single space and joins soft line breaks
    (single newlines) into the surrounding text, while keeping hard paragraph
    breaks (two or more consecutive newlines) intact as exactly two newlines.

    Args:
        text: The input string to normalize.

    Returns:
        The normalized string with soft line breaks joined and excess
        whitespace collapsed, but paragraph structure preserved.

    Example:
        >>> sanatize("Hello\\nworld.\\n\\nNew paragraph.  Extra space.")
        'Hello world.\\n\\nNew paragraph. Extra space.'
    """
    text = re.sub(_PARA_BREAK_RE, _P, text)
    text = re.sub(r"\n", " ", text)
    text = re.sub(_P, "\n\n", text)
    text = re.sub(r"  +", " ", text)
    return text


# ---------------------------------------------------------------------------
# 1.  Segment raw_text into sentences while preserving paragraphs
# ---------------------------------------------------------------------------


def segment_into_sentences(raw_text: str, doc_id: str | None = None) -> Document:
    """
    Split *raw_text* into a list of sentences.

    Parameters
    ----------
    raw_text :
        Input string — any language or encoding.
        Input is expected to be one paragraph per line,
        paragraphs/lines seperated by at least two
        new-line characters.

    Returns
    -------
    list of str
        Sentences in order; empty strings are omitted.
    """

    if not raw_text.strip():
        return Document()

    masked = _mask_dots(raw_text)
    assert len(masked) == len(raw_text), (
        "Masking error: input and output length do not agree."
    )

    # Paragraph-break cut positions (index of first char of the new paragraph)
    par_cuts: list[int] = [m.end() for m in _PARA_BREAK_RE.finditer(masked)]
    # Boundary positions = end of the whitespace group (= start of next sentence)
    sent_cuts: list[int] = [m.end() for m in _BOUNDARY_RE.finditer(masked)]
    # Combining the two into one list
    cuts = sorted(set(par_cuts + sent_cuts)) + [len(raw_text)]

    # sentences: list[dict[str, str | list[str]]] = []
    doc = Document()

    sent_counter = 1
    prev = 0
    par_initial = True
    for cut in cuts:
        # If the next chunk is non-empty, add as sentence
        chunk = raw_text[prev:cut].strip()
        if chunk:
            metadata: dict[str, str | None] = {}
            if sent_counter == 1:
                metadata["newdoc"] = None
            if par_initial:
                metadata["newpar"] = None
            if doc_id is not None:
                metadata["sent_id"] = f"{doc_id}-{sent_counter:04d}"
            else:
                metadata["sent_id"] = f"sentence-{sent_counter:04d}"
            metadata["text"] = chunk

            sent = Sentence(metadata=metadata)
            doc.sentences.append(sent)

            sent_counter += 1
            par_initial = False

        prev = cut

        # Check if sentence is paragraph-initial
        if prev in par_cuts:
            par_initial = True

    # return sentences
    return doc


# ---------------------------------------------------------------------------
# 2.  Tokenize sentences and documents
# ---------------------------------------------------------------------------


"""
preprocessing.py
============
A lossless word tokenizer for Low Saxon / German texts.

Tokenization rules
------------------
* Spaces are attached to the *preceding* token (no characters are lost).
* Abbreviations (single letters + known stems, each followed by a dot) are
  kept as one token, trailing dot included.
* Words containing an apostrophe (e.g. ''t, d'r, an't) are kept as one token.
* All other punctuation characters become their own token.
* Everything else (runs of word characters) is a plain word token.
"""


@overload
def tokenize(doc_or_sent: Sentence) -> Sentence: ...
@overload
def tokenize(doc_or_sent: Document) -> Document: ...
def tokenize(doc_or_sent: Sentence | Document):
    # If type Document is given, iterate over its sentences
    if isinstance(doc_or_sent, Document):
        tokenized_doc = Document()
        for sent in doc_or_sent:
            tokenized_sent = tokenize(sent)
            tokenized_doc.sentences.append(tokenized_sent)
        return tokenized_doc

    sent = deepcopy(doc_or_sent)

    raw: str = sent.metadata.get("text", "") or ""
    if not raw.strip():
        raise ValueError("Empty string cannot be tokenized")

    masked = _mask_dots(raw)
    assert len(masked) == len(raw), "Masking error: masked and raw text lengths differ."

    id = 1  # 1-based token index within the sentence
    for m in _TOKEN_RE.finditer(masked):
        form_masked = m.group()
        form = _unmask(form_masked)

        # Separate the space that was absorbed into this token
        space_match = re.search(r"\s+$", form_masked)
        if space_match:
            form_surface = form[: space_match.start()]
            word = Word(id=id, form=form_surface)
        else:
            form_surface = form
            word = Word(id=id, form=form_surface, misc={"SpaceAfter": "No"})

        token = Token(words=[word])

        sent.tokens.append(token)
        id += 1

    # Remove misc dict of the last token.
    # This dict contains "SpaceAfter=No"
    # at most so no information is lost.
    if sent[-1].words[0].misc:
        sent[-1].words[0].misc = None

    # Warn user if reconstruction does not equal the original string
    reconstructed = "".join(t.words[0].text or "" for t in sent).strip()
    if not reconstructed == raw:
        warnings.warn(
            (
                f"Tokenization was not lossless. Some Whitespace likely got stripped:\n"
                f"  original:       {raw!r}\n"
                f"  reconstructed:  {reconstructed!r}"
            ),
            UserWarning,
        )

    return sent

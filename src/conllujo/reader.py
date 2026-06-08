from copy import deepcopy
from typing import overload
from pathlib import Path

from . import Document, Sentence, Token, Word

SPACEAFTER = "SpaceAfter"
YES = "Yes"
NO = "No"


def _post_process(doc: Document) -> Document:
    doc = deepcopy(doc)
    # Make sure the "SpaceAfter=No" attribute is also assigned
    # at the token level.
    for token in doc.tokens:
        for word in token:
            if not word.space_after:
                # dict is only created if it is also being populated
                if token.misc is None:
                    token.misc = {}
                token.misc[SPACEAFTER] = NO
    return doc


@overload
def read_conllu(source: Path) -> Document: ...
@overload
def read_conllu(source: str) -> Document: ...
def read_conllu(source: Path | str | object) -> Document:
    if isinstance(source, Path):
        with open(source, "r") as f:
            text = f.read()
    elif isinstance(source, str):
        text = source
    else:
        raise ValueError("Can only read conllu from Path or str")

    # --- Helper methods for parsing the different ---
    # --- kinds of fields (int / str / dict).      ---
    def _parse_int(value) -> int | None:
        if value == "_":
            return None
        return int(value)

    def _parse_str(value) -> str | None:
        if value == "_":
            return None
        return str(value)

    @overload
    def _parse_dict(
        value: str,
        *,
        delimiter: str = "|",
        relater: str = "=",
    ) -> dict[str, str] | None: ...
    @overload
    def _parse_dict(
        value: str,
        *,
        delimiter: str = "|",
        relater: str = "=",
        dtype_key: type[str],
    ) -> dict[str, str] | None: ...
    @overload
    def _parse_dict(
        value: str,
        *,
        delimiter: str = "|",
        relater: str = "=",
        dtype_key: type[int],
    ) -> dict[int, str] | None: ...
    def _parse_dict(
        value: str,
        *,
        delimiter: str = "|",
        relater: str = "=",
        dtype_key: type = str,
    ) -> dict[str, str] | dict[int, str] | None:
        if value == "_":
            return None
        parsed = {}
        for f in value.split(delimiter):
            kv = f.split(relater)
            if len(kv) != 2:
                continue
            key, value = kv
            parsed[dtype_key(key.strip())] = value.strip()

        return parsed

    # --- Document parsing logic ---
    doc = Document()
    prev = ""
    lines = text.split("\n")
    words_to_mwt = 0
    for line in lines:
        PREV_WAS_BLANK = not prev
        IS_BLANK = not line
        IS_COMMENT = not IS_BLANK and line[0] == "#"
        prev = line

        # If the previous line was blank and the
        # current one is not, create a new sentence.
        if PREV_WAS_BLANK and not IS_BLANK:
            doc.sentences.append(Sentence())

        # If the current line is a comment, append
        # to list of comments. Do nothing if blank.
        if IS_COMMENT:
            comment = line.removeprefix("#").strip()
            key, _, value = comment.partition("=")
            doc.sentences[-1].metadata[key.strip()] = value.strip()
            continue
        elif IS_BLANK:
            continue

        # Unpack the line's content
        id_str, form, lemma, upos, xpos, feats, head, deprel, deps, misc = line.split(
            "\t"
        )

        # If the current line represents a multi-word
        # token, append a new token and set the
        # `words_to_mwt`-counter to the right number
        # of words.
        if "-" in id_str:
            token_start, token_end = [int(i) for i in id_str.split("-")]
            words_to_mwt = token_end - token_start + 1
            doc.sentences[-1].tokens.append(Token(form=form))
            continue

        # Append a new token if the current line is a
        # word that is not part of a multi-word token.
        if not words_to_mwt:
            doc.sentences[-1].tokens.append(Token(form=form, misc=_parse_dict(misc)))

        # Create a `Word` from the current line and
        # append it to the token's list of words.
        word = Word(
            id=_parse_int(id_str),
            form=_parse_str(form),
            lemma=_parse_str(lemma),
            upos=_parse_str(upos),
            xpos=_parse_str(xpos),
            feats=_parse_dict(feats),
            head=_parse_int(head),
            deprel=_parse_str(deprel),
            deps=_parse_dict(deps, relater=":", dtype_key=int),
            misc=_parse_dict(misc),
        )
        doc.sentences[-1].tokens[-1].words.append(word)

        # Reduce the number of words belonging to
        # the current multi-word token.
        words_to_mwt = max(words_to_mwt - 1, 0)

    doc = _post_process(doc)
    return doc

from copy import deepcopy
from pathlib import Path
from typing import overload

from .constants import EMPTY_FIELD, NO, SPACEAFTER, CORRECT, TOKEN_LEVEL_MISC, TOKEN_LEVEL_FEATS
from .models import Document, Sentence, Token, Word


def _post_process(doc: Document) -> Document:
    doc = deepcopy(doc)
    # Make sure the "SpaceAfter=No" attribute is also assigned
    # at the token level.
    for token in doc.tokens:
        for word in token:
            if not word.space_after:
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
        if value == EMPTY_FIELD:
            return None
        return int(value)

    def _parse_str(value) -> str | None:
        if value == EMPTY_FIELD:
            return None
        return str(value)

    @overload
    def _parse_dict(
        value: str,
        *,
        delimiter: str = "|",
        relater: str = "=",
    ) -> dict[str, str]: ...
    @overload
    def _parse_dict(
        value: str,
        *,
        delimiter: str = "|",
        relater: str = "=",
        dtype_key: type[str],
    ) -> dict[str, str]: ...
    @overload
    def _parse_dict(
        value: str,
        *,
        delimiter: str = "|",
        relater: str = "=",
        dtype_key: type[int],
    ) -> dict[int, str]: ...
    def _parse_dict(
        value: str,
        *,
        delimiter: str = "|",
        relater: str = "=",
        dtype_key: type = str,
    ) -> dict[str, str] | dict[int, str]:
        if value == EMPTY_FIELD:
            return {}
        parsed = {}
        for f in value.split(delimiter):
            kv = f.split(relater)
            if len(kv) != 2:
                continue
            key, value = kv
            parsed[dtype_key(key.strip())] = value.strip()

        return parsed

    # Checks whether an attribute is defined at the token level or word level.
    def _is_token_level(key: str) -> bool:
                if key in TOKEN_LEVEL_MISC + TOKEN_LEVEL_FEATS or key.startswith(CORRECT):
                    return True
                else:
                    return False

    # Filters out word level and token level attributes, respectively.            
    def _filter_token_level(misc_parsed: dict[str, str]) -> dict[str, str]:
        return {k:v for k, v in misc_parsed.items() if _is_token_level(k)}

    def _filter_word_level(misc_parsed: dict[str, str]) -> dict[str, str]:
        return {k:v for k, v in misc_parsed.items() if not _is_token_level(k)}

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

        misc_parsed = _parse_dict(misc)
        feats_parsed = _parse_dict(feats)


        token = Token(form=form, 
                      feats=_filter_token_level(feats_parsed), 
                      misc=_filter_token_level(misc_parsed))
        doc.sentences[-1].tokens.append(token)

        if "-" in id_str:
            token_start, token_end = [int(i) for i in id_str.split("-")]
            words_to_mwt = token_end - token_start + 1
            continue

        # Create a `Word` from the current line and
        # append it to the token's list of words.
        word = Word(
            id=_parse_int(id_str),
            form=_parse_str(form),
            lemma=_parse_str(lemma),
            upos=_parse_str(upos),
            xpos=_parse_str(xpos),
            feats=_filter_word_level(feats_parsed),
            head=_parse_int(head),
            deprel=_parse_str(deprel),
            deps=_parse_dict(deps, relater=":", dtype_key=int),
            misc=_filter_word_level(misc_parsed),
        )
        doc.sentences[-1].tokens[-1].words.append(word)

        # Reduce the number of words belonging to
        # the current multi-word token.
        words_to_mwt = max(words_to_mwt - 1, 0)

    doc = _post_process(doc)
    return doc

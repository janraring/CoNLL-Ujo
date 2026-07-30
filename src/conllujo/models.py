from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, Iterator, ClassVar, overload
from copy import deepcopy


@dataclass
class CoNLLUNode:
    UNDERSCORE: ClassVar[str] = "_"

    form: str | None = None
    misc: dict[str, str] = field(default_factory=dict)

    @property
    def text(self):
        if self.form is None:
            return None
        if self.misc is not None and self.misc.get("SpaceAfter", "Yes") == "No":
            return self.form
        return self.form + " "

    @property
    def space_after(self):
        if self.misc is None:
            return True
        if self.misc.get("SpaceAfter", "Yes") == "Yes":
            return True
        return False

    def _serialize_field(self, f: int | str | None) -> str:
        if f is None:
            return self.UNDERSCORE
        return str(f)

    def _serialize_kv_field(
        self,
        d: dict[int, str] | dict[str, str] | None,
        *,
        delimiter: str = "|",
        relator: str = "=",
    ) -> str:
        # Sort keywords for CoNLL-U complience
        if d is None or not d:
            return self.UNDERSCORE
        kv_list = [
            f"{str(k)}{relator}{v}"
            for k, v in sorted(d.items(), key=lambda x: str(x[0]).lower())
        ]
        return f"{delimiter}".join(kv_list)


@dataclass(slots=True)
class Word(CoNLLUNode):
    id: int | None = None
    lemma: str | None = None
    upos: str | None = None
    xpos: str | None = None
    feats: dict[str, str] = field(default_factory=dict)
    head: int | None = None
    deprel: str | None = None
    deps: dict[int, str] = field(default_factory=dict)

    def to_conllu(self):
        fields = [
            self._serialize_field(self.id),
            self._serialize_field(self.form),
            self._serialize_field(self.lemma),
            self._serialize_field(self.upos),
            self._serialize_field(self.xpos),
            self._serialize_kv_field(self.feats),
            self._serialize_field(self.head),
            self._serialize_field(self.deprel),
            self._serialize_kv_field(self.deps, relator=":"),
            self._serialize_kv_field(self.misc),
        ]
        return "\t".join(fields)

    def to_dict(self):
        return {
            "id": self._serialize_field(self.id),
            "form": self._serialize_field(self.form),
            "lemma": self._serialize_field(self.lemma),
            "upos": self._serialize_field(self.upos),
            "xpos": self._serialize_field(self.xpos),
            "feats": self._serialize_kv_field(self.feats),
            "head": self._serialize_field(self.head),
            "deprel": self._serialize_field(self.deprel),
            "deps": self._serialize_kv_field(self.deps, relator=":"),
            "misc": self._serialize_kv_field(self.misc),
        }


@dataclass(slots=True)
class Token(CoNLLUNode):
    words: list[Word] = field(default_factory=list)

    def _mwt_to_conllu(self) -> str:
        first_id = self.words[0].id
        last_id = self.words[-1].id
        misc = self._serialize_kv_field(self.misc)
        fields = [
            f"{first_id}-{last_id}",
            f"{self.form}",
            self.UNDERSCORE,
            self.UNDERSCORE,
            self.UNDERSCORE,
            self.UNDERSCORE,
            self.UNDERSCORE,
            self.UNDERSCORE,
            self.UNDERSCORE,
            f"{misc}",
        ]
        return "\t".join(fields)

    def to_conllu(self) -> str:
        lines = []
        if len(self.words) > 1:
            lines.append(self._mwt_to_conllu())

        words = deepcopy(self.words)
        words[-1].misc = words[-1].misc | self.misc
        for word in words:
            lines.append(word.to_conllu())
        return "\n".join(lines)

    def __getitem__(self, idx) -> Word:
        return self.words[idx]

    def __iter__(self) -> Iterator:
        return iter(self.words)

    def __len__(self) -> int:
        return len(self.words)


@dataclass(slots=True)
class Sentence:
    tokens: list[Token] = field(default_factory=list)
    metadata: dict[str, str | None] = field(default_factory=dict)

    @property
    def id(self):
        return self.metadata.get("sent_id", None)

    @id.setter
    def id(self, value):
        self.metadata["sent_id"] = value

    @property
    def text(self):
        return self.metadata.get("text", None)

    @text.setter
    def text(self, value):
        self.metadata["text"] = value

    @property
    def form(self):
        form = ""
        for token in self.tokens:
            if token.form is not None:
                form += token.form
            else:
                continue
            if token.space_after:
                form += " "
        return form.strip()

    @property
    def words(self) -> Generator[Word]:
        for token in self:
            for word in token:
                yield word

    def to_conllu(self) -> str:
        lines = []
        for key, value in self.metadata.items():
            if value is None:
                comment = f"# {key}"
            else:
                comment = f"# {key} = {value}"
            lines.append(comment)
        for token in self:
            lines.append(token.to_conllu())
        lines.append("")
        return "\n".join(lines)

    def __getitem__(self, idx) -> Token:
        return self.tokens[idx]

    def __iter__(self) -> Iterator:
        return iter(self.tokens)

    def __len__(self) -> int:
        return len(self.tokens)


class Document:
    def __init__(
        self,
        sentences: list[Sentence] | None = None,
        metadata: dict[str, str] | None = None,
    ):
        self.sentences = sentences if sentences is not None else []
        self.metadata = metadata if metadata is not None else {}

    @property
    def tokens(self) -> Generator[Token]:
        for sent in self:
            for token in sent.tokens:
                yield token

    @property
    def words(self) -> Generator[Word]:
        for sent in self:
            for word in sent.words:
                yield word

    def to_conllu(self) -> str:
        blocks = []
        for sent in self:
            blocks.append(sent.to_conllu())
        blocks.append("")
        return "\n".join(blocks)

    def reindex(self) -> None:
        for sent in self:
            for idx, word in enumerate(sent.words, start=1):
                word.id = idx

    @overload
    def save(self, path: Path) -> None: ...
    @overload
    def save(self, path: str) -> None: ...
    def save(self, path: Path | str) -> None:
        if not isinstance(path, Path):
            try:
                path = Path(path)
            except ValueError:
                print(f"Invalid path {path!r}. File has NOT been saved!")
                return

        with open(path, "w") as f:
            f.write(self.to_conllu())

    def __add__(self, other) -> Document:
        return Document(self.sentences + other.sentences)

    @overload
    def __getitem__(self, idx: int) -> Sentence: ...
    @overload
    def __getitem__(self, idx: slice) -> Document: ...
    def __getitem__(self, idx) -> Sentence | Document:
        if isinstance(idx, int):
            return self.sentences[idx]
        elif isinstance(idx, slice):
            return Document(sentences=self.sentences[idx], metadata=self.metadata)
        else:
            raise TypeError(f"Invalid index type: {type(idx)}")

    def __iter__(self) -> Iterator:
        return iter(self.sentences)

    def __len__(self) -> int:
        return len(self.sentences)

import conllujo as cujo

# TODO: Move this to some "central" place
# TODO: Make lists of token-level `misc` fields (SpaceAfter, Typo, etc.)
SPACEAFTER = "SpaceAfter"
YES = "Yes"
NO = "No"


def test_load_empty_sent():
    raw = """_	_	_	_	_	_	_	_	_	_
"""
    doc = cujo.read_conllu(raw)
    # The top three lines and the bottom three lines should be equivalent
    assert len(doc) == 1
    assert len(doc.sentences[0]) == 1
    assert len(doc.sentences[0].tokens[0]) == 1

    assert len(doc.sentences) == 1
    assert len(doc.sentences[0].tokens) == 1
    assert len(doc.sentences[0].tokens[0].words) == 1


def test_space_after():
    raw = f"""# sent_id = sent-1
# text = A BC DE, F.
1	A	_	_	_	_	_	_	_	_
2-3	BC	_	_	_	_	_	_	_	_
2	B	_	_	_	_	_	_	_	_
3	C	_	_	_	_	_	_	_	_
4-5	DE	_	_	_	_	_	_	_	{SPACEAFTER}={NO}
4	D	_	_	_	_	_	_	_	_
5	E	_	_	_	_	_	_	_	_
6	,	_	_	_	_	_	_	_	_
7	F	_	_	_	_	_	_	_	{SPACEAFTER}={NO}
8	.	_	_	_	_	_	_	_	_
"""
    doc = cujo.read_conllu(raw)
    sent = doc[0]
    assert sent[0].space_after
    assert sent[1].space_after
    assert not sent[2].space_after
    assert sent[3].space_after
    assert not sent[4].space_after
    assert sent[5].space_after

    for word in sent.words:
        assert word.misc.get(SPACEAFTER, None) is None


def test_sent_text_vs_form():
    raw = f"""# sent_id = sent-1
# text = A BC DE, F.
1	A	_	_	_	_	_	_	_	_
2-3	BC	_	_	_	_	_	_	_	_
2	B	_	_	_	_	_	_	_	_
3	C	_	_	_	_	_	_	_	_
4-5	DE	_	_	_	_	_	_	_	{SPACEAFTER}={NO}
4	D	_	_	_	_	_	_	_	_
5	E	_	_	_	_	_	_	_	_
6	,	_	_	_	_	_	_	_	_
7	F	_	_	_	_	_	_	_	{SPACEAFTER}={NO}
8	.	_	_	_	_	_	_	_	_
"""
    doc = cujo.read_conllu(raw)
    sent = doc[0]
    assert sent.text == sent.form


def test_invariance():
    raw = f"""# sent_id = sent-1
# text = A BC DE, F.
1	A	_	_	_	_	_	_	_	_
2-3	BC	_	_	_	_	_	_	_	_
2	B	_	_	_	_	_	_	_	_
3	C	_	_	_	_	_	_	_	_
4-5	DE	_	_	_	_	_	_	_	{SPACEAFTER}={NO}
4	D	_	_	_	_	_	_	_	_
5	E	_	_	_	_	_	_	_	_
6	,	_	_	_	_	_	_	_	_
7	F	_	_	_	_	_	_	_	{SPACEAFTER}={NO}
8	.	_	_	_	_	_	_	_	_
"""
    doc = cujo.read_conllu(raw)
    assert doc.to_conllu() == raw

import conllujo as cujo

# test_file = "data/nds_short.conllu"
test_file = "data/nds.conllu"
with open(test_file, "r") as f:
    nds_teststring = f.read()


def test_invariance():
    doc = cujo.read_conllu(nds_teststring)
    assert doc.to_conllu() == nds_teststring


def test_sent():
    doc = cujo.read_conllu(nds_teststring)
    assert doc[0].text == doc[0].form, f"# text = {doc[0].text}\n# form = {doc[0].form}"


def test_space_after():
    test_data = """# sent_id = LSDC_0021_DWF_1931_OWL_ravensbergsk_heinrich-stolte_ravensberg_der-bauernhof-um-1870
# text_orig = An dem annern Enne fanner Küöken stonn doe lange Oekendisk, wo innen Sommer gieden weort.
# text = An dem anderen ende van'er küäken stund dee lange eykendisk, wår in'en sommer giaten word.
1	An	an	ADP	_	AdpType=Prep	4	case	_	lemma_gml=an
2	dem	de	DET	_	Case=Dat|Definite=Def|Gender=Masc|Number=Sing|PronType=Art	4	det	_	lemma_gml=dê¹
3	anderen	ander	ADJ	_	Case=Dat|Degree=Pos|Gender=Masc|Number=Sing	4	amod	_	lemma_gml=ander
4	ende	ende	NOUN	_	Case=Dat|Gender=Neut|Number=Sing	9	obl	_	lemma_gml=ende²
5-7	van'er	_	_	_	_	_	_	_	_
5	van	van	ADP	_	AdpType=Prep	8	case	_	lemma_gml=van¹
6	'	'	PUNCT	_	_	7	punct	_	_
7	er	de	DET	_	Case=Dat|Definite=Def|Gender=Fem|Number=Sing|PronType=Art	8	det	_	lemma_gml=dê¹
8	küäken	köäken	NOUN	_	Case=Dat|Gender=Fem|Number=Sing	4	nmod:poss	_	lemma_gml=kȫke²
9	stund	stån	VERB	_	Mood=Ind|Number=Sing|Person=3|Tense=Past	0	root	_	lemma_gml=stân
10	dee	de	DET	_	Case=Nom|Definite=Def|Gender=Masc|Number=Sing|PronType=Art	12	det	_	lemma_gml=dê¹
11	lange	lang	ADJ	_	Case=Nom|Degree=Pos|Gender=Masc|Number=Sing	12	amod	_	lemma_gml=lanc
12	eykendisk	eykendisk	NOUN	_	Case=Nom|Gender=Masc|Number=Sing	9	nsubj	_	SpaceAfter=No
13	,	,	PUNCT	_	_	19	punct	_	_
14	wår	woor	ADV	_	_	19	advmod	_	lemma_gml=wôr(e)
15-17	in'en	_	_	_	_	_	_	_	_
15	in	in	ADP	_	AdpType=Prep	18	case	_	lemma_gml=in²
16	'	'	PUNCT	_	_	17	punct	_	_
17	en	de	DET	_	Case=Acc,Dat|Definite=Def|Gender=Masc|Number=Sing|PronType=Art	18	det	_	lemma_gml=dê¹|SpaceAfter=No
18	sommer	soamer	NOUN	_	Case=Acc,Dat|Gender=Masc|Number=Sing	19	obl	_	lemma_gml=sōmer²
19	giaten	eaten	VERB	_	Aspect=Perf|VerbForm=Part	12	acl	_	lemma_gml=ēten
20	word	werden	AUX	_	Mood=Ind|Number=Sing|Person=3|Tense=Past|VerbType=Aux	19	aux:pass	_	lemma_gml=wērden¹|SpaceAfter=No
21	.	.	PUNCT	_	_	9	punct	_	_
"""
    doc = cujo.read_conllu(test_data)
    sent = doc[0]

    assert sent[4].space_after
    assert not sent[12].space_after, f"{sent[12].space_after} != True"


def test_form():
    doc = cujo.read_conllu(nds_teststring)
    for sent in doc:
        for tok in sent:
            assert tok.form is not None

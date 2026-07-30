# CoNLL-Ujo

CoNLL-Ujo is a Python library for building CoNLL-U treebanks from scratch, with a clear separation between creation and validation. It's designed around the fact that data is often messy or incomplete while you're still creating it: CoNLL-Ujo doesn't force you to populate fields you're not ready to set, and it doesn't validate on every read or write. Compliance checking is instead a separate step you run once the treebank is ready.

Besides the core data model and basic file handling, CoNLL-Ujo provides a handful of general-purpose tools to support the early stages of treebank creation — most notably rule-based sentence segmentation and pre-tokenization.

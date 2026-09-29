# FIR NLP module (MO-based case linking)

    pip install sentence-transformers scikit-learn pandas
    python generate_firs.py --per-cluster 50
    python evaluate_fir.py --methods tfidf,sbert
    python finetune_sbert.py --steps 100
    python evaluate_fir.py --methods tfidf,sbert,sbert_ft --ft-model ft_sbert

Data is SYNTHETIC (10 known MOs + 2 held-out novel MOs). Results reflect the generator, not real FIRs.
`linker.py` (FIRLinker) is what the backend calls: add(case_id, text), link(text).

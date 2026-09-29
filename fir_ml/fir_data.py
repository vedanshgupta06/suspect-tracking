import json, random

NOVEL_LABEL = "__novel__"


def load_split(path="firs.json", seed=0, train_frac=0.3, db_frac=0.35, novel_queries_per_mo=20):
    """train: only for fine-tuning | db: existing unsolved cases | query: new FIRs to link."""
    blob = json.load(open(path))
    novel = set(blob["novel"])
    rng = random.Random(seed)
    by_mo = {}
    for d in blob["firs"]:
        by_mo.setdefault(d["mo"], []).append(d)
    train, db, query = [], [], []
    for mo, items in by_mo.items():
        items = items[:]
        rng.shuffle(items)
        if mo in novel:
            query += [dict(d, label=NOVEL_LABEL) for d in items[:novel_queries_per_mo]]
        else:
            a, b = int(len(items) * train_frac), int(len(items) * (train_frac + db_frac))
            train += [dict(d, label=mo) for d in items[:a]]
            db += [dict(d, label=mo) for d in items[a:b]]
            query += [dict(d, label=mo) for d in items[b:]]
    return train, db, query

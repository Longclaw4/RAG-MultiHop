import json
from ask import plain_rag, graph_rag

RUNS = 3

# type: multihop (chain through the graph), docs2 (needs 2 files, no chain),
#       single (one fact in one file), unans (docs don't say; correct reply is NOT_ENOUGH_INFO)
tests = [
    # --- multihop (original 14) ---
    {"q": "Who is the CEO of the company that acquired Instagram?", "a": ["zuckerberg"], "type": "multihop"},
    {"q": "Where is the company founded by Dario Amodei headquartered?", "a": ["san francisco"], "type": "multihop"},
    {"q": "Who founded the company that owns YouTube?", "a": ["larry page", "sergey brin"], "type": "multihop"},
    {"q": "Where is the headquarters of the company that owns Instagram?", "a": ["menlo park"], "type": "multihop"},
    {"q": "Who is the CEO of the company that owns WhatsApp?", "a": ["zuckerberg"], "type": "multihop"},
    {"q": "Which company is the parent of the company that offers Google Earth?", "a": ["alphabet"], "type": "multihop"},
    {"q": "Who co-founded the company where Daniela Amodei is president?", "a": ["dario"], "type": "multihop"},
    {"q": "Who founded the company that acquired DeepMind?", "a": ["larry page", "sergey brin"], "type": "multihop"},
    {"q": "Where is the headquarters of the company Mark Zuckerberg chairs?", "a": ["menlo park"], "type": "multihop"},
    {"q": "Where is the headquarters of the company that owns the company that acquired Instagram?", "a": ["menlo park"], "type": "multihop"},
    {"q": "Who is the CEO of Microsoft?", "a": ["nadella"], "type": "multihop"},
    {"q": "Where is Anthropic headquartered?", "a": ["san francisco"], "type": "multihop"},
    {"q": "Which company develops Claude?", "a": ["anthropic"], "type": "multihop"},
    {"q": "Who is the CEO of Anthropic?", "a": ["dario"], "type": "multihop"},

    # --- docs2: each needs facts from 2 different files ---
    {"q": "Where is the headquarters of the company that owns WhatsApp?", "a": ["menlo park"], "type": "docs2"},
    {"q": "In what year was YouTube bought by the company founded by Larry Page and Sergey Brin?", "a": ["2006"], "type": "docs2"},
    {"q": "Who is the CEO of the company that owns YouTube?", "a": ["pichai"], "type": "docs2"},
    {"q": "What year was the company that acquired DeepMind founded?", "a": ["1998"], "type": "docs2"},
    {"q": "In what year did the company that owns Instagram rebrand under its current name?", "a": ["2021"], "type": "docs2"},
    {"q": "What is the estimated net worth of the chairman of the company that rebranded as Meta Platforms?", "a": ["258"], "type": "docs2"},
    {"q": "Where is the headquarters of the company where Dario Amodei was previously vice president of research?", "a": ["san francisco"], "type": "docs2"},
    {"q": "Who is the president of the company that Dario Amodei co-founded?", "a": ["daniela"], "type": "docs2"},

    # --- single: one fact, one file ---
    {"q": "When was Instagram launched for iOS?", "a": ["2010"], "type": "single"},
    {"q": "How many monthly active users did WhatsApp have as of May 2025?", "a": ["3 billion"], "type": "single"},
    {"q": "Where is YouTube headquartered?", "a": ["san bruno"], "type": "single"},
    {"q": "Who launched Facebook at Harvard in February 2004?", "a": ["zuckerberg"], "type": "single"},

    # --- unans: the docs do not contain these answers ---
    {"q": "What is the population of Menlo Park?", "a": [], "type": "unans"},
    {"q": "What was Anthropic's revenue in 2025?", "a": [], "type": "unans"},
    {"q": "Which university did Daniela Amodei attend?", "a": [], "type": "unans"},
    {"q": "How many employees does Anthropic have?", "a": [], "type": "unans"},

    # --- unans_hard: about a related entity; the graph has nearby facts that could tempt a guess ---
    {"q": "What is the mayor of Menlo Park?", "a": [], "type": "unans_hard"},
    {"q": "Who is the CEO of YouTube?", "a": [], "type": "unans_hard"},
    {"q": "Who is the chief financial officer of Meta Platforms?", "a": [], "type": "unans_hard"},
    {"q": "In which city in India was Sundar Pichai born?", "a": [], "type": "unans_hard"},
]

# Phrases that mean the model said it can't answer from the context
REFUSAL_PHRASES = [
    "doesn't say", "does not say", "doesn't state", "does not state", "not stated",
    "doesn't mention", "does not mention", "not mentioned", "isn't mentioned",
    "doesn't specify", "does not specify", "not specified", "doesn't contain",
    "does not contain", "not provided", "context doesn't", "context does not",
]


def is_correct(answer, t):
    a = answer.lower()
    if t["type"].startswith("unans"):
        # Flipped rule: abstaining is the correct behaviour
        return "not_enough_info" in a
    if "not_enough_info" in a or any(p in a for p in REFUSAL_PHRASES):
        return False
    return any(word in a for word in t["a"])


# Each system returns (answer, graph_fact_count); the count is None for plain RAG
SYSTEMS = {
    "plain k=2": lambda q: (plain_rag(q, k=2), None),
    "plain k=5": lambda q: (plain_rag(q, k=5), None),
    "plain k=10": lambda q: (plain_rag(q, k=10), None),
    "graphrag": graph_rag,
}
CATEGORIES = ["multihop", "docs2", "single", "unans", "unans_hard"]


def run_once():
    rows = []
    for t in tests:
        q = t["q"]
        row = {"q": q, "type": t["type"]}
        for name, fn in SYSTEMS.items():
            ans, n_facts = fn(q)
            row[name] = is_correct(ans, t)
            row[name + " answer"] = ans
            if n_facts is not None:
                row[name + " facts"] = n_facts
        rows.append(row)
        print(t["type"][:6].ljust(6), q, "->", {n: row[n] for n in SYSTEMS})
    return rows


def score(rows, name, category=None):
    picked = [r for r in rows if category is None or r["type"] == category]
    return sum(r[name] for r in picked), len(picked)


all_runs = []
for i in range(RUNS):
    print("\n=== run", i + 1, "of", RUNS, "===")
    all_runs.append(run_once())

print("\nScores across", RUNS, "runs (min-max)")
for name in SYSTEMS:
    overall = [score(rows, name)[0] for rows in all_runs]
    total = score(all_runs[0], name)[1]
    line = name + ": " + str(min(overall)) + "-" + str(max(overall)) + " / " + str(total)
    for cat in CATEGORIES:
        vals = [score(rows, name, cat)[0] for rows in all_runs]
        n = score(all_runs[0], name, cat)[1]
        line += " | " + cat + " " + str(min(vals)) + "-" + str(max(vals)) + "/" + str(n)
    print(line)

facts = [r["graphrag facts"] for rows in all_runs for r in rows if r["type"] == "unans_hard"]
print("GraphRAG graph facts on unans_hard questions: min", min(facts), "max", max(facts))

with open("eval_results.json", "w", encoding="utf-8") as f:
    json.dump({"runs": all_runs}, f, indent=2)

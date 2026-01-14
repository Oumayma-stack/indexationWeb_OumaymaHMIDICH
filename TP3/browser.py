import json
import math
from collections import defaultdict
import string
import nltk
from nltk.corpus import stopwords


# *************************
# File loading utilities
# *************************

def load_jsonl(filepath):
    """
    Load a JSONL file where each line corresponds to a JSON document.

    Each line is parsed independently to avoid failing on malformed entries.

    Args:
        filepath (str): Path to the JSONL file.

    Returns:
        list: List of parsed JSON documents.
    """
    documents = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            try:
                documents.append(json.loads(line))
            except json.JSONDecodeError:
                # Ignore malformed JSON lines
                continue
    return documents


def load_json(filepath):
    """
    Load a standard JSON file.

    Args:
        filepath (str): Path to the JSON file.

    Returns:
        dict: Parsed JSON content.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_results(results, filename):
    """
    Save search results to a JSON file.

    Args:
        results (dict): Result dictionary to save.
        filename (str): Output file path.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


# *************************
# Load indexes and documents
# *************************

# Inverted indexes built during TP2
title_index = load_json("input/title_index.json")
description_index = load_json("input/description_index.json")
brand_index = load_json("input/brand_index.json")
origin_index = load_json("input/origin_index.json")
reviews_index = load_json("input/reviews_index.json")

# Original product documents
products = load_jsonl("input/rearranged_products.jsonl")


# *************************
# Text preprocessing
# *************************

# Download and load English stopwords
nltk.download("stopwords")
STOPWORDS = stopwords.words("english")


def tokenize(text):
    """
    Normalize and tokenize a text string.

    Steps:
    - lowercase
    - remove punctuation
    - split on whitespace

    Args:
        text (str): Input text.

    Returns:
        list: List of raw tokens.
    """
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    tokens = text.split()
    return tokens


def normalize(tokens):
    """
    Remove stopwords from a list of tokens.

    Args:
        tokens (list): List of tokens.

    Returns:
        list: Filtered tokens.
    """
    return [t for t in tokens if t not in STOPWORDS]


# *************************
# Query expansion (synonyms)
# *************************

# Synonyms dictionary (for product origin)
synonyms = load_json("input/origin_synonyms.json")


def expand_with_synonyms(tokens):
    """
    Expand query tokens using predefined synonyms.

    Args:
        tokens (list): Query tokens.

    Returns:
        list: Expanded list of tokens.
    """
    expanded = set(tokens)
    for t in tokens:
        if t in synonyms:
            expanded.update(synonyms[t])
    return list(expanded)


def process_query(query):
    """
    Full query processing pipeline:
    - tokenization
    - normalization
    - synonym expansion

    Args:
        query (str): User query.

    Returns:
        list: Final list of query tokens.
    """
    tokens = tokenize(query)
    tokens = normalize(tokens)
    tokens = expand_with_synonyms(tokens)
    return tokens


# *************************
# Document filtering
# *************************

def filter_any_token(tokens, index):
    """
    Retrieve documents containing at least one query token (OR logic).

    Args:
        tokens (list): Query tokens.
        index (dict): Inverted index.

    Returns:
        set: Set of candidate document URLs.
    """
    docs = set()
    for t in tokens:
        if t in index:
            docs.update(index[t].keys())
    return docs


def filter_all_tokens(tokens, index):
    """
    Retrieve documents containing all query tokens (AND logic),
    implemented via intersection of posting lists.

    Args:
        tokens (list): Query tokens.
        index (dict): Inverted index.

    Returns:
        set: Set of document URLs matching all tokens.
    """
    doc_sets = []
    for t in tokens:
        if t in index:
            doc_sets.append(set(index[t].keys()))
    if not doc_sets:
        return set()
    return set.intersection(*doc_sets)


def filter_documents(tokens):
    """
    Global filtering strategy:
    - OR filtering across all indexes to maximize recall
    - AND filtering on the title index to improve precision

    Args:
        tokens (list): Query tokens.

    Returns:
        set: Final set of candidate documents.
    """
    candidates = set()

    for idx in [title_index, description_index, brand_index, origin_index]:
        candidates |= filter_any_token(tokens, idx)

    strict = filter_all_tokens(tokens, title_index)
    return candidates | strict


# *************************
# BM25 scoring
# *************************

def bm25_score(tf, df, doc_len, avgdl, N, k1=1.5, b=0.75):
    """
    Compute the BM25 score for a single term-document pair.
    """
    idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
    return idf * ((tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avgdl)))


def bm25(tokens, index, doc_lengths):
    """
    Compute BM25 scores for candidate documents using a given index.

    Args:
        tokens (list): Query tokens.
        index (dict): Inverted index {token: {url: [positions]}}.
        doc_lengths (dict): Document lengths.

    Returns:
        dict: BM25 scores per document.
    """
    N = len(doc_lengths)
    avgdl = sum(doc_lengths.values()) / N
    scores = defaultdict(float)

    for t in tokens:
        if t not in index:
            continue
        postings = index[t]
        df = len(postings)

        for url, positions in postings.items():
            tf = len(positions)
            doc_len = doc_lengths.get(url, 1)
            scores[url] += bm25_score(tf, df, doc_len, avgdl, N)

    return scores


# *************************
# Additional ranking signals
# *************************

def exact_match_score(tokens, title_tokens):
    """
    Check whether all query tokens appear in the title.

    Returns:
        int: 1 if exact match, 0 otherwise.
    """
    return int(set(tokens).issubset(set(title_tokens)))


# *************************
# Document metadata
# *************************

def build_documents_metadata(products):
    """
    Build per-document metadata required for scoring and display.

    Args:
        products (list): List of product documents.

    Returns:
        dict: Metadata indexed by document URL.
    """
    metadata = {}

    for p in products:
        url = p["url"]
        title = p["title"]
        description = p.get("description", "")
        reviews = p.get("reviews", [])

        title_tokens = normalize(tokenize(title))

        metadata[url] = {
            "title": title,
            "description": description,
            "title_tokens": title_tokens,
            "review_count": len(reviews),
            "doc_length": len(normalize(tokenize(description)))
        }

    return metadata


documents_metadata = build_documents_metadata(products)


# *************************
# Final scoring function
# *************************

def compute_score(doc, tokens, stats):
    """
    Compute a linear ranking score combining multiple signals:
    - term frequency in title, description and reviews
    - exact match in title
    - number of reviews
    """
    score = 0.0

    for t in tokens:
        if t in title_index and doc in title_index[t]:
            score += 3 * len(title_index[t][doc])

        if t in description_index and doc in description_index[t]:
            score += 1 * len(description_index[t][doc])

        if t in reviews_index and doc in reviews_index[t]:
            score += 0.5 * len(reviews_index[t][doc])

    score += 5 * exact_match_score(tokens, stats["title_tokens"])
    score += 0.1 * stats["review_count"]

    return score


# *************************
# Search pipeline
# *************************

def search(query, documents_metadata):
    """
    Execute a search query:
    - process query
    - filter candidate documents
    - compute ranking scores
    - sort and save results
    """
    tokens = process_query(query)
    filtered_docs = filter_documents(tokens)

    results = []

    for doc in filtered_docs:
        stats = documents_metadata[doc]
        score = compute_score(doc, tokens, stats)

        results.append({
            "title": stats["title"],
            "url": doc,
            "description": stats["description"],
            "score": round(score, 3)
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    results = {
        "query": query,
        "total_documents": len(documents_metadata),
        "filtered_documents": len(filtered_docs),
        "results": results
    }

    save_results(results, "output/results.jsonl")


# *************************
# Entry point
# *************************

if __name__ == "__main__":
    
    query = "white beanie"
    search(query, documents_metadata)

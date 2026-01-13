#As input, i didsn't use my input from TP1, since i didn't extract information such as product_features
import json
import re
import string
from collections import defaultdict
from statistics import mean


def load_jsonl(filepath):
    """
    Load a JSONL file where each line is a JSON document.

    Args:
        filepath (str): Path to the JSONL file

    Returns:
        list: List of parsed JSON documents
    """
    documents = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            try:
                documents.append(json.loads(line))
            except json.JSONDecodeError:
                # Skip malformed JSON lines
                continue
    return documents


def extract_product_id_and_variant(url):
    """
    Extract product ID and variant from a product URL.

    Args:
        url (str): Product URL

    Returns:
        tuple: (product_id, variant)
    """
    product_id = None
    variant = None

    # Extract numeric product ID from URL
    match = re.search(r"/(\d+)", url)
    if match:
        product_id = match.group(1)

    # Extract variant if present
    if "variant=" in url:
        variant = url.split("variant=")[1]

    return product_id, variant


# Common English stopwords removed during tokenization
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "while", "with", "of", "at", "by", "for",
    "in", "on", "to", "from", "as", "is", "are", "was", "were", "be", "been", "has", "have",
    "it", "this", "that", "these", "those", "so", "not", "your", "my", "their", "our",
    "can", "will", "just", "i", "you", "he", "she", "they", "we", "me", "him", "her",
    "them", "do", "does", "did"
}


def tokenize(text):
    """
    Normalize and tokenize a text string.

    - Lowercase
    - Remove punctuation
    - Split by spaces
    - Remove stopwords

    Args:
        text (str): Input text

    Returns:
        list: List of filtered tokens
    """
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    tokens = text.split()
    return [t for t in tokens if t not in STOPWORDS]


def save_results(results, filename):
    """
    Save an index or result dictionary to a JSON file.

    Args:
        results (dict): Index data
        filename (str): Output file path
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def build_inverted_index(documents, field):
    """
    Build a positional inverted index for a given text field.

    Structure:
    token -> { url -> [positions] }

    Args:
        documents (list): List of product documents
        field (str): Field to index (title or description)

    Returns:
        dict: Positional inverted index
    """
    index = defaultdict(dict)

    for doc in documents:
        url = doc.get("url")
        text = doc.get(field, "")

        # Tokenize text
        tokens = set(tokenize(text))

        # Map each token to its positions in the document
        positions_map = defaultdict(list)
        split_tokens = tokenize(text)
        for idx, t in enumerate(split_tokens):
            positions_map[t].append(idx)

        # Store positions per token and URL
        for token in tokens:
            index[token][url] = positions_map[token]

    # Save index to disk
    save_results(index, "output/" + field + "_index.json")

    return index


def build_reviews_index(documents):
    """
    Build a non-inverted index for product reviews.

    Structure:
    url -> {
        total_reviews,
        mean_mark,
        last_rating
    }

    Args:
        documents (list): List of product documents

    Returns:
        dict: Reviews index
    """
    reviews_index = {}

    for doc in documents:
        url = doc.get("url")
        reviews = doc.get("product_reviews", [])

        # Handle products with no reviews
        if not reviews:
            reviews_index[url] = {
                "total_reviews": 0,
                "mean_mark": 0,
                "last_rating": 0
            }
            continue

        # Extract numerical ratings
        ratings = [r["rating"] for r in reviews if "rating" in r]

        reviews_index[url] = {
            "total_reviews": len(ratings),
            "mean_mark": mean(ratings),
            "last_rating": ratings[-1]
        }

    save_results(reviews_index, "output/reviews_index.json")
    return reviews_index


def build_feature_indexes(documents):
    """
    Build one inverted index per product feature (brand, origin, etc.).

    Structure per feature:
    token -> [urls]

    Args:
        documents (list): List of product documents

    Returns:
        dict: All feature indexes
    """
    # Collect all possible feature names
    all_features = set()
    for doc in documents:
        features = doc.get("product_features", {})
        all_features.update(features.keys())

    all_indexes = {}

    for feature in all_features:
        feature_indexes = defaultdict(list)

        for doc in documents:
            url = doc.get("url", "")
            features = doc.get("product_features", {})

            if feature in features:
                feature_value = features[feature]
                tokens = tokenize(str(feature_value))
                for token in tokens:
                    feature_indexes[token].append(url)

        # Special case for "made in" feature naming
        if feature == "made in":
            file_path = "output/origin_index.json"
        else:
            file_path = f"output/{feature}_index.json"

        save_results(feature_indexes, file_path)
        all_indexes[feature] = feature_indexes

    return all_indexes


def main():
    """
    Main execution pipeline:
    - Load data
    - Build title and description indexes
    - Build reviews index
    - Build feature indexes
    """
    documents = load_jsonl("input/products.jsonl")

    build_inverted_index(documents, "title")
    build_inverted_index(documents, "description")
    build_reviews_index(documents)
    build_feature_indexes(documents)


if __name__ == "__main__":
    main()

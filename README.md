# TP1: Web Crawler

A polite, priority-based web crawler that respects robots.txt rules and rate limits to avoid overloading servers.

## Features

- **robots.txt compliance** – Parses and follows robots.txt rules
- **Priority queue** – Prioritizes URLs containing `"product"` to discover product pages faster
- **Rate limiting** – Configurable delay between requests
- **Internal links only** – Crawls links within the same domain
- **Data extraction** – Extracts page title, first paragraph, and internal links
- **JSON output** – Saves results to a structured JSON file

Crawler steps:
1. Start from `https://web-scraping.dev/products`
2. Crawl up to 50 pages (configurable)
3. Wait 1 second between requests (configurable)
4. Save results to `products.json`

## Output format

Results are saved as a JSON array, each entry contains:

```json
{
  "url": "https://example.com/page",
  "title": "Page title",
  "description": "First paragraph text...",
  "links": ["https://example.com/link1", "https://example.com/link2"]
}
```

# TP2 – Inverted Index Construction

Builds multiple inverted indexes from product data stored in JSONL.

## Description

Indexes built from a JSONL product file:
- **Inverted indexes** on titles and descriptions
- **Reviews index** with stats (average, total count, last rating)
- **Feature indexes** (brand, origin, etc.)

## Project structure

```
TP2/
├── index_builder.py           # Main script
├── input/
│   └── products.jsonl         # Input file (JSONL)
└── output/                    # Output directory
    ├── title_index.json       # Title inverted index
    ├── description_index.json # Description inverted index
    ├── reviews_index.json     # Reviews stats index
    ├── brand_index.json       # Brand feature index
    └── origin_index.json      # Origin feature index
```

## Features

### 1. Inverted index (`build_inverted_index`)
Builds an inverted index for a given field (title or description).
- **Structure**: `{token: {url: [positions]}}`
- Tokens map to URLs and their positions
- Stopwords removed, punctuation stripped, lowercased

### 2. Reviews index (`build_reviews_index`)
Creates per-product review statistics.
- **Structure**: `{url: {total_reviews, mean_mark, last_rating}}`
- Computes total reviews, average rating, last rating

### 3. Feature indexes (`build_feature_indexes`)
Builds inverted indexes for specific features (brand, origin, etc.).
- **Structure**: `{token: [urls]}`
- Tokenizes feature values and maps tokens to product URLs

## Usage

### Input format

The input file must be JSONL, each line like:
```json
{
  "url": "https://example.com/product/1",
  "title": "Product name",
  "description": "Product description...",
  "product_features": {
    "brand": "Brand",
    "made in": "Country of origin"
  },
  "product_reviews": [
    {"rating": 5, "date": "2023-01-01", "text": "Great product"},
    {"rating": 4, "date": "2023-02-01", "text": "Very good"}
  ]
}
```

### Run

```bash
python index_builder.py
```

Steps:
1. Load documents from `products.jsonl`
2. Build title index → `output/title_index.json`
3. Build description index → `output/description_index.json`
4. Build reviews index → `output/reviews_index.json`
5. Build feature indexes → `output/brand_index.json` and `output/origin_index.json`

### Customize

Edit `main()` to change input or indexed features:

```python
def main():
    documents = load_jsonl("your_file.jsonl")
    
    build_inverted_index(documents, "title")
    build_inverted_index(documents, "description")
    build_reviews_index(documents)
    build_feature_indexes(documents, "brand")
    build_feature_indexes(documents, "made in")
```

## Output format

### Inverted index
```json
{
  "token1": {
    "https://example.com/product/1": [0, 5, 10],
    "https://example.com/product/2": [2, 8]
  },
  "token2": {
    "https://example.com/product/1": [1, 3]
  }
}
```

### Reviews index
```json
{
  "https://example.com/product/1": {
    "total_reviews": 5,
    "mean_mark": 4.2,
    "last_rating": 5
  }
}
```

### Feature index (brand)
```json
{
  "brand1": [
    "https://example.com/product/1",
    "https://example.com/product/2"
  ],
  "brand2": [
    "https://example.com/product/3"
  ]
}
```

## Key functions

- `load_jsonl(filepath)`: load JSONL to a list of dicts
- `tokenize(text)`: lowercase, strip punctuation, split, filter stopwords
- `build_inverted_index(documents, field)`: build inverted index for a field
- `build_reviews_index(documents)`: build review stats index
- `build_feature_indexes(documents, feature)`: build feature index
- `save_results(results, filename)`: save JSON output

# TP3 – Search Engine

A search engine that uses the TP2 indexes to search and rank products by relevance.

## Description

The engine can:
- Process user queries (tokenize, normalize, expand synonyms)
- Filter candidate documents across multiple indexes
- Compute relevance scores (BM25 + additional signals)
- Rank and return results by relevance

## Project structure

```
TP3/
├── browser.py                  # Main search engine
├── input/
│   ├── title_index.json        # Title index (TP2)
│   ├── description_index.json  # Description index (TP2)
│   ├── brand_index.json        # Brand index (TP2)
│   ├── origin_index.json       # Origin index (TP2)
│   ├── reviews_index.json      # Reviews index (TP2)
│   ├── origin_synonyms.json    # Synonyms for origins
│   └── rearranged_products.jsonl # Product documents
└── output/
    └── results.jsonl           # Search results
```

## Features

### 1. Query processing (`process_query`)
Pipeline:
- Tokenization: lowercase, remove punctuation
- Normalization: remove stopwords
- Synonym expansion: add equivalent terms (e.g., "usa" → "united states", "america")

### 2. Document filtering

#### `filter_any_token(tokens, index)`
- Docs containing **at least one** token (OR logic); maximizes recall

#### `filter_all_tokens(tokens, index)`
- Docs containing **all** tokens (AND logic); improves precision

#### `filter_documents(tokens)`
- Hybrid strategy:
  - OR across all indexes (title, description, brand, origin)
  - AND on title index
  - Union of both candidate sets

### 3. BM25 scoring (`bm25`)
- Implements BM25:
  - **IDF** for rare terms
  - **TF** term frequency
  - Length normalization
  - Defaults: `k1=1.5`, `b=0.75`

### 4. Combined score (`compute_score`)
- Title occurrences: ×3 per occurrence
- Description occurrences: ×1
- Review occurrences: ×0.5
- Exact match in title: +5 if all tokens present
- Review count: +0.1 per review (boosts popularity)

### 5. Search function (`search`)
Full pipeline:
1. Process query
2. Filter candidate docs
3. Compute scores per doc
4. Sort by descending score
5. Save results

## Prerequisites

- Python 3.x
- NLTK
  ```bash
  pip install nltk
  ```

## Usage

### Run

```bash
python browser.py
```

Steps:
1. Load indexes from `input/`
2. Process the query in `main()` (e.g., `"white beanie"`)
3. Filter and score documents
4. Save results to `output/results.jsonl`

## Output format

Results are saved as JSONL:

```json
{
  "query": "white beanie",
  "total_documents": 157,
  "filtered_documents": 12,
  "results": [
    {
      "title": "White Wool Beanie",
      "url": "https://web-scraping.dev/product/5",
      "description": "Product description...",
      "score": 8
    },
    {
      "title": "Beanie White",
      "url": "https://web-scraping.dev/product/8",
      "description": "Another description...",
      "score": 6
    }
  ]
}
```

Results are sorted by descending score.

## Key functions

- `load_jsonl(filepath)` / `load_json(filepath)`: load data
- `tokenize(text)`: tokenize text
- `normalize(tokens)`: remove stopwords
- `expand_with_synonyms(tokens)`: add synonyms
- `process_query(query)`: full query pipeline
- `filter_any_token(tokens, index)`: OR filtering
- `filter_all_tokens(tokens, index)`: AND filtering
- `filter_documents(tokens)`: hybrid filtering
- `bm25_score(tf, df, doc_len, avgdl, N)`: BM25 term score
- `bm25(tokens, index, doc_lengths)`: BM25 document scoring
- `exact_match_score(tokens, title_tokens)`: exact title match
- `compute_score(doc, tokens, stats)`: combined relevance score
- `search(query, documents_metadata)`: main search function

## Author

Oumayma HMIDICH

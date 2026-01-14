# TP1 : Web Crawler - Indexation Web

Un crawler web poli et basé sur les priorités qui respecte les règles robots.txt et implémente un système de limitation de débit pour explorer les sites web de manière efficace.

## Fonctionnalités

- **Respect de robots.txt** - Vérifie et suit automatiquement les règles robots.txt
- **File d'attente prioritaire** - Priorise les URLs contenant "product" pour découvrir plus rapidement les pages produits
- **Limitation de débit** - Délais configurables entre les requêtes pour éviter de surcharger les serveurs
- **Liens internes uniquement** - Explore uniquement les liens du même domaine
- **Extraction de données** - Extrait le titre de la page, le premier paragraphe et tous les liens internes
- **Sortie JSON** - Sauvegarde les résultats dans un format JSON structuré


Le crawler va :
1. Commencer depuis `https://web-scraping.dev/products`
2. Explorer jusqu'à 50 pages (configurable)
3. Attendre 1 seconde entre les requêtes (configurable)
4. Sauvegarder les résultats dans `products.json`


## Format de sortie

Les résultats sont sauvegardés sous forme de tableau JSON, où chaque entrée contient :

```json
{
  "url": "https://example.com/page",
  "title": "Titre de la page",
  "description": "Texte du premier paragraphe...",
  "links": ["https://example.com/link1", "https://example.com/link2"]
}
```

# TP2 - Construction d'Index Inversé

Ce projet implémente un système de construction d'index inversé pour la recherche d'information sur des documents produits au format JSONL.

## Description

Le système construit plusieurs types d'index à partir d'un fichier JSONL contenant des données de produits :
- **Index inversé** sur les titres et descriptions
- **Index des avis** avec statistiques (moyenne, nombre total, dernière note)
- **Index des caractéristiques** (marque, origine, etc.)

## Structure du projet

```
TP2/
├── index_builder.py          # Script principal
├── input/
│   └── products.jsonl        # Fichier d'entrée (format JSONL)
└── output/                   # Répertoire de sortie
    ├── title_index.json      # Index inversé des titres
    ├── description_index.json # Index inversé des descriptions
    ├── reviews_index.json     # Index des avis produits
    ├── brand_index.json       # Index des marques
    └── origin_index.json     # Index des origines
```

## Fonctionnalités

### 1. Index inversé (`build_inverted_index`)
Construit un index inversé pour un champ donné (titre ou description).
- **Structure** : `{token: {url: [positions]}}`
- Chaque token est associé aux URLs où il apparaît et à leurs positions dans le texte
- Les mots vides (stopwords) sont filtrés
- La ponctuation est supprimée
- Les tokens sont en minuscules

### 2. Index des avis (`build_reviews_index`)
Crée un index des statistiques d'avis pour chaque produit.
- **Structure** : `{url: {total_reviews, mean_mark, last_rating}}`
- Calcule le nombre total d'avis
- Calcule la note moyenne
- Récupère la dernière note donnée

### 3. Index des caractéristiques (`build_feature_indexes`)
Construit un index inversé pour une caractéristique spécifique (marque, origine, etc.).
- **Structure** : `{token: [urls]}`
- Tokenise la valeur de la caractéristique
- Associe chaque token aux URLs des produits correspondants


## Utilisation

### Format d'entrée

Le fichier d'entrée doit être au format JSONL, où chaque ligne contient un objet JSON avec :
```json
{
  "url": "https://example.com/product/1",
  "title": "Nom du produit",
  "description": "Description du produit...",
  "product_features": {
    "brand": "Marque",
    "made in": "Pays d'origine"
  },
  "product_reviews": [
    {"rating": 5, "date": "2023-01-01", "text": "Excellent produit"},
    {"rating": 4, "date": "2023-02-01", "text": "Très bien"}
  ]
}
```

### Exécution

```bash
python index_builder.py
```

Le script va :
1. Charger les documents depuis `products.jsonl`
2. Construire l'index inversé des titres → `output/title_index.json`
3. Construire l'index inversé des descriptions → `output/description_index.json`
4. Construire l'index des avis → `output/reviews_index.json`
5. Construire les index des caractéristiques → `output/brand_index.json` et `output/origin_index.json`

### Personnalisation

Pour modifier le fichier d'entrée ou les caractéristiques indexées, modifiez la fonction `main()` :

```python
def main():
    documents = load_jsonl("votre_fichier.jsonl")
    
    build_inverted_index(documents, "title")
    build_inverted_index(documents, "description")
    build_reviews_index(documents)
    build_feature_indexes(documents, "brand")
    build_feature_indexes(documents, "made in")
```

## Format de sortie

### Index inversé
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

### Index des avis
```json
{
  "https://example.com/product/1": {
    "total_reviews": 5,
    "mean_mark": 4.2,
    "last_rating": 5
  }
}
```

### Index des caractéristiques (brand)
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

## Fonctions principales

- `load_jsonl(filepath)` : Charge un fichier JSONL et retourne une liste de dictionnaires
- `tokenize(text)` : Tokenise un texte (minuscules, suppression ponctuation, filtrage stopwords)
- `build_inverted_index(documents, field)` : Construit un index inversé pour un champ donné
- `build_reviews_index(documents)` : Construit l'index des statistiques d'avis
- `build_feature_indexes(documents, feature)` : Construit l'index d'une caractéristique spécifique
- `save_results(results, filename)` : Sauvegarde les résultats au format JSON

# TP3 - Moteur de Recherche

Ce projet implémente un moteur de recherche complet utilisant les index inversés construits dans le TP2 pour rechercher et classer des produits selon leur pertinence.

## Description

Le moteur de recherche permet de :
- Traiter les requêtes utilisateur (tokenisation, normalisation, expansion de synonymes)
- Filtrer les documents candidats à partir de plusieurs index
- Calculer des scores de pertinence (BM25 + signaux additionnels)
- Classer et retourner les résultats triés par pertinence

## Structure du projet

```
TP3/
├── browser.py                 # Moteur de recherche principal
├── input/
│   ├── title_index.json       # Index inversé des titres (TP2)
│   ├── description_index.json # Index inversé des descriptions (TP2)
│   ├── brand_index.json       # Index des marques (TP2)
│   ├── origin_index.json      # Index des origines (TP2)
│   ├── reviews_index.json     # Index des avis (TP2)
│   ├── origin_synonyms.json   # Dictionnaire de synonymes pour les origines
│   └── rearranged_products.jsonl # Documents produits
└── output/
    └── results.jsonl          # Résultats de recherche
```

## Fonctionnalités

### 1. Traitement de requête (`process_query`)

Pipeline complet de traitement :
- **Tokenisation** : Conversion en minuscules, suppression de la ponctuation
- **Normalisation** : Suppression des stopwords (mots vides)
- **Expansion de synonymes** : Ajout de termes synonymes (ex: "USA" → "United States", "America")

### 2. Filtrage de documents

#### `filter_any_token(tokens, index)`
- Retourne les documents contenant **au moins un** token de la requête (logique OR)
- Utilisé pour maximiser le rappel (recall)

#### `filter_all_tokens(tokens, index)`
- Retourne les documents contenant **tous** les tokens de la requête (logique AND)
- Utilisé pour améliorer la précision (precision)

#### `filter_documents(tokens)`
- Stratégie hybride :
  - Filtrage OR sur tous les index (titre, description, marque, origine)
  - Filtrage AND strict sur l'index des titres
  - Union des deux ensembles de candidats

### 3. Scoring BM25 (`bm25`)

Implémentation de l'algorithme BM25 (Best Matching 25) :
- **IDF (Inverse Document Frequency)** : Poids des termes rares
- **TF (Term Frequency)** : Fréquence des termes dans le document
- **Normalisation de longueur** : Ajustement selon la longueur du document
- Paramètres par défaut : `k1=1.5`, `b=0.75`

### 4. Score combiné (`compute_score`)

Score de pertinence combinant plusieurs signaux :
- **Occurrences dans le titre** : ×3 par occurrence
- **Occurrences dans la description** : ×1 par occurrence
- **Occurrences dans les avis** : ×0.5 par occurrence
- **Match exact dans le titre** : +5 si tous les tokens sont présents
- **Nombre d'avis** : +0.1 par avis (favorise les produits populaires)

### 5. Fonction de recherche (`search`)

Pipeline complet :
1. Traitement de la requête
2. Filtrage des documents candidats
3. Calcul des scores pour chaque document
4. Tri par score décroissant
5. Sauvegarde des résultats

## Prérequis

- Python 3.x
- NLTK (Natural Language Toolkit)
  ```bash
  pip install nltk
  ```

## Utilisation

### Exécution

```bash
python browser.py
```

Le script va :
1. Charger tous les index depuis le répertoire `input/`
2. Traiter la requête définie dans `main()` (ex: `"white beanie"`)
3. Filtrer et scorer les documents
4. Sauvegarder les résultats dans `output/results.jsonl`


## Format de sortie

Les résultats sont sauvegardés au format JSONL avec la structure suivante :

```json
{
  "query": "white beanie",
  "total_documents": 157,
  "filtered_documents": 12,
  "results": [
    {
      "title": "White Wool Beanie",
      "url": "https://web-scraping.dev/product/5",
      "description": "Description du produit...",
      "score": 8
    },
    {
      "title": "Beanie White",
      "url": "https://web-scraping.dev/product/8",
      "description": "Autre description...",
      "score": 6
    }
  ]
}
```

Les résultats sont triés par score décroissant (du plus pertinent au moins pertinent).


# Web Crawler - Indexation Web

Un crawler web poli et basé sur les priorités qui respecte les règles robots.txt et implémente un système de limitation de débit pour explorer les sites web de manière efficace.

## Fonctionnalités

- **Respect de robots.txt** - Vérifie et suit automatiquement les règles robots.txt
- **File d'attente prioritaire** - Priorise les URLs contenant "product" pour découvrir plus rapidement les pages produits
- **Limitation de débit** - Délais configurables entre les requêtes pour éviter de surcharger les serveurs
- **Liens internes uniquement** - Explore uniquement les liens du même domaine
- **Extraction de données** - Extrait le titre de la page, le premier paragraphe et tous les liens internes
- **Sortie JSON** - Sauvegarde les résultats dans un format JSON structuré

## Prérequis

- Python 3.x
- BeautifulSoup4

## Installation

```bash
pip install beautifulsoup4
```

## Utilisation

```bash
python crawler.py
```

Le crawler va :
1. Commencer depuis `https://web-scraping.dev/products`
2. Explorer jusqu'à 50 pages (configurable)
3. Attendre 1 seconde entre les requêtes (configurable)
4. Sauvegarder les résultats dans `products.json`

### Personnalisation

Vous pouvez modifier la fonction `main()` dans `crawler.py` pour changer :
- L'URL de départ
- Le nombre maximum de pages (`max_pages`)
- Le délai entre les requêtes (`delay`)

## Format de sortie

Les résultats sont sauvegardés sous forme de tableau JSON, où chaque entrée contient :

```json
{
  "url": "https://example.com/page",
  "title": "Titre de la page",
  "first_paragraph": "Texte du premier paragraphe...",
  "links": ["https://example.com/link1", "https://example.com/link2"]
}
```

## Fonctionnement

1. **Système de priorité** : Les URLs contenant "product" obtiennent la priorité 0 (la plus haute), les autres obtiennent la priorité 1
2. **Conformité robots.txt** : Vérifie `robots.txt` avant d'explorer chaque URL
3. **Parcours en largeur avec priorité** : Utilise une file d'attente prioritaire pour traiter d'abord les URLs à haute priorité
4. **Limitation de débit** : Implémente des délais entre les requêtes pour être respectueux envers les serveurs



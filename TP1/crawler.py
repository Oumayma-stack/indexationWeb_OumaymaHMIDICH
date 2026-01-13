"""
Web Crawler Module

This module implements a polite web crawler that respects robots.txt rules,
uses priority-based crawling (prioritizing product pages), and includes
rate limiting to avoid overloading servers.

Features:
- Respects robots.txt files
- Priority queue system (product URLs have higher priority)
- Rate limiting with configurable delays
- Extracts title, first paragraph, and links from pages
- Saves results to JSON format
"""

import json
import time
import heapq
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen
from urllib.robotparser import RobotFileParser
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup


def get_robot_parser(start_url):
    """
    Fetches and parses the robots.txt file for a given domain.
    
    Args:
        start_url (str): The starting URL from which to extract the domain
        
    Returns:
        RobotFileParser: A parser object that can check if URLs are allowed
    """
    parsed = urlparse(start_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    rp.read()
    return rp


def can_fetch(url, robot_parser):
    """
    Checks if a URL can be fetched according to robots.txt rules.
    
    Args:
        url (str): The URL to check
        robot_parser (RobotFileParser): The parser containing robots.txt rules
        
    Returns:
        bool: True if the URL can be fetched, False otherwise
    """
    return robot_parser.can_fetch("*", url)


def get_html(url):
    """
    Fetches the HTML content from a URL.
    
    Args:
        url (str): The URL to fetch
        
    Returns:
        bytes: The HTML content as bytes, or None if an error occurred
    """
    try:
        with urlopen(url, timeout=10) as response:
            return response.read()
    except (URLError, HTTPError):
        return None


def parse_html(html):
    """
    Parses HTML content using BeautifulSoup.
    
    Args:
        html (bytes): The HTML content to parse
        
    Returns:
        BeautifulSoup: A parsed BeautifulSoup object for navigating the HTML
    """
    return BeautifulSoup(html, "html.parser")


def get_priority(url):
    """
    Assigns a priority to a URL based on its content.
    Lower priority numbers indicate higher priority.
    
    Args:
        url (str): The URL to assign a priority to
        
    Returns:
        int: Priority 0 for URLs containing 'product', priority 1 for others
    """
    return 0 if "product" in url.lower() else 1


def is_internal_link(link, base_url):
    """
    Checks if a link belongs to the same domain as the base URL.
    
    Args:
        link (str): The link to check
        base_url (str): The base URL to compare against
        
    Returns:
        bool: True if the link is internal (same domain), False otherwise
    """
    return urlparse(link).netloc == urlparse(base_url).netloc


def crawl_website(start_url, max_pages=50, delay=1):
    """
    Crawls a website starting from a given URL using a priority-based approach.
    
    The crawler:
    - Respects robots.txt rules
    - Uses a priority queue (product URLs are crawled first)
    - Only crawls internal links 
    - Extracts title, first paragraph, and links from each page
    - Implements rate limiting with delays between requests
    
    Args:
        start_url (str): The starting URL to begin crawling from
        max_pages (int, optional): Maximum number of pages to crawl. Defaults to 50.
        delay (int, optional): Delay in seconds between requests. Defaults to 1.
        
    Returns:
        list: A list of dictionaries, each containing:
            - url: The crawled URL
            - title: The page title
            - first_paragraph: The first paragraph of text
            - links: List of internal links found on the page
    """
    # Initialize robots.txt parser for the domain
    robot_parser = get_robot_parser(start_url)

    visited = set()  # Track visited URLs to avoid duplicates
    results = []  # Store extracted data from each page
    queue = []  # Priority queue for URLs to crawl

    # Start with the initial URL
    heapq.heappush(queue, (get_priority(start_url), start_url))

    while queue and len(visited) < max_pages:
        # Get the highest priority URL from the queue
        _, url = heapq.heappop(queue)

        # Skip if already visited or not allowed by robots.txt
        if url in visited or not can_fetch(url, robot_parser):
            continue

        # Fetch and parse the HTML content
        html = get_html(url)
        if html is None:
            continue

        soup = parse_html(html)

        # Extract page title
        title = soup.title.string.strip() if soup.title else ""
        # Extract first paragraph
        p = soup.find("p")
        first_paragraph = p.get_text(strip=True) if p else ""

        # Extract and process links
        links = []
        for a in soup.find_all("a", href=True):
            link = urljoin(url, a["href"])
            # Only process internal links (same domain)
            if is_internal_link(link, start_url):
                links.append(link)
                # Add new links to the priority queue if not already visited
                if link not in visited:
                    heapq.heappush(queue, (get_priority(link), link))

        visited.add(url)

        # Store the extracted data
        results.append({
            "url": url,
            "title": title,
            "description": first_paragraph,
            "links": links
        })

        # Rate limiting: wait before next request
        time.sleep(delay)

    return results


def save_results(results, filename="products.jsonl"):
    """
    Saves the crawling results to a JSONL file (one JSON object per line).
    
    Args:
        results (list): List of dictionaries containing crawled page data
        filename (str, optional): Name of the output file. Defaults to "products.jsonl".
    """
    with open(filename, "w", encoding="utf-8") as f:
        for result in results:
            # Write each result as a single line of JSON
            f.write(json.dumps(result, ensure_ascii=False) + "\n")


def main():
    """
    Main function that orchestrates the web crawling process.
    Crawls the target website and saves the results to a JSONL file.
    """
    start_url = "https://web-scraping.dev/products"
    results = crawl_website(start_url, max_pages=50)
    save_results(results, "products.jsonl")
    print(f"{len(results)} pages crawlées.")


if __name__ == "__main__":
    main()

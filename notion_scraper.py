import requests
from bs4 import BeautifulSoup
import json


def scrape_notion_help_articles():
    # Set up request headers to mimic a real browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    # Target URL for Notion's help center
    url = "https://www.notion.com/help"
    
    # Send HTTP GET request with headers
    response = requests.get(url, headers=headers)
    
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Use a set to store article URLs to automatically deduplicate
    articles = set()

    # Find all anchor tags with href attributes
    for link in soup.find_all('a', href=True):
        article_url = link['href']
        
        # Filter for valid help article URLs and exclude Notion Academy content
        if article_url.startswith('/help/') and 'academy' not in article_url:
            # Construct full URL
            full_url = f"https://www.notion.com{article_url}"
            articles.add(full_url)  # Add to set for automatic deduplication

    # Convert set to list before returning
    return list(articles)


def extract_text_from_article(url):
    # Send HTTP GET request to fetch article content
    response = requests.get(url)
    
    # Parse HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    text_content = []

    # Extract core text elements while ignoring images and other media
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li', 'blockquote']):
        if element.name.startswith('h'):
            # Format headings with their level and text
            text_content.append(f"\n{element.name.upper()}: {element.get_text(strip=True)}\n")
        elif element.name == 'p':
            # Add paragraph text
            text_content.append(f"{element.get_text(strip=True)}\n")
        elif element.name in ['ul', 'ol']:
            # Handle unordered and ordered lists
            text_content.append("\n")
            for li in element.find_all('li'):
                text_content.append(f"- {li.get_text(strip=True)}\n")
            text_content.append("\n")
        elif element.name == 'blockquote':
            # Handle blockquote elements as notes
            text_content.append(f"\nNOTE: {element.get_text(strip=True)}\n")

    # Join all extracted text elements into a single string
    return ''.join(text_content)


def split_into_chunks(text, max_chars=750):
    chunks = []
    current_chunk = []
    current_length = 0

    # Split text into lines for processing
    lines = text.split('\n')
    for line in lines:
        line_length = len(line)
        
        # Check if adding the current line would exceed the chunk size limit
        if current_length + line_length + 1 > max_chars:
            # If line is a header or list item, merge with current chunk
            if line.strip().startswith(('-', '#')) or line.strip().endswith(':'):
                current_chunk.append(line + '\n')
                current_length += line_length + 1
            else:
                # Save current chunk and start a new one
                chunks.append(''.join(current_chunk))
                current_chunk = [line + '\n']
                current_length = line_length + 1
        else:
            # Add line to current chunk
            current_chunk.append(line + '\n')
            current_length += line_length + 1

    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(''.join(current_chunk))

    return chunks


def main():
    # Step 1: Scrape all help articles
    articles = scrape_notion_help_articles()
    print(f"Found {len(articles)} unique help articles.")

    # Step 2: Extract text content from each article
    all_text = []
    for article_url in articles:
        print(f"Processing: {article_url}")
        text = extract_text_from_article(article_url)
        all_text.append(text)

    # Step 3: Split text into manageable chunks
    chunks = []
    for text in all_text:
        chunks.extend(split_into_chunks(text))

    # Output results
    print(f"Generated {len(chunks)} chunks.")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1} ({len(chunk)} chars):\n{chunk}\n{'-'*50}")
    
    # Save chunks to a JSON file
    with open('notion_help_chunks.json', 'w') as f:
        json.dump(chunks, f, indent=2)


if __name__ == "__main__":
    main()
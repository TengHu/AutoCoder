import requests
from bs4 import BeautifulSoup


def crawl_web(start_url, max_pages):
    # Create a list to store the URLs to be crawled
    pages_to_crawl = [start_url]
    # Create a set to store the visited URLs
    visited_pages = set()

    # Continue crawling until either the maximum number of pages is reached or there are no more pages to crawl
    while pages_to_crawl and len(visited_pages) < max_pages:
        # Get the next URL to crawl
        url = pages_to_crawl.pop(0)

        # Skip if the URL has already been visited
        if url in visited_pages:
            continue

        try:
            # Send an HTTP GET request to the URL
            response = requests.get(url)
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.content, 'html.parser')

            # Process the page (e.g., extract data, store in database, etc.)
            process_page(url, soup)

            # Add the URL to the set of visited pages
            visited_pages.add(url)

            # Find all anchor tags in the HTML and extract the URLs
            for link in soup.find_all('a'):
                href = link.get('href')
                if href.startswith('http') and href not in visited_pages:
                    # Add the URL to the list of pages to crawl
                    pages_to_crawl.append(href)

        except requests.exceptions.RequestException:
            # Handle any errors that occur during the crawling process
            handle_error(url)

    # Crawl completed
    print("Crawling completed.")



def process_page(url, soup):
    # Implement your logic to process the page here
    # This could include extracting data, storing in a database, etc.
    print("Processing:", url)


def handle_error(url):
    # Implement your logic to handle errors here
    # This could include logging the error, retrying the request, etc.
    print("Error occurred while crawling:", url)


# Example usage
crawl_web("https://example.com", 10)
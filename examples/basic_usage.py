#!/usr/bin/env python3
"""
Basic usage example of Grab framework.
This script demonstrates how to make requests and extract data from web pages.
"""

import sys
import os
import logging
from pathlib import Path

# Add the parent directory to sys.path to be able to import grab
parent_dir = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, parent_dir)

from grab import HttpClient
from grab.errors import GrabError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('grab-example')

def simple_get_request():
    """Demonstrate a simple GET request and response processing."""
    client = HttpClient()
    try:
        # Make a request to a public API
        resp = client.request('https://httpbin.org/get')
        
        # Check if request was successful
        logger.info(f'Status code: {resp.code}')
        logger.info(f'Request URL: {resp.url}')
        
        # Parse JSON response
        response_data = resp.json
        logger.info(f'Response data: {response_data}')
        
        return True
    except GrabError as e:
        logger.error(f'Error making request: {e}')
        return False

def post_request_with_data():
    """Demonstrate a POST request with form data."""
    client = HttpClient()
    try:
        # Prepare form data
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'message': 'Hello from Grab framework!'
        }
        
        # Make a POST request using fields parameter
        resp = client.request('https://httpbin.org/post', method='POST', fields=data)
        
        # Check if request was successful
        logger.info(f'Status code: {resp.code}')
        
        # Parse JSON response
        response_data = resp.json
        logger.info(f'Form data sent: {response_data["form"]}')
        
        return True
    except GrabError as e:
        logger.error(f'Error making POST request: {e}')
        return False

def scrape_html_content():
    """Demonstrate HTML content extraction using lxml."""
    client = HttpClient()
    try:
        # Make a request to example.com
        resp = client.request('http://example.com')
        
        # Extract title using XPath
        title = resp.select('//title').text()
        logger.info(f'Page title: {title}')
        
        # Extract paragraphs
        paragraphs = resp.select('//p')
        for p in paragraphs:
            logger.info(f'Paragraph text: {p.text()}')
        
        return True
    except GrabError as e:
        logger.error(f'Error scraping HTML: {e}')
        return False

def handle_cookies():
    """Demonstrate cookie handling."""
    client = HttpClient()
    try:
        # Make a request to set a cookie
        client.request('https://httpbin.org/cookies/set?name=value')
        
        # Make another request and get the cookies
        resp = client.request('https://httpbin.org/cookies')
        
        # Parse JSON response
        response_data = resp.json
        logger.info(f'Cookies: {response_data["cookies"]}')
        
        return True
    except GrabError as e:
        logger.error(f'Error handling cookies: {e}')
        return False

def main():
    """Run all examples."""
    logger.info('Starting Grab examples...')
    
    logger.info('\n=== Simple GET Request ===')
    simple_get_request()
    
    logger.info('\n=== POST Request with Data ===')
    post_request_with_data()
    
    logger.info('\n=== HTML Content Extraction ===')
    scrape_html_content()
    
    logger.info('\n=== Cookie Handling ===')
    handle_cookies()
    
    logger.info('\nAll examples completed.')

if __name__ == '__main__':
    main() 
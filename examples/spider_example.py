#!/usr/bin/env python3
"""
Spider usage example of Grab framework.
This script demonstrates how to create and use a Spider for concurrent crawling.
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Generator, Optional, cast, Any

# Add the parent directory to sys.path to be able to import grab
parent_dir = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, parent_dir)

from grab.spider import Spider, Task
from grab.spider.errors import SpiderError
from grab import HttpClient, Document

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('grab-spider-example')

class SimpleSpider(Spider):
    """A simple spider to crawl a website and extract basic information."""
    
    # Initial URLs to start crawling from
    initial_urls = ['http://example.com']
    
    def task_initial(self, grab: Document, task: Task) -> Generator[Task, None, None]:
        """Process the initial task."""
        logger.info(f'Processing initial URL: {task.url}')
        
        # Extract and log the title
        title = grab.select('//title').text()
        logger.info(f'Page title: {title}')
        
        # Extract links and follow them
        links = grab.select('//a[@href]')
        for link in links:
            href = link.attr('href')
            if href and href.startswith('http'):
                logger.info(f'Found link: {href}')
                # Create new task for each link with the "page" handler
                yield Task('page', url=href, depth=task.depth + 1)
    
    def task_page(self, grab: Document, task: Task) -> None:
        """Process secondary pages."""
        logger.info(f'Processing page URL: {task.url} (depth: {task.depth})')
        
        # Extract and log the title
        title = grab.select('//title').text()
        logger.info(f'Page title: {title}')
        
        # Extract meta description if available
        meta_desc = grab.select('//meta[@name="description"]')
        if meta_desc:
            content = meta_desc.attr('content')
            if content:
                logger.info(f'Meta description: {content}')
        
        # We don't follow links from secondary pages in this example


class QuotesSpider(Spider):
    """A spider to extract quotes from quotes.toscrape.com."""
    
    # Initial URL to start crawling from
    initial_urls = ['http://quotes.toscrape.com']
    
    def prepare(self) -> None:
        """Called before the crawler starts."""
        # Create storage for quotes
        self.collected_quotes = []
    
    def task_initial(self, grab: Document, task: Task) -> Generator[Task, None, None]:
        """Process the main page and extract quotes."""
        # Extract quotes from current page
        self._extract_quotes(grab)
        
        # Find pagination links and follow them
        next_page = grab.select('//li[@class="next"]/a/@href').text()
        if next_page:
            next_url = f'http://quotes.toscrape.com{next_page}'
            logger.info(f'Following pagination: {next_url}')
            yield Task('page', url=next_url)
    
    def task_page(self, grab: Document, task: Task) -> Generator[Task, None, None]:
        """Process pagination pages."""
        # Extract quotes from current page
        self._extract_quotes(grab)
        
        # Find pagination links and follow them
        next_page = grab.select('//li[@class="next"]/a/@href').text()
        if next_page:
            next_url = f'http://quotes.toscrape.com{next_page}'
            logger.info(f'Following pagination: {next_url}')
            yield Task('page', url=next_url)
    
    def _extract_quotes(self, grab: Document) -> None:
        """Helper method to extract quotes from a page."""
        quotes = grab.select('//div[@class="quote"]')
        for quote in quotes:
            text = quote.select('./span[@class="text"]').text()
            author = quote.select('./span/small[@class="author"]').text()
            
            quote_data = {
                'text': text,
                'author': author
            }
            
            self.collected_quotes.append(quote_data)
            logger.info(f'Extracted quote: {text[:50]}... by {author}')
    
    def shutdown(self) -> None:
        """Called after the crawler finishes."""
        logger.info(f'Total quotes collected: {len(self.collected_quotes)}')
        # In a real application, you might save these to a database or file


def run_simple_spider():
    """Run the simple spider example."""
    logger.info('Starting Simple Spider...')
    try:
        spider = SimpleSpider(thread_number=2)
        spider.run()
        logger.info('Simple Spider completed.')
    except SpiderError as e:
        logger.error(f'Spider error: {e}')


def run_quotes_spider():
    """Run the quotes spider example."""
    logger.info('Starting Quotes Spider...')
    try:
        spider = QuotesSpider(thread_number=2)
        spider.run()
        logger.info('Quotes Spider completed.')
    except SpiderError as e:
        logger.error(f'Spider error: {e}')


def main():
    """Run all spider examples."""
    logger.info('Starting Grab Spider examples...')
    
    # Uncomment one at a time to test each spider
    # run_simple_spider()
    run_quotes_spider()
    
    logger.info('All spider examples completed.')


if __name__ == '__main__':
    main() 
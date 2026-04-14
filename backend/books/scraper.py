import requests
from bs4 import BeautifulSoup
import time
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://books.toscrape.com/"
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

def scrape_books(max_pages=2):
    """Scrape books from books.toscrape.com"""
    books = []
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; BookScraper/1.0)'}
    
    for page in range(1, max_pages + 1):
        try:
            url = f"{BASE_URL}catalogue/page-{page}.html"
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            articles = soup.select('article.product_pod')
            logger.info(f"Page {page}: found {len(articles)} books")
            
            for article in articles:
                try:
                    book_data = parse_book_listing(article)
                    if book_data:
                        # fetch detail page
                        detail_url = BASE_URL + "catalogue/" + article.select_one('h3 a')['href'].replace('../', '')
                        book_data['book_url'] = detail_url
                        detail = scrape_book_detail(detail_url, headers)
                        book_data.update(detail)
                        books.append(book_data)
                        time.sleep(0.3)
                except Exception as e:
                    logger.error(f"Error parsing book: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error scraping page {page}: {e}")
            break
    
    return books


def parse_book_listing(article):
    """Parse a book from the listing page"""
    try:
        title_tag = article.select_one('h3 a')
        title = title_tag['title'] if title_tag else 'Unknown'
        
        rating_tag = article.select_one('p.star-rating')
        rating_class = rating_tag['class'][1] if rating_tag else 'One'
        rating = RATING_MAP.get(rating_class, 1)
        
        price_tag = article.select_one('p.price_color')
        price_str = price_tag.text.strip() if price_tag else '0'
        price = float(price_str.replace('£', '').replace('Â', '').strip())
        
        img_tag = article.select_one('img.thumbnail')
        img_src = img_tag['src'] if img_tag else ''
        cover_url = BASE_URL + img_src.replace('../', '').replace('../../', '')
        
        return {
            'title': title,
            'rating': rating,
            'price': price,
            'cover_image_url': cover_url,
        }
    except Exception as e:
        logger.error(f"Error in parse_book_listing: {e}")
        return None


def scrape_book_detail(detail_url, headers=None):
    """Scrape individual book detail page"""
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0'}
    
    result = {
        'description': '',
        'genre': '',
        'author': '',
        'num_reviews': 0,
    }
    
    try:
        response = requests.get(detail_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Description
        desc_tag = soup.select_one('#product_description ~ p')
        if desc_tag:
            result['description'] = desc_tag.text.strip()
        
        # Genre from breadcrumb
        breadcrumbs = soup.select('ul.breadcrumb li')
        if len(breadcrumbs) >= 3:
            result['genre'] = breadcrumbs[-2].text.strip()
        
        # Product table info
        table = soup.select('table.table tr')
        for row in table:
            th = row.select_one('th')
            td = row.select_one('td')
            if th and td:
                if 'UPC' in th.text:
                    pass
                elif 'Number of reviews' in th.text:
                    try:
                        result['num_reviews'] = int(td.text.strip())
                    except Exception:
                        pass
    except Exception as e:
        logger.error(f"Error scraping detail {detail_url}: {e}")
    
    return result

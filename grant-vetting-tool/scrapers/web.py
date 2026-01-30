"""
Web/Blog scraper for the Grant Applicant Vetting Tool.

This scraper handles general websites and blogs. It can:
- Scrape article content from blog posts
- Extract author information
- Find linked social media profiles
- Archive page content
"""

import re
from datetime import datetime
from typing import Optional, List
from urllib.parse import urljoin, urlparse
import logging

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None

try:
    import tldextract
except ImportError:
    tldextract = None

from .base import BaseScraper, ScraperResult

logger = logging.getLogger(__name__)


class WebScraper(BaseScraper):
    """Scraper for blogs and general web content."""

    PLATFORM_NAME = "web"

    # Common blog platforms and their article selectors
    PLATFORM_SELECTORS = {
        'medium.com': {
            'article': 'article',
            'title': 'h1',
            'content': 'article section',
            'author': 'a[data-testid="authorName"]',
            'date': 'span[data-testid="storyPublishDate"]'
        },
        'substack.com': {
            'article': 'article',
            'title': 'h1.post-title',
            'content': 'div.body',
            'author': 'a.frontend-pencraft-Text-module__decoration-hover-underline',
            'date': 'time'
        },
        'wordpress': {
            'article': 'article, .post, .entry',
            'title': 'h1.entry-title, h1.post-title, h1',
            'content': '.entry-content, .post-content, article',
            'author': '.author-name, .entry-author, .post-author',
            'date': 'time, .entry-date, .post-date'
        },
        'ghost': {
            'article': 'article',
            'title': 'h1.article-title',
            'content': 'section.article-content',
            'author': '.author-name',
            'date': 'time'
        },
        'default': {
            'article': 'article, main, .post, .content, #content',
            'title': 'h1',
            'content': 'article, .post-content, .entry-content, .content, main',
            'author': '.author, .byline, [rel="author"]',
            'date': 'time, .date, .published'
        }
    }

    # User agent for requests
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.timeout = self.config.get('timeout', 30)
        self.session = None
        if requests:
            self.session = requests.Session()
            self.session.headers.update({'User-Agent': self.USER_AGENT})

    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a page and parse it with BeautifulSoup."""
        if not self.session or not BeautifulSoup:
            self.logger.error("requests or beautifulsoup4 not installed")
            return None

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'lxml')
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def _detect_platform(self, url: str) -> str:
        """Detect which blog platform a URL belongs to."""
        if not tldextract:
            return 'default'

        extracted = tldextract.extract(url)
        domain = f"{extracted.domain}.{extracted.suffix}"

        if 'medium.com' in domain or extracted.suffix == 'medium.com':
            return 'medium.com'
        if 'substack.com' in domain or extracted.suffix == 'substack.com':
            return 'substack.com'

        # Try to detect by content
        return 'default'

    def _get_selectors(self, url: str, soup: BeautifulSoup) -> dict:
        """Get the appropriate selectors for a given URL/page."""
        platform = self._detect_platform(url)

        # Check for WordPress
        if soup.find('meta', {'name': 'generator', 'content': re.compile(r'WordPress', re.I)}):
            platform = 'wordpress'

        # Check for Ghost
        if soup.find('meta', {'name': 'generator', 'content': re.compile(r'Ghost', re.I)}):
            platform = 'ghost'

        return self.PLATFORM_SELECTORS.get(platform, self.PLATFORM_SELECTORS['default'])

    def _extract_text(self, soup: BeautifulSoup, selector: str) -> Optional[str]:
        """Extract text from the first matching element."""
        element = soup.select_one(selector)
        if element:
            return element.get_text(strip=True)
        return None

    def _extract_date(self, soup: BeautifulSoup, selectors: dict) -> Optional[datetime]:
        """Extract and parse publication date."""
        date_element = soup.select_one(selectors['date'])
        if not date_element:
            return None

        # Try datetime attribute first
        dt = date_element.get('datetime')
        if dt:
            try:
                return datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except ValueError:
                pass

        # Try parsing text content
        date_text = date_element.get_text(strip=True)
        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y',
            '%m/%d/%Y',
            '%d/%m/%Y',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue

        return None

    def _find_social_links(self, soup: BeautifulSoup, base_url: str) -> List[dict]:
        """Find social media links on the page."""
        social_patterns = {
            'twitter': r'(?:twitter\.com|x\.com)/([^/?#]+)',
            'instagram': r'instagram\.com/([^/?#]+)',
            'linkedin': r'linkedin\.com/in/([^/?#]+)',
            'facebook': r'facebook\.com/([^/?#]+)',
            'youtube': r'youtube\.com/(?:@|channel/|user/)([^/?#]+)',
            'github': r'github\.com/([^/?#]+)',
            'nostr': r'(npub1[a-z0-9]+)',
        }

        found_links = []
        seen = set()

        for link in soup.find_all('a', href=True):
            href = link.get('href', '')

            for platform, pattern in social_patterns.items():
                match = re.search(pattern, href, re.I)
                if match:
                    username = match.group(1)
                    key = f"{platform}:{username.lower()}"
                    if key not in seen:
                        seen.add(key)
                        found_links.append({
                            'platform': platform,
                            'username': username,
                            'url': href
                        })
                    break

        return found_links

    def scrape_profile(self, identifier: str) -> ScraperResult:
        """
        Scrape profile/author information from a blog or website.

        For blogs, this attempts to find the author page or about page.
        """
        url = identifier if identifier.startswith('http') else f'https://{identifier}'

        soup = self._get_page(url)
        if not soup:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"Could not fetch page: {url}"
            )

        selectors = self._get_selectors(url, soup)

        # Try to find author info
        author_name = self._extract_text(soup, selectors['author'])

        # Try to find bio/about
        bio = None
        for selector in ['.author-bio', '.about', '.bio', 'meta[name="description"]']:
            element = soup.select_one(selector)
            if element:
                bio = element.get('content') if element.name == 'meta' else element.get_text(strip=True)
                break

        # Find social links
        social_links = self._find_social_links(soup, url)

        # Get page title
        title = soup.title.string if soup.title else None

        profile_data = {
            'url': url,
            'display_name': author_name,
            'title': title,
            'bio': bio,
            'social_links': social_links,
            'domain': urlparse(url).netloc
        }

        return ScraperResult(
            success=True,
            platform=self.PLATFORM_NAME,
            profile_data=profile_data,
            raw_data={'url': url, 'social_links': social_links}
        )

    def scrape_content(
        self,
        identifier: str,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> ScraperResult:
        """
        Scrape article content from a blog URL.

        If the URL is a blog homepage, attempts to find and scrape individual articles.
        If it's an article URL, scrapes that single article.
        """
        url = identifier if identifier.startswith('http') else f'https://{identifier}'
        limit = limit or 20

        soup = self._get_page(url)
        if not soup:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"Could not fetch page: {url}"
            )

        selectors = self._get_selectors(url, soup)
        content_items = []

        # Check if this is a single article or a listing page
        article = soup.select_one(selectors['article'])
        title = self._extract_text(soup, selectors['title'])

        if article and title and len(title) > 10:
            # This looks like a single article page
            item = self._parse_article(soup, selectors, url)
            if item:
                content_items.append(item)
        else:
            # This might be a listing page - find article links
            article_links = self._find_article_links(soup, url)

            for link in article_links[:limit]:
                try:
                    article_soup = self._get_page(link)
                    if article_soup:
                        article_selectors = self._get_selectors(link, article_soup)
                        item = self._parse_article(article_soup, article_selectors, link)
                        if item:
                            # Apply date filters
                            pub_date = item.get('published_at')
                            if pub_date:
                                try:
                                    dt = datetime.fromisoformat(pub_date)
                                    if since and dt < since:
                                        continue
                                    if until and dt > until:
                                        continue
                                except ValueError:
                                    pass
                            content_items.append(item)
                except Exception as e:
                    self.logger.error(f"Error scraping article {link}: {e}")
                    continue

        return ScraperResult(
            success=True,
            platform=self.PLATFORM_NAME,
            content_items=content_items
        )

    def _parse_article(self, soup: BeautifulSoup, selectors: dict, url: str) -> Optional[dict]:
        """Parse an article page into a content item."""
        title = self._extract_text(soup, selectors['title'])
        if not title:
            return None

        # Get content
        content_element = soup.select_one(selectors['content'])
        content = ''
        if content_element:
            # Remove script and style elements
            for tag in content_element.find_all(['script', 'style', 'nav', 'aside']):
                tag.decompose()
            content = content_element.get_text(separator='\n', strip=True)

        # Get author
        author = self._extract_text(soup, selectors['author'])

        # Get date
        pub_date = self._extract_date(soup, selectors)

        # Get images
        media_urls = []
        if content_element:
            for img in content_element.find_all('img', src=True):
                src = img.get('src')
                if src:
                    media_urls.append(urljoin(url, src))

        return {
            'platform': self.PLATFORM_NAME,
            'content_type': 'article',
            'platform_content_id': url,
            'url': url,
            'text_content': f"{title}\n\n{content}",
            'title': title,
            'author': author,
            'published_at': pub_date.isoformat() if pub_date else None,
            'media_urls': media_urls[:10],  # Limit media URLs
            'raw_content': {'title': title, 'url': url}
        }

    def _find_article_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find links to articles on a blog listing page."""
        article_links = []
        seen = set()

        # Look for links within article-like containers
        for container in soup.select('article, .post, .entry, .blog-post, .post-preview'):
            link = container.find('a', href=True)
            if link:
                href = urljoin(base_url, link.get('href'))
                if href not in seen and self._is_article_url(href, base_url):
                    seen.add(href)
                    article_links.append(href)

        # Also look for common article link patterns
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            full_url = urljoin(base_url, href)

            if full_url in seen:
                continue

            # Check if it looks like an article URL
            if self._is_article_url(full_url, base_url):
                # Make sure link text suggests it's an article
                text = link.get_text(strip=True)
                if len(text) > 20:  # Title-like text
                    seen.add(full_url)
                    article_links.append(full_url)

        return article_links

    def _is_article_url(self, url: str, base_url: str) -> bool:
        """Check if a URL looks like it could be an article."""
        parsed = urlparse(url)
        base_parsed = urlparse(base_url)

        # Must be same domain
        if parsed.netloc != base_parsed.netloc:
            return False

        path = parsed.path.lower()

        # Exclude common non-article paths
        excluded = [
            '/tag/', '/tags/', '/category/', '/categories/',
            '/author/', '/about', '/contact', '/search',
            '/page/', '/feed', '/rss', '/sitemap',
            '/login', '/register', '/account', '/admin',
            '/wp-admin', '/wp-content', '/wp-includes'
        ]
        if any(excl in path for excl in excluded):
            return False

        # Should have some path (not just homepage)
        if path in ['', '/', '/blog', '/blog/']:
            return False

        return True

    def scrape_single_article(self, url: str) -> ScraperResult:
        """Scrape a single article URL."""
        soup = self._get_page(url)
        if not soup:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"Could not fetch page: {url}"
            )

        selectors = self._get_selectors(url, soup)
        item = self._parse_article(soup, selectors, url)

        if item:
            return ScraperResult(
                success=True,
                platform=self.PLATFORM_NAME,
                content_items=[item]
            )

        return ScraperResult(
            success=False,
            platform=self.PLATFORM_NAME,
            error_message="Could not parse article content"
        )

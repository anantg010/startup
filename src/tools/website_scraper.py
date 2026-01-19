from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from typing import Dict, Optional, List
import asyncio


class WebsiteScraper:
    """
    Scrape startup websites using Playwright
    Handles dynamic content, JavaScript, and complex websites
    Enhanced with better error handling and fallback mechanisms
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize website scraper
        
        Args:
            timeout: Timeout in seconds for page load
        """
        self.timeout = timeout * 1000  # Convert to milliseconds
        self.max_content_length = 15000  # Increased from 10000
    
    
    async def scrape_website(self, url: str) -> Dict:
        """
        Scrape website content with enhanced error handling and fallbacks
        
        Args:
            url: Website URL (e.g., "https://techcorp.com" or "techcorp.com")
            
        Returns:
            Dict with scraped content and metadata
            
        Example:
            result = await scraper.scrape_website("https://techcorp.ai")
            print(result["main_text"])
        """
        try:
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            # Remove trailing slash for consistency
            url = url.rstrip('/')
            
            print(f"🌐 Scraping website: {url}")
            
            async with async_playwright() as p:
                # Launch browser with additional args for better compatibility
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-web-security',
                        '--ignore-certificate-errors'
                    ]
                )
                
                try:
                    # Create new page with realistic user agent
                    context = await browser.new_context(
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        viewport={'width': 1920, 'height': 1080},
                        ignore_https_errors=True  # Ignore SSL certificate errors
                    )
                    page = await context.new_page()
                    
                    # Try with 'load' first (faster), fallback to 'domcontentloaded' if timeout
                    print(f"  ⏳ Loading page...")
                    
                    try:
                        # Try networkidle first (best for dynamic sites)
                        await page.goto(url, wait_until='networkidle', timeout=self.timeout)
                    except PlaywrightTimeoutError:
                        print(f"  ⚠️ networkidle timeout, trying domcontentloaded...")
                        try:
                            await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                        except PlaywrightTimeoutError:
                            print(f"  ⚠️ domcontentloaded timeout, trying load...")
                            await page.goto(url, wait_until='load', timeout=self.timeout)
                    
                    # Small wait for any remaining JS to execute
                    await asyncio.sleep(1)
                    
                    # Get page title
                    title = await page.title()
                    
                    # Get full HTML content
                    content = await page.content()
                    
                    # Get main text content - enhanced extraction
                    main_text = await page.evaluate("""
                        () => {
                            // Remove script and style elements
                            const scripts = document.querySelectorAll('script, style, noscript, iframe');
                            scripts.forEach(el => el.remove());
                            
                            // Get text from body
                            let text = document.body.innerText || document.body.textContent || '';
                            
                            // Clean up whitespace
                            text = text.replace(/\\s+/g, ' ').trim();
                            
                            return text;
                        }
                    """)
                    
                    # Get meta description - with proper error handling
                    meta_description = ""
                    try:
                        meta_el = page.locator('meta[name="description"]')
                        if await meta_el.count() > 0:
                            meta_description = await meta_el.first.get_attribute('content') or ""
                    except Exception:
                        pass
                    
                    # Try og:description as fallback
                    if not meta_description:
                        try:
                            og_el = page.locator('meta[property="og:description"]')
                            if await og_el.count() > 0:
                                meta_description = await og_el.first.get_attribute('content') or ""
                        except Exception:
                            pass
                    
                    # Get meta keywords - with proper error handling
                    meta_keywords = ""
                    try:
                        keywords_el = page.locator('meta[name="keywords"]')
                        if await keywords_el.count() > 0:
                            meta_keywords = await keywords_el.first.get_attribute('content') or ""
                    except Exception:
                        pass
                    
                    # Extract headings for better context
                    headings = await page.evaluate("""
                        () => {
                            const result = [];
                            document.querySelectorAll('h1, h2, h3').forEach(h => {
                                const text = h.innerText.trim();
                                if (text && text.length > 0) {
                                    result.push({
                                        tag: h.tagName.toLowerCase(),
                                        text: text
                                    });
                                }
                            });
                            return result.slice(0, 20);
                        }
                    """)
                    
                    # Extract links
                    links = await page.evaluate("""
                        () => {
                            return Array.from(document.querySelectorAll('a'))
                                .map(a => ({
                                    text: a.textContent.trim(),
                                    href: a.href
                                }))
                                .filter(l => l.text.length > 0 && l.href.startsWith('http'))
                                .slice(0, 30);
                        }
                    """)
                    
                    # Extract important paragraphs
                    paragraphs = await page.evaluate("""
                        () => {
                            return Array.from(document.querySelectorAll('p'))
                                .map(p => p.innerText.trim())
                                .filter(t => t.length > 50)
                                .slice(0, 10);
                        }
                    """)
                    
                    # Extract company/about info if available
                    about_text = await page.evaluate("""
                        () => {
                            // Look for about sections
                            const aboutSelectors = [
                                '[id*="about"]', '[class*="about"]',
                                '[id*="company"]', '[class*="company"]',
                                '[id*="mission"]', '[class*="mission"]',
                                'section[id*="about"]', 'div[id*="about"]'
                            ];
                            
                            for (const selector of aboutSelectors) {
                                const el = document.querySelector(selector);
                                if (el) {
                                    const text = el.innerText.trim();
                                    if (text.length > 100) {
                                        return text.substring(0, 2000);
                                    }
                                }
                            }
                            return '';
                        }
                    """)
                    
                    # Extract products/services if available
                    products_text = await page.evaluate("""
                        () => {
                            const productSelectors = [
                                '[id*="product"]', '[class*="product"]',
                                '[id*="service"]', '[class*="service"]',
                                '[id*="solution"]', '[class*="solution"]'
                            ];
                            
                            for (const selector of productSelectors) {
                                const el = document.querySelector(selector);
                                if (el) {
                                    const text = el.innerText.trim();
                                    if (text.length > 100) {
                                        return text.substring(0, 2000);
                                    }
                                }
                            }
                            return '';
                        }
                    """)
                    
                    # Limit text content
                    if len(main_text) > self.max_content_length:
                        main_text = main_text[:self.max_content_length]
                    
                    print(f"  ✓ Page loaded successfully")
                    print(f"    - Title: {title[:50]}..." if len(title) > 50 else f"    - Title: {title}")
                    print(f"    - Text: {len(main_text)} characters")
                    print(f"    - Headings: {len(headings)}")
                    print(f"    - Links: {len(links)}")
                    
                    return {
                        "success": True,
                        "url": url,
                        "title": title,
                        "description": meta_description,
                        "keywords": meta_keywords,
                        "main_text": main_text,
                        "headings": headings,
                        "paragraphs": paragraphs,
                        "about_text": about_text,
                        "products_text": products_text,
                        "html_content": content[:8000],  # First 8000 chars of HTML
                        "links": links
                    }
                
                finally:
                    await browser.close()
        
        except PlaywrightTimeoutError:
            error_msg = f"Page load timeout after {self.timeout // 1000} seconds"
            print(f"  ❌ {error_msg}")
            return {
                "success": False,
                "url": url,
                "error": error_msg,
                "main_text": "",
                "title": ""
            }
        
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ Error: {error_msg}")
            
            # If Playwright fails, try a simpler HTTP request as fallback
            print("  🔄 Attempting fallback with HTTP request...")
            fallback_result = await self._fallback_scrape(url)
            if fallback_result["success"]:
                return fallback_result
            
            return {
                "success": False,
                "url": url,
                "error": error_msg,
                "main_text": "",
                "title": ""
            }
    
    
    async def _fallback_scrape(self, url: str) -> Dict:
        """
        Fallback scraping using httpx when Playwright fails
        Lightweight but doesn't handle JavaScript
        """
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                verify=False  # Ignore SSL errors
            ) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for element in soup(['script', 'style', 'noscript', 'iframe']):
                    element.decompose()
                
                # Get title
                title = soup.title.string if soup.title else ""
                
                # Get meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                description = meta_desc['content'] if meta_desc and meta_desc.get('content') else ""
                
                # Get text
                main_text = soup.get_text(separator=' ', strip=True)
                if len(main_text) > self.max_content_length:
                    main_text = main_text[:self.max_content_length]
                
                # Get headings
                headings = []
                for tag in ['h1', 'h2', 'h3']:
                    for h in soup.find_all(tag):
                        text = h.get_text(strip=True)
                        if text:
                            headings.append({'tag': tag, 'text': text})
                
                print(f"  ✓ Fallback scrape successful")
                print(f"    - Title: {title[:50]}..." if len(title) > 50 else f"    - Title: {title}")
                print(f"    - Text: {len(main_text)} characters")
                
                return {
                    "success": True,
                    "url": url,
                    "title": title,
                    "description": description,
                    "keywords": "",
                    "main_text": main_text,
                    "headings": headings[:20],
                    "paragraphs": [],
                    "about_text": "",
                    "products_text": "",
                    "html_content": response.text[:8000],
                    "links": [],
                    "fallback_used": True
                }
        
        except ImportError:
            return {"success": False, "error": "httpx or beautifulsoup4 not installed for fallback"}
        except Exception as e:
            return {"success": False, "error": f"Fallback also failed: {str(e)}"}
    
    
    async def get_page_title(self, url: str) -> Dict:
        """
        Get only the page title
        Faster than full scrape
        
        Args:
            url: Website URL
            
        Returns:
            Dict with title
            
        Example:
            result = await scraper.get_page_title("techcorp.ai")
            print(result["title"])
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--ignore-certificate-errors']
                )
                
                try:
                    context = await browser.new_context(
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        ignore_https_errors=True
                    )
                    page = await context.new_page()
                    await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                    
                    title = await page.title()
                    
                    return {
                        "success": True,
                        "url": url,
                        "title": title
                    }
                
                finally:
                    await browser.close()
        
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "title": ""
            }
    
    
    async def extract_text_only(self, url: str) -> Dict:
        """
        Extract only the text content (faster, lighter)
        
        Args:
            url: Website URL
            
        Returns:
            Dict with text content
            
        Example:
            result = await scraper.extract_text_only("techcorp.ai")
            print(result["text"])
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            print(f"📝 Extracting text from: {url}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--ignore-certificate-errors']
                )
                
                try:
                    context = await browser.new_context(
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        ignore_https_errors=True
                    )
                    page = await context.new_page()
                    
                    try:
                        await page.goto(url, wait_until='networkidle', timeout=self.timeout)
                    except PlaywrightTimeoutError:
                        await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                    
                    # Get text
                    text = await page.evaluate("""
                        () => {
                            // Remove script and style
                            const scripts = document.querySelectorAll('script, style, noscript');
                            scripts.forEach(el => el.remove());
                            return document.body.innerText || '';
                        }
                    """)
                    
                    # Limit length
                    if len(text) > self.max_content_length:
                        text = text[:self.max_content_length]
                    
                    print(f"  ✓ Text extracted ({len(text)} characters)")
                    
                    return {
                        "success": True,
                        "url": url,
                        "text": text
                    }
                
                finally:
                    await browser.close()
        
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "text": ""
            }
    
    
    async def check_website_exists(self, url: str) -> Dict:
        """
        Quick check if website is accessible
        
        Args:
            url: Website URL
            
        Returns:
            Dict with accessibility status
            
        Example:
            result = await scraper.check_website_exists("techcorp.ai")
            if result["accessible"]:
                print("Website is up and running")
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--ignore-certificate-errors']
                )
                
                try:
                    context = await browser.new_context(
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        ignore_https_errors=True
                    )
                    page = await context.new_page()
                    response = await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                    
                    status_code = response.status if response else None
                    
                    return {
                        "success": True,
                        "url": url,
                        "accessible": status_code in [200, 301, 302],
                        "status_code": status_code
                    }
                
                finally:
                    await browser.close()
        
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "accessible": False,
                "error": str(e)
            }
    
    
    async def extract_headings(self, url: str) -> Dict:
        """
        Extract all headings (H1, H2, H3, etc.)
        
        Args:
            url: Website URL
            
        Returns:
            Dict with headings structure
            
        Example:
            result = await scraper.extract_headings("techcorp.ai")
            print(result["headings"]["h1"])
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            print(f"📋 Extracting headings from: {url}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--ignore-certificate-errors']
                )
                
                try:
                    context = await browser.new_context(
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        ignore_https_errors=True
                    )
                    page = await context.new_page()
                    
                    try:
                        await page.goto(url, wait_until='networkidle', timeout=self.timeout)
                    except PlaywrightTimeoutError:
                        await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                    
                    # Extract headings
                    headings = await page.evaluate("""
                        () => {
                            const result = {
                                h1: [],
                                h2: [],
                                h3: [],
                                h4: []
                            };
                            
                            document.querySelectorAll('h1').forEach(h => {
                                const text = h.innerText.trim();
                                if (text) result.h1.push(text);
                            });
                            
                            document.querySelectorAll('h2').forEach(h => {
                                const text = h.innerText.trim();
                                if (text) result.h2.push(text);
                            });
                            
                            document.querySelectorAll('h3').forEach(h => {
                                const text = h.innerText.trim();
                                if (text) result.h3.push(text);
                            });
                            
                            document.querySelectorAll('h4').forEach(h => {
                                const text = h.innerText.trim();
                                if (text) result.h4.push(text);
                            });
                            
                            return result;
                        }
                    """)
                    
                    print(f"  ✓ Extracted headings")
                    
                    return {
                        "success": True,
                        "url": url,
                        "headings": headings
                    }
                
                finally:
                    await browser.close()
        
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "headings": {}
            }
    
    
    async def extract_all_text_by_sections(self, url: str) -> Dict:
        """
        Extract text organized by sections/headings
        
        Args:
            url: Website URL
            
        Returns:
            Dict with sections and their text
            
        Example:
            result = await scraper.extract_all_text_by_sections("techcorp.ai")
            for section in result["sections"]:
                print(section["heading"], "->", section["text"][:100])
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            print(f"📑 Extracting sections from: {url}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--ignore-certificate-errors']
                )
                
                try:
                    context = await browser.new_context(
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        ignore_https_errors=True
                    )
                    page = await context.new_page()
                    
                    try:
                        await page.goto(url, wait_until='networkidle', timeout=self.timeout)
                    except PlaywrightTimeoutError:
                        await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
                    
                    # Extract sections
                    sections = await page.evaluate("""
                        () => {
                            const sections = [];
                            
                            // Get main content container
                            const contentArea = document.querySelector('main, [role="main"], article, body');
                            
                            let currentHeading = "Introduction";
                            let currentText = "";
                            
                            const processNode = (node) => {
                                if (node.tagName?.match(/^H[1-4]$/)) {
                                    if (currentText.trim()) {
                                        sections.push({
                                            heading: currentHeading,
                                            text: currentText.trim().substring(0, 1000)
                                        });
                                    }
                                    currentHeading = node.innerText.trim();
                                    currentText = "";
                                } else if (node.tagName === 'P' || node.tagName === 'DIV' || node.tagName === 'SPAN') {
                                    const text = node.innerText?.trim();
                                    if (text && text.length > 10) {
                                        currentText += text + " ";
                                    }
                                }
                            };
                            
                            // Walk through all elements
                            const walker = document.createTreeWalker(
                                contentArea,
                                NodeFilter.SHOW_ELEMENT,
                                null,
                                false
                            );
                            
                            let node;
                            while (node = walker.nextNode()) {
                                processNode(node);
                            }
                            
                            if (currentText.trim()) {
                                sections.push({
                                    heading: currentHeading,
                                    text: currentText.trim().substring(0, 1000)
                                });
                            }
                            
                            return sections.slice(0, 20);
                        }
                    """)
                    
                    print(f"  ✓ Extracted {len(sections)} sections")
                    
                    return {
                        "success": True,
                        "url": url,
                        "sections": sections
                    }
                
                finally:
                    await browser.close()
        
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "sections": []
            }
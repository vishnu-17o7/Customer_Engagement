import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://github.com/prof18/RSS-Parser",
        )
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
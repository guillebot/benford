"""Polite HTTP fetching with robots.txt checks."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "BenfordLawEducationalBot/1.0 (+https://en.wikipedia.org/wiki/Benford%27s_law; "
    "research/education; respects robots.txt)"
)

DEFAULT_TIMEOUT = 25.0
MAX_CONCURRENCY = 5


@dataclass
class FetchResult:
    url: str
    name: str
    ok: bool
    status: str
    http_status: int | None = None
    text: str = ""
    error: str = ""
    blocked_by_robots: bool = False


@dataclass
class RobotCache:
    parsers: dict[str, RobotFileParser] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def allowed(self, client: httpx.AsyncClient, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        async with self.lock:
            if origin not in self.parsers:
                rp = RobotFileParser()
                robots_url = f"{origin}/robots.txt"
                self.parsers[origin] = rp
                try:
                    resp = await client.get(robots_url, timeout=10.0)
                    if resp.status_code == 200:
                        rp.parse(resp.text.splitlines())
                    else:
                        rp.parse([])
                except Exception:
                    rp.parse([])
        return self.parsers[origin].can_fetch(USER_AGENT, url)


def html_to_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


async def fetch_one(
    client: httpx.AsyncClient,
    robots: RobotCache,
    name: str,
    url: str,
) -> FetchResult:
    try:
        if not await robots.allowed(client, url):
            return FetchResult(
                url=url,
                name=name,
                ok=False,
                status="blocked",
                blocked_by_robots=True,
                error="Disallowed by robots.txt for this user-agent",
            )
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code >= 400:
            return FetchResult(
                url=url,
                name=name,
                ok=False,
                status="failed",
                http_status=resp.status_code,
                error=f"HTTP {resp.status_code}",
            )
        text = html_to_visible_text(resp.text)
        return FetchResult(
            url=url,
            name=name,
            ok=True,
            status="ok",
            http_status=resp.status_code,
            text=text,
        )
    except httpx.TimeoutException:
        return FetchResult(url=url, name=name, ok=False, status="failed", error="timeout")
    except Exception as e:
        return FetchResult(url=url, name=name, ok=False, status="failed", error=str(e))


async def fetch_all_sites(
    sites: list[dict],
    *,
    max_concurrency: int = MAX_CONCURRENCY,
    timeout: float = DEFAULT_TIMEOUT,
) -> list[FetchResult]:
    robots = RobotCache()
    sem = asyncio.Semaphore(max_concurrency)
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}

    async with httpx.AsyncClient(
        headers=headers,
        timeout=timeout,
        limits=httpx.Limits(max_connections=max_concurrency + 2),
    ) as client:

        async def run(site: dict) -> FetchResult:
            async with sem:
                await asyncio.sleep(0.15)
                return await fetch_one(client, robots, site.get("name", site["url"]), site["url"])

        return await asyncio.gather(*[run(s) for s in sites])
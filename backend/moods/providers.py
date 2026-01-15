from __future__ import annotations

import dataclasses
import html
import logging
import random
import re
from typing import Protocol

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class TrendTopic:
    topic: str
    weight: float


class TrendProvider(Protocol):
    def get_trends(self, country: str) -> list[TrendTopic]:
        raise NotImplementedError

    def sample_posts(self, country: str, topic: str, limit: int) -> list[str]:
        raise NotImplementedError


class XProvider:
    BASE_URL = "https://api.x.com/2"

    def __init__(self, bearer_token: str) -> None:
        self.bearer_token = bearer_token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.bearer_token}"}

    def get_trends(self, country: str) -> list[TrendTopic]:
        if not self.bearer_token:
            return []
        woeid = None
        try:
            from moods.models import Country

            woeid = Country.objects.filter(code=country.upper()).values_list("woeid", flat=True).first()
        except Exception:
            woeid = None
        try:
            if woeid:
                response = requests.get(
                    f"{self.BASE_URL}/trends/by/woeid/{woeid}",
                    headers=self._headers(),
                    timeout=10,
                )
            else:
                response = requests.get(
                    f"{self.BASE_URL}/tweets/search/recent",
                    headers=self._headers(),
                    params={"query": country, "max_results": 10},
                    timeout=10,
                )
            if response.status_code == 429:
                logger.warning("X rate limit hit for trends")
                return []
            if response.status_code >= 400:
                logger.warning("X trends error: %s", response.text)
                return []
            data = response.json()
            if woeid:
                topics = data.get("data", [])
                return [TrendTopic(topic=item.get("name", ""), weight=1.0) for item in topics if item.get("name")]
            return [TrendTopic(topic=item.get("text", ""), weight=1.0) for item in data.get("data", []) if item.get("text")]
        except requests.RequestException as exc:
            logger.exception("X trends request failed: %s", exc)
            return []

    def sample_posts(self, country: str, topic: str, limit: int) -> list[str]:
        if not self.bearer_token:
            return []
        params = {
            "query": f"{topic} lang:en -is:retweet",
            "max_results": min(limit, 100),
        }
        try:
            response = requests.get(
                f"{self.BASE_URL}/tweets/search/recent",
                headers=self._headers(),
                params=params,
                timeout=10,
            )
            if response.status_code == 429:
                logger.warning("X rate limit hit for search")
                return []
            if response.status_code >= 400:
                logger.warning("X search error: %s", response.text)
                return []
            data = response.json()
            items = data.get("data", [])
            return [item.get("text", "").strip() for item in items if item.get("text")]
        except requests.RequestException as exc:
            logger.exception("X search request failed: %s", exc)
            return []


class ScrapeXProvider:
    SEARCH_URLS = (
        "https://r.jina.ai/http://x.com/search?q={query}&f=live",
        "https://r.jina.ai/http://nitter.net/search?f=tweets&q={query}",
    )

    def _fetch_search(self, query: str) -> list[str]:
        for url in self.SEARCH_URLS:
            try:
                response = requests.get(
                    url.format(query=requests.utils.quote(query)),
                    headers={"User-Agent": "global-mood-clock"},
                    timeout=10,
                )
                if response.status_code == 451:
                    logger.warning("X scrape unavailable (451); trying fallback source.")
                    continue
                if response.status_code >= 400:
                    logger.warning("X scrape error: %s", response.status_code)
                    continue
                posts = self._extract_posts(response.text)
                if posts:
                    return posts
            except requests.RequestException as exc:
                logger.exception("X scrape request failed: %s", exc)
        return []

    def _extract_posts(self, payload: str) -> list[str]:
        matches = re.findall(r'data-testid="tweetText".*?</div>', payload, re.DOTALL)
        if not matches:
            matches = re.findall(r'class="tweet-content[^"]*".*?</div>', payload, re.DOTALL)
        texts = []
        for block in matches:
            cleaned = re.sub(r"<[^>]+>", " ", block)
            cleaned = html.unescape(cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            if cleaned:
                texts.append(cleaned)
        return texts

    def get_trends(self, country: str) -> list[TrendTopic]:
        posts = self._fetch_search(country)
        hashtags: list[str] = []
        for post in posts:
            hashtags.extend(re.findall(r"#\\w+", post))
        unique_tags = list(dict.fromkeys(tag.lstrip("#") for tag in hashtags if tag))
        if not unique_tags:
            return [TrendTopic(topic=country, weight=1.0)]
        return [TrendTopic(topic=tag, weight=1.0) for tag in unique_tags[:5]]

    def sample_posts(self, country: str, topic: str, limit: int) -> list[str]:
        posts = self._fetch_search(topic or country)
        return posts[:limit]


class RedditProvider:
    BASE_URL = "https://oauth.reddit.com"
    TOKEN_URL = "https://www.reddit.com/api/v1/access_token"

    def __init__(self, client_id: str, client_secret: str, user_agent: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent

    def _get_token(self) -> str | None:
        if not self.client_id or not self.client_secret:
            return None
        try:
            auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
            data = {"grant_type": "client_credentials"}
            headers = {"User-Agent": self.user_agent}
            response = requests.post(self.TOKEN_URL, auth=auth, data=data, headers=headers, timeout=10)
            if response.status_code >= 400:
                logger.warning("Reddit token error: %s", response.text)
                return None
            return response.json().get("access_token")
        except requests.RequestException as exc:
            logger.exception("Reddit token request failed: %s", exc)
            return None

    def _headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}", "User-Agent": self.user_agent}

    def get_trends(self, country: str) -> list[TrendTopic]:
        token = self._get_token()
        if not token:
            return []
        subreddits = [f"{country.lower()}news", f"{country.lower()}"]
        topics: list[TrendTopic] = []
        for subreddit in subreddits:
            try:
                response = requests.get(
                    f"{self.BASE_URL}/r/{subreddit}/hot",
                    headers=self._headers(token),
                    params={"limit": 5},
                    timeout=10,
                )
                if response.status_code >= 400:
                    continue
                children = response.json().get("data", {}).get("children", [])
                for item in children:
                    title = item.get("data", {}).get("title")
                    if title:
                        topics.append(TrendTopic(topic=title, weight=1.0))
            except requests.RequestException:
                continue
        return topics

    def sample_posts(self, country: str, topic: str, limit: int) -> list[str]:
        token = self._get_token()
        if not token:
            return []
        try:
            response = requests.get(
                f"{self.BASE_URL}/search",
                headers=self._headers(token),
                params={"q": topic, "limit": min(limit, 100), "sort": "hot"},
                timeout=10,
            )
            if response.status_code >= 400:
                return []
            children = response.json().get("data", {}).get("children", [])
            texts = []
            for item in children:
                data = item.get("data", {})
                title = data.get("title") or ""
                selftext = data.get("selftext") or ""
                combined = f"{title} {selftext}".strip()
                if combined:
                    texts.append(combined)
            return texts
        except requests.RequestException:
            return []


class PublicRedditProvider:
    BASE_URL = "https://www.reddit.com"

    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent

    def _headers(self) -> dict[str, str]:
        return {"User-Agent": self.user_agent}

    def get_trends(self, country: str) -> list[TrendTopic]:
        subreddits = [f"{country.lower()}news", f"{country.lower()}"]
        topics: list[TrendTopic] = []
        for subreddit in subreddits:
            try:
                response = requests.get(
                    f"{self.BASE_URL}/r/{subreddit}/hot.json",
                    headers=self._headers(),
                    params={"limit": 5},
                    timeout=10,
                )
                if response.status_code >= 400:
                    continue
                children = response.json().get("data", {}).get("children", [])
                for item in children:
                    title = item.get("data", {}).get("title")
                    if title:
                        topics.append(TrendTopic(topic=title, weight=1.0))
            except requests.RequestException:
                continue
        return topics

    def sample_posts(self, country: str, topic: str, limit: int) -> list[str]:
        try:
            response = requests.get(
                f"{self.BASE_URL}/search.json",
                headers=self._headers(),
                params={"q": topic, "limit": min(limit, 100), "sort": "hot"},
                timeout=10,
            )
            if response.status_code >= 400:
                return []
            children = response.json().get("data", {}).get("children", [])
            texts = []
            for item in children:
                data = item.get("data", {})
                title = data.get("title") or ""
                selftext = data.get("selftext") or ""
                combined = f"{title} {selftext}".strip()
                if combined:
                    texts.append(combined)
            return texts
        except requests.RequestException:
            return []


class CompositeProvider:
    def __init__(self, x_provider: TrendProvider, reddit_provider: TrendProvider) -> None:
        self.x_provider = x_provider
        self.reddit_provider = reddit_provider

    def get_trends(self, country: str) -> list[TrendTopic]:
        x_trends = self.x_provider.get_trends(country)
        reddit_trends = self.reddit_provider.get_trends(country)
        topics = {trend.topic: trend for trend in x_trends + reddit_trends}
        x_topic_set = {trend.topic for trend in x_trends}
        merged: list[TrendTopic] = []
        for topic in topics.values():
            weight = settings.SOURCE_WEIGHT_X if topic.topic in x_topic_set else settings.SOURCE_WEIGHT_REDDIT
            merged.append(TrendTopic(topic=topic.topic, weight=weight))
        return merged

    def sample_posts(self, country: str, topic: str, limit: int) -> list[str]:
        x_limit = int(limit * settings.SOURCE_WEIGHT_X)
        reddit_limit = max(limit - x_limit, 1)
        posts = []
        posts.extend(self.x_provider.sample_posts(country, topic, x_limit))
        posts.extend(self.reddit_provider.sample_posts(country, topic, reddit_limit))
        return posts


class MockProvider:
    def __init__(self) -> None:
        self.seed = 42

    def get_trends(self, country: str) -> list[TrendTopic]:
        random.seed(f"{country}-{self.seed}")
        topics = [
            "economy outlook",
            "local sports",
            "weather alerts",
            "election buzz",
            "tech investments",
            "public health",
        ]
        random.shuffle(topics)
        return [TrendTopic(topic=topic, weight=1.0) for topic in topics[:5]]

    def sample_posts(self, country: str, topic: str, limit: int) -> list[str]:
        random.seed(f"{country}-{topic}-{self.seed}")
        base = [
            f"People are talking about {topic} in {country}.",
            f"Mixed feelings around {topic} right now.",
            f"News cycles keep highlighting {topic}.",
            f"Lots of reactions to {topic} today.",
            f"Community discussions focus on {topic} recently.",
        ]
        random.shuffle(base)
        return base[:limit]


def provider_from_settings() -> TrendProvider:
    provider = settings.PROVIDER
    if provider == "x":
        if not settings.X_BEARER_TOKEN:
            return ScrapeXProvider()
        return XProvider(settings.X_BEARER_TOKEN)
    if provider == "reddit":
        if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
            return PublicRedditProvider(settings.REDDIT_USER_AGENT)
        return RedditProvider(settings.REDDIT_CLIENT_ID, settings.REDDIT_CLIENT_SECRET, settings.REDDIT_USER_AGENT)
    if provider == "composite":
        x_provider: TrendProvider = (
            XProvider(settings.X_BEARER_TOKEN) if settings.X_BEARER_TOKEN else ScrapeXProvider()
        )
        reddit_provider: TrendProvider = (
            RedditProvider(settings.REDDIT_CLIENT_ID, settings.REDDIT_CLIENT_SECRET, settings.REDDIT_USER_AGENT)
            if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET
            else PublicRedditProvider(settings.REDDIT_USER_AGENT)
        )
        return CompositeProvider(x_provider, reddit_provider)
    return MockProvider()

from email.mime import text
import re
import time
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from crawler.text_cleaner import clean_text


class MetacriticCrawler:
    """
    Metacritic 電影評論爬蟲。

    第一版功能：
    1. 接收英文電影名稱
    2. 將電影名稱轉成 Metacritic slug
    3. 進入 /movie/{slug}/user-reviews/
    4. 抓取前 limit 則 user reviews
    5. 回傳專案指定 JSON 格式

    注意：
    這一版不負責 aspect 分類。
    aspect / sentiment / topic classification 應該交給 NLP 模組處理。
    """

    BASE_URL = "https://www.metacritic.com"

    def __init__(self, delay_seconds: float = 1.0):
        self.delay_seconds = delay_seconds

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def fetch_movie_reviews(self, movie_name: str, limit: int = 60) -> list[dict]:
        """
        對外主要方法。

        輸入：
            movie_name: 英文電影名稱，例如 "Inception"
            limit: 最多抓幾則評論

        輸出：
            [
                {
                    "canonical_title": "Inception",
                    "aliases": [],
                    "reviews": [
                        {
                            "rating": 4.5,
                            "text": "..."
                        }
                    ]
                }
            ]
        """
        movie_name = movie_name.strip()

        if not movie_name:
            raise ValueError("movie_name 不可以是空字串")

        slug = self._movie_name_to_slug(movie_name)
        canonical_title = self._slug_to_title(slug)

        reviews = self._fetch_reviews_by_slug(
            slug=slug,
            limit=limit
        )

        return [
            {
                "canonical_title": canonical_title,
                "aliases": [],
                "reviews": reviews,
            }
        ]

    def _movie_name_to_slug(self, movie_name: str) -> str:
        """
        將英文電影名稱轉成 Metacritic URL slug。

        範例：
            Inception -> inception
            The Dark Knight -> the-dark-knight
            Spider-Man: No Way Home -> spider-man-no-way-home
        """
        slug = movie_name.lower().strip()

        # 將 & 改成 and，例如 "Fast & Furious" -> "fast and furious"
        slug = slug.replace("&", " and ")

        # 移除單引號與雙引號
        slug = slug.replace("'", "").replace('"', "")

        # 非英文字母、數字的字元都轉成 -
        slug = re.sub(r"[^a-z0-9]+", "-", slug)

        # 移除前後多餘 -
        slug = slug.strip("-")

        return slug

    def _slug_to_title(self, slug: str) -> str:
        """
        將 slug 轉回比較好看的標題。

        範例：
            inception -> Inception
            the-dark-knight -> The Dark Knight
        """
        words = slug.split("-")
        return " ".join(word.capitalize() for word in words)

    def _fetch_reviews_by_slug(self, slug: str, limit: int) -> list[dict]:
        """
        根據電影 slug 抓取 user reviews。
        """
        reviews = []
        page = 0

        while len(reviews) < limit:
            #回傳的是html網頁原始碼，裡面包含了所有評論的內容
            html = self._download_review_page(slug=slug, page=page)
            page_reviews = self._parse_reviews_from_html(html)

            if not page_reviews:
                break

            for review in page_reviews:
                reviews.append(review)

                if len(reviews) >= limit:
                    break

            page += 1
            time.sleep(self.delay_seconds)

        return reviews[:limit]

    def _download_review_page(self, slug: str, page: int) -> str:
        """
        下載 Metacritic user reviews 頁面的 HTML。
        """
        url = f"{self.BASE_URL}/movie/{quote(slug)}/user-reviews/"

        params = {}
        if page > 0:
            params["page"] = page

        response = requests.get(
            url,
            headers=self.headers,
            params=params,
            timeout=15
        )

        if response.status_code == 404:
            raise ValueError(f"找不到電影頁面，slug={slug}")

        if response.status_code != 200:
            raise RuntimeError(
                f"下載 Metacritic 頁面失敗：status_code={response.status_code}, url={response.url}"
            )

        return response.text

    def _parse_reviews_from_html(self, html: str) -> list[dict]:
        """
        從 HTML 中解析評論。
        """
        #把 HTML 字串變成可以查找的結構
        soup = BeautifulSoup(html, "lxml")

        # 移除不需要的區塊，避免干擾文字解析
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        #把所有網站內的可見文字抓出來
        text = soup.get_text("\n")
        lines = [clean_text(line) for line in text.split("\n")]
        lines = [line for line in lines if line]

        return self._extract_reviews_from_lines(lines)

    def _extract_reviews_from_lines(self, lines: list[str]) -> list[dict]:
        """
        從文字行中抓出評論。

        目標格式：
            {
                "rating": 4.5,
                "text": "評論文字"
            }
        """
        reviews = []
        i = 0

        while i < len(lines):
            if not self._looks_like_date(lines[i]):
                i += 1
                continue

            rating = None
            review_text_parts = []

            j = i + 1

            # 在日期後面五行尋找 rating
            while j < len(lines) and j < i + 6:
                possible_rating = self._extract_rating_from_line(lines[j])

                if possible_rating is not None:
                    rating = possible_rating
                    j += 1
                    break

                j += 1

            if rating is None:
                i += 1
                continue

            # rating 後面到 report-review Report 或下一個日期之間，視為評論文字
            while j < len(lines):
                current_line = lines[j]

            # 遇到 report_review / report-review / Report，代表這則評論結束
                if self._is_review_end_marker(current_line):
                    break

            # 遇到下一個日期，代表下一則評論開始
                if self._looks_like_date(current_line):
                    break

                if not self._should_ignore_line(current_line):
                    review_text_parts.append(current_line)

                    j += 1

            review_text = clean_text(" ".join(review_text_parts))

            if review_text and self._is_valid_review_text(review_text):
                reviews.append({
                    "rating": self._normalize_rating(rating),
                    "text": review_text,
                })

            i = max(j + 1, i + 1)

        return reviews

    def _looks_like_date(self, line: str) -> bool:
        """
        判斷一行文字是否像日期。

        範例：
            May 28, 2026
            Jan 20, 2026
        """
        return bool(
            re.match(
                r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}$",
                line
            )
        )

    def _extract_rating_from_line(self, line: str) -> int | None:
        """
        從一行文字抓 rating。

        Metacritic 常見文字可能是：
            7 username
            10 username

        這裡抓開頭的 0~10 整數。
        """
        match = re.match(r"^(10|[0-9])\b", line)

        if not match:
            return None

        return int(match.group(1))

    def _normalize_rating(self, rating_10_scale: int) -> float:
        """
        將 Metacritic 0~10 分轉成你們要求的 1.0~5.0。

        範例：
            10 -> 5.0
            8  -> 4.0
            7  -> 3.5
            1  -> 1.0
            0  -> 1.0
        """
        rating = rating_10_scale / 2

        if rating < 1.0:
            rating = 1.0

        if rating > 5.0:
            rating = 5.0

        return round(rating, 1)

    def _should_ignore_line(self, line: str) -> bool:
        """
        過濾掉不是評論內容的雜訊文字。
        """
        ignore_exact = {
            "Add My Review",
            "All Reviews",
            "Positive Reviews",
            "Mixed Reviews",
            "Negative Reviews",
            "Recently Added",
            "Score Recently Added",
            "User Reviews",
            "Critic Reviews",
            "Cast & Crew",
            "Details",
            "Overview",
            "Advertisement",
            "report_review",
            "report-review",
            "report-review Report",
            "Report",
            "[SPOILER ALERT: This review contains spoilers.]",
        }

        if line in ignore_exact:
            return True

        if self._is_review_end_marker(line):
            return True

        return False

    def _is_review_end_marker(self, line: str) -> bool:
        """
        判斷這一行是不是評論結束標記。

        Metacritic 頁面裡常見的檢舉按鈕文字可能長這樣：
        - report_review
        - report-review
        - report-review Report
        - report review
        - Report
        """
        if not line:
            return False

        normalized = clean_text(line).lower()
        normalized = normalized.replace("_", "-")
        normalized = re.sub(r"\s+", " ", normalized).strip()

        end_markers = {
            "report",
            "report-review",
            "report-review report",
            "report review",
            "report review report",
        }

        return normalized in end_markers

    def _is_valid_review_text(self, text: str) -> bool:
        """
        避免把太短或無意義的文字當成評論。
        """
        if len(text) < 10:
            return False

        if text.lower() in {"report", "report_review", "report-review"}:
            return False

        return True
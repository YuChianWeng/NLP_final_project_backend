from crawler.metacritic_crawler import MetacriticCrawler


def get_movie_reviews(movie_name: str, limit: int = 60) -> list[dict]:
    """
    給後端呼叫的主要函式。

    Example:
        result = get_movie_reviews("Inception", limit=60)
    """
    crawler = MetacriticCrawler(delay_seconds=1.0)

    return crawler.fetch_movie_reviews(
        movie_name=movie_name,
        limit=limit
    )
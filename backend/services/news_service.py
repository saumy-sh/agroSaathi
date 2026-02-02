from newsapi import NewsApiClient
from config import AGRI_NEWS_API_KEY

def get_agriculture_news():
    """
    Fetch agriculture news from NewsAPI.org using newsapi-python
    """
    if not AGRI_NEWS_API_KEY:
        return {"error": "Agri News API key not configured"}

    try:
        # Initialize client
        newsapi = NewsApiClient(api_key=AGRI_NEWS_API_KEY)
        
        print("[NEWS] Fetching agriculture news articles from NewsAPI...")
        # Search for agriculture and farming news
        # We use a broad query to get relevant results
        all_articles = newsapi.get_everything(
            q="agricultural schemes",
            language='en',
            sort_by='publishedAt',
            page_size=12
        )
        
        # Debug print the response structure (limited)
        print(f"[NEWS] API Status: {all_articles.get('status')}")
        print(f"[NEWS] Total Results: {all_articles.get('totalResults')}")
        
        return all_articles
        
    except Exception as err:
        print(f"[NEWS] Error during news fetch: {str(err)}")
        return {"error": str(err)}

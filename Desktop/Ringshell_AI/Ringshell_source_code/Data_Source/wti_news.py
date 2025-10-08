import requests
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path to import from DataBase_Connection_Source
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from DataBase_Connection_Source.RedisDatabaseStorage import RedisDatabaseStorage

FMP_API_KEY = '9dfbbfa29d93f4793f246e8fb5ca5e74'

def get_wti_news(days_back: int = 730) -> list:
    """Get WTI news with timestamps from FMP API"""
    
    redis_client = RedisDatabaseStorage()
    new_key = "Crude_Oil:NEWS:WTI:new"
    new_data_check = redis_client.get_json(new_key)
    
    if "error" in new_data_check:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
    else:
        end_date = datetime.now()
        last_update = new_data_check.get("last_update", "")
        
        if last_update:
            last_update_date = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S")
            hours_since_update = (end_date - last_update_date).total_seconds() / 3600
            
            if hours_since_update < 24:
                return new_data_check.get("news", [])
        else:
            hours_since_update = 48
            
        start_date = end_date - timedelta(days=min(7, hours_since_update / 24))
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    wti_news = []  # WTI-specific news
    general_news = []  # General market news
    
    # Fetch WTI-specific stock news
    for page in range(1, 6):
        stock_news_url = "https://financialmodelingprep.com/stable/news/stock"
        stock_params = {
            "symbols": "WTI",
            "from": start_date_str,
            "to": end_date_str,
            "page": page,
            "limit": 100,
            "apikey": FMP_API_KEY,
        }
        
        response = requests.get(stock_news_url, params=stock_params)
        if response.status_code == 200:
            news_data = response.json()
            if not news_data:
                break
            for item in news_data:
                wti_news.append({
                    "ticker": "WTI",
                    "source": "WTI_Stock",
                    "timestamp": item.get("publishedDate", ""),
                    "title": item.get("title", ""),
                    "text": item.get("text", ""),
                    "url": item.get("url", ""),
                    "site": item.get("site", "")
                })
    
    # Fetch General news with BROADER keywords
    # Enhanced keywords: oil + economy + geopolitics + macro + dollar + risk
    oil_keywords = ['oil', 'crude', 'wti', 'brent', 'opec', 'energy', 'petroleum', 'gasoline', 'refinery']
    
    macro_keywords = ['fed', 'inflation', 'economy', 'gdp', 'recession', 'interest rate', 'monetary policy', 
                      'fiscal', 'stimulus', 'bond', 'treasury', 'central bank']
    
    dollar_keywords = ['dollar', 'dxy', 'usd', 'currency', 'exchange rate', 'dollar index', 'forex', 
                       'dollar strength', 'greenback']
    
    geo_keywords = ['russia', 'ukraine', 'middle east', 'iran', 'saudi', 'war', 'sanctions', 'conflict',
                    'geopolitical', 'geopolitics', 'tension', 'crisis', 'israel', 'gaza', 'strait',
                    'venezuela', 'libya', 'iraq', 'syria', 'yemen', 'gulf']
    
    china_keywords = ['china', 'beijing', 'chinese economy', 'xi jinping', 'china demand', 
                      'china stimulus', 'china growth', 'asia']
    
    market_keywords = ['commodities', 'futures', 'trading', 'hedge', 'speculation', 'inventory', 
                       'stockpiles', 'reserves', 'supply', 'demand']
    
    all_keywords = oil_keywords + macro_keywords + dollar_keywords + geo_keywords + china_keywords + market_keywords
    
    for page in range(1, 6):
        general_news_url = "https://financialmodelingprep.com/stable/news/general-latest"
        general_params = {
            "from": start_date_str,
            "to": end_date_str,
            "page": page,
            "limit": 100,
            "apikey": FMP_API_KEY,
        }
        
        response = requests.get(general_news_url, params=general_params)
        if response.status_code == 200:
            news_data = response.json()
            if not news_data:
                break
            for item in news_data:
                title = item.get("title", "").lower()
                text = item.get("text", "").lower()
                
                # Check if any keyword appears in title or text
                if any(keyword in title or keyword in text for keyword in all_keywords):
                    general_news.append({
                        "ticker": "WTI",
                        "source": "General",
                        "timestamp": item.get("publishedDate", ""),
                        "title": item.get("title", ""),
                        "text": item.get("text", ""),
                        "url": item.get("url", ""),
                        "site": item.get("site", "")
                    })
    
    # Combine and deduplicate by URL
    seen_urls = set()
    all_news = []
    
    for article in wti_news + general_news:
        url = article.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            all_news.append(article)
        elif not url:
            all_news.append(article)  # Include if no URL
    
    all_news.sort(key=lambda x: x['timestamp'], reverse=True)
    
    print(f"📊 News fetched:")
    print(f"   WTI-specific: {len(wti_news)}")
    print(f"   General (filtered): {len(general_news)}")
    print(f"   Combined (deduplicated): {len(all_news)}")
    
    if "error" in new_data_check:
        shared_data = {
            "news": all_news,
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_count": len(all_news),
            "wti_count": len(wti_news),
            "general_count": len(general_news),
            "sources": {
                "wti_stock": len(wti_news),
                "general_filtered": len(general_news)
            }
        }
        # Store initial news data (both new and old)
        redis_client.store_json(shared_data, "Crude_Oil:NEWS:WTI:new")
        redis_client.store_json(shared_data, "Crude_Oil:NEWS:WTI:old")
        return all_news
    else:
        old_key = "Crude_Oil:NEWS:WTI:old"
        old_data = redis_client.get_json(old_key)
        old_json = old_data.get("news", [])
        old_timestamps = [article["timestamp"] for article in old_json]
        
        unique_new_news = []
        for article in all_news:
            if article["timestamp"] not in old_timestamps:
                unique_new_news.append(article)
        
        merged_news = unique_new_news + old_json
        
        old_json_data = {
            "news": old_json,
            "last_update": old_data.get("last_update", ""),
            "total_count": len(old_json)
        }
        new_json_data = {
            "news": merged_news,
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_count": len(merged_news),
            "new_articles_added": len(unique_new_news),
            "wti_count": len(wti_news),
            "general_count": len(general_news),
            "sources": {
                "wti_stock": len(wti_news),
                "general_filtered": len(general_news)
            }
        }
        
        # WTI News controls its own two-version stack
        # Move current new to old
        current_new = redis_client.get_json("Crude_Oil:NEWS:WTI:new")
        if "error" not in current_new:
            redis_client.store_json(current_new, "Crude_Oil:NEWS:WTI:old")
            print("📦 WTI News: Moved previous data to old version")
        
        # Store new data as new
        redis_client.store_json(new_json_data, "Crude_Oil:NEWS:WTI:new")
        print("📦 WTI News: Stored new data")
        
        return merged_news
import requests
import toml
import json

def load_config():
    return toml.load("secrets.toml")

def get_ig_data(endpoint, params):
    config = load_config()
    base_url = f"https://graph.facebook.com/{config['API_VERSION']}/"
    params['access_token'] = config['PAGE_ACCESS_TOKEN']
    
    response = requests.get(base_url + endpoint, params=params)
    return response.json()

def fetch_full_report():
    config = load_config()
    ig_id = config['IG_USER_ID']

    # 1. Top-Line: Profil Performance
    print("--- 1. TOP-LINE PROFILE DATA ---")
    profile_fields = "username,name,followers_count,media_count,biography"
    profile_data = get_ig_data(ig_id, {'fields': profile_fields})
    print(json.dumps(profile_data, indent=2))

    # 2. Media-Inventory: Die letzten 10 Beiträge abrufen
    print("\n--- 2. RECENT MEDIA & ENGAGEMENT ---")
    media_params = {
        'fields': 'id,caption,media_type,timestamp,like_count,comments_count,permalink'
    }
    media_list = get_ig_data(f"{ig_id}/media", media_params)

    if 'data' in media_list:
        for item in media_list['data']:
            media_id = item['id']
            print(f"\nBeitrag ID: {media_id}")
            print(f"Caption: {item.get('caption', 'Keine Caption')[:50]}...")
            print(f"Likes: {item.get('like_count')} | Kommentare: {item.get('comments_count')}")
            
            # 3. Deep Dive: Insights pro Beitrag (nur für Posts/Reels)
            # Hinweis: Insights funktionieren nur für Medien, die nach dem Umzug auf Business erstellt wurden
            insight_params = {
                'metric': 'impressions,reach,engagement'
            }
            insights = get_ig_data(f"{media_id}/insights", insight_params)
            
            if 'data' in insights:
                for metric in insights['data']:
                    print(f"  - {metric['name']}: {metric['values'][0]['value']}")
            else:
                print("  - Insights für diesen Beitrag nicht verfügbar (zu alt oder kein Business-Post).")
    else:
        print("Keine Medien gefunden.")

if __name__ == "__main__":
    fetch_full_report()

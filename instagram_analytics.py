import requests
import toml
import pandas as pd
import json

# Konfiguration laden
def load_config():
    return toml.load("secrets.toml")

def get_data(endpoint, params, config):
    base_url = f"https://graph.facebook.com/{config['API_VERSION']}/"
    params['access_token'] = config['PAGE_ACCESS_TOKEN']
    response = requests.get(base_url + endpoint, params=params)
    return response.json()

def main():
    config = load_config()
    ig_id = config['IG_USER_ID']

    print("--- 1. PROFIL-DATEN ABRUFEN ---")
    # Profil-Metriken holen
    profile_params = {'fields': 'username,name,followers_count,media_count'}
    profile_data = get_data(ig_id, profile_params, config)
    
    followers = profile_data.get('followers_count', 1) # Vermeidung Division durch 0
    
    # Profil als DataFrame (Einzeilig)
    df_profile = pd.DataFrame([profile_data])
    print(df_profile[['username', 'followers_count', 'media_count']].to_string(index=False))

    print("\n--- 2. CONTENT-ANALYSE ---")
    # Medien abrufen (Limit 20 für Testzwecke)
    media_params = {
        'fields': 'id,caption,media_type,timestamp,like_count,comments_count,permalink,media_url',
        'limit': 20
    }
    media_json = get_data(f"{ig_id}/media", media_params, config)

    if 'data' in media_json:
        posts = []
        for item in media_json['data']:
            # Basis-Daten
            likes = item.get('like_count', 0)
            comments = item.get('comments_count', 0)
            
            # Berechnung Engagement Rate: (Likes + Comments) / Follower * 100
            engagement_rate = ((likes + comments) / followers) * 100
            
            post_data = {
                'Datum': item['timestamp'][:10],
                'Typ': item['media_type'],
                'Likes': likes,
                'Comments': comments,
                'Engagement Rate (%)': round(engagement_rate, 2),
                'Caption': item.get('caption', '')[:30] + "..." # Gekürzt
            }
            posts.append(post_data)

        # Erstellung des Haupt-DataFrames
        df_posts = pd.DataFrame(posts)
        
        # Sortieren und formatieren
        if not df_posts.empty:
            print(df_posts.to_string(index=False))
            
            # Export Option (auskommentiert)
            # df_posts.to_csv("instagram_data.csv", index=False)
        else:
            print("Keine Beiträge gefunden.")
    else:
        print("API lieferte keine Medien-Daten.")

if __name__ == "__main__":
    main()

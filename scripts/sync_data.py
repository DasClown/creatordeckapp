import os
import requests
from supabase import create_client

# Credentials aus GitHub Secrets (ähnlich wie Streamlit Secrets)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
INSTAGRAM_TOKEN = os.environ.get("INSTAGRAM_TOKEN")
USER_ID = os.environ.get("USER_ID", "default")  # Optional: für Multi-User Support

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def sync_instagram():
    # Beispiel-Abruf (vereinfacht)
    url = f"https://graph.facebook.com/v18.0/me?fields=followers_count&access_token={INSTAGRAM_TOKEN}"
    response = requests.get(url).json()
    
    followers = response.get("followers_count", 0)
    
    # In DB schreiben (Historie für Graphen)
    supabase.table("stats_history").insert({
        "platform": "instagram",
        "metric": "followers",
        "value": followers,
        "user_id": USER_ID  # Dynamische User-ID für Multi-User Support
    }).execute()
    print(f"Synced {followers} followers for user {USER_ID}.")

if __name__ == "__main__":
    sync_instagram()

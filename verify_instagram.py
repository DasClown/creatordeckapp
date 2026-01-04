import requests
import toml
import json

def load_config():
    """Lädt die Konfiguration aus der secrets.toml."""
    return toml.load("secrets.toml")

def get_instagram_profile_info(config):
    """Ruft die verifizierten Profil-Daten ab."""
    url = f"https://graph.facebook.com/{config['API_VERSION']}/{config['IG_USER_ID']}"
    params = {
        'fields': 'username,name,biography,followers_count,media_count',
        'access_token': config['PAGE_ACCESS_TOKEN']
    }
    
    response = requests.get(url, params=params)
    return response.json()

def main():
    # 1. Konfiguration laden
    try:
        config = load_config()
    except FileNotFoundError:
        print("Fehler: secrets.toml nicht gefunden.")
        return

    # 2. Daten abrufen
    profile = get_instagram_profile_info(config)

    # 3. Ergebnis ausgeben
    if "error" not in profile:
        print(f"Erfolgreich verbunden mit: @{profile['username']}")
        print(json.dumps(profile, indent=4))
    else:
        print("Fehler bei der Abfrage:")
        print(json.dumps(profile, indent=4))

if __name__ == "__main__":
    main()

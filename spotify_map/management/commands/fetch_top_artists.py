from django.core.management.base import BaseCommand
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import httpx
import time
from datetime import datetime

from spotify_map.models import Artists
from spotify_map.coordinates import get_coords
from django.conf import settings

SPOTIFY_ARTIST_URL = "https://api.spotify.com/v1/artists/"
MUSICBRAINZ_URL = "https://musicbrainz.org/ws/2/artist/?query=artist:"


class Command(BaseCommand):
    help = "Imports new artists from a CSV using Spotify ID, enriches with MusicBrainz, and stores them in the database."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to the CSV file")

    def handle(self, *args, **options):
        csv_path = options["csv_path"]

        client_id = settings.SPOTIPY_CLIENT_ID
        client_secret = settings.SPOTIPY_CLIENT_SECRET

        if not client_id or not client_secret:
            self.stderr.write(self.style.ERROR("❌ Spotify credentials missing."))
            return

        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        ))

        df = pd.read_csv(csv_path)
        df = df[df["followers"] > 1]
        df = df.sort_values(by="popularity", ascending=False)

        existing_ids = set(Artists.objects.values_list("spotify_id", flat=True))
        new_count = 0
        skipped_count = 0

        for _, row in df.iterrows():
            spotify_id = str(row["id"])
            if spotify_id in existing_ids:
                name = row.get("name", "[Unknown Name]")
                print(self.style.WARNING(f"⏭️ Skipping {name} (already in database)"))
                skipped_count += 1
                continue

            artist_data = self.fetch_data(spotify_id, sp)
            if artist_data:
                print(self.style.SUCCESS(f"✅ Fetched from Spotify: {artist_data['name']}"))
                self.store_artist(artist_data)
                new_count += 1

        self.stdout.write(self.style.SUCCESS(f"🎉 Done! {new_count} new artists added. {skipped_count} were already in the database."))

    def fetch_data(self, spotify_id, sp):
        try:
            spotify_info = sp.artist(spotify_id)
        except Exception as e:
            print(self.style.ERROR(f"❌ Spotify fetch failed for {spotify_id}: {e}"))
            return None

        name = spotify_info["name"]
        artist_data = {
            "spotify_id": spotify_id,
            "name": name,
            "spotify_info": spotify_info,
        }

        # MusicBrainz search
        time.sleep(1.5)
        url = MUSICBRAINZ_URL + f"{name}&fmt=json"
        with httpx.Client() as client:
            r2 = client.get(url)
        if r2.status_code != 200:
            print(self.style.ERROR(f"❌ MusicBrainz fetch failed for {name}"))
            return artist_data

        data = r2.json()
        found_mb_data = []

        for mb_artist in data.get("artists", []):
            if name.lower() == mb_artist["name"].lower():
                birth_date = mb_artist.get("life-span", {}).get("begin")
                if birth_date and self.is_valid_date(birth_date):
                    artist_data["birth_date"] = birth_date
                    found_mb_data.append(f"🎂 Birthday: {birth_date}")

                birth_city = mb_artist.get("begin-area", {}).get("name", "")
                birth_country = mb_artist.get("area", {}).get("name", "")
                if birth_city or birth_country:
                    location = ", ".join(filter(None, [birth_city, birth_country]))
                    artist_data["birth_location"] = location
                    coords = get_coords(location)
                    if coords:
                        artist_data["birth_latitude"] = coords[0]
                        artist_data["birth_longitude"] = coords[1]
                        found_mb_data.append(f"📍 Location: {location} (coords: {coords})")
                    else:
                        found_mb_data.append(f"📍 Location: {location} (coords not found)")
                break

        if found_mb_data:
            print(self.style.SUCCESS(f"🔎 MusicBrainz for {name}: {' | '.join(found_mb_data)}"))
        else:
            print(self.style.WARNING(f"🔎 MusicBrainz for {name}: No additional data found."))

        return artist_data

    def store_artist(self, artist_data):
        Artists.objects.update_or_create(
            spotify_id=artist_data["spotify_id"],
            defaults={
                "name": artist_data["name"],
                "birth_latitude": artist_data.get("birth_latitude"),
                "birth_longitude": artist_data.get("birth_longitude"),
                "birth_date": artist_data.get("birth_date"),
                "birth_location": artist_data.get("birth_location"),
                "complete_artist_json": artist_data.get("spotify_info"),
            },
        )

    def is_valid_date(self, date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

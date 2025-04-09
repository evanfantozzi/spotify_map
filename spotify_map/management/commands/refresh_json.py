from django.core.management.base import BaseCommand
from django.conf import settings
from spotify_map.models import Artists
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time


class Command(BaseCommand):
    help = "Refresh Spotify raw JSON for all artists in the database."

    def handle(self, *args, **kwargs):
        client_id = settings.SPOTIPY_CLIENT_ID
        client_secret = settings.SPOTIPY_CLIENT_SECRET

        if not client_id or not client_secret:
            self.stderr.write(self.style.ERROR("❌ Spotify credentials not found in environment variables."))
            return

        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        ))

        updated = 0
        for artist in Artists.objects.all()[1:]:
            time.sleep(.5)
            if not artist.spotify_id:
                self.stdout.write(self.style.WARNING(f"⚠ No Spotify ID for {artist.name}, skipping."))
                continue

            try:
                data = sp.artist(artist.spotify_id)
                artist.complete_artist_json = data
                artist.save(update_fields=['complete_artist_json'])
                self.stdout.write(self.style.SUCCESS(f"✔ Updated: {artist.name}"))
                updated += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error for {artist.name}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"🎉 Done! {updated} artists updated."))

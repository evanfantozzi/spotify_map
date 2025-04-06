import csv
import json
from django.core.management.base import BaseCommand
from spotify_map.models import Artists  # Adjust if needed
from spotify_map.coordinates import get_coords


class Command(BaseCommand):
    help = 'Import artist data from CSV to the database'

    def handle(self, *args, **kwargs):
        csv_file_path = '/home/evanfantozzi/spotify_map/spotify_map/spotify_map_artists_updater.csv'

        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:

                # Get birth coordinates if available
                birth_location = row.get('birth_location', '')
                if birth_location:
                    coords = get_coords(birth_location)
                    birth_latitude, birth_longitude = (
                        float(coords[0]), float(coords[1])
                    ) if coords else (None, None)
                else:
                    birth_latitude, birth_longitude = None, None

                try:
                    # Use complete JSON only if it exists
                    complete_json_raw = row.get('complete_artist_json')
                    complete_artist_json = json.loads(complete_json_raw) if complete_json_raw else None

                    # Build update fields
                    defaults = {
                        'name': row['name'],
                        'birth_latitude': birth_latitude,
                        'birth_longitude': birth_longitude,
                        'birth_date': row['birth_date'] if row['birth_date'] else None,
                        'birth_location': birth_location,
                    }

                    if complete_artist_json:
                        defaults['complete_artist_json'] = complete_artist_json

                    artist, created = Artists.objects.update_or_create(
                        spotify_id=row['spotify_id'],
                        defaults=defaults
                    )

                    action = "Created" if created else "Updated"
                    self.stdout.write(self.style.SUCCESS(f"{action} artist: {row['name']}"))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"Error processing artist {row.get('name', 'UNKNOWN')}: {str(e)}"
                    ))

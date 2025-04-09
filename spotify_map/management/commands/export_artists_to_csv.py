import csv
from django.core.management.base import BaseCommand
from spotify_map.models import Artists


class Command(BaseCommand):
    help = 'Export artist info to CSV file. Optionally filter by artist name.'

    def add_arguments(self, parser):
        parser.add_argument(
            'artist_name',
            nargs='?',
            type=str,
            default=None,
            help='Optional: The name of the artist to export'
        )

    def handle(self, *args, **options):
        artist_name = options['artist_name']
        output_file_path = '/home/evanfantozzi/spotify_map/spotify_map/spotify_map_artists_updater.csv'

        if artist_name:
            artists = Artists.objects.filter(name__icontains=artist_name)
        else:
            artists = Artists.objects.all()

        if not artists.exists():
            message = f"No artists found matching '{artist_name}'" if artist_name else "No artists found in database"
            self.stdout.write(self.style.ERROR(message))
            return

        # Sort by birth_location (empty locations will appear first)
        artists = artists.order_by('birth_location')

        with open(output_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['spotify_id', 'name', 'birth_date', 'birth_location'])

            for artist in artists:
                writer.writerow([
                    artist.spotify_id,
                    artist.name,
                    artist.birth_date or '',
                    artist.birth_location or ''
                ])

        self.stdout.write(self.style.SUCCESS(f"Exported {artists.count()} artist(s) to {output_file_path}, sorted by birth_location"))

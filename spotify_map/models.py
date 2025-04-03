from django.db import models
class Artists(models.Model):
    spotify_id = models.CharField(max_length=255, primary_key=True)  # Set spotify_id as the primary key
    name = models.CharField(max_length=255)  
    birth_latitude = models.FloatField(null=True, blank=True) 
    birth_longitude = models.FloatField(null=True, blank=True)  
    birth_date = models.DateField(null=True, blank=True) 
    birth_location = models.CharField(max_length=255, null=True, blank=True)  
    complete_artist_json = models.JSONField(null=True, blank=True)  

    def __str__(self):
        return self.name

class Coordinates(models.Model):
    location = models.CharField(max_length=255, unique=True)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
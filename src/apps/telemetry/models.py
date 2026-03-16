from django.db import models

class Zone(models.Model):

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "zones"

    def __str__(self):
        return self.name

class Device(models.Model):

    DEVICE_TYPES = [
        ("track_sensor", "Track Sensor"),
        ("locomotive", "Locomotive"),
        ("crossing", "Level Crossing"),
    ]

    device_id = models.CharField(max_length=100, unique=True)
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT, db_column="zone_id")
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPES)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "devices"

    def __str__(self):
        return self.device_id

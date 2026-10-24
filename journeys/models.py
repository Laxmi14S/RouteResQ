from django.db import models


class Route(models.Model):
    TRANSPORT_CHOICES = [
        ("Bus", "Bus"),
        ("Train", "Train"),
        ("Train + Bus", "Train + Bus"),
    ]

    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    transport = models.CharField(
        max_length=20,
        choices=TRANSPORT_CHOICES
    )
    duration_minutes = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    transfers = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return (
            f"{self.source} to {self.destination} - "
            f"{self.transport}"
        )
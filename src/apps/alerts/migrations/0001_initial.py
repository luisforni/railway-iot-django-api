from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Alert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("device_id", models.CharField(db_index=True, max_length=100)),
                ("zone", models.CharField(db_index=True, max_length=100)),
                ("metric", models.CharField(max_length=50)),
                ("value", models.FloatField()),
                ("threshold", models.FloatField()),
                ("severity", models.CharField(
                    choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
                    db_index=True,
                    max_length=20,
                )),
                ("message", models.TextField()),
                ("acknowledged", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]

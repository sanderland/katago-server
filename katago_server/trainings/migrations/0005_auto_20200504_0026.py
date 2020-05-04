# Generated by Django 3.0.5 on 2020-05-04 00:26

import django.core.files.storage
from django.db import migrations, models
import katago_server.contrib.validators
import katago_server.trainings.models.network


class Migration(migrations.Migration):

    dependencies = [
        ('trainings', '0004_auto_20200428_0416'),
    ]

    operations = [
        migrations.AlterField(
            model_name='network',
            name='model_file',
            field=models.FileField(max_length=200, storage=django.core.files.storage.FileSystemStorage(location='/data/network'), upload_to=katago_server.trainings.models.network.upload_network_to, validators=[katago_server.contrib.validators.FileValidator(content_types=('application/zip',), max_size=314572800)], verbose_name='network Archive url'),
        ),
    ]

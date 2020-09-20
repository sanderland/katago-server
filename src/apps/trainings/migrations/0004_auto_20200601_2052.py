# Generated by Django 3.0.6 on 2020-06-01 20:52

import django.core.files.storage
from django.db import migrations, models
import src.contrib.validators
import src.apps.trainings.models.network


class Migration(migrations.Migration):

    dependencies = [
        ('trainings', '0003_auto_20200511_0248'),
    ]

    operations = [
        migrations.AlterField(
            model_name='network',
            name='model_file',
            field=models.FileField(blank=True, help_text='Url to download network model file.', max_length=200, storage=django.core.files.storage.FileSystemStorage(base_url='/media/networks/', location='/data/networks'), upload_to=src.apps.trainings.models.network.upload_network_to, validators=[
                src.contrib.validators.FileValidator(content_types=('application/gzip',), max_size=1073741824)], verbose_name='model file url'),
        ),
    ]
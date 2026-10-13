from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Galpon_Proyecto', '0003_venta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='venta',
            name='cantidad_huevos',
            field=models.PositiveIntegerField(default=0, help_text='Se calcula automáticamente: cubetas × 30'),
        ),
    ]
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Galpon_Proyecto', '0017_merge_20261117_0930'),
    ]

    operations = [
        migrations.RenameField(
            model_name='venta',
            old_name='cliente',
            new_name='cliente_texto',
        ),
        migrations.AddField(
            model_name='venta',
            name='cliente',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='ventas',
                to='Galpon_Proyecto.cliente',
            ),
        ),
    ]
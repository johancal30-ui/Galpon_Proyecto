from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Galpon_Proyecto', '0019_venta_cliente_datos'),
    ]

    operations = [
        migrations.AlterField(
            model_name='venta',
            name='cliente',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='ventas',
                to='Galpon_Proyecto.cliente',
            ),
        ),
        migrations.RemoveField(
            model_name='venta',
            name='cliente_texto',
        ),
    ]
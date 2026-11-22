from django.db import migrations


def ventas_a_clientes(apps, schema_editor):
    Venta = apps.get_model('Galpon_Proyecto', 'Venta')
    Cliente = apps.get_model('Galpon_Proyecto', 'Cliente')

    for venta in Venta.objects.all():
        nombre = (venta.cliente_texto or '').strip()[:100] or 'SIN NOMBRE'
        cliente = Cliente.objects.filter(nombre__iexact=nombre).first()
        if cliente is None:
            cliente = Cliente.objects.create(nombre=nombre)
        venta.cliente = cliente
        venta.save(update_fields=['cliente'])


class Migration(migrations.Migration):

    dependencies = [
        ('Galpon_Proyecto', '0018_venta_cliente_paso1'),
    ]

    operations = [
        migrations.RunPython(ventas_a_clientes, migrations.RunPython.noop),
    ]
from django.db import migrations
from django.utils import timezone


def crear_lote_principal(apps, schema_editor):
    lote = apps.get_model('Galpon_Proyecto', 'Lote')
    lotes = lote.objects.using(schema_editor.connection.alias)
    existentes = list(lotes.values('pk', 'nombre')[:2])
    if not existentes:
        lotes.create(
            nombre='Lote principal',
            fecha_ingreso=timezone.localdate(),
            cantidad_inicial=1100,
        )
    elif len(existentes) == 1 and existentes[0]['nombre'].strip().casefold() == 'lote principal':
        lotes.filter(pk=existentes[0]['pk'], cantidad_inicial=1000).update(cantidad_inicial=1100)


class Migration(migrations.Migration):
    dependencies = [
        ('Galpon_Proyecto', '0014_merge_20261027_0616'),
        ('Galpon_Proyecto', '0014_merge_20261027_0624'),
    ]

    operations = [
        migrations.RunPython(crear_lote_principal, migrations.RunPython.noop),
    ]

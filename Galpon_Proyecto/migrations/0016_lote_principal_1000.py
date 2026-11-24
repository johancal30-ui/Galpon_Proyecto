from django.db import migrations
from django.utils import timezone


def ajustar_lote_principal(apps, schema_editor):
    lote = apps.get_model('Galpon_Proyecto', 'Lote')
    lotes = lote.objects.using(schema_editor.connection.alias)
    if not lotes.exists():
        lotes.create(
            nombre='LOTE PRINCIPAL',
            fecha_ingreso=timezone.localdate(),
            cantidad_inicial=1000,
        )
    else:
        lotes.filter(nombre__iexact='Lote principal').update(
            nombre='LOTE PRINCIPAL',
            cantidad_inicial=1000,
        )


class Migration(migrations.Migration):
    dependencies = [
        ('Galpon_Proyecto', '0015_lote_principal'),
    ]

    operations = [
        migrations.RunPython(ajustar_lote_principal, migrations.RunPython.noop),
    ]

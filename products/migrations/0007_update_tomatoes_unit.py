from django.db import migrations


def set_tomatoes_to_kg(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    qs = Product.objects.filter(name__icontains='tomato')
    qs.update(unit='kg')


def revert_tomatoes_to_pcs(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    qs = Product.objects.filter(name__icontains='tomato')
    qs.update(unit='pcs')


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_update_units_to_kg'),
    ]

    operations = [
        migrations.RunPython(set_tomatoes_to_kg, revert_tomatoes_to_pcs),
    ]

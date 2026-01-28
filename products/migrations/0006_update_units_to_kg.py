from django.db import migrations


def set_units_to_kg(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    targets = ['irish potatoes', 'green peas', 'rice carotes']
    for t in targets:
        # use case-insensitive contains to catch minor variations
        qs = Product.objects.filter(name__icontains=t)
        qs.update(unit='kg')


def revert_units_to_pcs(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    targets = ['irish potatoes', 'green peas', 'rice carotes']
    for t in targets:
        qs = Product.objects.filter(name__icontains=t)
        qs.update(unit='pcs')


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_product_unit'),
    ]

    operations = [
        migrations.RunPython(set_units_to_kg, revert_units_to_pcs),
    ]

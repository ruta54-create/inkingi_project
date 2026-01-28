from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'List unit values for specific product names (for verification)'

    def handle(self, *args, **options):
        from products.models import Product
        targets = ['irish potatoes', 'green peas', 'rice carotes', 'tomato']
        for t in targets:
            qs = Product.objects.filter(name__icontains=t)
            if not qs.exists():
                self.stdout.write(self.style.WARNING(f'No products found matching "{t}"'))
                continue
            for p in qs:
                self.stdout.write(f'[{p.id}] {p.name} -> unit="{p.unit}"')

from django.db import migrations, models
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    Product = apps.get_model('web', 'Product')
    seen = set()
    for p in Product.objects.all().order_by('pk'):
        base = slugify(p.name) or f'product-{p.pk}'
        slug = base
        n = 1
        while slug in seen:
            slug = f'{base}-{n}'
            n += 1
        seen.add(slug)
        p.slug = slug
        p.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0006_quoterequest_linked_customer'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='slug',
            field=models.SlugField(max_length=350, null=True, blank=True, unique=False),
        ),
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='product',
            name='slug',
            field=models.SlugField(max_length=350, unique=True),
        ),
    ]

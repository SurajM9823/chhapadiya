from django.core.management.base import BaseCommand
from web.models import Role, Permission


class Command(BaseCommand):
    help = 'Initialize predefined roles with permissions'

    def handle(self, *args, **options):
        roles_config = {
            'superuser': {
                'description': 'Full system access',
                'permissions': [
                    ('products', 'view'), ('products', 'create'), ('products', 'edit'), ('products', 'delete'),
                    ('orders', 'view'), ('orders', 'create'), ('orders', 'edit'), ('orders', 'delete'),
                    ('customers', 'view'), ('customers', 'create'), ('customers', 'edit'), ('customers', 'delete'),
                    ('quotations', 'view'), ('quotations', 'create'), ('quotations', 'edit'), ('quotations', 'delete'),
                    ('stock', 'view'), ('stock', 'create'), ('stock', 'edit'), ('stock', 'delete'),
                    ('reports', 'view'), ('reports', 'create'), ('reports', 'edit'), ('reports', 'delete'),
                    ('settings', 'view'), ('settings', 'create'), ('settings', 'edit'), ('settings', 'delete'),
                ]
            },
            'admin_purchase': {
                'description': 'Purchase department admin',
                'permissions': [
                    ('products', 'view'), ('products', 'create'), ('products', 'edit'),
                    ('stock', 'view'), ('stock', 'create'), ('stock', 'edit'),
                    ('quotations', 'view'), ('quotations', 'create'), ('quotations', 'edit'),
                    ('reports', 'view'),
                ]
            },
            'admin_sales': {
                'description': 'Sales department admin',
                'permissions': [
                    ('products', 'view'),
                    ('orders', 'view'), ('orders', 'create'), ('orders', 'edit'),
                    ('customers', 'view'), ('customers', 'create'), ('customers', 'edit'),
                    ('quotations', 'view'), ('quotations', 'create'), ('quotations', 'edit'),
                    ('reports', 'view'),
                ]
            },
            'admin_logistics': {
                'description': 'Logistics department admin',
                'permissions': [
                    ('orders', 'view'), ('orders', 'edit'),
                    ('stock', 'view'), ('stock', 'edit'),
                    ('reports', 'view'),
                ]
            },
            'admin_finance': {
                'description': 'Finance department admin',
                'permissions': [
                    ('orders', 'view'),
                    ('customers', 'view'),
                    ('reports', 'view'), ('reports', 'create'), ('reports', 'edit'),
                ]
            },
        }

        for role_name, config in roles_config.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={'description': config['description']}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created role: {role.get_name_display()}'))
            else:
                self.stdout.write(f'• Role already exists: {role.get_name_display()}')
            
            # Add permissions
            for module, action in config['permissions']:
                perm, perm_created = Permission.objects.get_or_create(
                    role=role,
                    module=module,
                    action=action
                )
                if perm_created:
                    self.stdout.write(f'  ✓ Added permission: {module} - {action}')

        self.stdout.write(self.style.SUCCESS('\n✓ Role initialization complete!'))

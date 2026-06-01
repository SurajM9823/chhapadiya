from django.core.management.base import BaseCommand
from web.models import Role, Permission


class Command(BaseCommand):
    help = 'Create default roles with permissions'

    def handle(self, *args, **kwargs):
        roles_data = [
            ('superuser', 'Superuser (Admin)', 'Full system access'),
            ('admin_purchase', 'Admin - Purchase', 'Manage purchases and suppliers'),
            ('admin_sales', 'Admin - Sales', 'Manage sales and orders'),
            ('admin_logistics', 'Admin - Logistics', 'Manage inventory and delivery'),
            ('admin_finance', 'Admin - Finance', 'Manage billing and payments'),
            ('customer', 'Customer', 'Customer access'),
            ('staff', 'Staff', 'General staff access'),
        ]

        created_count = 0
        for role_name, display_name, description in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={'description': description}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created role: {display_name}'))
            else:
                self.stdout.write(f'Role already exists: {display_name}')

        superuser_role = Role.objects.filter(name='superuser').first()
        if superuser_role:
            modules = ['products', 'orders', 'customers', 'content', 'settings', 'users', 'quotations', 'packages', 'stock']
            actions = ['view', 'create', 'edit', 'delete']
            
            for module in modules:
                for action in actions:
                    Permission.objects.get_or_create(
                        role=superuser_role,
                        module=module,
                        action=action
                    )
            self.stdout.write(self.style.SUCCESS('Created permissions for Superuser'))

        customer_role = Role.objects.filter(name='customer').first()
        if customer_role:
            Permission.objects.get_or_create(
                role=customer_role,
                module='orders',
                action='view'
            )
            self.stdout.write(self.style.SUCCESS('Created permissions for Customer'))

        staff_role = Role.objects.filter(name='staff').first()
        if staff_role:
            for module in ['products', 'orders', 'customers']:
                for action in ['view', 'create']:
                    Permission.objects.get_or_create(
                        role=staff_role,
                        module=module,
                        action=action
                    )
            self.stdout.write(self.style.SUCCESS('Created permissions for Staff'))

        self.stdout.write(self.style.SUCCESS(f'Done! Created {created_count} new roles.'))

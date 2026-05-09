import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    help = 'Setup Google OAuth credentials from environment variables'

    def handle(self, *args, **options):
        site_domain = os.getenv('SITE_DOMAIN', 'localhost:8000')
        site_name = os.getenv('SITE_NAME', 'Local Development')
        google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        google_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if not google_client_id or not google_secret:
            self.stdout.write(self.style.ERROR('✗ Error: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables are required'))
            return
        
        site, created = Site.objects.get_or_create(
            id=1,
            defaults={
                'domain': site_domain,
                'name': site_name
            }
        )
        
        if not created:
            site.domain = site_domain
            site.name = site_name
            site.save()
        
        self.stdout.write(f'Site: {site.domain} ({site.name})')
        
        google_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': google_client_id,
                'secret': google_secret,
            }
        )
        
        if not created:
            google_app.client_id = google_client_id
            google_app.secret = google_secret
            google_app.save()
        
        google_app.sites.add(site)
        
        self.stdout.write(self.style.SUCCESS('✓ Google OAuth setup complete!'))
        self.stdout.write(f'Provider: {google_app.provider}')
        self.stdout.write(f'Name: {google_app.name}')
        self.stdout.write(f'Site: {site.domain}')
        self.stdout.write(f'Client ID: {google_app.client_id[:20]}...')

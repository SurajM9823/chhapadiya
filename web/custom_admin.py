from django.contrib import admin
from django.utils.html import format_html


class CustomAdminSite(admin.AdminSite):
    site_header = "Chhapadiya Admin"
    site_title = "Admin Portal"
    index_title = "Dashboard"
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['user_management_url'] = '/admin/web/customeruser/'
        return super().index(request, extra_context)


custom_admin_site = CustomAdminSite(name='custom_admin')

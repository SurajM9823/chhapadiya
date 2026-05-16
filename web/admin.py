from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (SiteSettings, CarouselSlide, Reel, Category, SubCategory,
    Country, CustomerTier, Customer, Product, ProductImage, ProductTierPrice,
    Stat, TrustedClient, Testimonial, TeamMember, Service, WhyChooseUs, StockEntry,
    CustomerUser, Role, Permission, Package, PackageItem)


# ── Customize Admin Site ──────────────────────────────────────────────────────

class ChhapadiyaAdminSite(admin.AdminSite):
    site_header = "Chhapadiya Admin"
    site_title = "Admin Portal"
    index_title = "Dashboard"
    
    def get_app_list(self, request):
        """Reorganize sidebar to show User Management first"""
        app_list = super().get_app_list(request)
        
        # Separate user management models from web app
        user_mgmt_models = []
        web_models = []
        
        for app in app_list:
            if app['app_label'] == 'web':
                for model in app['models']:
                    if model['object_name'] in ['CustomerUser', 'Role', 'Permission']:
                        user_mgmt_models.append(model)
                    else:
                        web_models.append(model)
                
                # Update web app with remaining models
                app['models'] = web_models
        
        # Create User Management section
        if user_mgmt_models:
            user_mgmt_app = {
                'name': 'User Management',
                'app_label': 'user_management',
                'app_url': '/admin/web/',
                'has_module_perms': True,
                'models': user_mgmt_models
            }
            # Insert User Management at the beginning
            app_list.insert(0, user_mgmt_app)
        
        return app_list


# Replace default admin site
admin.site.__class__ = ChhapadiyaAdminSite
admin.site.site_header = "Chhapadiya Admin"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Dashboard"


# ── User Management ────────────────────────────────────────────────────────────

class PermissionInline(admin.TabularInline):
    model = Permission
    extra = 1
    fields = ['module', 'action']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['get_name_display', 'created_at']
    readonly_fields = ['created_at']
    inlines = [PermissionInline]
    fieldsets = (
        ('Role Information', {
            'fields': ('name', 'description', 'created_at')
        }),
    )

    def get_name_display(self, obj):
        return obj.get_name_display()
    get_name_display.short_description = 'Role'


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'module', 'action']
    list_filter = ['role', 'module', 'action']
    search_fields = ['role__name']
    fieldsets = (
        ('Permission Details', {
            'fields': ('role', 'module', 'action')
        }),
    )


@admin.register(CustomerUser)
class CustomerUserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'get_role', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'phone']
    readonly_fields = ['date_joined', 'last_login']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'phone', 'avatar')
        }),
        ('Role & Permissions', {
            'fields': ('role',),
            'description': 'Assign a role to control user permissions across modules'
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('Authentication', {
            'fields': ('password', 'google_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role')
        }),
    )

    def get_role(self, obj):
        return obj.role.get_name_display() if obj.role else '—'
    get_role.short_description = 'Role'


# ── Site Settings ─────────────────────────────────────────────────────────────

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'email', 'phone']


# ── Products ──────────────────────────────────────────────────────────────────

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductTierPriceInline(admin.TabularInline):
    model = ProductTierPrice
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'mrp', 'stock_quantity', 'is_active', 'is_featured']
    list_filter = ['category', 'is_active', 'is_featured']
    search_fields = ['name', 'sku']
    inlines = [ProductImageInline, ProductTierPriceInline]
    autocomplete_fields = ['category', 'sub_category', 'origin']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['name']


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'order', 'is_active']
    list_filter = ['category']
    list_editable = ['order', 'is_active']
    search_fields = ['name', 'category__name']


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name']


@admin.register(CustomerTier)
class CustomerTierAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    list_editable = ['order', 'is_active']


# ── Customers & Orders ────────────────────────────────────────────────────────

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'tier', 'is_active']
    list_filter = ['tier', 'is_active']
    search_fields = ['name', 'email']


@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):
    list_display = ['product', 'entry_type', 'quantity_change', 'created_at']
    list_filter = ['entry_type']


# ── Website Content ───────────────────────────────────────────────────────────

@admin.register(CarouselSlide)
class CarouselSlideAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(Reel)
class ReelAdmin(admin.ModelAdmin):
    list_display = ['title', 'video_type', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['video_type', 'is_active']
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'video_type', 'order', 'is_active')
        }),
        ('Video Source', {
            'fields': ('video', 'youtube_url', 'tiktok_url'),
            'description': 'Choose one: Upload a video file, paste a YouTube URL, or paste a TikTok URL'
        }),
        ('Thumbnail', {
            'fields': ('thumbnail',),
            'description': 'Optional: Upload a custom thumbnail image'
        }),
    )


@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = ['value', 'label', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(TrustedClient)
class TrustedClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'author_role', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(WhyChooseUs)
class WhyChooseUsAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active']
    list_editable = ['order', 'is_active']


# ── Package System ────────────────────────────────────────────────────────────

class PackageItemInline(admin.TabularInline):
    model = PackageItem
    extra = 1
    fields = ['product', 'quantity', 'item_discount', 'get_item_total']
    readonly_fields = ['get_item_total']
    autocomplete_fields = ['product']
    
    def get_item_total(self, obj):
        if obj.pk:
            return f"₹{obj.item_total:.2f}"
        return "—"
    get_item_total.short_description = 'Item Total'


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'get_total_mrp', 'overall_discount', 'selling_price', 'get_savings', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'sku']
    readonly_fields = ['total_mrp', 'created_at', 'updated_at', 'get_final_calculation']
    inlines = [PackageItemInline]
    
    fieldsets = (
        ('Package Information', {
            'fields': ('name', 'sku', 'description', 'is_active')
        }),
        ('Pricing', {
            'fields': ('total_mrp', 'overall_discount', 'selling_price', 'get_final_calculation'),
            'description': 'Total MRP is auto-calculated from items. Apply overall discount and set final selling price.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    class Media:
        css = {'all': ('admin/css/package_admin.css',)}
        js = ('admin/js/package_admin.js',)
    
    def get_total_mrp(self, obj):
        return f"₹{obj.total_mrp:.2f}"
    get_total_mrp.short_description = 'Total MRP'
    
    def get_savings(self, obj):
        savings = obj.total_mrp - obj.selling_price
        if savings > 0:
            percent = (savings / obj.total_mrp * 100) if obj.total_mrp > 0 else 0
            return f"₹{savings:.2f} ({percent:.1f}%)"
        return "—"
    get_savings.short_description = 'Savings'
    
    def get_final_calculation(self, obj):
        if obj.pk:
            html = f"""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px;">
                <table style="width: 100%; max-width: 400px;">
                    <tr>
                        <td><strong>Total MRP (Items):</strong></td>
                        <td style="text-align: right;">₹{obj.total_mrp:.2f}</td>
                    </tr>
                    <tr>
                        <td><strong>Overall Discount:</strong></td>
                        <td style="text-align: right; color: #dc3545;">- ₹{obj.overall_discount:.2f}</td>
                    </tr>
                    <tr style="border-top: 2px solid #dee2e6;">
                        <td><strong>Selling Price:</strong></td>
                        <td style="text-align: right; font-size: 18px; color: #28a745;"><strong>₹{obj.selling_price:.2f}</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Total Savings:</strong></td>
                        <td style="text-align: right; color: #007bff;">₹{obj.total_mrp - obj.selling_price:.2f} ({((obj.total_mrp - obj.selling_price) / obj.total_mrp * 100) if obj.total_mrp > 0 else 0:.1f}%)</td>
                    </tr>
                </table>
            </div>
            """
            return html
        return "Save package to see calculation"
    get_final_calculation.short_description = 'Price Breakdown'

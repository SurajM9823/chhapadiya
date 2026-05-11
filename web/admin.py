from django.contrib import admin
from .models import (SiteSettings, CarouselSlide, Reel, Category, SubCategory,
    Country, CustomerTier, Customer, Product, ProductImage, ProductTierPrice,
    Stat, TrustedClient, Testimonial, TeamMember, Service, WhyChooseUs, StockEntry)

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'email', 'phone']

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'order', 'is_active']
    list_filter = ['category']
    list_editable = ['order', 'is_active']

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name']

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

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    list_editable = ['order', 'is_active']

@admin.register(CustomerTier)
class CustomerTierAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    list_editable = ['order', 'is_active']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'tier', 'is_active']
    list_filter = ['tier', 'is_active']
    search_fields = ['name', 'email']

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

@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):
    list_display = ['product', 'entry_type', 'quantity_change', 'created_at']
    list_filter = ['entry_type']

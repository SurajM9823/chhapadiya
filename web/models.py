from django.db import models
from django.contrib.auth.models import AbstractUser


# ── Roles & Permissions ────────────────────────────────────────────────────────

class Role(models.Model):
    ROLE_CHOICES = [
        ('superuser', 'Superuser (Admin)'),
        ('admin_purchase', 'Admin - Purchase'),
        ('admin_sales', 'Admin - Sales'),
        ('admin_logistics', 'Admin - Logistics'),
        ('admin_finance', 'Admin - Finance'),
    ]
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.get_name_display()


class Permission(models.Model):
    ACTION_CHOICES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
    ]
    MODULE_CHOICES = [
        ('products', 'Products'),
        ('packages', 'Packages'),
        ('orders', 'Orders'),
        ('customers', 'Customers'),
        ('quotations', 'Quotations'),
        ('stock', 'Stock'),
        ('reports', 'Reports'),
        ('settings', 'Settings'),
        ('content', 'Content Management'),
        ('users', 'User Management'),
    ]
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    module = models.CharField(max_length=50, choices=MODULE_CHOICES)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    class Meta:
        unique_together = ('role', 'module', 'action')
        ordering = ['module', 'action']
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'

    def __str__(self):
        return f"{self.role.get_name_display()} - {self.get_module_display()} ({self.get_action_display()})"


# ── Customer User ─────────────────────────────────────────────────────────────

class CustomerUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('agent', 'Agent'),
    ]
    
    phone = models.CharField(max_length=20, blank=True)
    google_id = models.CharField(max_length=200, blank=True)
    avatar = models.URLField(blank=True)
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL, related_name='users')
    
    # User type and reference
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='customer')
    reference_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    
    # Company/Organization details
    company_name = models.CharField(max_length=200, blank=True)
    company_address = models.TextField(blank=True)
    company_phone = models.CharField(max_length=20, blank=True)
    company_email = models.EmailField(blank=True)
    company_website = models.URLField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True, verbose_name='Tax ID/VAT Number')
    
    # Agent specific
    referral_code = models.CharField(max_length=9, unique=True, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Generate reference number if not exists
        if not self.reference_number:
            import random
            self.reference_number = f'REF{random.randint(100000, 999999)}'
        
        # Generate referral code for agents if not exists
        if self.user_type == 'agent' and not self.referral_code:
            import random
            self.referral_code = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email or self.username

    def has_permission(self, module, action):
        """Check if user has permission for a module action."""
        if self.is_superuser:
            return True
        if not self.role:
            return False
        return self.role.permissions.filter(module=module, action=action).exists()


# ── Cart ──────────────────────────────────────────────────────────────────────

class Cart(models.Model):
    user = models.OneToOneField(CustomerUser, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user}"

    @property
    def total_items(self):
        return sum(i.quantity for i in self.items.all())

    @property
    def total_price(self):
        return sum(i.subtotal for i in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def subtotal(self):
        return self.product.mrp * self.quantity


# ── Favourites ────────────────────────────────────────────────────────────────

class Favourite(models.Model):
    user = models.ForeignKey(CustomerUser, on_delete=models.CASCADE, related_name='favourites')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='favourited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user} ♥ {self.product.name}"


# ── Orders ─────────────────────────────────────────────────────────────

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('confirmed',  'Confirmed'),
        ('processing', 'Processing'),
        ('shipped',    'Shipped'),
        ('delivered',  'Delivered'),
        ('cancelled',  'Cancelled'),
    ]
    DELIVERY_CHOICES = [
        ('delivery', 'Home Delivery'),
        ('pickup',   'Store Pickup'),
    ]
    PAYMENT_CHOICES = [
        ('cod',    'Cash on Delivery'),
        ('online', 'Online Payment'),
        ('pickup', 'Pay at Store'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('unpaid',  'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid',    'Paid'),
    ]
    user            = models.ForeignKey(CustomerUser, on_delete=models.SET_NULL, null=True, related_name='orders')
    order_number    = models.CharField(max_length=20, unique=True)
    is_package_order = models.BooleanField(default=False, help_text='Is this a package order?')
    package_name    = models.CharField(max_length=300, blank=True, help_text='Package name if package order')
    agent_referral_code = models.CharField(max_length=9, blank=True, help_text='Agent referral code')
    referred_agent  = models.ForeignKey(CustomerUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_orders', limit_choices_to={'user_type': 'agent'})
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_type   = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='delivery')
    full_name       = models.CharField(max_length=200)
    phone           = models.CharField(max_length=30)
    email           = models.EmailField(blank=True)
    address         = models.TextField(blank=True)
    city            = models.CharField(max_length=100, blank=True)
    lat             = models.FloatField(null=True, blank=True)
    lng             = models.FloatField(null=True, blank=True)
    billing_address = models.TextField(blank=True)
    billing_city    = models.CharField(max_length=100, blank=True)
    note            = models.TextField(blank=True)
    payment_method  = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')
    payment_status  = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    subtotal        = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=8,  decimal_places=2, default=0)
    total           = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_receipt = models.ImageField(upload_to='receipts/', blank=True, null=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import random, string
            self.order_number = 'ORD' + ''.join(random.choices(string.digits, k=7))
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order        = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product      = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=300)
    product_sku  = models.CharField(max_length=100, blank=True)
    unit_price   = models.DecimalField(max_digits=12, decimal_places=2)
    quantity     = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class OrderPayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI / Online'),
        ('cheque', 'Cheque'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    note = models.TextField(blank=True)
    recorded_by = models.ForeignKey('CustomerUser', on_delete=models.SET_NULL, null=True, related_name='recorded_payments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment Rs.{self.amount} for Order #{self.order.order_number}"


class ProductReview(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(CustomerUser, on_delete=models.CASCADE, related_name='reviews')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user', 'order')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.product.name} ({self.rating}★)"



class SiteSettings(models.Model):
    business_name = models.CharField(max_length=200)
    tagline = models.CharField(max_length=300, blank=True)
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    phone2 = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    tiktok = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    map_embed = models.TextField(blank=True, help_text='Google Maps embed src URL')
    hours_weekday = models.CharField(max_length=100, blank=True, default='Sun – Fri: 9:00 AM – 6:00 PM')
    hours_saturday = models.CharField(max_length=100, blank=True, default='Saturday: 10:00 AM – 3:00 PM')
    bank_name = models.CharField(max_length=200, blank=True)
    bank_account_name = models.CharField(max_length=200, blank=True)
    bank_account_number = models.CharField(max_length=100, blank=True)
    bank_branch = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.business_name

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'business_name': 'My Business'})
        return obj

class ContactInquiry(models.Model):
    INQUIRY_TYPES = [
        ('product', 'Product Inquiry'),
        ('b2b', 'B2B / Bulk Order Quote'),
        ('shipping', 'Shipping & Delivery'),
        ('partnership', 'Partnership / Reseller'),
        ('support', 'After-Sales Support'),
        ('other', 'Other'),
    ]
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    company = models.CharField(max_length=200, blank=True)
    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_TYPES, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Contact Inquiries'

    def __str__(self):
        return f"{self.full_name} — {self.created_at.strftime('%d %b %Y')}"


class CarouselSlide(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='carousel/')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Reel(models.Model):
    VIDEO_TYPE_CHOICES = [
        ('upload', 'Upload Video'),
        ('youtube', 'YouTube Link'),
        ('tiktok', 'TikTok Link'),
    ]
    title = models.CharField(max_length=200)
    video_type = models.CharField(max_length=20, choices=VIDEO_TYPE_CHOICES, default='upload')
    thumbnail = models.ImageField(upload_to='reels/thumbnails/', blank=True, null=True)
    video = models.FileField(upload_to='reels/videos/', blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True, help_text='YouTube video URL (e.g., https://www.youtube.com/watch?v=...)')
    tiktok_url = models.URLField(blank=True, null=True, help_text='TikTok video URL (e.g., https://www.tiktok.com/@.../video/...)')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title
    
    def get_video_url(self):
        if self.video_type == 'youtube' and self.youtube_url:
            return self.youtube_url
        elif self.video_type == 'tiktok' and self.tiktok_url:
            return self.tiktok_url
        elif self.video_type == 'upload' and self.video:
            return self.video.url
        return None
    
    def get_embed_url(self):
        if self.video_type == 'youtube' and self.youtube_url:
            url = self.youtube_url
            video_id = None
            # Handle youtube.com/watch?v=
            if 'youtube.com/watch?v=' in url:
                video_id = url.split('v=')[1].split('&')[0]
            # Handle youtu.be/
            elif 'youtu.be/' in url:
                video_id = url.split('youtu.be/')[1].split('?')[0]
            # Handle youtube.com/shorts/
            elif 'youtube.com/shorts/' in url:
                video_id = url.split('shorts/')[1].split('?')[0].split('/')[0]
            # Fallback
            else:
                video_id = url.split('v=')[-1].split('&')[0] if 'v=' in url else url.split('/')[-1].split('?')[0]
            
            return f'https://www.youtube-nocookie.com/embed/{video_id}' if video_id else None
        elif self.video_type == 'tiktok' and self.tiktok_url:
            return self.tiktok_url
        return None


class Category(models.Model):
    name = models.CharField(max_length=200)
    icon = models.ImageField(upload_to='categories/icons/')
    link = models.CharField(max_length=300, default='/')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    @property
    def safe_link(self):
        return f'/products/?category={self.id}'


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Sub Categories'

    def __str__(self):
        return f"{self.category.name} › {self.name}"


# ── Country of Origin ───────────────────────────────────────────────────────────

class Country(models.Model):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=5, blank=True, help_text='ISO code e.g. CN, IN, US')

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Countries'

    def __str__(self):
        return self.name


# ── Customer Tiers ────────────────────────────────────────────────────────────

class CustomerTier(models.Model):
    name = models.CharField(max_length=100)          # e.g. "Gold", "Silver", "Wholesale"
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class DeliveryTimeTier(models.Model):
    TIME_UNIT_CHOICES = [
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
    ]
    
    name = models.CharField(max_length=100)
    min_time = models.IntegerField()
    min_unit = models.CharField(max_length=10, choices=TIME_UNIT_CHOICES, default='days')
    max_time = models.IntegerField()
    max_unit = models.CharField(max_length=10, choices=TIME_UNIT_CHOICES, default='days')
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({self.min_time} {self.min_unit} - {self.max_time} {self.max_unit})"
    
    def get_display_time(self):
        return f"{self.min_time} {self.min_unit} - {self.max_time} {self.max_unit}"


class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    pan_number = models.CharField(max_length=10, blank=True, verbose_name='PAN Number')
    company = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    tier = models.ForeignKey(CustomerTier, null=True, blank=True, on_delete=models.SET_NULL, related_name='customers')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email})"


# ── Products ──────────────────────────────────────────────────────────────────

class Product(models.Model):
    # Identity
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    sku = models.CharField(max_length=100, unique=True)
    product_code = models.CharField(max_length=100, blank=True)
    brand = models.CharField(max_length=200, blank=True)
    origin = models.ForeignKey('Country', null=True, blank=True, on_delete=models.SET_NULL, related_name='products')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='products')
    sub_category = models.ForeignKey('SubCategory', null=True, blank=True, on_delete=models.SET_NULL, related_name='products')
    linked_package = models.ForeignKey('Package', null=True, blank=True, on_delete=models.SET_NULL, related_name='linked_products', help_text='Link this product to a package offer')

    # Descriptions
    short_description = models.TextField(blank=True)
    full_description = models.TextField(blank=True)
    specifications = models.TextField(blank=True, help_text='JSON or plain text specs')

    # Pricing
    mrp = models.DecimalField(max_digits=12, decimal_places=2, help_text='Public / normal user price')
    tax_included = models.BooleanField(default=True, help_text='Is VAT/tax included in MRP?')
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Tax % if not included')

    # Delivery
    delivery_time = models.ForeignKey(DeliveryTimeTier, null=True, blank=True, on_delete=models.SET_NULL, related_name='products')

    # Related products (self M2M)
    related_products = models.ManyToManyField('self', blank=True, symmetrical=False)

    # Visibility & status
    is_active = models.BooleanField(default=True, help_text='Show on website')
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} [{self.sku}]"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base = slugify(self.name)
            slug = base
            n = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        if not img:
            img = self.images.first()
        return img

    @property
    def stock_quantity(self):
        from django.db.models import Sum
        result = self.stock_entries.aggregate(total=Sum('quantity_change'))
        return result['total'] or 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/images/')
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - image {self.order}"


class ProductTierPrice(models.Model):
    """Custom price per CustomerTier for a product."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='tier_prices')
    tier = models.ForeignKey(CustomerTier, on_delete=models.CASCADE, related_name='tier_prices')
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('product', 'tier')

    def __str__(self):
        return f"{self.product.name} — {self.tier.name}: {self.price}"


# ── Services Page ────────────────────────────────────────────────────────────

class Stat(models.Model):
    value = models.CharField(max_length=20)
    label = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.value} {self.label}"


class TrustedClient(models.Model):
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='trusted/', blank=True, null=True)
    icon = models.CharField(max_length=100, blank=True, help_text='Material icon fallback e.g. precision_manufacturing')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Testimonial(models.Model):
    quote = models.TextField()
    author_name = models.CharField(max_length=200)
    author_role = models.CharField(max_length=200, blank=True)
    initials = models.CharField(max_length=5, blank=True)
    photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.author_name


class TeamMember(models.Model):
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='team/', blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Service(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=100, blank=True, help_text='Material Symbols icon name e.g. bakery_dining')
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class WhyChooseUs(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=100, blank=True, help_text='Material Symbols icon name e.g. local_shipping')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Why Choose Us'

    def __str__(self):
        return self.title


# ── POS Billing ───────────────────────────────────────────────────────────────

class Billing(models.Model):
    SALE_TYPE_CHOICES = [
        ('counter', 'Counter Sale'),
        ('online_pos', 'Online POS'),
        ('agent', 'Agent Sale'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('unpaid', 'Unpaid'),
    ]

    bill_number     = models.CharField(max_length=20, unique=True)
    sale_type       = models.CharField(max_length=20, choices=SALE_TYPE_CHOICES, default='counter')
    customer        = models.ForeignKey('Customer', null=True, blank=True, on_delete=models.SET_NULL, related_name='billings')
    walk_in_name    = models.CharField(max_length=200, blank=True)
    walk_in_phone   = models.CharField(max_length=30, blank=True)
    agent           = models.ForeignKey('CustomerUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='agent_billings', limit_choices_to={'user_type': 'agent'})
    billed_by       = models.ForeignKey('CustomerUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='created_billings')
    subtotal        = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    item_discount   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overall_discount= models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total           = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # Split payment
    cash_amount     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    card_amount     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    online_amount   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status  = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='paid')
    note            = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Bill #{self.bill_number}"

    def save(self, *args, **kwargs):
        if not self.bill_number:
            import random, string
            self.bill_number = 'BILL' + ''.join(random.choices(string.digits, k=6))
        super().save(*args, **kwargs)

    @property
    def balance_due(self):
        return self.total - self.amount_paid


class BillingItem(models.Model):
    billing      = models.ForeignKey(Billing, on_delete=models.CASCADE, related_name='items')
    product      = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=300)
    product_sku  = models.CharField(max_length=100, blank=True)
    unit_price   = models.DecimalField(max_digits=12, decimal_places=2)
    quantity     = models.PositiveIntegerField(default=1)
    discount     = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def subtotal(self):
        return (self.unit_price * self.quantity) - self.discount

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"


class StockEntry(models.Model):
    ENTRY_TYPES = [
        ('import', 'Import / Stock In'),
        ('sale', 'Sale / Stock Out'),
        ('adjustment', 'Adjustment In'),
        ('adjustment_out', 'Adjustment Out'),
        ('return', 'Return'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_entries')
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES)
    quantity_change = models.IntegerField(help_text='Positive = in, Negative = out')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    customer = models.ForeignKey('Customer', null=True, blank=True, on_delete=models.SET_NULL, related_name='stock_entries')
    note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} | {self.entry_type} | {self.quantity_change}"


# ── Quote Requests ────────────────────────────────────────────────────────────

class QuotationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('responded', 'Responded'),
        ('closed', 'Closed'),
    ]
    user_email = models.EmailField()
    user_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    linked_customer = models.ForeignKey('Customer', null=True, blank=True, on_delete=models.SET_NULL, related_name='quotations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Quotation #{self.pk} by {self.user_email}"


class QuotationRequestItem(models.Model):
    quotation = models.ForeignKey(QuotationRequest, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='quotation_items')
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('quotation', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.name if self.product else 'Unknown'}"


# Keep old QuoteRequest for backward compatibility (deprecated)
class QuoteRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('responded', 'Responded'),
        ('closed', 'Closed'),
    ]
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='quote_requests')
    user_email = models.EmailField()
    user_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    linked_customer = models.ForeignKey('Customer', null=True, blank=True, on_delete=models.SET_NULL, related_name='quotes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Quote: {self.product} by {self.user_email}"


# ── Package System ────────────────────────────────────────────────────────────

class Package(models.Model):
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, unique=True)
    total_mrp = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    overall_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} [{self.sku}]"

    def calculate_total_mrp(self):
        from django.db.models import Sum, F
        result = self.items.aggregate(
            total=Sum(F('product__mrp') * F('quantity') - F('item_discount'))
        )
        return result['total'] or 0

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.total_mrp = self.calculate_total_mrp()
        if self.pk:
            Package.objects.filter(pk=self.pk).update(total_mrp=self.total_mrp)


class PackageItem(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    item_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def item_total(self):
        return (self.product.mrp * self.quantity) - self.item_discount

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.package.save()

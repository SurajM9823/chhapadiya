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
        ('customer', 'Customer'),
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

class CustomerUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('agent', 'Agent'),
        ('staff', 'Staff'),
    ]
    
    # New: Customer Subtype (Retailer by default for customers)
    CUSTOMER_SUBTYPE_CHOICES = [
        ('retailer', 'Retailer Customer'),
        ('dealer', 'Dealer'),
    ]

    phone = models.CharField(max_length=20, blank=True)
    google_id = models.CharField(max_length=200, blank=True)
    avatar = models.URLField(blank=True)
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL, related_name='users')
    
    # User type and reference
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='customer')
    
    # New field: Only applicable for customers
    customer_subtype = models.CharField(
        max_length=10, 
        choices=CUSTOMER_SUBTYPE_CHOICES, 
        default='retailer',
        blank=True,
        null=True
    )
    
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
        
        # === NEW LOGIC: Set default subtype for customers ===
        if self.user_type == 'customer':
            if not self.customer_subtype:
                self.customer_subtype = 'retailer'
        else:
            # For agents, clear the customer subtype
            self.customer_subtype = None

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
    
    def can_update_order_status(self, from_status, to_status):
        """Check if user can update order from one status to another."""
        if self.is_superuser:
            return True
        if not self.role:
            return False
        return self.role.order_status_permissions.filter(
            from_status=from_status, 
            to_status=to_status
        ).exists()

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

class OrderStatusPermission(models.Model):
    """Defines which order statuses a role can update to."""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='order_status_permissions')
    from_status = models.CharField(max_length=20, help_text='Current order status')
    to_status = models.CharField(max_length=20, help_text='Status that can be updated to')
    
    class Meta:
        unique_together = ('role', 'from_status', 'to_status')
        verbose_name = 'Order Status Permission'
        verbose_name_plural = 'Order Status Permissions'
    
    def __str__(self):
        return f"{self.role.get_name_display()}: {self.from_status} → {self.to_status}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('confirmed',  'Confirmed'),
        ('processing', 'Processing'),
        ('shipped',    'Shipped'),
        ('delivered',  'Delivered'),
        ('cancelled',  'Cancelled'),
        ('return',  'Return'),
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
    billing_contact = models.CharField(max_length=30, null=True, blank=True)
    billing_org_name = models.CharField(max_length=200, blank=True)
    billing_person_name = models.CharField(max_length=200, blank=True)
    note            = models.TextField(blank=True)
    payment_method  = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')
    payment_status  = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    subtotal        = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=8,  decimal_places=2, default=0)
    total           = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_receipt = models.ImageField(upload_to='receipts/', blank=True, null=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    is_avilable     = models.BooleanField(default=False, help_text='Is this avilable?')

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
    map_embed = models.TextField(default='https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3532.822830843477!2d85.3188547!3d27.6918809!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x39eb19b26e0df391%3A0xc48afebfca84b55c!2sKathmandu%2010000%2C%20Nepal!5e0!3m2!1sen!2sus!4v1715000000000!5m2!1sen!2sus', blank=True, help_text='Google Maps embed src URL')
    hours_weekday = models.CharField(max_length=100, blank=True, default='Sun – Fri: 9:00 AM – 6:00 PM')
    hours_saturday = models.CharField(max_length=100, blank=True, default='Saturday: 10:00 AM – 3:00 PM')
    bank_name = models.CharField(max_length=200, blank=True)
    bank_account_name = models.CharField(max_length=200, blank=True)
    bank_account_number = models.CharField(max_length=100, blank=True)
    bank_branch = models.CharField(max_length=200, blank=True)
    bank_qr = models.ImageField(upload_to='site/', blank=True, null=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.business_name

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={
            'business_name': 'My Business',
            'map_embed': 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3532.822830843477!2d85.3188547!3d27.6918809!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x39eb19b26e0df391%3A0xc48afebfca84b55c!2sKathmandu%2010000%2C%20Nepal!5e0!3m2!1sen!2sus!4v1715000000000!5m2!1sen!2sus'
        })
        return obj


class AboutContent(models.Model):
    mission_title = models.CharField(max_length=200, default='Our Mission')
    mission_content = models.TextField(
        default='To deliver high-quality products at competitive prices while building lasting relationships through reliability, transparency, and exceptional service. We strive to be the most trusted trading partner for businesses of all sizes.'
    )
    vision_title = models.CharField(max_length=200, default='Our Vision')
    vision_content = models.TextField(
        default='To become the region\'s most comprehensive and trusted multi-category trading company — expanding our reach globally while maintaining the personal touch and quality standards that define us.'
    )
    quote_content = models.TextField(
        default='"Reliability isn\'t just a metric; it\'s our promise to every partner we serve."'
    )
    quote_author = models.CharField(max_length=200, blank=True, help_text='Optional author of the quote')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'About Content'
        verbose_name_plural = 'About Contents'
        ordering = ['order']

    def __str__(self):
        return f"About Content - {self.mission_title}"

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).first()

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


# models.py
class Customer(models.Model):  
    name = models.CharField(max_length=200)
    user = models.OneToOneField(
        'CustomerUser',          # or your custom user model
        on_delete=models.CASCADE,
        related_name='customer',   # optional but recommended
        unique=True,
        null= True,
        blank=True
    )
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    pan_number = models.CharField(max_length=10, blank=True, verbose_name='PAN Number')
    company = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    
    # New: Customer Type
    CUSTOMER_TYPE_CHOICES = [
        ('retailer', 'Retailer'),
        ('dealer', 'Dealer'),
    ]
    customer_type = models.CharField(
        max_length=10, 
        choices=CUSTOMER_TYPE_CHOICES, 
        default='retailer'
    )
    
    tier = models.ForeignKey(
        'CustomerTier', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='customers'
    )
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
    
    # New Fields
    retail_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Retail price (if different from MRP). Defaults to MRP if not provided.'
    )
    dealer_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Dealer price (if different from MRP). Defaults to MRP if not provided.'
    )
    
    tax_included = models.BooleanField(default=True, help_text='Is VAT/tax included in MRP?')
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Tax % if not included')

    # Delivery
    delivery_time = models.ForeignKey(DeliveryTimeTier, null=True, blank=True, on_delete=models.SET_NULL, related_name='products')

    # Related products (self M2M)
    related_products = models.ManyToManyField(
        'self', 
        blank=True, 
        symmetrical=False,
        related_name='related_to',           # ← Fixed: Added related_name
        verbose_name="Related Products"
    )

    # Visibility & status
    is_active = models.BooleanField(default=True, help_text='Show on website')
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    alliance_products = models.ManyToManyField(
        'self',
        through='ProductAlliance',
        through_fields=('product', 'alliance_product'),
        blank=True,
        symmetrical=False,
        related_name='alliance_with_products',   # ← Fixed: Added unique related_name
        verbose_name="Alliance Products",
        help_text="Other products allied with this product"
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} [{self.sku}]"

    def save(self, *args, **kwargs):
        # Auto-set retail_price and dealer_price to MRP if not provided
        if self.retail_price is None:
            self.retail_price = self.mrp
            
        if self.dealer_price is None:
            self.dealer_price = self.mrp

        # Generate slug if not provided
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
    
    @property
    def display_retail_price(self):
        return self.retail_price or self.mrp

    @property
    def display_dealer_price(self):
        return self.dealer_price or self.mrp


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


class ProductAlliance(models.Model):
    """Through model for Alliance Products"""
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='product_alliances'      # Main product's alliances
    )
    alliance_product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='alliance_with'          # This is fine
    )
    
    discount_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Discount offered when buying together"
    )
    
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower number = higher priority)"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'alliance_product')
        ordering = ['priority', '-created_at']

    def __str__(self):
        return f"{self.product.name} ↔ {self.alliance_product.name}"

    def save(self, *args, **kwargs):
        # Prevent a product from being allied with itself
        if self.product == self.alliance_product:
            raise ValueError("A product cannot be allied with itself.")
        super().save(*args, **kwargs)

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


class Founder(models.Model):
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='founders/', blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Founder'
        verbose_name_plural = 'Founders'

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

    @property
    def savings(self):
        return self.total_mrp - self.selling_price

    def calculate_total_mrp(self):
        from django.db.models import Sum, F, ExpressionWrapper, DecimalField
        result = self.items.annotate(
            line=ExpressionWrapper(
                F('product__mrp') * F('quantity') - F('item_discount'),
                output_field=DecimalField()
            )
        ).aggregate(total=Sum('line'))
        return result['total'] or 0

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.pk:
            new_total = self.calculate_total_mrp()
            Package.objects.filter(pk=self.pk).update(total_mrp=new_total)
            self.total_mrp = new_total  # Keep instance in sync

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        if not img:
            img = self.images.first()
        return img


class PackageImage(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='packages/images/')
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.package.name} - image {self.order}"


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
        new_total = self.package.calculate_total_mrp()
        Package.objects.filter(pk=self.package_id).update(total_mrp=new_total)

    def delete(self, *args, **kwargs):
        package = self.package
        super().delete(*args, **kwargs)
        new_total = package.calculate_total_mrp()
        Package.objects.filter(pk=package.pk).update(total_mrp=new_total)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import SiteSettings, CarouselSlide, Reel, Category, SubCategory, Country, CustomerTier, Customer, Product, ProductImage, ProductTierPrice, Stat, TrustedClient, Testimonial, TeamMember, Service, WhyChooseUs, StockEntry, ContactInquiry, Order, OrderItem
from .email_utils import send_order_status_update_email

def is_superuser(user):
    return user.is_superuser

def panel_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('panel_dashboard')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user and user.is_superuser:
            login(request, user)
            return redirect('panel_dashboard')
        messages.error(request, 'Invalid credentials or not a superuser.')
    return render(request, 'panel/login.html')

def panel_logout(request):
    logout(request)
    return redirect('panel_login')

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_dashboard(request):
    from django.db.models import Sum, Count, Q
    from datetime import timedelta
    from django.utils import timezone
    
    # Orders Statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status__in=['pending', 'confirmed', 'processing']).count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()
    
    # Income Calculation (only from delivered orders)
    delivered_income = Order.objects.filter(status='delivered').aggregate(total=Sum('total'))['total'] or 0
    pending_income = Order.objects.filter(status__in=['pending', 'confirmed', 'processing']).aggregate(total=Sum('total'))['total'] or 0
    total_income = delivered_income
    
    # Pending Orders List
    pending_order_list = Order.objects.filter(status__in=['pending', 'confirmed', 'processing']).select_related('user').prefetch_related('items')[:5]
    
    # Top Customers (by total spent on delivered orders)
    from django.db.models import F
    top_customers = Order.objects.filter(status='delivered').values('user__email', 'user__first_name', 'user__last_name').annotate(
        total_spent=Sum('total'),
        order_count=Count('id')
    ).order_by('-total_spent')[:5]
    
    # Format top customers
    top_customers_list = []
    for cust in top_customers:
        top_customers_list.append({
            'email': cust['user__email'],
            'full_name': f"{cust['user__first_name']} {cust['user__last_name']}".strip() or cust['user__email'],
            'total_spent': cust['total_spent'],
            'order_count': cust['order_count']
        })
    
    # Low Stock Products (stock < 10)
    low_stock_products = []
    for product in Product.objects.all():
        stock = product.stock_quantity
        if stock < 10:
            low_stock_products.append({
                'name': product.name,
                'sku': product.sku,
                'stock': stock,
                'mrp': product.mrp
            })
    low_stock_products = low_stock_products[:5]
    
    # Recent Inquiries
    recent_inquiries = ContactInquiry.objects.all()[:5]
    
    # Visitor Data (last 7 days)
    visitor_data = []
    for i in range(6, -1, -1):
        date = timezone.now() - timedelta(days=i)
        visitor_data.append({
            'date': date.strftime('%a'),
            'count': (i * 15 + 20) if i > 0 else 45  # Mock data
        })
    
    # Sales by Status
    sales_by_status = Order.objects.values('status').annotate(
        count=Count('id'),
        total=Sum('total')
    ).order_by('-count')
    
    # Site Visitors (mock data - would need analytics integration)
    total_visitors = 1250
    mobile_users = 750
    desktop_users = 500
    
    # Inquiries Count
    total_inquiries = ContactInquiry.objects.count()
    unread_inquiries = ContactInquiry.objects.filter(is_read=False).count()
    
    # Stock Report
    total_products = Product.objects.count()
    low_stock_count = sum(1 for p in Product.objects.all() if p.stock_quantity < 10)
    out_of_stock_count = sum(1 for p in Product.objects.all() if p.stock_quantity == 0)
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'total_income': total_income,
        'pending_income': pending_income,
        'pending_order_list': pending_order_list,
        'top_customers': top_customers_list,
        'low_stock_products': low_stock_products,
        'recent_inquiries': recent_inquiries,
        'visitor_data': visitor_data,
        'sales_by_status': sales_by_status,
        'total_visitors': total_visitors,
        'mobile_users': mobile_users,
        'desktop_users': desktop_users,
        'total_inquiries': total_inquiries,
        'unread_inquiries': unread_inquiries,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }
    return render(request, 'panel/dashboard.html', context)


# ── Site Settings ─────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_settings(request):
    s = SiteSettings.get()
    if request.method == 'POST':
        s.business_name = request.POST.get('business_name', '')
        s.tagline = request.POST.get('tagline', '')
        s.email = request.POST.get('email', '')
        s.phone = request.POST.get('phone', '')
        s.phone2 = request.POST.get('phone2', '')
        s.address = request.POST.get('address', '')
        s.facebook = request.POST.get('facebook', '')
        s.instagram = request.POST.get('instagram', '')
        s.whatsapp = request.POST.get('whatsapp', '')
        s.tiktok = request.POST.get('tiktok', '')
        s.linkedin = request.POST.get('linkedin', '')
        s.twitter = request.POST.get('twitter', '')
        s.map_embed = request.POST.get('map_embed', '')
        s.hours_weekday = request.POST.get('hours_weekday', '')
        s.hours_saturday = request.POST.get('hours_saturday', '')
        s.bank_name = request.POST.get('bank_name', '')
        s.bank_account_name = request.POST.get('bank_account_name', '')
        s.bank_account_number = request.POST.get('bank_account_number', '')
        s.bank_branch = request.POST.get('bank_branch', '')
        if 'logo' in request.FILES:
            s.logo = request.FILES['logo']
        s.save()
        messages.success(request, 'Settings saved.')
        return redirect('panel_settings')
    return render(request, 'panel/settings.html', {'settings': s})


# ── Carousel ──────────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_carousel_add(request):
    if request.method == 'POST':
        CarouselSlide.objects.create(
            title=request.POST['title'], image=request.FILES['image'],
            order=request.POST.get('order', 0), is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Slide added.')
        return redirect('panel_dashboard')
    return render(request, 'panel/carousel_form.html', {'action': 'Add'})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_carousel_edit(request, pk):
    slide = get_object_or_404(CarouselSlide, pk=pk)
    if request.method == 'POST':
        slide.title = request.POST['title']
        slide.order = request.POST.get('order', 0)
        slide.is_active = request.POST.get('is_active') == 'on'
        if 'image' in request.FILES:
            slide.image = request.FILES['image']
        slide.save()
        messages.success(request, 'Slide updated.')
        return redirect('panel_dashboard')
    return render(request, 'panel/carousel_form.html', {'action': 'Edit', 'slide': slide})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_carousel_delete(request, pk):
    get_object_or_404(CarouselSlide, pk=pk).delete()
    messages.success(request, 'Slide deleted.')
    return redirect('panel_dashboard')


# ── Reels ─────────────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_reels(request):
    from django.core.paginator import Paginator
    reels_list = Reel.objects.all()
    paginator = Paginator(reels_list, 10)
    page_number = request.GET.get('page', 1)
    reels = paginator.get_page(page_number)
    return render(request, 'panel/reels.html', {'reels': reels})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_reel_add(request):
    if request.method == 'POST':
        Reel.objects.create(
            title=request.POST['title'], thumbnail=request.FILES['thumbnail'],
            video=request.FILES['video'], order=request.POST.get('order', 0),
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Reel added.')
        return redirect('panel_reels')
    return render(request, 'panel/reel_form.html', {'action': 'Add'})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_reel_edit(request, pk):
    reel = get_object_or_404(Reel, pk=pk)
    if request.method == 'POST':
        reel.title = request.POST['title']
        reel.order = request.POST.get('order', 0)
        reel.is_active = request.POST.get('is_active') == 'on'
        if 'thumbnail' in request.FILES:
            reel.thumbnail = request.FILES['thumbnail']
        if 'video' in request.FILES:
            reel.video = request.FILES['video']
        reel.save()
        messages.success(request, 'Reel updated.')
        return redirect('panel_reels')
    return render(request, 'panel/reel_form.html', {'action': 'Edit', 'reel': reel})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_reel_delete(request, pk):
    get_object_or_404(Reel, pk=pk).delete()
    messages.success(request, 'Reel deleted.')
    return redirect('panel_reels')


# ── Categories ────────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_categories(request):
    categories = Category.objects.prefetch_related('subcategories').all()
    return render(request, 'panel/categories.html', {'categories': categories})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_category_add(request):
    if request.method == 'POST':
        Category.objects.create(
            name=request.POST['name'], icon=request.FILES['icon'],
            link=request.POST.get('link', '/'), order=request.POST.get('order', 0),
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Category added.')
        return redirect('panel_categories')
    return render(request, 'panel/category_form.html', {'action': 'Add'})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.name = request.POST['name']
        category.link = request.POST.get('link', '/')
        category.order = request.POST.get('order', 0)
        category.is_active = request.POST.get('is_active') == 'on'
        if 'icon' in request.FILES:
            category.icon = request.FILES['icon']
        category.save()
        messages.success(request, 'Category updated.')
        return redirect('panel_categories')
    return render(request, 'panel/category_form.html', {'action': 'Edit', 'category': category})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_category_delete(request, pk):
    get_object_or_404(Category, pk=pk).delete()
    messages.success(request, 'Category deleted.')
    return redirect('panel_categories')


# ── Sub Categories ────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_subcategories(request, cat_pk):
    category = get_object_or_404(Category, pk=cat_pk)
    return render(request, 'panel/subcategories.html', {'category': category, 'subs': category.subcategories.all()})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_subcategory_add(request, cat_pk):
    category = get_object_or_404(Category, pk=cat_pk)
    if request.method == 'POST':
        SubCategory.objects.create(
            category=category, name=request.POST['name'],
            order=request.POST.get('order', 0),
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Sub-category added.')
        return redirect('panel_subcategories', cat_pk=cat_pk)
    return render(request, 'panel/subcategory_form.html', {'action': 'Add', 'category': category})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_subcategory_edit(request, cat_pk, pk):
    category = get_object_or_404(Category, pk=cat_pk)
    sub = get_object_or_404(SubCategory, pk=pk, category=category)
    if request.method == 'POST':
        sub.name = request.POST['name']
        sub.order = request.POST.get('order', 0)
        sub.is_active = request.POST.get('is_active') == 'on'
        sub.save()
        messages.success(request, 'Sub-category updated.')
        return redirect('panel_subcategories', cat_pk=cat_pk)
    return render(request, 'panel/subcategory_form.html', {'action': 'Edit', 'category': category, 'sub': sub})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_subcategory_delete(request, cat_pk, pk):
    get_object_or_404(SubCategory, pk=pk, category_id=cat_pk).delete()
    messages.success(request, 'Sub-category deleted.')
    return redirect('panel_subcategories', cat_pk=cat_pk)


# ── Product Detail ────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('category', 'sub_category').prefetch_related('images', 'tier_prices__tier', 'related_products'), pk=pk)
    return render(request, 'panel/product_detail.html', {'product': product})


# ── Countries ─────────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_countries(request):
    return render(request, 'panel/countries.html', {'countries': Country.objects.all()})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_country_save(request, pk=None):
    country = get_object_or_404(Country, pk=pk) if pk else None
    if request.method == 'POST':
        name = request.POST['name']
        code = request.POST.get('code', '')
        if country:
            country.name = name; country.code = code; country.save()
            messages.success(request, 'Country updated.')
        else:
            Country.objects.create(name=name, code=code)
            messages.success(request, 'Country added.')
        return redirect('panel_countries')
    return render(request, 'panel/country_form.html', {'action': 'Edit' if country else 'Add', 'country': country})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_country_delete(request, pk):
    get_object_or_404(Country, pk=pk).delete()
    messages.success(request, 'Country deleted.')
    return redirect('panel_countries')


# ── Customer Tiers ────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_tiers(request):
    return render(request, 'panel/tiers.html', {'tiers': CustomerTier.objects.all()})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_tier_add(request):
    if request.method == 'POST':
        CustomerTier.objects.create(
            name=request.POST['name'], description=request.POST.get('description', ''),
            order=request.POST.get('order', 0), is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Tier added.')
        return redirect('panel_tiers')
    return render(request, 'panel/tier_form.html', {'action': 'Add'})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_tier_edit(request, pk):
    tier = get_object_or_404(CustomerTier, pk=pk)
    if request.method == 'POST':
        tier.name = request.POST['name']
        tier.description = request.POST.get('description', '')
        tier.order = request.POST.get('order', 0)
        tier.is_active = request.POST.get('is_active') == 'on'
        tier.save()
        messages.success(request, 'Tier updated.')
        return redirect('panel_tiers')
    return render(request, 'panel/tier_form.html', {'action': 'Edit', 'tier': tier})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_tier_delete(request, pk):
    get_object_or_404(CustomerTier, pk=pk).delete()
    messages.success(request, 'Tier deleted.')
    return redirect('panel_tiers')


# ── Customers ─────────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_customers(request):
    return render(request, 'panel/customers.html', {'customers': Customer.objects.select_related('tier').all()})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_customer_add(request):
    tiers = CustomerTier.objects.filter(is_active=True)
    if request.method == 'POST':
        Customer.objects.create(
            name=request.POST['name'], email=request.POST['email'],
            phone=request.POST.get('phone', ''), company=request.POST.get('company', ''),
            address=request.POST.get('address', ''),
            tier_id=request.POST.get('tier') or None,
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Customer added.')
        return redirect('panel_customers')
    return render(request, 'panel/customer_form.html', {'action': 'Add', 'tiers': tiers})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    tiers = CustomerTier.objects.filter(is_active=True)
    if request.method == 'POST':
        customer.name = request.POST['name']
        customer.email = request.POST['email']
        customer.phone = request.POST.get('phone', '')
        customer.company = request.POST.get('company', '')
        customer.address = request.POST.get('address', '')
        customer.tier_id = request.POST.get('tier') or None
        customer.is_active = request.POST.get('is_active') == 'on'
        customer.save()
        messages.success(request, 'Customer updated.')
        return redirect('panel_customers')
    return render(request, 'panel/customer_form.html', {'action': 'Edit', 'customer': customer, 'tiers': tiers})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_customer_delete(request, pk):
    get_object_or_404(Customer, pk=pk).delete()
    messages.success(request, 'Customer deleted.')
    return redirect('panel_customers')


# ── Products ──────────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_products(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    search = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', '').strip()
    status = request.GET.get('status', '').strip()
    page = request.GET.get('page', 1)
    limit = request.GET.get('limit', 20)
    
    try:
        limit = int(limit)
        if limit > 100:
            limit = 100
        if limit < 5:
            limit = 5
    except:
        limit = 20
    
    qs = Product.objects.select_related('category', 'sub_category').all()
    
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(sku__icontains=search) | Q(brand__icontains=search))
    
    if category_id:
        try:
            qs = qs.filter(category_id=int(category_id))
        except:
            pass
    
    if status:
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        elif status == 'featured':
            qs = qs.filter(is_featured=True)
    
    qs = qs.order_by('-created_at')
    
    paginator = Paginator(qs, limit)
    products = paginator.get_page(page)
    categories = Category.objects.filter(is_active=True).values('id', 'name').order_by('name')
    
    return render(request, 'panel/products.html', {
        'products': products,
        'categories': list(categories),
        'search': search,
        'category_id': category_id,
        'status': status,
        'limit': limit,
        'total_count': paginator.count,
    })

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_product_add(request):
    categories = Category.objects.prefetch_related('subcategories').filter(is_active=True)
    tiers = CustomerTier.objects.filter(is_active=True)
    all_products = Product.objects.all()
    countries = Country.objects.all()
    if request.method == 'POST':
        product = Product.objects.create(
            name=request.POST['name'], sku=request.POST['sku'],
            brand=request.POST.get('brand', ''), origin_id=request.POST.get('origin') or None,
            category_id=request.POST.get('category') or None,
            sub_category_id=request.POST.get('sub_category') or None,
            short_description=request.POST.get('short_description', ''),
            full_description=request.POST.get('full_description', ''),
            specifications=request.POST.get('specifications', ''),
            mrp=request.POST['mrp'],
            tax_included=request.POST.get('tax_included') == 'on',
            tax_percent=request.POST.get('tax_percent') or 0,
            is_active=request.POST.get('is_active') == 'on',
            is_featured=request.POST.get('is_featured') == 'on',
        )
        for img in request.FILES.getlist('images'):
            ProductImage.objects.create(product=product, image=img)
        if product.images.exists():
            first = product.images.first(); first.is_primary = True; first.save()
        for tier in tiers:
            price_val = request.POST.get(f'tier_price_{tier.pk}')
            if price_val:
                ProductTierPrice.objects.create(product=product, tier=tier, price=price_val)
        related_ids = request.POST.getlist('related_products')
        if related_ids:
            product.related_products.set(related_ids)
        initial_stock = request.POST.get('initial_stock')
        if initial_stock and int(initial_stock) > 0:
            StockEntry.objects.create(product=product, entry_type='import', quantity_change=int(initial_stock), note='Initial stock')
        messages.success(request, 'Product added.')
        return redirect('panel_products')
    return render(request, 'panel/product_form.html', {
        'action': 'Add', 'categories': categories, 'tiers': tiers,
        'all_products': all_products, 'countries': countries,
    })

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.prefetch_related('subcategories').filter(is_active=True)
    tiers = CustomerTier.objects.filter(is_active=True)
    all_products = Product.objects.exclude(pk=pk)
    countries = Country.objects.all()
    tier_prices = {tp.tier_id: tp.price for tp in product.tier_prices.all()}
    if request.method == 'POST':
        product.name = request.POST['name']
        product.sku = request.POST['sku']
        product.brand = request.POST.get('brand', '')
        product.origin_id = request.POST.get('origin') or None
        product.category_id = request.POST.get('category') or None
        product.sub_category_id = request.POST.get('sub_category') or None
        product.short_description = request.POST.get('short_description', '')
        product.full_description = request.POST.get('full_description', '')
        product.specifications = request.POST.get('specifications', '')
        product.mrp = request.POST['mrp']
        product.tax_included = request.POST.get('tax_included') == 'on'
        product.tax_percent = request.POST.get('tax_percent') or 0
        product.is_active = request.POST.get('is_active') == 'on'
        product.is_featured = request.POST.get('is_featured') == 'on'
        product.save()
        for img in request.FILES.getlist('images'):
            ProductImage.objects.create(product=product, image=img)
        if not product.images.filter(is_primary=True).exists() and product.images.exists():
            first = product.images.first(); first.is_primary = True; first.save()
        for img_id in request.POST.getlist('delete_images'):
            ProductImage.objects.filter(pk=img_id, product=product).delete()
        for tier in tiers:
            price_val = request.POST.get(f'tier_price_{tier.pk}')
            if price_val:
                ProductTierPrice.objects.update_or_create(product=product, tier=tier, defaults={'price': price_val})
            else:
                ProductTierPrice.objects.filter(product=product, tier=tier).delete()
        product.related_products.set(request.POST.getlist('related_products'))
        messages.success(request, 'Product updated.')
        return redirect('panel_products')
    return render(request, 'panel/product_form.html', {
        'action': 'Edit', 'product': product, 'categories': categories,
        'tiers': tiers, 'tier_prices': tier_prices, 'all_products': all_products, 'countries': countries,
    })

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_product_delete(request, pk):
    get_object_or_404(Product, pk=pk).delete()
    messages.success(request, 'Product deleted.')
    return redirect('panel_products')


@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_products_import(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        import openpyxl
        from openpyxl.drawing.image import Image as XLImage
        import os
        from django.core.files.base import ContentFile
        
        excel_file = request.FILES['excel_file']
        try:
            wb = openpyxl.load_workbook(excel_file)
            ws = wb.active
            
            imported = 0
            errors = []
            
            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
                try:
                    name = row[0].value
                    sku = row[1].value
                    brand = row[2].value or ''
                    category_name = row[3].value
                    subcategory_name = row[4].value
                    origin_name = row[5].value
                    mrp = row[6].value
                    short_desc = row[7].value or ''
                    full_desc = row[8].value or ''
                    specs = row[9].value or ''
                    is_active = str(row[10].value or 'Yes').lower() in ['yes', 'true', '1']
                    is_featured = str(row[11].value or 'No').lower() in ['yes', 'true', '1']
                    
                    if not name or not sku or not mrp:
                        errors.append(f"Row {row_idx}: Missing required fields (Name, SKU, MRP)")
                        continue
                    
                    if Product.objects.filter(sku=sku).exists():
                        errors.append(f"Row {row_idx}: SKU '{sku}' already exists")
                        continue
                    
                    category = None
                    if category_name:
                        category = Category.objects.filter(name__iexact=category_name, is_active=True).first()
                        if not category:
                            errors.append(f"Row {row_idx}: Category '{category_name}' not found")
                            continue
                    
                    subcategory = None
                    if subcategory_name and category:
                        subcategory = SubCategory.objects.filter(name__iexact=subcategory_name, category=category, is_active=True).first()
                        if not subcategory:
                            errors.append(f"Row {row_idx}: Sub-category '{subcategory_name}' not found")
                            continue
                    
                    origin = None
                    if origin_name:
                        origin = Country.objects.filter(name__iexact=origin_name).first()
                        if not origin:
                            errors.append(f"Row {row_idx}: Country '{origin_name}' not found")
                            continue
                    
                    product = Product.objects.create(
                        name=name,
                        sku=sku,
                        brand=brand,
                        category=category,
                        sub_category=subcategory,
                        origin=origin,
                        mrp=float(mrp),
                        short_description=short_desc,
                        full_description=full_desc,
                        specifications=specs,
                        is_active=is_active,
                        is_featured=is_featured,
                    )
                    
                    image_cols = [12, 13, 14, 15]
                    for img_col_idx, col_idx in enumerate(image_cols):
                        if col_idx < len(row) and row[col_idx].value:
                            try:
                                image_path = row[col_idx].value
                                if isinstance(image_path, str) and os.path.exists(image_path):
                                    with open(image_path, 'rb') as img_file:
                                        filename = os.path.basename(image_path)
                                        ProductImage.objects.create(
                                            product=product,
                                            image=ContentFile(img_file.read(), name=filename),
                                            is_primary=(img_col_idx == 0),
                                            order=img_col_idx,
                                        )
                            except Exception as e:
                                errors.append(f"Row {row_idx}: Image upload failed - {str(e)}")
                    
                    imported += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_idx}: {str(e)}")
            
            if imported > 0:
                messages.success(request, f'Successfully imported {imported} products!')
            if errors:
                for error in errors[:10]:
                    messages.warning(request, error)
                if len(errors) > 10:
                    messages.warning(request, f'... and {len(errors) - 10} more errors')
            
            return redirect('panel_products')
        except Exception as e:
            messages.error(request, f'Excel import failed: {str(e)}')
    
    categories = Category.objects.filter(is_active=True).prefetch_related('subcategories')
    countries = Country.objects.all()
    tiers = CustomerTier.objects.filter(is_active=True)
    
    return render(request, 'panel/products_import.html', {
        'categories': categories,
        'countries': countries,
        'tiers': tiers,
    })


# ── Stock ─────────────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_stock(request, pk):
    product = get_object_or_404(Product, pk=pk)
    entries = product.stock_entries.select_related('customer').all()
    customers = Customer.objects.filter(is_active=True).select_related('tier')
    if request.method == 'POST':
        entry_type = request.POST['entry_type']
        qty = abs(int(request.POST['quantity_change']))
        if entry_type in ('sale', 'adjustment_out'):
            qty = -qty
        customer_id = request.POST.get('customer_id') or None
        if request.POST.get('new_customer_name') and not customer_id:
            new_c = Customer.objects.create(
                name=request.POST['new_customer_name'],
                email=request.POST.get('new_customer_email', f"guest_{Product.objects.count()}@guest.local"),
                phone=request.POST.get('new_customer_phone', ''),
            )
            customer_id = new_c.pk
        entry = StockEntry.objects.create(
            product=product, entry_type=entry_type, quantity_change=qty,
            note=request.POST.get('note', ''), customer_id=customer_id,
            unit_price=request.POST.get('unit_price') or None,
        )
        messages.success(request, 'Stock entry added.')
        return redirect(f"{request.path}?receipt={entry.pk}")
    receipt_entry = None
    receipt_id = request.GET.get('receipt')
    if receipt_id:
        receipt_entry = StockEntry.objects.filter(pk=receipt_id, product=product).select_related('customer__tier').first()
    return render(request, 'panel/stock.html', {
        'product': product, 'entries': entries,
        'customers': customers, 'receipt_entry': receipt_entry,
    })


# ── Services ──────────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_services(request):
    return render(request, 'panel/services.html', {
        'services': Service.objects.all(),
        'why_items': WhyChooseUs.objects.all(),
    })

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_service_add(request):
    if request.method == 'POST':
        Service.objects.create(
            title=request.POST['title'], description=request.POST['description'],
            icon=request.POST.get('icon', ''), order=request.POST.get('order', 0),
            is_active=request.POST.get('is_active') == 'on',
            image=request.FILES.get('image') or None,
        )
        messages.success(request, 'Service added.')
        return redirect('panel_services')
    return render(request, 'panel/service_form.html', {'action': 'Add'})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        service.title = request.POST['title']
        service.description = request.POST['description']
        service.icon = request.POST.get('icon', '')
        service.order = request.POST.get('order', 0)
        service.is_active = request.POST.get('is_active') == 'on'
        if 'image' in request.FILES:
            service.image = request.FILES['image']
        service.save()
        messages.success(request, 'Service updated.')
        return redirect('panel_services')
    return render(request, 'panel/service_form.html', {'action': 'Edit', 'service': service})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_service_delete(request, pk):
    get_object_or_404(Service, pk=pk).delete()
    messages.success(request, 'Service deleted.')
    return redirect('panel_services')


# ── Why Choose Us ─────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_why_add(request):
    if request.method == 'POST':
        WhyChooseUs.objects.create(
            title=request.POST['title'], description=request.POST['description'],
            icon=request.POST.get('icon', ''), order=request.POST.get('order', 0),
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Item added.')
        return redirect('panel_services')
    return render(request, 'panel/why_form.html', {'action': 'Add'})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_why_edit(request, pk):
    item = get_object_or_404(WhyChooseUs, pk=pk)
    if request.method == 'POST':
        item.title = request.POST['title']
        item.description = request.POST['description']
        item.icon = request.POST.get('icon', '')
        item.order = request.POST.get('order', 0)
        item.is_active = request.POST.get('is_active') == 'on'
        item.save()
        messages.success(request, 'Item updated.')
        return redirect('panel_services')
    return render(request, 'panel/why_form.html', {'action': 'Edit', 'item': item})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_why_delete(request, pk):
    get_object_or_404(WhyChooseUs, pk=pk).delete()
    messages.success(request, 'Item deleted.')
    return redirect('panel_services')


# ── About Page ────────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_about(request):
    return render(request, 'panel/about.html', {
        'stats': Stat.objects.all(),
        'trusted_clients': TrustedClient.objects.all(),
        'testimonials': Testimonial.objects.all(),
        'team': TeamMember.objects.all(),
    })

# Stats
@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_stat_save(request, pk=None):
    stat = get_object_or_404(Stat, pk=pk) if pk else None
    if request.method == 'POST':
        data = dict(value=request.POST['value'], label=request.POST['label'],
                    order=request.POST.get('order', 0), is_active=request.POST.get('is_active') == 'on')
        if stat:
            for k, v in data.items(): setattr(stat, k, v)
            stat.save()
        else:
            Stat.objects.create(**data)
        messages.success(request, 'Stat saved.')
        return redirect('panel_about')
    return render(request, 'panel/stat_form.html', {'action': 'Edit' if stat else 'Add', 'stat': stat})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_stat_delete(request, pk):
    get_object_or_404(Stat, pk=pk).delete()
    messages.success(request, 'Stat deleted.')
    return redirect('panel_about')

# Trusted Clients
@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_trusted_save(request, pk=None):
    obj = get_object_or_404(TrustedClient, pk=pk) if pk else None
    if request.method == 'POST':
        data = dict(name=request.POST['name'], icon=request.POST.get('icon', ''),
                    order=request.POST.get('order', 0), is_active=request.POST.get('is_active') == 'on')
        if obj:
            for k, v in data.items(): setattr(obj, k, v)
            if 'logo' in request.FILES: obj.logo = request.FILES['logo']
            obj.save()
        else:
            obj = TrustedClient.objects.create(**data)
            if 'logo' in request.FILES: obj.logo = request.FILES['logo']; obj.save()
        messages.success(request, 'Client saved.')
        return redirect('panel_about')
    return render(request, 'panel/trusted_form.html', {'action': 'Edit' if obj else 'Add', 'obj': obj})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_trusted_delete(request, pk):
    get_object_or_404(TrustedClient, pk=pk).delete()
    messages.success(request, 'Client deleted.')
    return redirect('panel_about')

# Testimonials
@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_testimonial_save(request, pk=None):
    obj = get_object_or_404(Testimonial, pk=pk) if pk else None
    if request.method == 'POST':
        data = dict(quote=request.POST['quote'], author_name=request.POST['author_name'],
                    author_role=request.POST.get('author_role', ''), initials=request.POST.get('initials', ''),
                    order=request.POST.get('order', 0), is_active=request.POST.get('is_active') == 'on')
        if obj:
            for k, v in data.items(): setattr(obj, k, v)
            if 'photo' in request.FILES: obj.photo = request.FILES['photo']
            obj.save()
        else:
            obj = Testimonial.objects.create(**data)
            if 'photo' in request.FILES: obj.photo = request.FILES['photo']; obj.save()
        messages.success(request, 'Testimonial saved.')
        return redirect('panel_about')
    return render(request, 'panel/testimonial_form.html', {'action': 'Edit' if obj else 'Add', 'obj': obj})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_testimonial_delete(request, pk):
    get_object_or_404(Testimonial, pk=pk).delete()
    messages.success(request, 'Testimonial deleted.')
    return redirect('panel_about')

# Team Members
@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_team_save(request, pk=None):
    obj = get_object_or_404(TeamMember, pk=pk) if pk else None
    if request.method == 'POST':
        data = dict(name=request.POST['name'], role=request.POST['role'],
                    phone=request.POST.get('phone', ''), bio=request.POST.get('bio', ''),
                    order=request.POST.get('order', 0), is_active=request.POST.get('is_active') == 'on')
        if obj:
            for k, v in data.items(): setattr(obj, k, v)
            if 'photo' in request.FILES: obj.photo = request.FILES['photo']
            obj.save()
        else:
            obj = TeamMember.objects.create(**data)
            if 'photo' in request.FILES: obj.photo = request.FILES['photo']; obj.save()
        messages.success(request, 'Team member saved.')
        return redirect('panel_about')
    return render(request, 'panel/team_form.html', {'action': 'Edit' if obj else 'Add', 'obj': obj})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_team_delete(request, pk):
    get_object_or_404(TeamMember, pk=pk).delete()
    messages.success(request, 'Team member deleted.')
    return redirect('panel_about')


# ── Contact Inquiries ─────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_inquiries(request):
    inquiries = ContactInquiry.objects.all()
    # mark as read when viewed
    inquiries.filter(is_read=False).update(is_read=True)
    return render(request, 'panel/inquiries.html', {'inquiries': inquiries})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_inquiry_delete(request, pk):
    get_object_or_404(ContactInquiry, pk=pk).delete()
    messages.success(request, 'Inquiry deleted.')
    return redirect('panel_inquiries')


# ── Quote Requests ────────────────────────────────────────────────────────────

from .models import QuoteRequest as QuoteRequestModel, QuotationRequest, QuotationRequestItem

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_quotes(request):
    quotations = QuotationRequest.objects.select_related('linked_customer__tier').prefetch_related('items__product__tier_prices__tier').all()
    tiers = CustomerTier.objects.filter(is_active=True)
    return render(request, 'panel/quotations.html', {'quotations': quotations, 'tiers': tiers})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_quote_update(request, pk):
    quotation = get_object_or_404(QuotationRequest, pk=pk)
    if request.method == 'POST':
        quotation.status = request.POST.get('status', quotation.status)
        quotation.admin_note = request.POST.get('admin_note', '')
        quotation.save()
        messages.success(request, 'Quotation updated.')
    return redirect('panel_quotes')

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_quote_create_customer(request, pk):
    quotation = get_object_or_404(QuotationRequest, pk=pk)
    tiers = CustomerTier.objects.filter(is_active=True)
    existing_customer = Customer.objects.filter(email=quotation.user_email).first()
    if request.method == 'POST':
        tier_id = request.POST.get('tier') or None
        if existing_customer:
            if tier_id:
                existing_customer.tier_id = tier_id
                existing_customer.save()
            messages.success(request, 'Customer tier updated.')
            customer = existing_customer
        else:
            customer = Customer.objects.create(
                name=quotation.user_name,
                email=quotation.user_email,
                phone=quotation.phone,
                tier_id=tier_id,
            )
            messages.success(request, f'Customer "{customer.name}" created.')
        quotation.linked_customer = customer
        quotation.status = 'responded'
        quotation.save()
        return redirect('panel_quotes')
    selected_tier = existing_customer.tier_id if existing_customer else None
    return render(request, 'panel/quote_create_customer.html', {
        'quotation': quotation,
        'tiers': tiers,
        'existing_customer': existing_customer,
        'selected_tier': selected_tier,
    })

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_quote_delete(request, pk):
    get_object_or_404(QuotationRequest, pk=pk).delete()
    messages.success(request, 'Quotation deleted.')
    return redirect('panel_quotes')


# ── Orders ────────────────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_orders(request):
    from django.core.paginator import Paginator
    orders_list = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')
    paginator = Paginator(orders_list, 20)
    page_number = request.GET.get('page', 1)
    orders = paginator.get_page(page_number)
    return render(request, 'panel/orders.html', {'orders': orders})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('user').prefetch_related('items__product'), pk=pk)
    if request.method == 'POST':
        old_status = order.status
        new_status = request.POST.get('status', order.status)
        order.status = new_status
        order.save()
        if old_status != new_status:
            send_order_status_update_email(order, old_status, new_status)
        if old_status != 'delivered' and new_status == 'delivered':
            for item in order.items.all():
                if item.product:
                    StockEntry.objects.create(
                        product=item.product,
                        entry_type='sale',
                        quantity_change=-item.quantity,
                        note=f'Order {order.order_number} delivered',
                    )
        messages.success(request, 'Order status updated.')
        return redirect('panel_order_detail', pk=pk)
    return render(request, 'panel/order_detail.html', {'order': order})

@login_required(login_url='panel_login')
@user_passes_test(is_superuser, login_url='panel_login')
def panel_order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order_number = order.order_number
    order.delete()
    messages.success(request, f'Order {order_number} deleted.')
    return redirect('panel_orders')

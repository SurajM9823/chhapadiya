from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import SiteSettings, CarouselSlide, Reel, Category, SubCategory, Country, CustomerTier, DeliveryTimeTier, Customer, Product, ProductImage, ProductTierPrice, Stat, TrustedClient, Testimonial, TeamMember, Service, WhyChooseUs, StockEntry, ContactInquiry, Order, OrderItem, CustomerUser, Role, Permission, Billing, BillingItem, Package, PackageItem
from .email_utils import send_order_status_update_email
from .permissions import permission_required, check_permission

def is_staff_user(user):
    return user.is_superuser or user.is_staff

def panel_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.role:
            return redirect('panel_dashboard')
        else:
            messages.error(request, f'Your account does not have a role assigned. Please contact administrator.')
            logout(request)
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user:
            if user.is_superuser or user.role:
                login(request, user)
                return redirect('panel_dashboard')
            else:
                messages.error(request, f'User "{username}" does not have a role assigned. Contact administrator.')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'panel/login.html')

def panel_logout(request):
    logout(request)
    return redirect('panel_login')

@login_required(login_url='panel_login')
def panel_dashboard(request):
    # Allow all authenticated users with a role to see dashboard
    if not (request.user.is_superuser or request.user.role):
        messages.error(request, 'Access denied. Role assignment required.')
        return redirect('panel_login')
    from django.db.models import Sum, Count, Q
    from datetime import timedelta
    from django.utils import timezone
    
    # Check permissions for different modules
    can_view_orders = request.user.is_superuser or check_permission(request.user, 'orders', 'view')
    can_view_customers = request.user.is_superuser or check_permission(request.user, 'customers', 'view')
    can_view_products = request.user.is_superuser or check_permission(request.user, 'products', 'view')
    can_view_content = request.user.is_superuser or check_permission(request.user, 'content', 'view')
    
    # Orders Statistics (only if user has permission)
    total_orders = 0
    pending_orders = 0
    delivered_orders = 0
    cancelled_orders = 0
    delivered_income = 0
    pending_income = 0
    total_income = 0
    pending_order_list = []
    sales_by_status = []
    
    if can_view_orders:
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status__in=['pending', 'confirmed', 'processing']).count()
        delivered_orders = Order.objects.filter(status='delivered').count()
        cancelled_orders = Order.objects.filter(status='cancelled').count()
        delivered_income = Order.objects.filter(status='delivered').aggregate(total=Sum('total'))['total'] or 0
        pending_income = Order.objects.filter(status__in=['pending', 'confirmed', 'processing']).aggregate(total=Sum('total'))['total'] or 0
        total_income = delivered_income
        pending_order_list = Order.objects.filter(status__in=['pending', 'confirmed', 'processing']).select_related('user').prefetch_related('items')[:5]
        sales_by_status = Order.objects.values('status').annotate(count=Count('id'), total=Sum('total')).order_by('-count')
    
    # Top Customers (only if user has permission)
    top_customers_list = []
    if can_view_customers and can_view_orders:
        from django.db.models import F
        top_customers = Order.objects.filter(status='delivered').values('user__email', 'user__first_name', 'user__last_name').annotate(
            total_spent=Sum('total'),
            order_count=Count('id')
        ).order_by('-total_spent')[:5]
        
        for cust in top_customers:
            top_customers_list.append({
                'email': cust['user__email'],
                'full_name': f"{cust['user__first_name']} {cust['user__last_name']}".strip() or cust['user__email'],
                'total_spent': cust['total_spent'],
                'order_count': cust['order_count']
            })
    
    # Low Stock Products (only if user has permission)
    low_stock_products = []
    total_products = 0
    low_stock_count = 0
    out_of_stock_count = 0
    
    if can_view_products:
        total_products = Product.objects.count()
        for product in Product.objects.all():
            stock = product.stock_quantity
            if stock < 10:
                if len(low_stock_products) < 5:
                    low_stock_products.append({
                        'name': product.name,
                        'sku': product.sku,
                        'stock': stock,
                        'mrp': product.mrp
                    })
            if stock < 10:
                low_stock_count += 1
            if stock == 0:
                out_of_stock_count += 1
    
    # Recent Inquiries (only if user has permission)
    recent_inquiries = []
    total_inquiries = 0
    unread_inquiries = 0
    
    if can_view_content:
        recent_inquiries = ContactInquiry.objects.all()[:5]
        total_inquiries = ContactInquiry.objects.count()
        unread_inquiries = ContactInquiry.objects.filter(is_read=False).count()
    
    # Visitor Data (mock data - available to all)
    visitor_data = []
    for i in range(6, -1, -1):
        date = timezone.now() - timedelta(days=i)
        visitor_data.append({
            'date': date.strftime('%a'),
            'count': (i * 15 + 20) if i > 0 else 45
        })
    
    # Site Visitors (mock data - available to all)
    total_visitors = 1250
    mobile_users = 750
    desktop_users = 500
    
    context = {
        'can_view_orders': can_view_orders,
        'can_view_customers': can_view_customers,
        'can_view_products': can_view_products,
        'can_view_content': can_view_content,
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



# â”€â”€ Site Settings â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('settings', 'view')
def panel_settings(request):
    s = SiteSettings.get()
    
    # Check if user can edit when trying to save
    if request.method == 'POST':
        if not (request.user.is_superuser or check_permission(request.user, 'settings', 'edit')):
            messages.error(request, 'You do not have permission to edit settings.')
            return redirect('panel_settings')
        
        s.business_name = request.POST.get('business_name', '')
        s.tagline = request.POST.get('tagline', '')
        s.email = request.POST.get('email', '')
        s.phone = request.POST.get('phone', '')
        s.phone2 = request.POST.get('phone2', '')
        s.address = request.POST.get('address', '')
        s.facebook = request.POST.get('facebook', '')
        s.instagram = request.POST.get('instagram', '')
        s.youtube = request.POST.get('youtube', '')
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
    
    # Pass permission info to template
    can_edit = request.user.is_superuser or check_permission(request.user, 'settings', 'edit')
    return render(request, 'panel/settings.html', {'settings': s, 'can_edit': can_edit})


# â”€â”€ Carousel â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_carousel(request):
    slides = CarouselSlide.objects.all().order_by('order')
    
    can_create = request.user.is_superuser or check_permission(request.user, 'content', 'create')
    can_edit = request.user.is_superuser or check_permission(request.user, 'content', 'edit')
    can_delete = request.user.is_superuser or check_permission(request.user, 'content', 'delete')
    
    return render(request, 'panel/carousel.html', {
        'slides': slides,
        'can_create': can_create,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_carousel_add(request):
    # Check create permission
    if not (request.user.is_superuser or check_permission(request.user, 'content', 'create')):
        messages.error(request, 'You do not have permission to create carousel slides.')
        return redirect('panel_carousel')
    if request.method == 'POST':
        CarouselSlide.objects.create(
            title=request.POST['title'], image=request.FILES['image'],
            order=request.POST.get('order', 0), is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Slide added.')
        return redirect('panel_carousel')
    return render(request, 'panel/carousel_form.html', {'action': 'Add'})

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_carousel_edit(request, pk):
    slide = get_object_or_404(CarouselSlide, pk=pk)
    
    # Check edit permission when saving
    if request.method == 'POST':
        if not (request.user.is_superuser or check_permission(request.user, 'content', 'edit')):
            messages.error(request, 'You do not have permission to edit carousel slides.')
            return redirect('panel_carousel')
        slide.title = request.POST['title']
        slide.order = request.POST.get('order', 0)
        slide.is_active = request.POST.get('is_active') == 'on'
        if 'image' in request.FILES:
            slide.image = request.FILES['image']
        slide.save()
        messages.success(request, 'Slide updated.')
        return redirect('panel_carousel')
    
    can_edit = request.user.is_superuser or check_permission(request.user, 'content', 'edit')
    return render(request, 'panel/carousel_form.html', {'action': 'Edit', 'slide': slide, 'can_edit': can_edit})

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_carousel_delete(request, pk):
    # Check delete permission
    if not (request.user.is_superuser or check_permission(request.user, 'content', 'delete')):
        messages.error(request, 'You do not have permission to delete carousel slides.')
        return redirect('panel_carousel')
    
    get_object_or_404(CarouselSlide, pk=pk).delete()
    messages.success(request, 'Slide deleted.')
    return redirect('panel_carousel')


# â”€â”€ Reels â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_reels(request):
    from django.core.paginator import Paginator
    reels_list = Reel.objects.all()
    paginator = Paginator(reels_list, 10)
    page_number = request.GET.get('page', 1)
    reels = paginator.get_page(page_number)
    
    can_create = request.user.is_superuser or check_permission(request.user, 'content', 'create')
    can_edit = request.user.is_superuser or check_permission(request.user, 'content', 'edit')
    can_delete = request.user.is_superuser or check_permission(request.user, 'content', 'delete')
    
    return render(request, 'panel/reels.html', {
        'reels': reels,
        'can_create': can_create,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_reel_add(request):
    # Check create permission
    if not (request.user.is_superuser or check_permission(request.user, 'content', 'create')):
        messages.error(request, 'You do not have permission to create reels.')
        return redirect('panel_reels')
    if request.method == 'POST':
        video_type = request.POST.get('video_type', 'upload')
        data = {
            'title': request.POST['title'],
            'video_type': video_type,
            'order': request.POST.get('order', 0),
            'is_active': request.POST.get('is_active') == 'on',
        }
        if video_type == 'upload' and 'video' in request.FILES:
            data['video'] = request.FILES['video']
        elif video_type == 'youtube':
            data['youtube_url'] = request.POST.get('youtube_url', '')
        elif video_type == 'tiktok':
            data['tiktok_url'] = request.POST.get('tiktok_url', '')
        
        if 'thumbnail' in request.FILES:
            data['thumbnail'] = request.FILES['thumbnail']
        
        Reel.objects.create(**data)
        messages.success(request, 'Reel added.')
        return redirect('panel_reels')
    return render(request, 'panel/reel_form.html', {'action': 'Add'})

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_reel_edit(request, pk):
    reel = get_object_or_404(Reel, pk=pk)
    
    # Check edit permission when saving
    if request.method == 'POST':
        if not (request.user.is_superuser or check_permission(request.user, 'content', 'edit')):
            messages.error(request, 'You do not have permission to edit reels.')
            return redirect('panel_reels')
        reel.title = request.POST['title']
        reel.video_type = request.POST.get('video_type', 'upload')
        reel.order = request.POST.get('order', 0)
        reel.is_active = request.POST.get('is_active') == 'on'
        
        if reel.video_type == 'upload' and 'video' in request.FILES:
            reel.video = request.FILES['video']
        elif reel.video_type == 'youtube':
            reel.youtube_url = request.POST.get('youtube_url', '')
            reel.video = None
        elif reel.video_type == 'tiktok':
            reel.tiktok_url = request.POST.get('tiktok_url', '')
            reel.video = None
        
        if 'thumbnail' in request.FILES:
            reel.thumbnail = request.FILES['thumbnail']
        
        reel.save()
        messages.success(request, 'Reel updated.')
        return redirect('panel_reels')
    
    can_edit = request.user.is_superuser or check_permission(request.user, 'content', 'edit')
    return render(request, 'panel/reel_form.html', {'action': 'Edit', 'reel': reel, 'can_edit': can_edit})

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_reel_delete(request, pk):
    # Check delete permission
    if not (request.user.is_superuser or check_permission(request.user, 'content', 'delete')):
        messages.error(request, 'You do not have permission to delete reels.')
        return redirect('panel_reels')
    
    get_object_or_404(Reel, pk=pk).delete()
    messages.success(request, 'Reel deleted.')
    return redirect('panel_reels')


# â”€â”€ Categories â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_categories(request):
    categories = Category.objects.prefetch_related('subcategories').all()
    
    can_create = request.user.is_superuser or check_permission(request.user, 'content', 'create')
    can_edit = request.user.is_superuser or check_permission(request.user, 'content', 'edit')
    can_delete = request.user.is_superuser or check_permission(request.user, 'content', 'delete')
    
    return render(request, 'panel/categories.html', {
        'categories': categories,
        'can_create': can_create,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_category_add(request):
    # Check create permission
    if not (request.user.is_superuser or check_permission(request.user, 'content', 'create')):
        messages.error(request, 'You do not have permission to create categories.')
        return redirect('panel_categories')
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
@permission_required('content', 'view')
def panel_category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    # Check edit permission when saving
    if request.method == 'POST':
        if not (request.user.is_superuser or check_permission(request.user, 'content', 'edit')):
            messages.error(request, 'You do not have permission to edit categories.')
            return redirect('panel_categories')
        category.name = request.POST['name']
        category.link = request.POST.get('link', '/')
        category.order = request.POST.get('order', 0)
        category.is_active = request.POST.get('is_active') == 'on'
        if 'icon' in request.FILES:
            category.icon = request.FILES['icon']
        category.save()
        messages.success(request, 'Category updated.')
        return redirect('panel_categories')
    
    can_edit = request.user.is_superuser or check_permission(request.user, 'content', 'edit')
    return render(request, 'panel/category_form.html', {'action': 'Edit', 'category': category, 'can_edit': can_edit})

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_category_delete(request, pk):
    # Check delete permission
    if not (request.user.is_superuser or check_permission(request.user, 'content', 'delete')):
        messages.error(request, 'You do not have permission to delete categories.')
        return redirect('panel_categories')
    
    get_object_or_404(Category, pk=pk).delete()
    messages.success(request, 'Category deleted.')
    return redirect('panel_categories')


# â”€â”€ Sub Categories â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_subcategories(request, cat_pk):
    category = get_object_or_404(Category, pk=cat_pk)
    return render(request, 'panel/subcategories.html', {'category': category, 'subs': category.subcategories.all()})

@login_required(login_url='panel_login')
@permission_required('content', 'create')
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
@permission_required('content', 'edit')
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
@permission_required('content', 'delete')
def panel_subcategory_delete(request, cat_pk, pk):
    get_object_or_404(SubCategory, pk=pk, category_id=cat_pk).delete()
    messages.success(request, 'Sub-category deleted.')
    return redirect('panel_subcategories', cat_pk=cat_pk)


# â”€â”€ Product Detail â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('products', 'view')
def panel_product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('category', 'sub_category', 'linked_package').prefetch_related('images', 'tier_prices__tier', 'related_products', 'linked_package__items__product'), pk=pk)
    return render(request, 'panel/product_detail.html', {'product': product})


# â”€â”€ Countries â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('products', 'view')
def panel_countries(request):
    return render(request, 'panel/countries.html', {'countries': Country.objects.all()})

@login_required(login_url='panel_login')
@permission_required('products', 'edit')
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
@permission_required('products', 'delete')
def panel_country_delete(request, pk):
    get_object_or_404(Country, pk=pk).delete()
    messages.success(request, 'Country deleted.')
    return redirect('panel_countries')


# â”€â”€ Customer Tiers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('customers', 'view')
def panel_tiers(request):
    can_create = request.user.is_superuser or check_permission(request.user, 'customers', 'create')
    can_edit = request.user.is_superuser or check_permission(request.user, 'customers', 'edit')
    can_delete = request.user.is_superuser or check_permission(request.user, 'customers', 'delete')
    
    return render(request, 'panel/tiers.html', {
        'tiers': CustomerTier.objects.all(),
        'can_create': can_create,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })

@login_required(login_url='panel_login')
@permission_required('customers', 'create')
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
@permission_required('customers', 'edit')
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
@permission_required('customers', 'delete')
def panel_tier_delete(request, pk):
    get_object_or_404(CustomerTier, pk=pk).delete()
    messages.success(request, 'Tier deleted.')
    return redirect('panel_tiers')


# ── Delivery Time Tiers ──────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@permission_required('settings', 'view')
def panel_delivery_times(request):
    can_create = request.user.is_superuser or check_permission(request.user, 'settings', 'create')
    can_edit = request.user.is_superuser or check_permission(request.user, 'settings', 'edit')
    can_delete = request.user.is_superuser or check_permission(request.user, 'settings', 'delete')
    
    return render(request, 'panel/delivery_times.html', {
        'delivery_times': DeliveryTimeTier.objects.all(),
        'can_create': can_create,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })

@login_required(login_url='panel_login')
@permission_required('settings', 'create')
def panel_delivery_time_add(request):
    if request.method == 'POST':
        DeliveryTimeTier.objects.create(
            name=request.POST['name'],
            min_time=request.POST['min_time'],
            min_unit=request.POST['min_unit'],
            max_time=request.POST['max_time'],
            max_unit=request.POST['max_unit'],
            description=request.POST.get('description', ''),
            order=request.POST.get('order', 0),
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Delivery time tier added.')
        return redirect('panel_delivery_times')
    return render(request, 'panel/delivery_time_form.html', {'action': 'Add'})

@login_required(login_url='panel_login')
@permission_required('settings', 'edit')
def panel_delivery_time_edit(request, pk):
    delivery_time = get_object_or_404(DeliveryTimeTier, pk=pk)
    if request.method == 'POST':
        delivery_time.name = request.POST['name']
        delivery_time.min_time = request.POST['min_time']
        delivery_time.min_unit = request.POST['min_unit']
        delivery_time.max_time = request.POST['max_time']
        delivery_time.max_unit = request.POST['max_unit']
        delivery_time.description = request.POST.get('description', '')
        delivery_time.order = request.POST.get('order', 0)
        delivery_time.is_active = request.POST.get('is_active') == 'on'
        delivery_time.save()
        messages.success(request, 'Delivery time tier updated.')
        return redirect('panel_delivery_times')
    return render(request, 'panel/delivery_time_form.html', {'action': 'Edit', 'delivery_time': delivery_time})

@login_required(login_url='panel_login')
@permission_required('settings', 'delete')
def panel_delivery_time_delete(request, pk):
    get_object_or_404(DeliveryTimeTier, pk=pk).delete()
    messages.success(request, 'Delivery time tier deleted.')
    return redirect('panel_delivery_times')


# â”€â”€ Customers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('customers', 'view')
def panel_customers(request):
    can_create = request.user.is_superuser or check_permission(request.user, 'customers', 'create')
    can_edit = request.user.is_superuser or check_permission(request.user, 'customers', 'edit')
    can_delete = request.user.is_superuser or check_permission(request.user, 'customers', 'delete')
    
    return render(request, 'panel/customers.html', {
        'customers': Customer.objects.select_related('tier').all(),
        'can_create': can_create,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })

@login_required(login_url='panel_login')
@permission_required('customers', 'create')
def panel_customer_add(request):
    tiers = CustomerTier.objects.filter(is_active=True)
    if request.method == 'POST':
        Customer.objects.create(
            name=request.POST['name'], email=request.POST['email'],
            phone=request.POST.get('phone', ''), 
            pan_number=request.POST.get('pan_number', '').upper(),
            company=request.POST.get('company', ''),
            address=request.POST.get('address', ''),
            tier_id=request.POST.get('tier') or None,
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Customer added.')
        return redirect('panel_customers')
    return render(request, 'panel/customer_form.html', {'action': 'Add', 'tiers': tiers})

@login_required(login_url='panel_login')
@permission_required('customers', 'edit')
def panel_customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    tiers = CustomerTier.objects.filter(is_active=True)
    if request.method == 'POST':
        customer.name = request.POST['name']
        customer.email = request.POST['email']
        customer.phone = request.POST.get('phone', '')
        customer.pan_number = request.POST.get('pan_number', '').upper()
        customer.company = request.POST.get('company', '')
        customer.address = request.POST.get('address', '')
        customer.tier_id = request.POST.get('tier') or None
        customer.is_active = request.POST.get('is_active') == 'on'
        customer.save()
        messages.success(request, 'Customer updated.')
        return redirect('panel_customers')
    return render(request, 'panel/customer_form.html', {'action': 'Edit', 'customer': customer, 'tiers': tiers})

@login_required(login_url='panel_login')
@permission_required('customers', 'delete')
def panel_customer_delete(request, pk):
    get_object_or_404(Customer, pk=pk).delete()
    messages.success(request, 'Customer deleted.')
    return redirect('panel_customers')


# â”€â”€ Products â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('products', 'view')
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
    
    can_create = request.user.is_superuser or check_permission(request.user, 'products', 'create')
    can_edit = request.user.is_superuser or check_permission(request.user, 'products', 'edit')
    can_delete = request.user.is_superuser or check_permission(request.user, 'products', 'delete')
    can_export = request.user.is_superuser or check_permission(request.user, 'products', 'view')
    
    return render(request, 'panel/products.html', {
        'products': products,
        'categories': list(categories),
        'search': search,
        'category_id': category_id,
        'status': status,
        'limit': limit,
        'total_count': paginator.count,
        'can_create': can_create,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'can_export': can_export,
    })

@login_required(login_url='panel_login')
@permission_required('products', 'create')
def panel_product_add(request):
    categories = Category.objects.prefetch_related('subcategories').filter(is_active=True)
    tiers = CustomerTier.objects.filter(is_active=True)
    all_products = Product.objects.all()
    countries = Country.objects.all()
    delivery_times = DeliveryTimeTier.objects.filter(is_active=True)
    packages = Package.objects.filter(is_active=True)
    if request.method == 'POST':
        product = Product.objects.create(
            name=request.POST['name'], sku=request.POST['sku'],
            product_code=request.POST.get('product_code', ''),
            brand=request.POST.get('brand', ''), origin_id=request.POST.get('origin') or None,
            category_id=request.POST.get('category') or None,
            sub_category_id=request.POST.get('sub_category') or None,
            short_description=request.POST.get('short_description', ''),
            full_description=request.POST.get('full_description', ''),
            specifications=request.POST.get('specifications', ''),
            mrp=request.POST['mrp'],
            tax_included=request.POST.get('tax_included') == 'on',
            tax_percent=request.POST.get('tax_percent') or 0,
            delivery_time_id=request.POST.get('delivery_time') or None,
            linked_package_id=request.POST.get('linked_package') or None,
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
        'all_products': all_products, 'countries': countries, 'delivery_times': delivery_times, 'packages': packages,
    })

@login_required(login_url='panel_login')
@permission_required('products', 'edit')
def panel_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.prefetch_related('subcategories').filter(is_active=True)
    tiers = CustomerTier.objects.filter(is_active=True)
    all_products = Product.objects.exclude(pk=pk)
    countries = Country.objects.all()
    delivery_times = DeliveryTimeTier.objects.filter(is_active=True)
    packages = Package.objects.filter(is_active=True)
    tier_prices = {tp.tier_id: tp.price for tp in product.tier_prices.all()}
    if request.method == 'POST':
        product.name = request.POST['name']
        product.sku = request.POST['sku']
        product.product_code = request.POST.get('product_code', '')
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
        product.delivery_time_id = request.POST.get('delivery_time') or None
        product.linked_package_id = request.POST.get('linked_package') or None
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
        'tiers': tiers, 'tier_prices': tier_prices, 'all_products': all_products, 'countries': countries, 'delivery_times': delivery_times, 'packages': packages,
    })

@login_required(login_url='panel_login')
@permission_required('products', 'delete')
def panel_product_delete(request, pk):
    get_object_or_404(Product, pk=pk).delete()
    messages.success(request, 'Product deleted.')
    return redirect('panel_products')


@login_required(login_url='panel_login')
@permission_required('products', 'view')
def panel_products_export(request):
    from django.http import HttpResponse
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    from django.db.models import Q
    
    # Get filter parameters
    search = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', '').strip()
    status = request.GET.get('status', '').strip()
    
    qs = Product.objects.select_related('category', 'sub_category', 'origin', 'delivery_time', 'linked_package').prefetch_related('tier_prices__tier', 'images').all()
    
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
    
    qs = qs.order_by('name')
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Products'
    
    # Styles
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF', size=11)
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    border = Border(
        left=Side(style='thin', color='D0D0D0'),
        right=Side(style='thin', color='D0D0D0'),
        top=Side(style='thin', color='D0D0D0'),
        bottom=Side(style='thin', color='D0D0D0')
    )
    
    # Headers
    headers = [
        'SKU', 'Product Code', 'Name', 'Brand', 'Category', 'Sub-Category', 
        'Origin Country', 'MRP (Rs.)', 'Tax Included', 'Tax %', 
        'Stock Quantity', 'Delivery Time', 'Linked Package',
        'Short Description', 'Full Description', 'Specifications',
        'Status', 'Featured', 'Primary Image URL', 'All Image URLs',
        'Tier Prices', 'Created Date', 'Updated Date'
    ]
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border
    
    # Freeze header row
    ws.freeze_panes = 'A2'
    
    # Data rows
    for row_num, product in enumerate(qs, 2):
        # Basic Info
        ws.cell(row=row_num, column=1, value=product.sku)
        ws.cell(row=row_num, column=2, value=product.product_code)
        ws.cell(row=row_num, column=3, value=product.name)
        ws.cell(row=row_num, column=4, value=product.brand)
        ws.cell(row=row_num, column=5, value=product.category.name if product.category else '')
        ws.cell(row=row_num, column=6, value=product.sub_category.name if product.sub_category else '')
        ws.cell(row=row_num, column=7, value=product.origin.name if product.origin else '')
        
        # Pricing
        ws.cell(row=row_num, column=8, value=float(product.mrp))
        ws.cell(row=row_num, column=9, value='Yes' if product.tax_included else 'No')
        ws.cell(row=row_num, column=10, value=float(product.tax_percent))
        
        # Stock & Delivery
        ws.cell(row=row_num, column=11, value=product.stock_quantity)
        ws.cell(row=row_num, column=12, value=str(product.delivery_time) if product.delivery_time else '')
        ws.cell(row=row_num, column=13, value=product.linked_package.name if product.linked_package else '')
        
        # Descriptions
        ws.cell(row=row_num, column=14, value=product.short_description)
        ws.cell(row=row_num, column=15, value=product.full_description)
        ws.cell(row=row_num, column=16, value=product.specifications)
        
        # Status
        ws.cell(row=row_num, column=17, value='Active' if product.is_active else 'Inactive')
        ws.cell(row=row_num, column=18, value='Yes' if product.is_featured else 'No')
        
        # Images
        primary_img = product.primary_image
        if primary_img:
            ws.cell(row=row_num, column=19, value=request.build_absolute_uri(primary_img.image.url))
        
        all_images = product.images.all()
        if all_images:
            image_urls = ', '.join([request.build_absolute_uri(img.image.url) for img in all_images])
            ws.cell(row=row_num, column=20, value=image_urls)
        
        # Tier Prices
        tier_prices = product.tier_prices.all()
        if tier_prices:
            tier_price_text = ', '.join([f"{tp.tier.name}: Rs.{tp.price}" for tp in tier_prices])
            ws.cell(row=row_num, column=21, value=tier_price_text)
        
        # Dates
        ws.cell(row=row_num, column=22, value=product.created_at.strftime('%Y-%m-%d %H:%M:%S'))
        ws.cell(row=row_num, column=23, value=product.updated_at.strftime('%Y-%m-%d %H:%M:%S'))
        
        # Apply borders to all cells in row
        for col in range(1, len(headers) + 1):
            ws.cell(row=row_num, column=col).border = border
            ws.cell(row=row_num, column=col).alignment = Alignment(vertical='top', wrap_text=True)
    
    # Adjust column widths
    column_widths = {
        'A': 15,  # SKU
        'B': 15,  # Product Code
        'C': 40,  # Name
        'D': 20,  # Brand
        'E': 20,  # Category
        'F': 20,  # Sub-Category
        'G': 15,  # Origin
        'H': 12,  # MRP
        'I': 12,  # Tax Included
        'J': 10,  # Tax %
        'K': 12,  # Stock
        'L': 25,  # Delivery Time
        'M': 25,  # Linked Package
        'N': 50,  # Short Description
        'O': 60,  # Full Description
        'P': 50,  # Specifications
        'Q': 12,  # Status
        'R': 12,  # Featured
        'S': 60,  # Primary Image
        'T': 80,  # All Images
        'U': 40,  # Tier Prices
        'V': 20,  # Created Date
        'W': 20,  # Updated Date
    }
    
    for col, width in column_widths.items():
        ws.column_dimensions[col].width = width
    
    # Set row height for header
    ws.row_dimensions[1].height = 30
    
    # Create response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=products_detailed_export.xlsx'
    wb.save(response)
    
    return response


@login_required(login_url='panel_login')
@permission_required('products', 'create')
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


# â”€â”€ Stock â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('stock', 'edit')
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


# â”€â”€ Services â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_services(request):
    can_create = request.user.is_superuser or check_permission(request.user, 'content', 'create')
    can_edit = request.user.is_superuser or check_permission(request.user, 'content', 'edit')
    can_delete = request.user.is_superuser or check_permission(request.user, 'content', 'delete')
    
    return render(request, 'panel/services.html', {
        'services': Service.objects.all(),
        'why_items': WhyChooseUs.objects.all(),
        'can_create': can_create,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_service_add(request):
    # Check create permission
    if not (request.user.is_superuser or check_permission(request.user, 'content', 'create')):
        messages.error(request, 'You do not have permission to create services.')
        return redirect('panel_services')
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
@permission_required('content', 'view')
def panel_service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    
    # Check edit permission when saving
    if request.method == 'POST':
        if not (request.user.is_superuser or check_permission(request.user, 'content', 'edit')):
            messages.error(request, 'You do not have permission to edit services.')
            return redirect('panel_services')
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
    
    can_edit = request.user.is_superuser or check_permission(request.user, 'content', 'edit')
    return render(request, 'panel/service_form.html', {'action': 'Edit', 'service': service, 'can_edit': can_edit})

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_service_delete(request, pk):
    # Check delete permission
    if not (request.user.is_superuser or check_permission(request.user, 'content', 'delete')):
        messages.error(request, 'You do not have permission to delete services.')
        return redirect('panel_services')
    
    get_object_or_404(Service, pk=pk).delete()
    messages.success(request, 'Service deleted.')
    return redirect('panel_services')


# â”€â”€ Why Choose Us â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('content', 'create')
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
@permission_required('content', 'edit')
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
@permission_required('content', 'delete')
def panel_why_delete(request, pk):
    get_object_or_404(WhyChooseUs, pk=pk).delete()
    messages.success(request, 'Item deleted.')
    return redirect('panel_services')


# â”€â”€ About Page â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_about(request):
    can_create = request.user.is_superuser or check_permission(request.user, 'content', 'create')
    can_edit = request.user.is_superuser or check_permission(request.user, 'content', 'edit')
    can_delete = request.user.is_superuser or check_permission(request.user, 'content', 'delete')
    
    return render(request, 'panel/about.html', {
        'stats': Stat.objects.all(),
        'trusted_clients': TrustedClient.objects.all(),
        'testimonials': Testimonial.objects.all(),
        'team': TeamMember.objects.all(),
        'can_create': can_create,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })

# Stats
@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_stat_save(request, pk=None):
    stat = get_object_or_404(Stat, pk=pk) if pk else None
    
    # Check create/edit permission
    if request.method == 'POST':
        required_perm = 'edit' if stat else 'create'
        if not (request.user.is_superuser or check_permission(request.user, 'content', required_perm)):
            messages.error(request, f'You do not have permission to {required_perm} stats.')
            return redirect('panel_about')
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
@permission_required('content', 'view')
def panel_stat_delete(request, pk):
    # Check delete permission
    if not (request.user.is_superuser or check_permission(request.user, 'content', 'delete')):
        messages.error(request, 'You do not have permission to delete stats.')
        return redirect('panel_about')
    
    get_object_or_404(Stat, pk=pk).delete()
    messages.success(request, 'Stat deleted.')
    return redirect('panel_about')

# Trusted Clients
@login_required(login_url='panel_login')
@permission_required('content', 'edit')
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
@permission_required('content', 'view')
def panel_trusted_delete(request, pk):
    # Check delete permission
    if not (request.user.is_superuser or check_permission(request.user, 'content', 'delete')):
        messages.error(request, 'You do not have permission to delete clients.')
        return redirect('panel_about')
    
    get_object_or_404(TrustedClient, pk=pk).delete()
    messages.success(request, 'Client deleted.')
    return redirect('panel_about')

# Testimonials
@login_required(login_url='panel_login')
@permission_required('content', 'edit')
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
@permission_required('content', 'view')
def panel_testimonial_delete(request, pk):
    # Check delete permission
    if not (request.user.is_superuser or check_permission(request.user, 'content', 'delete')):
        messages.error(request, 'You do not have permission to delete testimonials.')
        return redirect('panel_about')
    
    get_object_or_404(Testimonial, pk=pk).delete()
    messages.success(request, 'Testimonial deleted.')
    return redirect('panel_about')

# Team Members
@login_required(login_url='panel_login')
@permission_required('content', 'edit')
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
@permission_required('content', 'view')
def panel_team_delete(request, pk):
    # Check delete permission
    if not (request.user.is_superuser or check_permission(request.user, 'content', 'delete')):
        messages.error(request, 'You do not have permission to delete team members.')
        return redirect('panel_about')
    
    get_object_or_404(TeamMember, pk=pk).delete()
    messages.success(request, 'Team member deleted.')
    return redirect('panel_about')


# â”€â”€ Contact Inquiries â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_inquiries(request):
    inquiries = ContactInquiry.objects.all()
    # mark as read when viewed
    inquiries.filter(is_read=False).update(is_read=True)
    
    can_delete = request.user.is_superuser or check_permission(request.user, 'content', 'delete')
    
    return render(request, 'panel/inquiries.html', {
        'inquiries': inquiries,
        'can_delete': can_delete,
    })

@login_required(login_url='panel_login')
@permission_required('content', 'view')
def panel_inquiry_delete(request, pk):
    # Check delete permission
    if not (request.user.is_superuser or check_permission(request.user, 'content', 'delete')):
        messages.error(request, 'You do not have permission to delete inquiries.')
        return redirect('panel_inquiries')
    
    get_object_or_404(ContactInquiry, pk=pk).delete()
    messages.success(request, 'Inquiry deleted.')
    return redirect('panel_inquiries')


# â”€â”€ Quote Requests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

from .models import QuoteRequest as QuoteRequestModel, QuotationRequest, QuotationRequestItem

@login_required(login_url='panel_login')
@permission_required('quotations', 'view')
def panel_quotes(request):
    quotations = QuotationRequest.objects.select_related('linked_customer__tier').prefetch_related('items__product__tier_prices__tier').all()
    tiers = CustomerTier.objects.filter(is_active=True)
    
    can_edit = request.user.is_superuser or check_permission(request.user, 'quotations', 'edit')
    can_delete = request.user.is_superuser or check_permission(request.user, 'quotations', 'delete')
    
    return render(request, 'panel/quotations.html', {
        'quotations': quotations,
        'tiers': tiers,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })

@login_required(login_url='panel_login')
@permission_required('quotations', 'edit')
def panel_quote_update(request, pk):
    quotation = get_object_or_404(QuotationRequest, pk=pk)
    if request.method == 'POST':
        quotation.status = request.POST.get('status', quotation.status)
        quotation.admin_note = request.POST.get('admin_note', '')
        quotation.save()
        messages.success(request, 'Quotation updated.')
    return redirect('panel_quotes')

@login_required(login_url='panel_login')
@permission_required('quotations', 'edit')
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
@permission_required('quotations', 'delete')
def panel_quote_delete(request, pk):
    get_object_or_404(QuotationRequest, pk=pk).delete()
    messages.success(request, 'Quotation deleted.')
    return redirect('panel_quotes')


# â”€â”€ Orders â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('orders', 'view')
def panel_orders(request):
    from django.core.paginator import Paginator
    orders_list = Order.objects.select_related('user', 'referred_agent').prefetch_related('items').order_by('-created_at')
    paginator = Paginator(orders_list, 20)
    page_number = request.GET.get('page', 1)
    orders = paginator.get_page(page_number)
    
    can_edit = request.user.is_superuser or check_permission(request.user, 'orders', 'edit')
    can_delete = request.user.is_superuser or check_permission(request.user, 'orders', 'delete')
    
    return render(request, 'panel/orders.html', {
        'orders': orders,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })

@login_required(login_url='panel_login')
@permission_required('orders', 'edit')
def panel_order_detail(request, pk):
    from .models import ProductReview, OrderPayment
    order = get_object_or_404(Order.objects.select_related('user', 'referred_agent').prefetch_related('items__product', 'payments').order_by('-created_at'), pk=pk)
    
    # Get billing records for this order
    from django.db.models import Sum
    order_billings = Billing.objects.filter(
        items__product__in=[item.product for item in order.items.all() if item.product]
    ).distinct()
    
    # Calculate total paid from billings linked to this order
    total_paid_amount = 0
    related_bills = []
    
    # Better approach: Check billings created after this order with matching items
    for billing in Billing.objects.filter(created_at__gte=order.created_at).order_by('created_at'):
        # Check if billing items match order items
        billing_product_ids = set(billing.items.values_list('product_id', flat=True))
        order_product_ids = set(order.items.values_list('product_id', flat=True))
        
        # If there's significant overlap, consider it related
        if billing_product_ids & order_product_ids:  # Intersection
            related_bills.append(billing)
            total_paid_amount += float(billing.amount_paid)
    
    # Add payments from OrderPayment model
    order_payments = order.payments.all()
    for payment in order_payments:
        total_paid_amount += float(payment.amount)
    
    # Recalculate and update payment status based on actual total paid
    order_total = float(order.total)
    if total_paid_amount >= order_total:
        if order.payment_status != 'paid':
            order.payment_status = 'paid'
            order.save()
    elif total_paid_amount > 0:
        if order.payment_status != 'partial':
            order.payment_status = 'partial'
            order.save()
    else:
        if order.payment_status != 'unpaid':
            order.payment_status = 'unpaid'
            order.save()
    
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
    
    # Get reviews for delivered orders
    items_with_reviews = []
    for item in order.items.all():
        review = None
        if item.product and order.status == 'delivered':
            review = ProductReview.objects.filter(product=item.product, user=order.user, order=order).first()
        items_with_reviews.append({'item': item, 'review': review})
    
    can_edit = request.user.is_superuser or check_permission(request.user, 'orders', 'edit')
    can_delete = request.user.is_superuser or check_permission(request.user, 'orders', 'delete')
    
    return render(request, 'panel/order_detail.html', {
        'order': order,
        'items_with_reviews': items_with_reviews,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'total_paid_amount': total_paid_amount,
        'remaining_amount': max(0, order_total - total_paid_amount),
        'related_bills': related_bills,
        'order_payments': order_payments,
    })

@login_required(login_url='panel_login')
@permission_required('orders', 'delete')
def panel_order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order_number = order.order_number
    order.delete()
    messages.success(request, f'Order {order_number} deleted.')
    return redirect('panel_orders')


@login_required(login_url='panel_login')
@permission_required('orders', 'edit')
def record_order_payment(request, pk):
    import json as _json
    from .models import OrderPayment
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    order = get_object_or_404(Order, pk=pk)
    
    try:
        data = _json.loads(request.body)
    except:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    amount = float(data.get('amount', 0))
    payment_method = data.get('payment_method', 'cash')
    note = data.get('note', '').strip()
    
    if amount <= 0:
        return JsonResponse({'error': 'Invalid amount'}, status=400)
    
    # Create payment record
    payment = OrderPayment.objects.create(
        order=order,
        amount=amount,
        payment_method=payment_method,
        note=note,
        recorded_by=request.user
    )
    
    # Calculate total paid from OrderPayment records
    from django.db.models import Sum
    total_paid_from_payments = order.payments.aggregate(total=Sum('amount'))['total'] or 0
    
    # Also check billings
    total_paid_from_billings = 0
    for billing in Billing.objects.filter(created_at__gte=order.created_at).order_by('created_at'):
        billing_product_ids = set(billing.items.values_list('product_id', flat=True))
        order_product_ids = set(order.items.values_list('product_id', flat=True))
        if billing_product_ids & order_product_ids:
            total_paid_from_billings += float(billing.amount_paid)
    
    total_paid = float(total_paid_from_payments) + float(total_paid_from_billings)
    
    # Update order payment status
    order_total = float(order.total)
    if total_paid >= order_total:
        order.payment_status = 'paid'
    elif total_paid > 0:
        order.payment_status = 'partial'
    else:
        order.payment_status = 'unpaid'
    order.save()
    
    return JsonResponse({
        'success': True,
        'payment_id': payment.pk,
        'total_paid': float(total_paid),
        'payment_status': order.payment_status
    })


# â”€â”€ User Management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@login_required(login_url='panel_login')
@permission_required('users', 'view')
def panel_users(request):
    from django.core.paginator import Paginator
    search = request.GET.get('search', '').strip()
    role_id = request.GET.get('role', '').strip()
    user_type = request.GET.get('user_type', '').strip()
    page = request.GET.get('page', 1)
    
    # Show all users (staff and non-staff) to see agents and customers
    qs = CustomerUser.objects.select_related('role').all()
    
    if search:
        qs = qs.filter(username__icontains=search) | qs.filter(email__icontains=search)
    
    if role_id:
        try:
            qs = qs.filter(role_id=int(role_id))
        except:
            pass
    
    if user_type:
        qs = qs.filter(user_type=user_type)
    
    qs = qs.order_by('-date_joined')
    
    paginator = Paginator(qs, 20)
    users = paginator.get_page(page)
    roles = Role.objects.all()
    
    can_create = request.user.is_superuser or check_permission(request.user, 'users', 'create')
    can_edit = request.user.is_superuser or check_permission(request.user, 'users', 'edit')
    can_delete = request.user.is_superuser or check_permission(request.user, 'users', 'delete')
    
    return render(request, 'panel/users.html', {
        'users': users,
        'roles': list(roles),
        'search': search,
        'role_id': role_id,
        'user_type': user_type,
        'total_count': paginator.count,
        'can_create': can_create,
        'can_edit': can_edit,
        'can_delete': can_delete,
    })

@login_required(login_url='panel_login')
@permission_required('users', 'create')
def panel_user_add(request):
    roles = Role.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        role_id = request.POST.get('role') or None
        is_staff = request.POST.get('is_staff') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        
        if not username or not email or not password:
            messages.error(request, 'Username, email, and password are required.')
            return render(request, 'panel/user_form.html', {'action': 'Add', 'roles': roles, 'user': None})
        
        if CustomerUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'panel/user_form.html', {'action': 'Add', 'roles': roles, 'user': None})
        
        if CustomerUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'panel/user_form.html', {'action': 'Add', 'roles': roles, 'user': None})
        
        user = CustomerUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role_id=role_id,
            is_staff=is_staff,
            is_active=is_active,
            is_superuser=False,  # Don't auto-make superuser
        )
        messages.success(request, f'User "{username}" created successfully.')
        return redirect('panel_users')
    
    return render(request, 'panel/user_form.html', {'action': 'Add', 'roles': roles, 'user': None})

@login_required(login_url='panel_login')
@permission_required('users', 'edit')
def panel_user_edit(request, pk):
    user = get_object_or_404(CustomerUser, pk=pk)
    roles = Role.objects.all()
    
    if request.method == 'POST':
        user.email = request.POST.get('email', user.email).strip()
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.phone = request.POST.get('phone', '').strip()
        user.role_id = request.POST.get('role') or None
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_active = request.POST.get('is_active') == 'on'
        user.is_superuser = False  # Don't auto-make superuser
        
        password = request.POST.get('password', '').strip()
        if password:
            user.set_password(password)
        
        user.save()
        messages.success(request, f'User "{user.username}" updated successfully.')
        return redirect('panel_users')
    
    return render(request, 'panel/user_form.html', {'action': 'Edit', 'user': user, 'roles': roles})

@login_required(login_url='panel_login')
@permission_required('users', 'delete')
def panel_user_delete(request, pk):
    user = get_object_or_404(CustomerUser, pk=pk)
    username = user.username
    user.delete()
    messages.success(request, f'User "{username}" deleted.')
    return redirect('panel_users')


@login_required(login_url='panel_login')
@permission_required('users', 'view')
def panel_roles(request):
    can_edit = request.user.is_superuser or check_permission(request.user, 'users', 'edit')
    
    roles = Role.objects.prefetch_related('permissions').all()
    return render(request, 'panel/roles.html', {
        'roles': roles,
        'can_edit': can_edit,
    })

@login_required(login_url='panel_login')
@permission_required('users', 'edit')
def panel_role_edit(request, pk):
    role = get_object_or_404(Role, pk=pk)
    permissions = role.permissions.all()
    all_modules = Permission.MODULE_CHOICES
    all_actions = Permission.ACTION_CHOICES
    
    if request.method == 'POST':
        role.description = request.POST.get('description', '')
        role.save()
        
        # Update permissions
        selected_perms = request.POST.getlist('permissions')
        role.permissions.all().delete()
        
        for perm_str in selected_perms:
            try:
                module, action = perm_str.split('|')
                Permission.objects.create(role=role, module=module, action=action)
            except:
                pass
        
        messages.success(request, f'Role "{role.get_name_display()}" updated.')
        return redirect('panel_roles')
    
    current_perms = set(f"{p.module}|{p.action}" for p in permissions)
    
    return render(request, 'panel/role_edit.html', {
        'role': role,
        'all_modules': all_modules,
        'all_actions': all_actions,
        'current_perms': current_perms,
    })


from django.http import JsonResponse


# ── POS Billing ───────────────────────────────────────────────────────────────

from .models import Billing, BillingItem

@login_required(login_url='panel_login')
@permission_required('orders', 'create')
def panel_billing(request):
    import json as _json
    from django.db.models import Sum, Count, Q
    from django.core.paginator import Paginator

    # Check if coming from order detail page
    order_id = request.GET.get('order_id')
    order_data = None
    if order_id:
        order = Order.objects.filter(pk=order_id).select_related('user').prefetch_related('items__product__images').first()
        if order:
            order_data = {
                'order_id': order.pk,
                'order_number': order.order_number,
                'customer_name': order.full_name,
                'customer_phone': order.phone,
                'customer_email': order.user.email if order.user else order.email,
                'is_package_order': order.is_package_order,
                'package_name': order.package_name if order.is_package_order else '',
                'total': float(order.total),
                'items': [{
                    'product_id': item.product_id,
                    'product_name': item.product_name,
                    'product_sku': item.product_sku,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'image': item.product.primary_image.image.url if item.product and item.product.primary_image else '',
                } for item in order.items.all()]
            }

    # ── POST: create a bill ──────────────────────────────────────────────────
    if request.method == 'POST':
        try:
            data = _json.loads(request.body)
        except Exception:
            return JsonResponse({'ok': False, 'error': 'Invalid JSON'})

        items_data = data.get('items', [])
        if not items_data:
            return JsonResponse({'ok': False, 'error': 'No items'})

        sale_type        = data.get('sale_type', 'counter')
        customer_id      = data.get('customer_id') or None
        walk_in_name     = data.get('walk_in_name', '').strip()
        walk_in_phone    = data.get('walk_in_phone', '').strip()
        agent_id         = data.get('agent_id') or None
        overall_discount = abs(float(data.get('overall_discount', 0)))
        payment_method   = data.get('payment_method', 'cash')
        amount_paid      = abs(float(data.get('amount_paid', 0)))
        split_payments   = data.get('split_payments')
        note             = data.get('note', '').strip()
        linked_order_id  = data.get('order_id') or None

        # Calculate payment amounts based on method
        cash_amount = 0
        card_amount = 0
        online_amount = 0
        
        if payment_method == 'split' and split_payments:
            for sp in split_payments:
                amt = abs(float(sp.get('amount', 0)))
                method = sp.get('method', 'cash')
                if method == 'cash':
                    cash_amount += amt
                elif method == 'card':
                    card_amount += amt
                elif method == 'upi':
                    online_amount += amt
        else:
            if payment_method == 'cash':
                cash_amount = amount_paid
            elif payment_method == 'card':
                card_amount = amount_paid
            elif payment_method == 'upi':
                online_amount = amount_paid

        subtotal = 0
        item_discount_total = 0
        bill_items = []

        for it in items_data:
            product = Product.objects.filter(pk=it.get('product_id'), is_active=True).first()
            if not product:
                return JsonResponse({'ok': False, 'error': f"Product {it.get('product_id')} not found"})
            qty      = max(1, int(it.get('qty', 1)))
            price    = float(it.get('unit_price', float(product.mrp)))
            discount = abs(float(it.get('discount', 0)))
            line_sub = price * qty
            subtotal += line_sub
            item_discount_total += discount
            bill_items.append({
                'product': product, 'qty': qty,
                'price': price, 'discount': discount,
            })

        total       = max(0, subtotal - item_discount_total - overall_discount)
        amount_paid = cash_amount + card_amount + online_amount
        if amount_paid >= total:
            pay_status = 'paid'
        elif amount_paid > 0:
            pay_status = 'partial'
        else:
            pay_status = 'unpaid'

        bill = Billing.objects.create(
            sale_type=sale_type,
            customer_id=customer_id,
            walk_in_name=walk_in_name,
            walk_in_phone=walk_in_phone,
            agent_id=agent_id,
            billed_by=request.user,
            subtotal=subtotal,
            item_discount=item_discount_total,
            overall_discount=overall_discount,
            total=total,
            cash_amount=cash_amount,
            card_amount=card_amount,
            online_amount=online_amount,
            amount_paid=amount_paid,
            payment_status=pay_status,
            note=note,
        )

        for it in bill_items:
            BillingItem.objects.create(
                billing=bill,
                product=it['product'],
                product_name=it['product'].name,
                product_sku=it['product'].sku,
                unit_price=it['price'],
                quantity=it['qty'],
                discount=it['discount'],
            )
            # deduct stock
            StockEntry.objects.create(
                product=it['product'],
                entry_type='sale',
                quantity_change=-it['qty'],
                unit_price=it['price'],
                note=f'POS Bill #{bill.bill_number}',
            )

        # Update order payment status if linked
        if linked_order_id:
            order = Order.objects.filter(pk=linked_order_id).first()
            if order:
                # Update payment status based on amount paid vs total
                if amount_paid >= order.total:
                    order.payment_status = 'paid'
                elif amount_paid > 0:
                    order.payment_status = 'partial'
                else:
                    order.payment_status = 'unpaid'
                order.save()

        return JsonResponse({'ok': True, 'bill_number': bill.bill_number, 'bill_id': bill.pk})

    # ── GET: render POS page ─────────────────────────────────────────────────
    # Products JSON for POS grid
    products_qs = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images', 'tier_prices__tier')
    products_data = []
    for p in products_qs:
        img = p.primary_image
        tier_prices = {tp.tier_id: float(tp.price) for tp in p.tier_prices.all()}
        products_data.append({
            'id': p.pk, 'name': p.name, 'sku': p.sku,
            'mrp': float(p.mrp),
            'stock': p.stock_quantity,
            'category': p.category.name if p.category else '',
            'category_id': p.category_id or 0,
            'image': img.image.url if img else '',
            'tier_prices': tier_prices,
        })

    customers_qs = Customer.objects.filter(is_active=True).select_related('tier')
    customers_data = [{
        'id': c.pk, 'name': c.name, 'phone': c.phone, 'email': c.email,
        'tier_id': c.tier_id, 'tier_name': c.tier.name if c.tier else '',
    } for c in customers_qs]

    agents_data = [{
        'id': a.pk,
        'name': (a.get_full_name() or a.username),
        'referral_code': a.referral_code or '',
    } for a in CustomerUser.objects.filter(user_type='agent', is_active=True)]

    categories = list(Category.objects.filter(is_active=True).values('id', 'name').order_by('name'))

    # ── Bills table (paginated, filtered) ────────────────────────────────────
    bills_qs = Billing.objects.select_related('customer', 'agent', 'billed_by').order_by('-created_at')

    f_search      = request.GET.get('search', '').strip()
    f_sale_type   = request.GET.get('sale_type', '').strip()
    f_pay_status  = request.GET.get('pay_status', '').strip()
    f_agent       = request.GET.get('agent', '').strip()
    f_date_from   = request.GET.get('date_from', '').strip()
    f_date_to     = request.GET.get('date_to', '').strip()
    page          = request.GET.get('page', 1)
    limit         = int(request.GET.get('limit', 20))

    if f_search:
        bills_qs = bills_qs.filter(
            Q(bill_number__icontains=f_search) |
            Q(walk_in_name__icontains=f_search) |
            Q(customer__name__icontains=f_search)
        )
    if f_sale_type:
        bills_qs = bills_qs.filter(sale_type=f_sale_type)
    if f_pay_status:
        bills_qs = bills_qs.filter(payment_status=f_pay_status)
    if f_agent:
        bills_qs = bills_qs.filter(agent_id=f_agent)
    if f_date_from:
        bills_qs = bills_qs.filter(created_at__date__gte=f_date_from)
    if f_date_to:
        bills_qs = bills_qs.filter(created_at__date__lte=f_date_to)

    paginator   = Paginator(bills_qs, limit)
    bills_page  = paginator.get_page(page)

    # ── Stats (unfiltered totals) ─────────────────────────────────────────────
    from decimal import Decimal
    stats = Billing.objects.aggregate(
        total_bills=Count('id'),
        total_revenue=Sum('total'),
        total_paid=Sum('amount_paid'),
    )
    
    # Calculate actual pending amount considering OrderPayments
    from .models import OrderPayment
    total_order_payments = OrderPayment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # Pending amount = Total Revenue - (Billing Payments + Order Payments)
    total_billed_paid = stats['total_paid'] or Decimal('0')
    total_revenue = stats['total_revenue'] or Decimal('0')
    actual_pending = total_revenue - total_billed_paid - total_order_payments

    return render(request, 'panel/billing.html', {
        'products_json':  _json.dumps(products_data),
        'customers_json': _json.dumps(customers_data),
        'agents_json':    _json.dumps(agents_data),
        'categories_json': _json.dumps(categories),
        'bills':          bills_page,
        'paginator':      paginator,
        'stats':          stats,
        'actual_pending': actual_pending,
        'f_search':       f_search,
        'f_sale_type':    f_sale_type,
        'f_pay_status':   f_pay_status,
        'f_agent':        f_agent,
        'f_date_from':    f_date_from,
        'f_date_to':      f_date_to,
        'limit':          limit,
        'order_data':     _json.dumps(order_data) if order_data else None,
    })


@login_required(login_url='panel_login')
@permission_required('orders', 'view')
def panel_billing_view(request, pk):
    bill = get_object_or_404(
        Billing.objects.select_related('customer', 'agent', 'billed_by').prefetch_related('items__product'),
        pk=pk
    )
    settings = SiteSettings.get()
    return render(request, 'panel/billing_invoice.html', {
        'bill': bill,
        'settings': settings,
    })


@login_required(login_url='panel_login')
@permission_required('orders', 'view')
def panel_billing_detail(request, pk):
    bill = get_object_or_404(
        Billing.objects.select_related('customer', 'agent', 'billed_by').prefetch_related('items__product'),
        pk=pk
    )
    return JsonResponse({
        'bill_number': bill.bill_number,
        'sale_type': bill.get_sale_type_display(),
        'customer': bill.customer.name if bill.customer else bill.walk_in_name or 'Walk-in',
        'phone': bill.customer.phone if bill.customer else bill.walk_in_phone,
        'agent': (bill.agent.get_full_name() or bill.agent.username) if bill.agent else '',
        'billed_by': (bill.billed_by.get_full_name() or bill.billed_by.username) if bill.billed_by else '',
        'subtotal': float(bill.subtotal),
        'item_discount': float(bill.item_discount),
        'overall_discount': float(bill.overall_discount),
        'total': float(bill.total),
        'cash_amount': float(bill.cash_amount),
        'card_amount': float(bill.card_amount),
        'online_amount': float(bill.online_amount),
        'amount_paid': float(bill.amount_paid),
        'balance_due': float(bill.balance_due),
        'payment_status': bill.payment_status,
        'note': bill.note,
        'created_at': bill.created_at.strftime('%d %b %Y, %H:%M'),
        'items': [{
            'name': i.product_name, 'sku': i.product_sku,
            'qty': i.quantity, 'unit_price': float(i.unit_price),
            'discount': float(i.discount), 'subtotal': float(i.subtotal),
        } for i in bill.items.all()],
    })


@login_required(login_url='panel_login')
@permission_required('orders', 'view')
def api_billing_products(request):
    """Search products for POS — returns JSON."""
    q = request.GET.get('q', '').strip()
    customer_id = request.GET.get('customer_id')
    tier_id = None
    if customer_id:
        c = Customer.objects.filter(pk=customer_id).select_related('tier').first()
        if c and c.tier_id:
            tier_id = c.tier_id

    qs = Product.objects.filter(is_active=True).prefetch_related('images', 'tier_prices__tier')
    if q:
        from django.db.models import Q as DQ
        qs = qs.filter(DQ(name__icontains=q) | DQ(sku__icontains=q))
    results = []
    for p in qs[:30]:
        img = p.primary_image
        price = float(p.mrp)
        if tier_id:
            tp = p.tier_prices.filter(tier_id=tier_id).first()
            if tp:
                price = float(tp.price)
        results.append({
            'id': p.pk, 'name': p.name, 'sku': p.sku,
            'price': price, 'mrp': float(p.mrp),
            'stock': p.stock_quantity,
            'image': img.image.url if img else '',
        })
    return JsonResponse({'results': results})


@login_required(login_url='panel_login')
@permission_required('orders', 'view')
def api_user_get(request, pk):
    user = get_object_or_404(CustomerUser, pk=pk)
    return JsonResponse({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': user.phone,
        'role_id': user.role_id,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
    })


@login_required(login_url='panel_login')
@permission_required('orders', 'view')
def api_customers(request):
    customers = Customer.objects.filter(is_active=True).select_related('tier')
    return JsonResponse([{
        'id': c.pk, 'name': c.name, 'phone': c.phone, 'email': c.email,
        'tier_id': c.tier_id, 'tier_name': c.tier.name if c.tier else '',
    } for c in customers], safe=False)


@login_required(login_url='panel_login')
@permission_required('customers', 'create')
def api_customer_create(request):
    import json as _json
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = _json.loads(request.body)
    except:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()
    pan_number = data.get('pan_number', '').strip().upper()
    
    if not name:
        return JsonResponse({'error': 'Name is required'}, status=400)
    
    # Check if customer already exists
    if email and Customer.objects.filter(email=email).exists():
        return JsonResponse({'error': 'Customer with this email already exists'}, status=400)
    
    customer = Customer.objects.create(
        name=name,
        phone=phone,
        email=email,
        pan_number=pan_number,
        is_active=True
    )
    
    return JsonResponse({
        'id': customer.pk,
        'name': customer.name,
        'phone': customer.phone,
        'email': customer.email,
        'pan_number': customer.pan_number
    })


@login_required(login_url='panel_login')
@permission_required('orders', 'view')
def api_agents(request):
    agents = CustomerUser.objects.filter(user_type='agent', is_active=True)
    return JsonResponse([{
        'id': a.pk, 'username': a.username,
        'name': a.get_full_name() or a.username,
    } for a in agents], safe=False)


@login_required(login_url='panel_login')
@permission_required('orders', 'view')
def api_billing_list(request):
    from django.db.models import Count, F, Value, Sum
    from django.db.models.functions import Coalesce
    from decimal import Decimal
    limit = int(request.GET.get('limit', 10))
    offset = int(request.GET.get('offset', 0))
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    sale_type = request.GET.get('sale_type', '').strip()
    payment_status = request.GET.get('payment_status', '').strip()
    agent_id = request.GET.get('agent', '').strip()
    
    qs = Billing.objects.select_related('customer', 'agent').prefetch_related('items')
    
    # Apply filters
    if start_date:
        qs = qs.filter(created_at__date__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__date__lte=end_date)
    if sale_type:
        qs = qs.filter(sale_type=sale_type)
    if payment_status:
        qs = qs.filter(payment_status=payment_status)
    if agent_id:
        qs = qs.filter(agent_id=agent_id)
    
    qs = qs.order_by('-created_at')
    count = qs.count()
    bills = qs[offset:offset+limit]
    
    # Calculate stats based on filtered queryset
    from decimal import Decimal
    from .models import OrderPayment
    filtered_bills = qs.all()
    total_bills = filtered_bills.count()
    total_revenue = sum(b.total for b in filtered_bills) or Decimal('0')
    
    # Calculate pending considering OrderPayments
    total_order_payments = OrderPayment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_billed_paid = sum(b.amount_paid for b in filtered_bills) or Decimal('0')
    pending_amount = total_revenue - total_billed_paid - total_order_payments
    
    total_discount = sum(b.overall_discount + b.item_discount for b in filtered_bills) or Decimal('0')
    
    return JsonResponse({
        'count': count,
        'results': [{
            'id': b.pk,
            'bill_number': b.bill_number,
            'created_at': b.created_at.isoformat(),
            'customer_name': b.customer.name if b.customer else b.walk_in_name or 'Walk-in',
            'sale_type': b.sale_type,
            'items_count': b.items.count(),
            'total': float(b.total),
            'amount_paid': float(b.amount_paid),
            'payment_status': b.payment_status,
        } for b in bills],
        'statistics': {
            'total_bills': total_bills,
            'total_revenue': float(total_revenue),
            'pending_amount': float(pending_amount),
            'total_discount': float(total_discount),
        }
    })


@login_required(login_url='panel_login')
@permission_required('orders', 'create')
def api_billing_create(request):
    import json as _json
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        data = _json.loads(request.body)
    except:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    items = data.get('items', [])
    if not items:
        return JsonResponse({'error': 'No items'}, status=400)
    
    customer_id = data.get('customer_id')
    walk_in_name = data.get('walk_in_name', '').strip()
    walk_in_phone = data.get('walk_in_phone', '').strip()
    sale_type = data.get('sale_type', 'counter')
    agent_id = data.get('agent_id')
    payment_method = data.get('payment_method', 'cash')
    payment_status = data.get('payment_status', 'paid')
    amount_paid = float(data.get('amount_paid', 0))
    overall_discount = float(data.get('overall_discount', 0))
    split_payments = data.get('split_payments')
    order_id = data.get('order_id')
    
    subtotal = 0
    item_discount_total = 0
    bill_items = []
    
    for item in items:
        product = Product.objects.filter(pk=item['product_id']).first()
        if not product:
            return JsonResponse({'error': f"Product {item['product_id']} not found"}, status=400)
        
        qty = int(item['quantity'])
        price = float(item['price'])
        discount_pct = float(item.get('discount', 0))
        
        line_total = price * qty
        line_discount = line_total * (discount_pct / 100)
        
        subtotal += line_total
        item_discount_total += line_discount
        
        bill_items.append({
            'product': product,
            'qty': qty,
            'price': price,
            'discount': line_discount,
        })
    
    overall_discount_amount = subtotal * (overall_discount / 100)
    total = subtotal - item_discount_total - overall_discount_amount
    
    cash_amount = 0
    card_amount = 0
    online_amount = 0
    
    if payment_method == 'split' and split_payments:
        for sp in split_payments:
            amt = float(sp['amount'])
            if sp['method'] == 'cash':
                cash_amount += amt
            elif sp['method'] == 'card':
                card_amount += amt
            elif sp['method'] == 'upi':
                online_amount += amt
    else:
        if payment_method == 'cash':
            cash_amount = amount_paid
        elif payment_method == 'card':
            card_amount = amount_paid
        elif payment_method == 'upi':
            online_amount = amount_paid
    
    total_paid = cash_amount + card_amount + online_amount
    
    bill = Billing.objects.create(
        sale_type=sale_type,
        customer_id=customer_id,
        walk_in_name=walk_in_name,
        walk_in_phone=walk_in_phone,
        agent_id=agent_id,
        billed_by=request.user,
        subtotal=subtotal,
        item_discount=item_discount_total,
        overall_discount=overall_discount_amount,
        total=total,
        cash_amount=cash_amount,
        card_amount=card_amount,
        online_amount=online_amount,
        amount_paid=total_paid,
        payment_status=payment_status,
    )
    
    for item in bill_items:
        BillingItem.objects.create(
            billing=bill,
            product=item['product'],
            product_name=item['product'].name,
            product_sku=item['product'].sku,
            unit_price=item['price'],
            quantity=item['qty'],
            discount=item['discount'],
        )
        StockEntry.objects.create(
            product=item['product'],
            entry_type='sale',
            quantity_change=-item['qty'],
            unit_price=item['price'],
            note=f'Bill #{bill.bill_number}',
        )
    
    # Update order payment status if linked
    if order_id:
        order = Order.objects.filter(pk=order_id).first()
        if order:
            # Calculate total paid from billings
            total_paid_from_billings = 0
            for billing in Billing.objects.filter(created_at__gte=order.created_at).order_by('created_at'):
                billing_product_ids = set(billing.items.values_list('product_id', flat=True))
                order_product_ids = set(order.items.values_list('product_id', flat=True))
                if billing_product_ids & order_product_ids:
                    total_paid_from_billings += float(billing.amount_paid)
            
            # Calculate total paid from OrderPayment records
            from django.db.models import Sum
            from .models import OrderPayment
            total_paid_from_payments = order.payments.aggregate(total=Sum('amount'))['total'] or 0
            
            total_paid_combined = float(total_paid_from_billings) + float(total_paid_from_payments)
            order_total = float(order.total)
            
            # Update payment status based on total paid vs order total
            if total_paid_combined >= order_total:
                order.payment_status = 'paid'
            elif total_paid_combined > 0:
                order.payment_status = 'partial'
            else:
                order.payment_status = 'unpaid'
            order.save()
    
    return JsonResponse({'bill_number': bill.bill_number, 'bill_id': bill.pk})




# ── Package Management ────────────────────────────────────────────────────────

@login_required(login_url='panel_login')
@permission_required('packages', 'view')
def panel_packages(request):
    packages = Package.objects.all().order_by('-created_at')
    return render(request, 'panel/packages.html', {'packages': packages})


@login_required(login_url='panel_login')
@permission_required('packages', 'create')
def panel_package_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        sku = request.POST.get('sku')
        description = request.POST.get('description', '')
        overall_discount = request.POST.get('overall_discount', 0)
        selling_price = request.POST.get('selling_price')
        
        package = Package.objects.create(
            name=name, sku=sku, description=description,
            overall_discount=overall_discount, selling_price=selling_price
        )
        
        # Add items
        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')
        item_discounts = request.POST.getlist('item_discount[]')
        
        for pid, qty, disc in zip(product_ids, quantities, item_discounts):
            if pid and qty:
                PackageItem.objects.create(
                    package=package,
                    product_id=pid,
                    quantity=int(qty),
                    item_discount=float(disc or 0)
                )
        
        messages.success(request, f'Package "{name}" created successfully!')
        return redirect('panel_packages')
    
    products = Product.objects.filter(is_active=True).order_by('name')
    return render(request, 'panel/package_form.html', {'products': products})


@login_required(login_url='panel_login')
@permission_required('packages', 'edit')
def panel_package_edit(request, pk):
    package = get_object_or_404(Package, pk=pk)
    
    if request.method == 'POST':
        package.name = request.POST.get('name')
        package.sku = request.POST.get('sku')
        package.description = request.POST.get('description', '')
        package.overall_discount = request.POST.get('overall_discount', 0)
        package.selling_price = request.POST.get('selling_price')
        package.is_active = request.POST.get('is_active') == 'on'
        package.save()
        
        # Update items
        package.items.all().delete()
        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')
        item_discounts = request.POST.getlist('item_discount[]')
        
        for pid, qty, disc in zip(product_ids, quantities, item_discounts):
            if pid and qty:
                PackageItem.objects.create(
                    package=package,
                    product_id=pid,
                    quantity=int(qty),
                    item_discount=float(disc or 0)
                )
        
        messages.success(request, f'Package "{package.name}" updated successfully!')
        return redirect('panel_packages')
    
    products = Product.objects.filter(is_active=True).order_by('name')
    return render(request, 'panel/package_form.html', {'package': package, 'products': products})


@login_required(login_url='panel_login')
@permission_required('packages', 'delete')
def panel_package_delete(request, pk):
    package = get_object_or_404(Package, pk=pk)
    package.delete()
    messages.success(request, 'Package deleted successfully!')
    return redirect('panel_packages')

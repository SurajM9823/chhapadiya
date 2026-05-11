from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import CarouselSlide, Reel, Category, Service, WhyChooseUs, Stat, TrustedClient, Testimonial, TeamMember, SiteSettings, ContactInquiry, Product, CustomerUser, Cart, CartItem, Favourite, Order, OrderItem, QuoteRequest, QuotationRequest, QuotationRequestItem, Country
from .email_utils import send_order_confirmation_email

def base_context():
    categories = Category.objects.filter(is_active=True).prefetch_related('subcategories').order_by('name')
    settings = SiteSettings.get()
    return {'categories': categories, 'settings': settings}

@ensure_csrf_cookie
def index(request):
    slides = CarouselSlide.objects.filter(is_active=True)
    reels = Reel.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)
    return render(request, 'web/index.html', {**base_context(), 'slides': slides, 'reels': reels, 'categories': categories})

def about(request):
    return render(request, 'web/about.html', {
        **base_context(),
        'stats': Stat.objects.filter(is_active=True),
        'trusted_clients': TrustedClient.objects.filter(is_active=True),
        'testimonials': Testimonial.objects.filter(is_active=True),
        'team': TeamMember.objects.filter(is_active=True),
        'default_team': TeamMember.objects.filter(is_active=True),
    })

def contact(request):
    s = SiteSettings.get()
    if request.method == 'POST':
        ContactInquiry.objects.create(
            full_name=request.POST.get('full_name', ''),
            phone=request.POST.get('phone', ''),
            email=request.POST.get('email', ''),
            company=request.POST.get('company', ''),
            inquiry_type=request.POST.get('inquiry_type', ''),
            message=request.POST.get('message', ''),
        )
        messages.success(request, 'Your inquiry has been sent. We will get back to you soon!')
        return redirect('contact')
    return render(request, 'web/contact.html', {**base_context(), 'settings': s})

def services(request):
    services = Service.objects.filter(is_active=True)
    why_items = WhyChooseUs.objects.filter(is_active=True)
    return render(request, 'web/services.html', {**base_context(), 'services': services, 'why_items': why_items})

@ensure_csrf_cookie
def products(request):
    import json as _json
    search_query = request.GET.get('search', '')
    qs = Product.objects.filter(is_active=True).select_related('category', 'sub_category').prefetch_related('images')
    products_data = []
    for p in qs:
        img = p.primary_image
        products_data.append({
            'id': p.pk,
            'slug': p.slug,
            'name': p.name,
            'brand': p.brand,
            'category_id': p.category_id or 0,
            'category_name': p.category.name if p.category else '',
            'sub_category_id': p.sub_category_id or 0,
            'sub_category_name': p.sub_category.name if p.sub_category else '',
            'origin_id': p.origin_id or 0,
            'mrp': float(p.mrp),
            'image': img.image.url if img else '',
            'is_featured': p.is_featured,
        })
    categories = Category.objects.filter(is_active=True).prefetch_related('subcategories').order_by('order', 'name')
    return render(request, 'web/products.html', {
        **base_context(),
        'search_query': search_query,
        'products_json': _json.dumps(products_data),
        'filter_categories': categories,
    })

def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category', 'sub_category', 'origin')
                       .prefetch_related('images', 'related_products__images'),
        slug=slug, is_active=True
    )
    related = product.related_products.filter(is_active=True).prefetch_related('images')[:4]
    specs = []
    if product.specifications:
        for line in product.specifications.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if ':' in line:
                label, _, value = line.partition(':')
                specs.append({'label': label.strip(), 'value': value.strip()})
            else:
                specs.append({'label': '', 'value': line})
    is_wishlisted = (
        request.user.is_authenticated and
        Favourite.objects.filter(user=request.user, product=product).exists()
    )
    return render(request, 'web/product_detail.html', {
        **base_context(),
        'product': product,
        'related': related,
        'specs': specs,
        'stock': product.stock_quantity,
        'is_wishlisted': is_wishlisted,
    })


def product_detail_redirect(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    return redirect('product_detail', slug=product.slug, permanent=True)


# ── Customer Auth ─────────────────────────────────────────────────────────────

@ensure_csrf_cookie
def customer_register(request):
    if request.user.is_authenticated:
        return JsonResponse({'ok': True})
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        if not email:
            return JsonResponse({'ok': False, 'error': 'Email is required.'})
        if password != password2:
            return JsonResponse({'ok': False, 'error': 'Passwords do not match.'})
        if len(password) < 8:
            return JsonResponse({'ok': False, 'error': 'Password must be at least 8 characters.'})
        if CustomerUser.objects.filter(email=email).exists():
            return JsonResponse({'ok': False, 'error': 'An account with this email already exists.'})
        user = CustomerUser.objects.create_user(username=email, email=email, password=password, phone=phone)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        request.session.save()
        pending = request.session.pop('pending_cart_product', None)
        if pending:
            cart, _ = Cart.objects.get_or_create(user=user)
            p = Product.objects.filter(pk=pending, is_active=True).first()
            if p:
                item, created = CartItem.objects.get_or_create(cart=cart, product=p)
                if not created:
                    item.quantity += 1
                    item.save()
        pending_fav = request.session.pop('pending_fav_product', None)
        if pending_fav:
            p = Product.objects.filter(pk=pending_fav, is_active=True).first()
            if p:
                Favourite.objects.get_or_create(user=user, product=p)
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False, 'error': 'Invalid request.'})


@ensure_csrf_cookie
def customer_login(request):
    if request.user.is_authenticated:
        return JsonResponse({'ok': True})
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user is None:
            try:
                u = CustomerUser.objects.get(email=email)
                user = authenticate(request, username=u.username, password=password)
            except CustomerUser.DoesNotExist:
                pass
        if user:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session.save()
            pending = request.session.pop('pending_cart_product', None)
            if pending:
                cart, _ = Cart.objects.get_or_create(user=user)
                p = Product.objects.filter(pk=pending, is_active=True).first()
                if p:
                    item, created = CartItem.objects.get_or_create(cart=cart, product=p)
                    if not created:
                        item.quantity += 1
                        item.save()
            pending_fav = request.session.pop('pending_fav_product', None)
            if pending_fav:
                p = Product.objects.filter(pk=pending_fav, is_active=True).first()
                if p:
                    Favourite.objects.get_or_create(user=user, product=p)
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'error': 'Invalid email or password.'})
    return JsonResponse({'ok': False, 'error': 'Invalid request.'})


def customer_logout(request):
    logout(request)
    return redirect('index')


# ── Cart ──────────────────────────────────────────────────────────────────────

@ensure_csrf_cookie
def cart_add(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    product_id = request.POST.get('product_id')
    if not request.user.is_authenticated:
        request.session['pending_cart_product'] = product_id
        return JsonResponse({'ok': False, 'require_login': True})
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()
    return JsonResponse({'ok': True, 'total_items': cart.total_items})


def cart_view(request):
    if not request.user.is_authenticated:
        return redirect('index')
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product').prefetch_related('product__images').all()
    return render(request, 'web/cart.html', {**base_context(), 'cart': cart, 'items': items})


def cart_remove(request, item_id):
    if not request.user.is_authenticated:
        return redirect('index')
    CartItem.objects.filter(pk=item_id, cart__user=request.user).delete()
    return redirect('cart')


def cart_update(request, item_id):
    if request.method == 'POST' and request.user.is_authenticated:
        qty = int(request.POST.get('quantity', 1))
        item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
        if qty < 1:
            item.delete()
        else:
            item.quantity = qty
            item.save()
    return JsonResponse({'ok': True})


# ── Favourites ────────────────────────────────────────────────────────────────

def favourite_toggle(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    product_id = request.POST.get('product_id')
    if not request.user.is_authenticated:
        request.session['pending_fav_product'] = product_id
        return JsonResponse({'ok': False, 'require_login': True})
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    fav, created = Favourite.objects.get_or_create(user=request.user, product=product)
    if not created:
        fav.delete()
        return JsonResponse({'ok': True, 'action': 'removed'})
    return JsonResponse({'ok': True, 'action': 'added'})


# ── Wishlist ──────────────────────────────────────────────────────────────────

def wishlist(request):
    if not request.user.is_authenticated:
        return redirect('index')
    favs = request.user.favourites.select_related('product').prefetch_related('product__images').order_by('-added_at')
    return render(request, 'web/wishlist.html', {**base_context(), 'favs': favs})


# ── Checkout & Orders ─────────────────────────────────────────────────────────

DELIVERY_CHARGE = 150  # Rs. flat delivery charge


def checkout(request):
    """Checkout from cart (multiple items)."""
    if not request.user.is_authenticated:
        return redirect('index')
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product').prefetch_related('product__images').all()
    if not items.exists():
        return redirect('cart')
    subtotal = cart.total_price
    s = SiteSettings.get()
    return render(request, 'web/checkout.html', {
        **base_context(), 'items': items, 'subtotal': subtotal,
        'delivery_charge': DELIVERY_CHARGE, 'settings': s, 'source': 'cart',
        'selected_items': None,
    })


def buy_now(request, slug):
    """Buy a single product directly."""
    if not request.user.is_authenticated:
        request.session['pending_buy_slug'] = slug
        return redirect('index')
    product = get_object_or_404(Product, slug=slug, is_active=True)
    qty = int(request.GET.get('qty', 1))
    subtotal = product.mrp * qty
    s = SiteSettings.get()
    return render(request, 'web/checkout.html', {
        **base_context(), 'buy_product': product, 'buy_qty': qty,
        'subtotal': subtotal, 'delivery_charge': DELIVERY_CHARGE,
        'settings': s, 'source': 'buy_now',
    })


def place_order(request):
    if request.method != 'POST' or not request.user.is_authenticated:
        return redirect('index')

    delivery_type  = request.POST.get('delivery_type', 'delivery')
    full_name      = request.POST.get('full_name', '').strip()
    phone          = request.POST.get('phone', '').strip()
    email          = request.POST.get('email', '').strip()
    address        = request.POST.get('address', '').strip()
    city           = request.POST.get('city', '').strip()
    note           = request.POST.get('note', '').strip()
    payment_method = request.POST.get('payment_method', 'cod')
    source         = request.POST.get('source', 'cart')
    receipt        = request.FILES.get('payment_receipt')

    charge = DELIVERY_CHARGE if delivery_type == 'delivery' else 0

    if source == 'buy_now':
        product_id = request.POST.get('product_id')
        qty        = int(request.POST.get('qty', 1))
        product    = get_object_or_404(Product, pk=product_id, is_active=True)
        subtotal   = product.mrp * qty
        total      = subtotal + charge
        order = Order.objects.create(
            user=request.user, status='pending',
            delivery_type=delivery_type, full_name=full_name, phone=phone,
            email=email, address=address, city=city, note=note,
            payment_method=payment_method,
            subtotal=subtotal, delivery_charge=charge, total=total,
        )
        if receipt: order.payment_receipt = receipt; order.save()
        OrderItem.objects.create(
            order=order, product=product,
            product_name=product.name, product_sku=product.sku,
            unit_price=product.mrp, quantity=qty,
        )
    else:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        import json as _json
        selected_items_raw = request.POST.get('selected_items')
        if selected_items_raw:
            try:
                selected_items = _json.loads(selected_items_raw)
                selected_ids = {item['product_id'] for item in selected_items}
                cart_items = cart.items.select_related('product').filter(product_id__in=selected_ids).all()
            except Exception:
                cart_items = cart.items.select_related('product').all()
        else:
            cart_items = cart.items.select_related('product').all()
        if not cart_items.exists():
            return redirect('cart')
        subtotal = sum(ci.subtotal for ci in cart_items)
        total    = subtotal + charge
        order = Order.objects.create(
            user=request.user, status='pending',
            delivery_type=delivery_type, full_name=full_name, phone=phone,
            email=email, address=address, city=city, note=note,
            payment_method=payment_method,
            subtotal=subtotal, delivery_charge=charge, total=total,
        )
        if receipt: order.payment_receipt = receipt; order.save()
        for ci in cart_items:
            OrderItem.objects.create(
                order=order, product=ci.product,
                product_name=ci.product.name, product_sku=ci.product.sku,
                unit_price=ci.product.mrp, quantity=ci.quantity,
            )
        cart_items.delete()

    send_order_confirmation_email(order)
    return redirect('order_success', order_number=order.order_number)


def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'web/order_success.html', {**base_context(), 'order': order})


def my_orders(request):
    if not request.user.is_authenticated:
        return redirect('index')
    orders = request.user.orders.prefetch_related('items').all()
    return render(request, 'web/my_orders.html', {**base_context(), 'orders': orders})


def order_detail(request, order_number):
    if not request.user.is_authenticated:
        return redirect('index')
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'web/order_detail.html', {**base_context(), 'order': order})


def update_order_location(request, order_number):
    if request.method != 'POST' or not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Invalid request'})
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    address = request.POST.get('address', '').strip()
    city = request.POST.get('city', '').strip()
    if not address or not city:
        return JsonResponse({'ok': False, 'error': 'Address and city are required'})
    order.address = address
    order.city = city
    order.save()
    return JsonResponse({'ok': True})


# ── Quote Request ─────────────────────────────────────────────────────────────

def compare_products(request, slug1, slug2):
    p1 = get_object_or_404(Product.objects.select_related('category', 'origin').prefetch_related('images'), slug=slug1, is_active=True)
    p2 = get_object_or_404(Product.objects.select_related('category', 'origin').prefetch_related('images'), slug=slug2, is_active=True)

    def parse_specs(product):
        specs = {}
        if product.specifications:
            for line in product.specifications.strip().splitlines():
                line = line.strip()
                if ':' in line:
                    label, _, value = line.partition(':')
                    specs[label.strip()] = value.strip()
        return specs

    specs1, specs2 = parse_specs(p1), parse_specs(p2)
    all_spec_keys = list(dict.fromkeys(list(specs1.keys()) + list(specs2.keys())))
    specs_comparison = [(k, specs1.get(k, '\u2014'), specs2.get(k, '\u2014')) for k in all_spec_keys]

    # Auto-suggest comparable products: same category as p1 or p2, exclude both
    from django.db.models import Q
    suggestions = (
        Product.objects.filter(is_active=True)
        .filter(Q(category=p1.category) | Q(category=p2.category))
        .exclude(pk__in=[p1.pk, p2.pk])
        .prefetch_related('images')
        .select_related('category')
        .order_by('?')[:8]
    )

    return render(request, 'web/compare.html', {
        **base_context(),
        'p1': p1, 'p2': p2,
        'specs_comparison': specs_comparison,
        'stock1': p1.stock_quantity,
        'stock2': p2.stock_quantity,
        'suggestions': suggestions,
    })


def compare_suggestions_api(request):
    """Return products similar to the ones being compared (by category/brand)."""
    slugs = request.GET.getlist('slug')
    from django.db.models import Q
    base = Product.objects.filter(is_active=True).exclude(slug__in=slugs)
    if slugs:
        ref = Product.objects.filter(slug__in=slugs, is_active=True).select_related('category')
        cat_ids = [p.category_id for p in ref if p.category_id]
        brands  = [p.brand for p in ref if p.brand]
        q = Q()
        if cat_ids: q |= Q(category_id__in=cat_ids)
        if brands:  q |= Q(brand__in=brands)
        if q: base = base.filter(q)
    results = []
    for p in base.prefetch_related('images').select_related('category').order_by('?')[:8]:
        img = p.primary_image
        results.append({
            'slug': p.slug, 'name': p.name, 'mrp': str(p.mrp),
            'category': p.category.name if p.category else '',
            'image': img.image.url if img else '',
        })
    return JsonResponse({'results': results})


def product_search_api(request):
    q = request.GET.get('q', '').strip()
    qs = Product.objects.filter(is_active=True).prefetch_related('images')
    if q:
        qs = qs.filter(name__icontains=q)
    results = []
    for p in qs[:20]:
        img = p.primary_image
        results.append({
            'id': p.pk,
            'slug': p.slug,
            'text': p.name,
            'sku': p.sku,
            'mrp': str(p.mrp),
            'image': img.image.url if img else ''
        })
    return JsonResponse({'results': results})


def quote_request(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'require_login': True})
    import json as _json
    items_raw = request.POST.get('items')
    if not items_raw:
        return JsonResponse({'success': False, 'message': 'No items provided'})
    try:
        items = _json.loads(items_raw)
    except Exception:
        return JsonResponse({'success': False, 'message': 'Invalid items format'})
    if not items:
        return JsonResponse({'success': False, 'message': 'No items provided'})
    from .models import QuotationRequest, QuotationRequestItem
    quotation = QuotationRequest.objects.create(
        user_email=request.user.email,
        user_name=request.POST.get('user_name', request.user.get_full_name() or request.user.email),
        phone=request.POST.get('phone', ''),
        message=request.POST.get('message', ''),
    )
    for item in items:
        pid = item.get('product_id')
        product = Product.objects.filter(pk=pid, is_active=True).first() if pid else None
        if product:
            QuotationRequestItem.objects.update_or_create(
                quotation=quotation,
                product=product,
                defaults={'quantity': item.get('quantity', 1)}
            )
    return JsonResponse({'success': True})


def my_quotes(request):
    if not request.user.is_authenticated:
        return redirect('index')
    quotations = QuotationRequest.objects.filter(user_email=request.user.email).select_related('linked_customer__tier').prefetch_related('items__product__tier_prices__tier').order_by('-created_at')
    return render(request, 'web/my_quotes.html', {**base_context(), 'quotations': quotations})


def quotation_pdf(request, pk):
    if not request.user.is_authenticated:
        return redirect('index')
    quotation = get_object_or_404(
        QuotationRequest.objects.select_related('linked_customer__tier')
                               .prefetch_related('items__product__tier_prices__tier', 'items__product__images'),
        pk=pk, user_email=request.user.email
    )
    site = SiteSettings.get()
    # Calculate total with tier pricing
    total = 0
    items_with_prices = []
    for item in quotation.items.all():
        offered_price = item.product.mrp
        tier_name = None
        if quotation.linked_customer and quotation.linked_customer.tier:
            tp = item.product.tier_prices.filter(tier=quotation.linked_customer.tier).first()
            if tp:
                offered_price = tp.price
                tier_name = quotation.linked_customer.tier.name
        subtotal = offered_price * item.quantity
        total += subtotal
        items_with_prices.append({
            'item': item,
            'offered_price': offered_price,
            'tier_name': tier_name,
            'subtotal': subtotal,
        })
    return render(request, 'web/quotation_pdf.html', {
        'quotation': quotation,
        'site': site,
        'items_with_prices': items_with_prices,
        'total': total,
    })


def wishlist_api(request):
    print(f'DEBUG wishlist_api: user={request.user}, is_auth={request.user.is_authenticated}, session_key={request.session.session_key}')
    if not request.user.is_authenticated:
        return JsonResponse({'wishlisted_ids': []})
    wishlisted = Favourite.objects.filter(user=request.user).values_list('product_id', flat=True)
    return JsonResponse({'wishlisted_ids': list(wishlisted)})


def origins_api(request):
    origins = Country.objects.filter(products__is_active=True).distinct().order_by('name')
    
    result = []
    for origin in origins:
        categories = {}
        products = origin.products.filter(is_active=True).select_related('category')
        for product in products:
            if product.category:
                if product.category.id not in categories:
                    categories[product.category.id] = product.category.name
        
        result.append({
            'id': origin.id,
            'name': origin.name,
            'categories': [{'id': cat_id, 'name': cat_name} for cat_id, cat_name in sorted(categories.items(), key=lambda x: x[1])]
        })
    
    return JsonResponse({'origins': result})

def featured_products_api(request):
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 10))
    offset = (page - 1) * limit
    
    products = Product.objects.filter(is_active=True, is_featured=True).select_related('category').prefetch_related('images').order_by('-created_at')[offset:offset+limit]
    
    result = []
    for p in products:
        img = p.primary_image
        result.append({
            'id': p.pk,
            'slug': p.slug,
            'name': p.name,
            'brand': p.brand,
            'mrp': float(p.mrp),
            'category': p.category.name if p.category else '',
            'image': img.image.url if img else '',
        })
    
    total = Product.objects.filter(is_active=True, is_featured=True).count()
    return JsonResponse({
        'products': result,
        'total': total,
        'page': page,
        'limit': limit,
        'has_more': (offset + limit) < total,
    })
def reels_api(request):
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 10))
    offset = (page - 1) * limit
    
    reels = Reel.objects.filter(is_active=True).order_by('-created_at')[offset:offset+limit]
    
    result = []
    for reel in reels:
        result.append({
            'id': reel.pk,
            'title': reel.title,
            'video_type': reel.video_type,
            'video_url': reel.get_video_url(),
            'embed_url': reel.get_embed_url(),
            'thumbnail_url': reel.thumbnail.url if reel.thumbnail else '',
        })
    
    total = Reel.objects.filter(is_active=True).count()
    return JsonResponse({
        'reels': result,
        'total': total,
        'page': page,
        'limit': limit,
        'has_more': (offset + limit) < total,
    })

@ensure_csrf_cookie
def google_login_callback(request):
    from allauth.socialaccount.models import SocialApp
    import requests
    
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error or not code:
        return redirect('index')
    
    try:
        google_app = SocialApp.objects.get(provider='google')
        
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'code': code,
            'client_id': google_app.client_id,
            'client_secret': google_app.secret,
            'redirect_uri': request.build_absolute_uri('/accounts/google/login/callback/'),
            'grant_type': 'authorization_code',
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        
        if 'error' in token_json:
            return redirect('index')
        
        access_token = token_json.get('access_token')
        user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(user_info_url, headers=headers)
        user_data = user_response.json()
        
        email = user_data.get('email', '').lower()
        name = user_data.get('name', '')
        
        if not email:
            return redirect('index')
        
        user, created = CustomerUser.objects.get_or_create(
            email=email,
            defaults={'username': email, 'first_name': name.split()[0] if name else ''}
        )
        
        print(f'DEBUG: Google login - user={user.email}, created={created}')
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        print(f'DEBUG: After login - is_auth={request.user.is_authenticated}, session_key={request.session.session_key}')
        
        pending = request.session.pop('pending_cart_product', None)
        if pending:
            cart, _ = Cart.objects.get_or_create(user=user)
            p = Product.objects.filter(pk=pending, is_active=True).first()
            if p:
                item, created = CartItem.objects.get_or_create(cart=cart, product=p)
                if not created:
                    item.quantity += 1
                    item.save()
        
        pending_fav = request.session.pop('pending_fav_product', None)
        if pending_fav:
            p = Product.objects.filter(pk=pending_fav, is_active=True).first()
            if p:
                Favourite.objects.get_or_create(user=user, product=p)
        
        response = redirect('index')
        return response
    except Exception as e:
        print(f'Google login error: {e}')
        import traceback
        traceback.print_exc()
        return redirect('index')

def b2b_request(request):
    if request.method == 'POST':
        company_name = request.POST.get('company_name', '').strip()
        contact_person = request.POST.get('contact_person', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        business_type = request.POST.get('business_type', '').strip()
        products_interested = request.POST.get('products_interested', '').strip()
        monthly_volume = request.POST.get('monthly_volume', '').strip()
        requirements = request.POST.get('requirements', '').strip()
        
        if not all([company_name, contact_person, email, phone, business_type, products_interested]):
            return JsonResponse({'success': False, 'message': 'Please fill in all required fields.'})
        
        ContactInquiry.objects.create(
            full_name=contact_person,
            phone=phone,
            email=email,
            company=company_name,
            inquiry_type='b2b',
            message=f"Business Type: {business_type}\nProducts Interested: {products_interested}\nMonthly Volume: {monthly_volume}\nRequirements: {requirements}"
        )
        return JsonResponse({'success': True})
    
    return render(request, 'web/b2b_request.html', {**base_context()})


def privacy_policy(request):
    return render(request, 'web/privacy_policy.html', {**base_context()})


def terms_conditions(request):
    return render(request, 'web/terms_conditions.html', {**base_context()})

from django.urls import path
from . import views, panel_views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('products/', views.products, name='products'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/', views.product_detail_redirect, name='product_detail_redirect'),

    # Panel auth
    path('panel/login/', panel_views.panel_login, name='panel_login'),
    path('panel/logout/', panel_views.panel_logout, name='panel_logout'),

    # Carousel
    path('panel/', panel_views.panel_dashboard, name='panel_dashboard'),
    path('panel/carousel/', panel_views.panel_carousel, name='panel_carousel'),
    path('panel/carousel/add/', panel_views.panel_carousel_add, name='panel_carousel_add'),
    path('panel/carousel/<int:pk>/edit/', panel_views.panel_carousel_edit, name='panel_carousel_edit'),
    path('panel/carousel/<int:pk>/delete/', panel_views.panel_carousel_delete, name='panel_carousel_delete'),

    # Reels
    path('panel/reels/', panel_views.panel_reels, name='panel_reels'),
    path('panel/reels/add/', panel_views.panel_reel_add, name='panel_reel_add'),
    path('panel/reels/<int:pk>/edit/', panel_views.panel_reel_edit, name='panel_reel_edit'),
    path('panel/reels/<int:pk>/delete/', panel_views.panel_reel_delete, name='panel_reel_delete'),

    # Categories
    path('panel/categories/', panel_views.panel_categories, name='panel_categories'),
    path('panel/categories/add/', panel_views.panel_category_add, name='panel_category_add'),
    path('panel/categories/<int:pk>/edit/', panel_views.panel_category_edit, name='panel_category_edit'),
    path('panel/categories/<int:pk>/delete/', panel_views.panel_category_delete, name='panel_category_delete'),
    # Sub Categories
    path('panel/categories/<int:cat_pk>/subs/', panel_views.panel_subcategories, name='panel_subcategories'),
    path('panel/categories/<int:cat_pk>/subs/add/', panel_views.panel_subcategory_add, name='panel_subcategory_add'),
    path('panel/categories/<int:cat_pk>/subs/<int:pk>/edit/', panel_views.panel_subcategory_edit, name='panel_subcategory_edit'),
    path('panel/categories/<int:cat_pk>/subs/<int:pk>/delete/', panel_views.panel_subcategory_delete, name='panel_subcategory_delete'),
    # Site Settings
    path('panel/settings/', panel_views.panel_settings, name='panel_settings'),

    # Countries
    path('panel/countries/', panel_views.panel_countries, name='panel_countries'),
    path('panel/countries/add/', panel_views.panel_country_save, name='panel_country_add'),
    path('panel/countries/<int:pk>/edit/', panel_views.panel_country_save, name='panel_country_edit'),
    path('panel/countries/<int:pk>/delete/', panel_views.panel_country_delete, name='panel_country_delete'),

    # Customer Tiers
    path('panel/tiers/', panel_views.panel_tiers, name='panel_tiers'),
    path('panel/tiers/add/', panel_views.panel_tier_add, name='panel_tier_add'),
    path('panel/tiers/<int:pk>/edit/', panel_views.panel_tier_edit, name='panel_tier_edit'),
    path('panel/tiers/<int:pk>/delete/', panel_views.panel_tier_delete, name='panel_tier_delete'),

    # Delivery Time Tiers
    path('panel/delivery-times/', panel_views.panel_delivery_times, name='panel_delivery_times'),
    path('panel/delivery-times/add/', panel_views.panel_delivery_time_add, name='panel_delivery_time_add'),
    path('panel/delivery-times/<int:pk>/edit/', panel_views.panel_delivery_time_edit, name='panel_delivery_time_edit'),
    path('panel/delivery-times/<int:pk>/delete/', panel_views.panel_delivery_time_delete, name='panel_delivery_time_delete'),

    # Customers
    path('panel/customers/', panel_views.panel_customers, name='panel_customers'),
    path('panel/customers/add/', panel_views.panel_customer_add, name='panel_customer_add'),
    path('panel/customers/<int:pk>/edit/', panel_views.panel_customer_edit, name='panel_customer_edit'),
    path('panel/customers/<int:pk>/delete/', panel_views.panel_customer_delete, name='panel_customer_delete'),

    # Products
    path('panel/products/', panel_views.panel_products, name='panel_products'),
    path('panel/products/import/', panel_views.panel_products_import, name='panel_products_import'),
    path('panel/products/add/', panel_views.panel_product_add, name='panel_product_add'),
    path('panel/products/<int:pk>/edit/', panel_views.panel_product_edit, name='panel_product_edit'),
    path('panel/products/<int:pk>/delete/', panel_views.panel_product_delete, name='panel_product_delete'),
    path('panel/products/<int:pk>/detail/', panel_views.panel_product_detail, name='panel_product_detail'),
    path('panel/products/<int:pk>/stock/', panel_views.panel_stock, name='panel_stock'),
    # Packages
    path('panel/packages/', panel_views.panel_packages, name='panel_packages'),
    path('panel/packages/add/', panel_views.panel_package_add, name='panel_package_add'),
    path('panel/packages/<int:pk>/edit/', panel_views.panel_package_edit, name='panel_package_edit'),
    path('panel/packages/<int:pk>/delete/', panel_views.panel_package_delete, name='panel_package_delete'),
    # Services CMS
    path('panel/services/', panel_views.panel_services, name='panel_services'),
    path('panel/services/add/', panel_views.panel_service_add, name='panel_service_add'),
    path('panel/services/<int:pk>/edit/', panel_views.panel_service_edit, name='panel_service_edit'),
    path('panel/services/<int:pk>/delete/', panel_views.panel_service_delete, name='panel_service_delete'),
    path('panel/why/add/', panel_views.panel_why_add, name='panel_why_add'),
    path('panel/why/<int:pk>/edit/', panel_views.panel_why_edit, name='panel_why_edit'),
    path('panel/why/<int:pk>/delete/', panel_views.panel_why_delete, name='panel_why_delete'),
    # About Page CMS
    path('panel/about/', panel_views.panel_about, name='panel_about'),
    path('panel/stats/add/', panel_views.panel_stat_save, name='panel_stat_add'),
    path('panel/stats/<int:pk>/edit/', panel_views.panel_stat_save, name='panel_stat_edit'),
    path('panel/stats/<int:pk>/delete/', panel_views.panel_stat_delete, name='panel_stat_delete'),
    path('panel/trusted/add/', panel_views.panel_trusted_save, name='panel_trusted_add'),
    path('panel/trusted/<int:pk>/edit/', panel_views.panel_trusted_save, name='panel_trusted_edit'),
    path('panel/trusted/<int:pk>/delete/', panel_views.panel_trusted_delete, name='panel_trusted_delete'),
    path('panel/testimonials/add/', panel_views.panel_testimonial_save, name='panel_testimonial_add'),
    path('panel/testimonials/<int:pk>/edit/', panel_views.panel_testimonial_save, name='panel_testimonial_edit'),
    path('panel/testimonials/<int:pk>/delete/', panel_views.panel_testimonial_delete, name='panel_testimonial_delete'),
    path('panel/team/add/', panel_views.panel_team_save, name='panel_team_add'),
    path('panel/team/<int:pk>/edit/', panel_views.panel_team_save, name='panel_team_edit'),
    path('panel/team/<int:pk>/delete/', panel_views.panel_team_delete, name='panel_team_delete'),
    # Contact Inquiries
    path('panel/inquiries/', panel_views.panel_inquiries, name='panel_inquiries'),
    path('panel/inquiries/<int:pk>/delete/', panel_views.panel_inquiry_delete, name='panel_inquiry_delete'),
    # Customer Auth
    path('auth/register/', views.customer_register, name='customer_register'),
    path('auth/login/', views.customer_login, name='customer_login'),
    path('auth/logout/', views.customer_logout, name='customer_logout'),
    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    # Favourites
    path('favourites/toggle/', views.favourite_toggle, name='favourite_toggle'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('api/wishlist/', views.wishlist_api, name='wishlist_api'),
    path('api/origins/', views.origins_api, name='origins_api'),
    path('api/featured-products/', views.featured_products_api, name='featured_products_api'),
    path('api/reels/', views.reels_api, name='reels_api'),
    # Checkout & Orders
    path('checkout/', views.checkout, name='checkout'),
    path('buy/<slug:slug>/', views.buy_now, name='buy_now'),
    path('place-order/', views.place_order, name='place_order'),
    path('profile/', views.my_profile, name='my_profile'),
    path('orders/', views.my_orders, name='my_orders'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_number>/update-location/', views.update_order_location, name='update_order_location'),
    path('orders/<str:order_number>/success/', views.order_success, name='order_success'),
    # Quote Requests
    path('quote/request/', views.quote_request, name='quote_request'),
    path('products/search/', views.product_search_api, name='product_search_api'),
    path('compare/<slug:slug1>-vs-<slug:slug2>/', views.compare_products, name='compare_products'),
    path('compare/suggestions/', views.compare_suggestions_api, name='compare_suggestions_api'),
    path('panel/quotes/', panel_views.panel_quotes, name='panel_quotes'),
    path('panel/quotes/<int:pk>/update/', panel_views.panel_quote_update, name='panel_quote_update'),
    path('panel/quotes/<int:pk>/delete/', panel_views.panel_quote_delete, name='panel_quote_delete'),
    path('panel/quotes/<int:pk>/create-customer/', panel_views.panel_quote_create_customer, name='panel_quote_create_customer'),
    path('panel/billing/', panel_views.panel_billing, name='panel_billing'),
    path('panel/billing/<int:pk>/detail/', panel_views.panel_billing_detail, name='panel_billing_detail'),
    path('panel/billing/<int:pk>/view/', panel_views.panel_billing_view, name='panel_billing_view'),
    path('panel/api/products/', panel_views.api_billing_products, name='api_products'),
    path('panel/api/customers/', panel_views.api_customers, name='api_customers'),
    path('panel/api/customers/create/', panel_views.api_customer_create, name='api_customer_create'),
    path('panel/api/agents/', panel_views.api_agents, name='api_agents'),
    path('panel/api/billing/', panel_views.api_billing_list, name='api_billing_list'),
    path('panel/api/billing/create/', panel_views.api_billing_create, name='api_billing_create'),
    path('panel/orders/', panel_views.panel_orders, name='panel_orders'),
    path('panel/orders/<int:pk>/', panel_views.panel_order_detail, name='panel_order_detail'),
    path('panel/orders/<int:pk>/delete/', panel_views.panel_order_delete, name='panel_order_delete'),

    path('my-quotes/', views.my_quotes, name='my_quotes'),
    path('my-quotes/<int:pk>/pdf/', views.quotation_pdf, name='quotation_pdf'),

    # User Management
    path('panel/users/', panel_views.panel_users, name='panel_users'),
    path('panel/users/add/', panel_views.panel_user_add, name='panel_user_add'),
    path('panel/users/<int:pk>/edit/', panel_views.panel_user_edit, name='panel_user_edit'),
    path('panel/users/<int:pk>/delete/', panel_views.panel_user_delete, name='panel_user_delete'),
    path('api/user/<int:pk>/', panel_views.api_user_get, name='api_user_get'),
    path('panel/roles/', panel_views.panel_roles, name='panel_roles'),
    path('panel/roles/<int:pk>/edit/', panel_views.panel_role_edit, name='panel_role_edit'),
    path('b2b-request/', views.b2b_request, name='b2b_request'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('review/save/', views.product_review_save, name='product_review_save'),
    path('review/delete/', views.product_review_delete, name='product_review_delete'),
]

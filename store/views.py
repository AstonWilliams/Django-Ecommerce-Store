from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Product, Category, Cart, CartItem
import logging
logger = logging.getLogger(__name__)

def home(request):
    products = Product.objects.select_related('category').annotate(
        review_count=Count('reviews'),
        avg_rating=Avg('reviews__rating')
    ).filter(is_active=True)[:12]
    
    categories = Category.objects.filter(is_active=True)
    
    # Get trending products
    trending_products = Product.objects.filter(
        is_trending=True, 
        is_active=True
    )[:8]
    
    context = {
        'products': products,
        'categories': categories,
        'trending_products': trending_products,
        'has_more_products': Product.objects.count() > 12,
    }
    
    # Add cart count for authenticated users
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        context['cart_count'] = CartItem.objects.filter(cart=cart).count()
        context['cart_total'] = sum(
            item.product.price * item.quantity 
            for item in CartItem.objects.filter(cart=cart)
        )
    
    return render(request, 'store/home.html', context)

def search_view(request):
    query = request.GET.get('q', '')
    products = Product.objects.none()
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related('category').annotate(
            review_count=Count('reviews'),
            avg_rating=Avg('reviews__rating')
        )
    
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'store/search.html', {
        'products': page_obj,
        'query': query,
        'total_results': products.count()
    })

def signin_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password')
            return render(request, 'store/signin.html')
        
        # Try to authenticate with username or email
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            # Try with email if username failed
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                
                # Redirect to next page or home
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Your account has been disabled')
        else:
            messages.error(request, 'Invalid username/email or password')
    
    return render(request, 'store/signin.html')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        errors = []
        
        if not all([username, email, password, confirm_password]):
            errors.append('All fields are required')
        
        if len(username) < 3:
            errors.append('Username must be at least 3 characters long')
        
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists')
        
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered')
        
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if not request.POST.get('terms'):
            errors.append('You must agree to the Terms of Service')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'store/signup.html')
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Auto login after signup
            login(request, user)
            messages.success(request, f'Welcome to Walmart Clone, {first_name or username}!')
            return redirect('home')
            
        except Exception as e:
            messages.error(request, 'An error occurred while creating your account')
    
    return render(request, 'store/signup.html')

def signout_view(request):
    if request.user.is_authenticated:
        username = request.user.first_name or request.user.username
        logout(request)
        messages.success(request, f'Goodbye, {username}! You have been signed out.')
    return redirect('home')

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product_id).annotate(
        review_count=Count('reviews'),
        avg_rating=Avg('reviews__rating')
    )[:8]
    
    # Track product view (for analytics)
    if hasattr(product, 'view_count'):
        product.view_count += 1
        product.save(update_fields=['view_count'])
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    
    # Add cart info for authenticated users
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        context['in_cart'] = CartItem.objects.filter(
            cart=cart, 
            product=product
        ).exists()
    
    return render(request, 'store/product_detail.html', context)

from decimal import Decimal

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('product')
    
    subtotal = sum(Decimal(item.product.price) * item.quantity for item in cart_items)
    shipping_cost = Decimal(0) if subtotal >= Decimal(35) else Decimal(5.99)
    tax_rate = Decimal(0.08)
    tax_amount = subtotal * tax_rate
    total = subtotal + shipping_cost + tax_amount
    
    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax_amount': tax_amount,
        'total': total,
        'free_shipping_threshold': Decimal(35),
    })

@require_http_methods(["POST"])
@login_required
def add_to_cart(request, product_id):
    try:
        logger.info(f"Adding product {product_id} to cart for user {request.user.id}")
        product = get_object_or_404(Product, id=product_id, is_active=True)
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            return JsonResponse({
                'success': False, 
                'message': 'Invalid quantity'
            })
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        # Get updated cart count
        cart_count = CartItem.objects.filter(cart=cart).count()
        cart_total = sum(
            Decimal(item.product.price) * item.quantity 
            for item in CartItem.objects.filter(cart=cart)
        )

        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart',
            'cart_count': cart_count,
            'cart_total': float(cart_total)  # Convert to float if needed for the frontend
        })

    except Exception as e:
        logger.error(f"Error adding item to cart: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Failed to add item to cart'
        })

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    
    messages.success(request, f'{product_name} removed from cart')
    return redirect('cart')

@require_http_methods(["POST"])
@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    try:
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated successfully')
        else:
            product_name = cart_item.product.name
            cart_item.delete()
            messages.success(request, f'{product_name} removed from cart')
            
    except ValueError:
        messages.error(request, 'Invalid quantity')
    
    return redirect('cart')

from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem

@require_http_methods(["POST"])
@login_required
def clear_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    item_count = CartItem.objects.filter(cart=cart).count()
    
    if item_count > 0:
        CartItem.objects.filter(cart=cart).delete()
        messages.success(request, f'Removed {item_count} items from your cart')
    else:
        messages.info(request, 'Your cart is already empty.')

    return redirect('cart')

@require_http_methods(["GET"])
def quick_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    context = {
        'product': product,
    }
    
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        context['in_cart'] = CartItem.objects.filter(
            cart=cart, 
            product=product
        ).exists()
    
    return render(request, 'store/quick_view.html', context)

def load_more_products(request):
    page = int(request.GET.get('page', 2))
    category = request.GET.get('category', 'all')
    sort_by = request.GET.get('sort', 'featured')
    
    products = Product.objects.filter(is_active=True)
    
    if category != 'all':
        products = products.filter(category__slug=category)
    
    # Apply sorting
    if sort_by == 'price-low':
        products = products.order_by('price')
    elif sort_by == 'price-high':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(page)
    
    products_data = []
    for product in page_obj:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'image': product.image.url if product.image else '/placeholder.svg',
            'rating': getattr(product, 'avg_rating', 0) or 0,
            'review_count': getattr(product, 'review_count', 0) or 0,
            'url': f'/product/{product.id}/',
        })
    
    return JsonResponse({
        'products': products_data,
        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None
    })

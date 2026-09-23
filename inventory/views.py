from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Q, F, Count
from django.db import transaction
from django.http import HttpResponse, JsonResponse, FileResponse
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import *
from .forms import *
from .decorators import role_required
from .barcode_utils import (
    generate_barcode_image,
    generate_qr_code_image,
    generate_product_qr_data,
    generate_barcode_for_product,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


# ============================================================
# AUTHENTICATION
# ============================================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            ActivityLog.objects.create(
                user=user,
                action='Logged in',
                module='Authentication',
                ip_address=get_client_ip(request)
            )
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')


def logout_view(request):
    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user,
            action='Logged out',
            module='Authentication',
            ip_address=get_client_ip(request)
        )
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')


# ============================================================
# DASHBOARD
# ============================================================

@login_required
def dashboard(request):
    today = timezone.now().date()
    month_start = today.replace(day=1)

    total_sales = Invoice.objects.aggregate(Sum('grand_total'))['grand_total__sum'] or 0
    today_sales = Invoice.objects.filter(created_at__date=today).aggregate(Sum('grand_total'))['grand_total__sum'] or 0

    total_products = Product.objects.count()
    total_stock = Product.objects.aggregate(total=Sum('quantity'))['total'] or 0
    low_stock = Product.objects.filter(quantity__gt=0, quantity__lte=F('low_stock_threshold'))
    low_stock_count = low_stock.count()
    out_of_stock_count = Product.objects.filter(quantity__lte=0).count()

    recent_invoices = Invoice.objects.select_related('customer').order_by('-created_at')[:5]

    # Chart data
    chart_labels = []
    chart_data = []
    for i in range(5, -1, -1):
        month_date = (today.replace(day=1) - timedelta(days=i*30))
        month_total = Invoice.objects.filter(
            created_at__year=month_date.year,
            created_at__month=month_date.month
        ).aggregate(Sum('grand_total'))['grand_total__sum'] or 0
        chart_labels.append(month_date.strftime('%b %Y'))
        chart_data.append(float(month_total))

    top_products = InvoiceItem.objects.values('product__name').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('total')
    ).order_by('-total_qty')[:5]

    context = {
        'currency_symbol': Settings.get_currency_symbol(),
        'total_sales': total_sales,
        'today_sales': today_sales,
        'total_products': total_products,
        'total_stock': total_stock,
        'low_stock': low_stock[:5],
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'recent_invoices': recent_invoices,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'top_products': top_products,
    }
    return render(request, 'dashboard.html', context)


# ============================================================
# INVENTORY MANAGEMENT
# ============================================================

@login_required
def inventory_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')

    products = Product.objects.select_related('category', 'supplier').all()

    if query:
        products = products.filter(Q(name__icontains=query) | Q(sku__icontains=query))
    if category_id:
        products = products.filter(category_id=category_id)
    if status_filter == 'low':
        products = products.filter(quantity__gt=0, quantity__lte=F('low_stock_threshold'))
    elif status_filter == 'out':
        products = products.filter(quantity__lte=0)
    elif status_filter == 'available':
        products = products.filter(quantity__gt=F('low_stock_threshold'))

    context = {
        'currency_symbol': Settings.get_currency_symbol(),
        'products': products,
        'categories': Category.objects.all(),
        'query': query,
        'category_id': category_id,
        'status_filter': status_filter,
        'total_products': Product.objects.count(),
        'total_stock': Product.objects.aggregate(total=Sum('quantity'))['total'] or 0,
        'low_stock_count': Product.objects.filter(quantity__gt=0, quantity__lte=F('low_stock_threshold')).count(),
        'out_of_stock_count': Product.objects.filter(quantity__lte=0).count(),
    }
    return render(request, 'inventory_list.html', context)


@login_required
@role_required(['Admin', 'Manager'])
def add_inventory(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                product = form.save(commit=False)
                if not product.sku:
                    product.sku = f"SKU-{Product.objects.count() + 1:05d}"
                product.save()

                try:
                    generate_barcode_for_product(product)
                except Exception as e:
                    print(f"Barcode error: {e}")

                if product.quantity > 0:
                    StockMovement.objects.create(
                        product=product,
                        quantity=product.quantity,
                        movement_type='IN',
                        quantity_before=0,
                        quantity_after=product.quantity,
                        reference='Initial Stock',
                        note='Initial stock entry',
                        created_by=request.user
                    )
                ActivityLog.objects.create(
                    user=request.user,
                    action=f'Added product: {product.name}',
                    module='Inventory',
                    ip_address=get_client_ip(request)
                )
            messages.success(request, 'Product added successfully!')
            return redirect('inventory_list')
    else:
        form = ProductForm()
    return render(request, 'add_inventory.html', {
        'form': form,
        'currency_symbol': Settings.get_currency_symbol(),
    })


@login_required
@role_required(['Admin', 'Manager'])
def edit_inventory(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    old_qty = product.quantity
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            with transaction.atomic():
                product = form.save()
                if old_qty != product.quantity:
                    diff = product.quantity - old_qty
                    StockMovement.objects.create(
                        product=product,
                        quantity=diff,
                        movement_type='ADJUST',
                        quantity_before=old_qty,
                        quantity_after=product.quantity,
                        reference='Manual Adjustment',
                        note='Quantity adjusted via edit',
                        created_by=request.user
                    )
                ActivityLog.objects.create(
                    user=request.user,
                    action=f'Updated product: {product.name}',
                    module='Inventory',
                    ip_address=get_client_ip(request)
                )
            messages.success(request, 'Product updated successfully!')
            return redirect('inventory_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'add_inventory.html', {
        'form': form,
        'product': product,
        'edit': True,
        'currency_symbol': Settings.get_currency_symbol(),
    })


@login_required
@role_required(['Admin'])
def delete_inventory(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        name = product.name
        product.delete()
        ActivityLog.objects.create(
            user=request.user,
            action=f'Deleted product: {name}',
            module='Inventory',
            ip_address=get_client_ip(request)
        )
        messages.success(request, f'Product "{name}" deleted successfully!')
        return redirect('inventory_list')
    return render(request, 'confirm_delete.html', {'object': product, 'type': 'Product'})


@login_required
@role_required(['Admin', 'Manager'])
def add_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        note = request.POST.get('note', '')
        if quantity > 0:
            with transaction.atomic():
                old_qty = product.quantity
                product.quantity += quantity
                product.save()
                StockMovement.objects.create(
                    product=product,
                    quantity=quantity,
                    movement_type='IN',
                    quantity_before=old_qty,
                    quantity_after=product.quantity,
                    reference='Manual Stock Entry',
                    note=note,
                    created_by=request.user
                )
                ActivityLog.objects.create(
                    user=request.user,
                    action=f'Added {quantity} units to {product.name}',
                    module='Stock',
                    ip_address=get_client_ip(request)
                )
            messages.success(request, f'Added {quantity} units to {product.name}')
        else:
            messages.error(request, 'Quantity must be greater than 0')
        return redirect('inventory_list')
    return render(request, 'add_stock.html', {
        'product': product,
        'currency_symbol': Settings.get_currency_symbol(),
    })


@login_required
def stock_history(request):
    movements = StockMovement.objects.select_related('product', 'created_by').all()
    product_id = request.GET.get('product')
    movement_type = request.GET.get('type')
    if product_id:
        movements = movements.filter(product_id=product_id)
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    return render(request, 'stock_history.html', {
        'movements': movements[:200],
        'products': Product.objects.all(),
        'product_id': product_id,
        'movement_type': movement_type,
        'currency_symbol': Settings.get_currency_symbol(),
    })


@login_required
def low_stock(request):
    products = Product.objects.filter(
        quantity__lte=F('low_stock_threshold')
    ).select_related('category', 'supplier').order_by('quantity')
    return render(request, 'low_stock.html', {
        'products': products,
        'currency_symbol': Settings.get_currency_symbol(),
    })


# ============================================================
# CUSTOMER MANAGEMENT
# ============================================================

@login_required
def customers(request):
    customers_list = Customer.objects.all()

    if request.method == 'POST':
        company_name = request.POST.get('company_name', '').strip()
        contact_person = request.POST.get('contact_person', '').strip()
        country_code = request.POST.get('country_code', '+92').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        city = request.POST.get('city', '').strip()
        country = request.POST.get('country', '').strip()
        trn = request.POST.get('trn', '').strip()
        address = request.POST.get('address', '').strip()

        if not company_name or not phone:
            messages.error(request, 'Company name and phone are required.')
        elif Customer.objects.filter(phone=phone, country_code=country_code).exists():
            messages.error(request, f'Customer with phone {country_code} {phone} already exists.')
        else:
            customer = Customer.objects.create(
                company_name=company_name,
                contact_person=contact_person,
                country_code=country_code,
                phone=phone,
                email=email,
                city=city,
                country=country,
                trn=trn,
                address=address,
                created_by=request.user,
            )
            ActivityLog.objects.create(
                user=request.user,
                action=f'Added customer: {customer.company_name}',
                module='Customers',
                ip_address=get_client_ip(request)
            )
            messages.success(request, f'Customer "{company_name}" added successfully!')
        return redirect('customers')

    query = request.GET.get('q', '')
    city_filter = request.GET.get('city', '')

    if query:
        customers_list = customers_list.filter(
            Q(company_name__icontains=query) |
            Q(contact_person__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )
    if city_filter:
        customers_list = customers_list.filter(city=city_filter)

    all_customers = Customer.objects.all()
    total_customers = all_customers.count()

    active_count = 0
    total_purchases = 0
    top_customer = "—"
    top_spent = 0

    for cust in all_customers:
        cust_total = cust.total_purchases
        if cust_total > 0:
            active_count += 1
            total_purchases += cust_total
            if cust_total > top_spent:
                top_spent = cust_total
                top_customer = cust.company_name

    cities = Customer.objects.exclude(city='').values_list('city', flat=True).distinct().order_by('city')

    return render(request, 'customers.html', {
        'currency_symbol': Settings.get_currency_symbol(),
        'customers': customers_list,
        'cities': cities,
        'query': query,
        'city_filter': city_filter,
        'total_customers': total_customers,
        'active_count': active_count,
        'total_purchases': total_purchases,
        'top_customer': top_customer,
    })


@login_required
def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    invoices = customer.invoices.all().order_by('-created_at')
    return render(request, 'customer_detail.html', {
        'customer': customer,
        'invoices': invoices,
        'currency_symbol': Settings.get_currency_symbol(),
    })


@login_required
def edit_customer(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == 'POST':
        customer.company_name = request.POST.get('company_name', '').strip()
        customer.contact_person = request.POST.get('contact_person', '').strip()
        customer.country_code = request.POST.get('country_code', '+92').strip()
        customer.phone = request.POST.get('phone', '').strip()
        customer.email = request.POST.get('email', '').strip()
        customer.city = request.POST.get('city', '').strip()
        customer.country = request.POST.get('country', '').strip()
        customer.trn = request.POST.get('trn', '').strip()
        customer.address = request.POST.get('address', '').strip()
        customer.save()

        ActivityLog.objects.create(
            user=request.user,
            action=f'Updated customer: {customer.company_name}',
            module='Customers',
            ip_address=get_client_ip(request)
        )
        messages.success(request, f'Customer "{customer.company_name}" updated successfully!')
        return redirect('customers')

    return render(request, 'edit_customer.html', {
        'customer': customer,
        'currency_symbol': Settings.get_currency_symbol(),
    })


@login_required
def delete_customer(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        name = customer.company_name
        customer.delete()
        ActivityLog.objects.create(
            user=request.user,
            action=f'Deleted customer: {name}',
            module='Customers',
            ip_address=get_client_ip(request)
        )
        messages.success(request, f'Customer "{name}" deleted successfully!')
        return redirect('customers')
    return render(request, 'confirm_delete.html', {'object': customer, 'type': 'Customer'})


# ============================================================
# SUPPLIER MANAGEMENT
# ============================================================

@login_required
def suppliers(request):
    suppliers_list = Supplier.objects.all()

    if request.method == 'POST':
        company_name = request.POST.get('company_name', '').strip()
        contact_person = request.POST.get('contact_person', '').strip()
        country_code = request.POST.get('country_code', '+92').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        city = request.POST.get('city', '').strip()
        country = request.POST.get('country', '').strip()
        trn = request.POST.get('trn', '').strip()
        address = request.POST.get('address', '').strip()

        if not company_name or not phone:
            messages.error(request, 'Company name and phone are required.')
        elif Supplier.objects.filter(phone=phone, country_code=country_code).exists():
            messages.error(request, f'Supplier with phone {country_code} {phone} already exists.')
        else:
            supplier = Supplier.objects.create(
                company_name=company_name,
                contact_person=contact_person,
                country_code=country_code,
                phone=phone,
                email=email,
                city=city,
                country=country,
                trn=trn,
                address=address,
                created_by=request.user,
            )
            ActivityLog.objects.create(
                user=request.user,
                action=f'Added supplier: {supplier.company_name}',
                module='Suppliers',
                ip_address=get_client_ip(request)
            )
            messages.success(request, f'Supplier "{company_name}" added successfully!')
        return redirect('suppliers')

    query = request.GET.get('q', '')
    city_filter = request.GET.get('city', '')

    if query:
        suppliers_list = suppliers_list.filter(
            Q(company_name__icontains=query) |
            Q(contact_person__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )
    if city_filter:
        suppliers_list = suppliers_list.filter(city=city_filter)

    all_suppliers = Supplier.objects.all()
    total_suppliers = all_suppliers.count()

    active_count = 0
    total_purchases = 0
    top_supplier = "—"
    top_spent = 0

    for sup in all_suppliers:
        sup_total = sup.total_purchases
        if sup_total > 0:
            active_count += 1
            total_purchases += sup_total
            if sup_total > top_spent:
                top_spent = sup_total
                top_supplier = sup.company_name

    cities = Supplier.objects.exclude(city='').values_list('city', flat=True).distinct().order_by('city')

    return render(request, 'suppliers.html', {
        'currency_symbol': Settings.get_currency_symbol(),
        'suppliers': suppliers_list,
        'cities': cities,
        'query': query,
        'city_filter': city_filter,
        'total_suppliers': total_suppliers,
        'active_count': active_count,
        'total_purchases': total_purchases,
        'top_supplier': top_supplier,
    })


@login_required
def supplier_detail(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    entries = supplier.stock_entries.all().order_by('-entry_date')
    return render(request, 'supplier_detail.html', {
        'supplier': supplier,
        'entries': entries,
        'currency_symbol': Settings.get_currency_symbol(),
    })


@login_required
def edit_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)

    if request.method == 'POST':
        supplier.company_name = request.POST.get('company_name', '').strip()
        supplier.contact_person = request.POST.get('contact_person', '').strip()
        supplier.country_code = request.POST.get('country_code', '+92').strip()
        supplier.phone = request.POST.get('phone', '').strip()
        supplier.email = request.POST.get('email', '').strip()
        supplier.city = request.POST.get('city', '').strip()
        supplier.country = request.POST.get('country', '').strip()
        supplier.trn = request.POST.get('trn', '').strip()
        supplier.address = request.POST.get('address', '').strip()
        supplier.save()

        ActivityLog.objects.create(
            user=request.user,
            action=f'Updated supplier: {supplier.company_name}',
            module='Suppliers',
            ip_address=get_client_ip(request)
        )
        messages.success(request, f'Supplier "{supplier.company_name}" updated successfully!')
        return redirect('suppliers')

    return render(request, 'edit_supplier.html', {
        'supplier': supplier,
        'currency_symbol': Settings.get_currency_symbol(),
    })


@login_required
def delete_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    if request.method == 'POST':
        name = supplier.company_name
        supplier.delete()
        ActivityLog.objects.create(
            user=request.user,
            action=f'Deleted supplier: {name}',
            module='Suppliers',
            ip_address=get_client_ip(request)
        )
        messages.success(request, f'Supplier "{name}" deleted successfully!')
        return redirect('suppliers')
    return render(request, 'confirm_delete.html', {'object': supplier, 'type': 'Supplier'})


# ============================================================
# INVOICE MANAGEMENT
# ============================================================

@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related('customer', 'created_by').all()
    query = request.GET.get('q', '')
    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query) |
            Q(customer__company_name__icontains=query) |
            Q(customer_name__icontains=query)
        )

    today = timezone.now().date()
    context = {
        'currency_symbol': Settings.get_currency_symbol(),
        'invoices': invoices,
        'query': query,
        'total_invoices': invoices.count(),
        'total_sales': invoices.aggregate(Sum('grand_total'))['grand_total__sum'] or 0,
        'paid_count': invoices.filter(payment_status='PAID').count(),
        'today_count': invoices.filter(created_at__date=today).count(),
    }
    return render(request, 'invoice_list.html', context)


@login_required
def create_invoice(request):
    settings_obj = Settings.get_settings()

    if request.method == 'POST':
        customer_id = request.POST.get('customer', '')
        customer_name = request.POST.get('customer_name', '')
        discount_percent = Decimal(request.POST.get('discount_percent', '0') or '0')
        tax_percent = Decimal(request.POST.get('tax_percent', '0') or '0')
        tax_name = request.POST.get('tax_name', settings_obj.tax_name)
        payment_method = request.POST.get('payment_method', 'CASH')
        notes = request.POST.get('notes', '')

        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')
        prices = request.POST.getlist('price[]')

        # ============================================================
        # STOCK VALIDATION
        # ============================================================
        stock_errors = []
        if product_ids:
            for i in range(len(product_ids)):
                product = Product.objects.filter(id=product_ids[i]).first()
                if product:
                    qty = int(quantities[i])
                    if qty > product.quantity:
                        stock_errors.append(
                            f"Only {product.quantity} units of '{product.name}' available."
                        )

        # ============================================================
        # IF STOCK ERROR → PRESERVE FORM DATA
        # ============================================================
        if stock_errors:
            for err in stock_errors:
                messages.error(request, err)

            form_items = []
            for i in range(len(product_ids)):
                p = Product.objects.filter(id=product_ids[i]).first()
                if p:
                    form_items.append({
                        'product_id': p.id,
                        'qty': int(quantities[i]),
                        'price': str(prices[i]),
                    })

            return render(request, 'create_invoice.html', {
                'currency_symbol': Settings.get_currency_symbol(),
                'settings': settings_obj,
                'customers': Customer.objects.all(),
                'products': Product.objects.filter(quantity__gt=0),
                'preserved': {
                    'customer_id': customer_id,
                    'customer_name': customer_name,
                    'discount_percent': str(discount_percent),
                    'tax_percent': str(tax_percent),
                    'payment_method': payment_method,
                    'notes': notes,
                    'items': form_items,
                },
            })

        # ============================================================
        # NO ERRORS → CREATE INVOICE
        # ============================================================
        if not product_ids:
            messages.error(request, 'Please add at least one product')
            return redirect('create_invoice')

        try:
            with transaction.atomic():
                customer = Customer.objects.filter(id=customer_id).first() if customer_id else None
                invoice = Invoice.objects.create(
                    invoice_number=f"INV-{timezone.now().strftime('%Y%m%d')}-{Invoice.objects.count() + 1:04d}",
                    customer=customer,
                    customer_name=customer_name,
                    created_by=request.user,
                    discount_percent=discount_percent,
                    tax_name=tax_name,
                    tax_percent=tax_percent,
                    payment_method=payment_method,
                    payment_status='PAID',
                    notes=notes
                )
                total = Decimal('0')
                for i in range(len(product_ids)):
                    product = get_object_or_404(Product, id=product_ids[i])
                    qty = int(quantities[i])
                    price = Decimal(prices[i])
                    item_total = price * qty
                    total += item_total
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        product=product,
                        quantity=qty,
                        price=price,
                        total=item_total
                    )
                    old_qty = product.quantity
                    product.quantity -= qty
                    product.save()
                    StockMovement.objects.create(
                        product=product,
                        quantity=-qty,
                        movement_type='OUT',
                        quantity_before=old_qty,
                        quantity_after=product.quantity,
                        reference=f'INV-{invoice.invoice_number}',
                        note='Sale',
                        created_by=request.user
                    )
                invoice.subtotal = total
                invoice.calculate_totals()
                invoice.save()

                # Low stock notification
                for product in Product.objects.filter(quantity__lte=F('low_stock_threshold'), quantity__gt=0):
                    if not Notification.objects.filter(user=request.user, title__icontains=product.name, is_read=False).exists():
                        Notification.objects.create(
                            user=request.user,
                            title=f'Low Stock: {product.name}',
                            message=f'{product.name} is running low. Only {product.quantity} units remaining.'
                        )

                ActivityLog.objects.create(
                    user=request.user,
                    action=f'Created invoice {invoice.invoice_number}',
                    module='Sales',
                    ip_address=get_client_ip(request)
                )
            messages.success(request, f'Invoice {invoice.invoice_number} created successfully!')
            return redirect('invoice_detail', invoice.id)

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('create_invoice')

    return render(request, 'create_invoice.html', {
        'currency_symbol': Settings.get_currency_symbol(),
        'settings': settings_obj,
        'customers': Customer.objects.all(),
        'products': Product.objects.filter(quantity__gt=0),
    })

@login_required
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    return render(request, 'invoice_detail.html', {
        'invoice': invoice,
        'settings': Settings.get_settings(),
        'currency_symbol': Settings.get_currency_symbol(),
    })


@login_required
def print_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    return render(request, 'print_invoice.html', {
        'invoice': invoice,
        'settings': Settings.get_settings(),
        'currency_symbol': Settings.get_currency_symbol(),
    })


@login_required
def download_invoice_pdf(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        settings_obj = Settings.get_settings()
        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        p.setFont("Helvetica-Bold", 18)
        p.drawString(50, height - 50, settings_obj.company_name)
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 70, settings_obj.company_address)
        p.drawString(50, height - 85, f"Phone: {settings_obj.company_phone}")

        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, height - 130, f"INVOICE: {invoice.invoice_number}")
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 150, f"Date: {invoice.created_at.strftime('%d %b %Y')}")
        customer_display = invoice.customer.company_name if invoice.customer else (invoice.customer_name or 'Walk-in')
        p.drawString(50, height - 165, f"Bill To: {customer_display}")

        y = height - 200
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y, "Product")
        p.drawString(300, y, "Qty")
        p.drawString(370, y, "Price")
        p.drawString(450, y, "Total")
        y -= 15
        p.setFont("Helvetica", 10)
        for item in invoice.items.all():
            p.drawString(50, y, item.product.name[:40])
            p.drawString(300, y, str(item.quantity))
            p.drawString(370, y, f"{Settings.get_currency_symbol()}{item.price}")
            p.drawString(450, y, f"{Settings.get_currency_symbol()}{item.total}")
            y -= 15

        y -= 20
        p.drawString(370, y, f"Subtotal: {Settings.get_currency_symbol()}{invoice.subtotal}"); y -= 15
        p.drawString(370, y, f"Discount: {Settings.get_currency_symbol()}{invoice.discount}"); y -= 15
        p.drawString(370, y, f"{invoice.tax_name}: {Settings.get_currency_symbol()}{invoice.tax}"); y -= 15
        p.setFont("Helvetica-Bold", 12)
        p.drawString(370, y, f"Grand Total: {Settings.get_currency_symbol()}{invoice.grand_total}")

        p.showPage()
        p.save()
    except ImportError:
        response = HttpResponse("PDF library not installed")
    return response


# ============================================================
# STOCK ENTRIES (PURCHASE FROM SUPPLIER)
# ============================================================

@login_required
@role_required(['Admin', 'Manager'])
def stock_entries(request):
    entries = StockEntry.objects.select_related('supplier', 'created_by').all()

    today = timezone.now().date()
    month_start = today.replace(day=1)

    total_value = entries.aggregate(total=Sum('total_amount'))['total'] or 0
    total_suppliers = StockEntry.objects.values('supplier').distinct().count()
    this_month_value = StockEntry.objects.filter(entry_date__gte=month_start).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    return render(request, 'stock_entries.html', {
        'entries': entries,
        'total_entries': entries.count(),
        'total_value': total_value,
        'total_suppliers': total_suppliers,
        'this_month_value': this_month_value,
        'currency_symbol': Settings.get_currency_symbol(),
    })


@login_required
@role_required(['Admin', 'Manager'])
def create_stock_entry(request):
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        invoice_no = request.POST.get('purchase_invoice_no')
        notes = request.POST.get('notes', '')
        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')
        costs = request.POST.getlist('unit_cost[]')

        if not product_ids:
            messages.error(request, 'Please add at least one product')
            return redirect('create_stock_entry')

        with transaction.atomic():
            supplier = Supplier.objects.filter(id=supplier_id).first()
            entry = StockEntry.objects.create(
                supplier=supplier,
                purchase_invoice_no=invoice_no or f"PO-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                notes=notes,
                created_by=request.user
            )
            total = Decimal('0')
            for i in range(len(product_ids)):
                product = get_object_or_404(Product, id=product_ids[i])
                qty = int(quantities[i])
                cost = Decimal(costs[i])
                subtotal = cost * qty
                total += subtotal
                StockEntryItem.objects.create(
                    stock_entry=entry,
                    product=product,
                    quantity=qty,
                    unit_cost=cost,
                    subtotal=subtotal
                )
                old_qty = product.quantity
                product.quantity += qty
                product.purchase_price = cost
                product.save()
                StockMovement.objects.create(
                    product=product,
                    quantity=qty,
                    movement_type='IN',
                    quantity_before=old_qty,
                    quantity_after=product.quantity,
                    reference=f'PO-{entry.purchase_invoice_no}',
                    note=f'Purchase from {supplier.company_name if supplier else "N/A"}',
                    created_by=request.user
                )
            entry.subtotal = total
            entry.total_amount = total
            entry.save()

            ActivityLog.objects.create(
                user=request.user,
                action=f'Created stock entry PO-{entry.purchase_invoice_no}',
                module='Stock',
                ip_address=get_client_ip(request)
            )
        messages.success(request, f'Stock entry created successfully! Total: {Settings.get_currency_symbol()}{total}')
        return redirect('stock_entries')

    return render(request, 'create_stock_entry.html', {
        'suppliers': Supplier.objects.all(),
        'products': Product.objects.all(),
        'currency_symbol': Settings.get_currency_symbol(),
    })
# ============================================================
# RETURNS
# ============================================================

@login_required
def returns(request):
    if request.method == 'POST':
        try:
            invoice_id = request.POST.get('invoice_id')
            product_id = request.POST.get('product_id')
            quantity = int(request.POST.get('quantity', 0))
            reason = request.POST.get('reason', '')
            condition = request.POST.get('condition', 'RESELLABLE')

            invoice = get_object_or_404(Invoice, id=invoice_id)
            product = get_object_or_404(Product, id=product_id)

            already_returned = ReturnItem.objects.filter(
                invoice=invoice, product=product
            ).aggregate(total=Sum('quantity'))['total'] or 0

            item = InvoiceItem.objects.filter(invoice=invoice, product=product).first()
            if not item:
                messages.error(request, 'This product is not in the selected invoice.')
                return redirect('returns')

            if quantity <= 0 or (already_returned + quantity) > item.quantity:
                messages.error(request, f'Invalid quantity. Max returnable: {item.quantity - already_returned}')
                return redirect('returns')

            with transaction.atomic():
                refund = item.price * quantity
                ReturnItem.objects.create(
                    invoice=invoice,
                    product=product,
                    quantity=quantity,
                    refund_amount=refund,
                    reason=reason,
                    condition=condition,
                    processed_by=request.user
                )
                if condition == 'RESELLABLE':
                    old_qty = product.quantity
                    product.quantity += quantity
                    product.save()
                    StockMovement.objects.create(
                        product=product,
                        quantity=quantity,
                        movement_type='IN',
                        quantity_before=old_qty,
                        quantity_after=product.quantity,
                        reference=f'Return from {invoice.invoice_number}',
                        note=f'Return processed - {reason}',
                        created_by=request.user
                    )
                ActivityLog.objects.create(
                    user=request.user,
                    action=f'Processed return for {product.name} (Invoice {invoice.invoice_number})',
                    module='Returns',
                    ip_address=get_client_ip(request)
                )
            messages.success(request, f'Return processed! Refund: {Settings.get_currency_symbol()}{refund}')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('returns')

    invoices = Invoice.objects.all().order_by('-created_at')
    products = Product.objects.all()
    returns_list = ReturnItem.objects.select_related('invoice', 'product', 'processed_by').all()

    total_refund = returns_list.aggregate(total=Sum('refund_amount'))['total'] or 0
    resellable_count = returns_list.filter(condition='RESELLABLE').count()
    damaged_count = returns_list.filter(condition='DAMAGED').count()

    return render(request, 'returns.html', {
        'invoices': invoices,
        'products': products,
        'returns_list': returns_list,
        'total_refund': total_refund,
        'resellable_count': resellable_count,
        'damaged_count': damaged_count,
        'currency_symbol': Settings.get_currency_symbol(),
    })


# ============================================================
# REPORTS
# ============================================================

@login_required
def reports(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    range_type = request.GET.get('range', '')

    today = timezone.now().date()

    if range_type == 'today':
        start_date = today.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif range_type == 'week':
        start_date = (today - timedelta(days=6)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif range_type == 'month':
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif range_type == 'year':
        start_date = today.replace(month=1, day=1).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    else:
        if not start_date:
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = today.strftime('%Y-%m-%d')

    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

    invoices = Invoice.objects.filter(created_at__range=[start, end]).select_related('customer')
    total_sales = invoices.aggregate(Sum('grand_total'))['grand_total__sum'] or 0
    total_invoices = invoices.count()

    product_sales = InvoiceItem.objects.filter(
        invoice__created_at__range=[start, end]
    ).values('product__name').annotate(
        qty=Sum('quantity'),
        revenue=Sum('total')
    ).order_by('-revenue')

    profit = Decimal('0')
    for item in InvoiceItem.objects.filter(invoice__created_at__range=[start, end]).select_related('product'):
        profit += (item.price - item.product.purchase_price) * item.quantity

    top_customers = Customer.objects.annotate(
        total=Sum('invoices__grand_total')
    ).filter(
        total__gt=0,
        invoices__created_at__range=[start, end]
    ).order_by('-total')[:5]

    # Chart data
    chart_labels = []
    chart_data = []
    profit_data = []
    for i in range(5, -1, -1):
        month_date = (today.replace(day=1) - timedelta(days=i*30))
        month_start = month_date.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)

        month_sales = Invoice.objects.filter(
            created_at__range=[month_start, next_month]
        ).aggregate(Sum('grand_total'))['grand_total__sum'] or 0

        month_profit = Decimal('0')
        for item in InvoiceItem.objects.filter(
            invoice__created_at__range=[month_start, next_month]
        ).select_related('product'):
            month_profit += (item.price - item.product.purchase_price) * item.quantity

        chart_labels.append(month_date.strftime('%b'))
        chart_data.append(float(month_sales))
        profit_data.append(float(month_profit))

    return render(request, 'reports.html', {
        'start_date': start_date,
        'end_date': end_date,
        'range_type': range_type,
        'invoices': invoices,
        'total_sales': total_sales,
        'total_invoices': total_invoices,
        'product_sales': product_sales,
        'profit': profit,
        'top_customers': top_customers,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'profit_data': json.dumps(profit_data),
        'currency_symbol': Settings.get_currency_symbol(),
    })


# ============================================================
# USER MANAGEMENT
# ============================================================

@login_required
@role_required(['Admin'])
def user_list(request):
    users_qs = User.objects.all().order_by('-date_joined')

    query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')

    if query:
        users_qs = users_qs.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    if role_filter == 'Admin':
        users_qs = users_qs.filter(is_superuser=True)
    elif role_filter == 'Manager':
        users_qs = users_qs.filter(is_staff=True, is_superuser=False)
    elif role_filter == 'Salesman':
        users_qs = users_qs.filter(is_staff=False, is_superuser=False)

    context = {
        'users': users_qs,
        'query': query,
        'role_filter': role_filter,
        'total_users': User.objects.count(),
        'admin_count': User.objects.filter(is_superuser=True).count(),
        'manager_count': User.objects.filter(is_staff=True, is_superuser=False).count(),
        'salesman_count': User.objects.filter(is_staff=False, is_superuser=False).count(),
        'currency_symbol': Settings.get_currency_symbol(),
    }
    return render(request, 'user_list.html', context)


@login_required
@role_required(['Admin'])
def create_staff(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', 'Salesman')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        if not username or not password:
            messages.error(request, 'Username and password are required.')
        elif len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already exists.')
        elif email and User.objects.filter(email=email).exists():
            messages.error(request, f'Email "{email}" already exists.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            if role == 'Manager':
                user.is_staff = True
                user.save()

            ActivityLog.objects.create(
                user=request.user,
                action=f'Created {role} account: {username}',
                module='User Management',
                ip_address=get_client_ip(request)
            )
            messages.success(request, f'{role} "{username}" created successfully!')
            return redirect('user_list')

        return redirect('create_staff')

    return render(request, 'create_staff.html')


@login_required
@role_required(['Admin'])
def toggle_user_status(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    if user_obj == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('user_list')

    user_obj.is_active = not user_obj.is_active
    user_obj.save()

    ActivityLog.objects.create(
        user=request.user,
        action=f'{"Activated" if user_obj.is_active else "Deactivated"} user: {user_obj.username}',
        module='User Management',
        ip_address=get_client_ip(request)
    )

    status = "activated" if user_obj.is_active else "deactivated"
    messages.success(request, f'User "{user_obj.username}" has been {status}.')
    return redirect('user_list')


# ============================================================
# ACTIVITY LOGS
# ============================================================

@login_required
@role_required(['Admin', 'Manager'])
def activity_logs(request):
    logs_qs = ActivityLog.objects.select_related('user').all()

    user_id = request.GET.get('user', '')
    module = request.GET.get('module', '')
    query = request.GET.get('q', '')

    if user_id:
        logs_qs = logs_qs.filter(user_id=user_id)
    if module:
        logs_qs = logs_qs.filter(module=module)
    if query:
        logs_qs = logs_qs.filter(action__icontains=query)

    today = timezone.now().date()
    context = {
        'logs': logs_qs[:500],
        'users': User.objects.all().order_by('username'),
        'modules': ActivityLog.objects.exclude(module='').values_list('module', flat=True).distinct().order_by('module'),
        'user_id': user_id,
        'module': module,
        'query': query,
        'total_logs': ActivityLog.objects.count(),
        'today_count': ActivityLog.objects.filter(timestamp__date=today).count(),
        'unique_users': ActivityLog.objects.values('user').distinct().count(),
    }
    return render(request, 'activity_logs.html', context)


# ============================================================
# NOTIFICATIONS
# ============================================================

@login_required
def notifications(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications.html', {'notifications': notifs})


# ============================================================
# GLOBAL SEARCH
# ============================================================

@login_required
def global_search(request):
    q = request.GET.get('q', '')
    results = {'products': [], 'customers': [], 'invoices': []}
    if q:
        results['products'] = Product.objects.filter(Q(name__icontains=q) | Q(sku__icontains=q))[:10]
        results['customers'] = Customer.objects.filter(Q(company_name__icontains=q) | Q(phone__icontains=q))[:10]
        results['invoices'] = Invoice.objects.filter(invoice_number__icontains=q)[:10]
    return render(request, 'search_results.html', {
        'query': q,
        'results': results,
        'currency_symbol': Settings.get_currency_symbol(),
    })


# ============================================================
# DATA BACKUP
# ============================================================

@login_required
@role_required(['Admin'])
def backup_data(request):
    data = {
        'settings': list(Settings.objects.values()),
        'products': list(Product.objects.values()),
        'customers': list(Customer.objects.values()),
        'suppliers': list(Supplier.objects.values()),
        'invoices': list(Invoice.objects.values()),
        'invoice_items': list(InvoiceItem.objects.values()),
        'stock_entries': list(StockEntry.objects.values()),
        'stock_movements': list(StockMovement.objects.values()),
        'returns': list(ReturnItem.objects.values()),
    }
    response = HttpResponse(json.dumps(data, indent=2, default=str), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="backup_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
    ActivityLog.objects.create(
        user=request.user,
        action='Downloaded data backup',
        module='System',
        ip_address=get_client_ip(request)
    )
    return response


# ============================================================
# BARCODE / QR CODE
# ============================================================

@login_required
def product_barcode(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if not product.barcode:
        product.barcode = f"{product.id:013d}"
        product.save()
    barcode_file = generate_barcode_image(product.barcode, product.name)
    if barcode_file:
        return HttpResponse(barcode_file.read(), content_type='image/png')
    return HttpResponse("Barcode generation failed", status=500)


@login_required
def product_qr(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    qr_data = generate_product_qr_data(product)
    qr_file = generate_qr_code_image(qr_data, product.sku or str(product.id))
    if qr_file:
        return HttpResponse(qr_file.read(), content_type='image/png')
    return HttpResponse("QR generation failed", status=500)


@login_required
def print_barcode_labels(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'print_barcode.html', {
        'product': product,
        'currency_symbol': Settings.get_currency_symbol(),
    })


@login_required
def scan_barcode(request):
    product = None
    error = None

    if request.method == 'POST':
        barcode_value = request.POST.get('barcode', '').strip()
        if barcode_value:
            product = Product.objects.filter(Q(barcode=barcode_value) | Q(sku=barcode_value)).first()
            if not product:
                error = f"No product found with barcode/SKU: {barcode_value}"
        else:
            error = "Please enter a barcode."

    return render(request, 'scan_barcode.html', {
        'product': product,
        'error': error,
        'currency_symbol': Settings.get_currency_symbol(),
    })


@login_required
def regenerate_barcode_qr(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if generate_barcode_for_product(product):
        messages.success(request, f'Barcode & QR regenerated for {product.name}')
    else:
        messages.error(request, 'Failed to regenerate barcode/QR')
    return redirect('edit_inventory', product_id=product.id)
@login_required
def notifications_count(request):
    """Returns count of unread notifications for polling."""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})
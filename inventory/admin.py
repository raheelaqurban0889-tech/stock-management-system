from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import (
    Settings, Category, Product, StockMovement,
    Customer, Supplier, StockEntry, StockEntryItem,
    Invoice, InvoiceItem, ReturnItem, ActivityLog, Notification
)


# ============================================================
# CUSTOM FORMS WITH DROPDOWNS
# ============================================================
COUNTRY_CODE_CHOICES = [
    ('+92', '🇵🇰 Pakistan (+92)'),
    ('+971', '🇦🇪 UAE (+971)'),
    ('+966', '🇸🇦 Saudi Arabia (+966)'),
    ('+974', '🇶🇦 Qatar (+974)'),
    ('+965', '🇰🇼 Kuwait (+965)'),
    ('+973', '🇧🇭 Bahrain (+973)'),
    ('+968', '🇴🇲 Oman (+968)'),
    ('+1', '🇺🇸 USA (+1)'),
    ('+44', '🇬🇧 UK (+44)'),
]


class SupplierAdminForm(forms.ModelForm):
    country_code = forms.ChoiceField(
        choices=COUNTRY_CODE_CHOICES,
        initial='+92',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Supplier
        fields = '__all__'


class CustomerAdminForm(forms.ModelForm):
    country_code = forms.ChoiceField(
        choices=COUNTRY_CODE_CHOICES,
        initial='+92',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Customer
        fields = '__all__'


# ============================================================
# SETTINGS ADMIN
# ============================================================
@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'country', 'currency', 'tax_name', 'tax_percent']

    def has_add_permission(self, request):
        return not Settings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# ============================================================
# CATEGORY ADMIN
# ============================================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


# ============================================================
# PRODUCT ADMIN
# ============================================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'barcode', 'category', 'price', 'quantity', 'status_badge']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'sku', 'barcode']
    list_editable = ['price', 'quantity']

    def status_badge(self, obj):
        if obj.quantity <= 0:
            color = '#ef4444'
            label = 'Out of Stock'
        elif obj.quantity <= obj.low_stock_threshold:
            color = '#f59e0b'
            label = 'Low Stock'
        else:
            color = '#10b981'
            label = 'Available'
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Status'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'quantity_before', 'quantity_after', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'reference']


# ============================================================
# CUSTOMER ADMIN (with country code dropdown)
# ============================================================
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    form = CustomerAdminForm
    list_display = ['company_name', 'contact_person', 'full_phone_display', 'email', 'city', 'country']
    search_fields = ['company_name', 'contact_person', 'phone', 'email']

    def full_phone_display(self, obj):
        return f"{obj.country_code} {obj.phone}"
    full_phone_display.short_description = 'Phone'


# ============================================================
# SUPPLIER ADMIN (with country code dropdown)
# ============================================================
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    form = SupplierAdminForm
    list_display = ['company_name', 'contact_person', 'full_phone_display', 'email', 'city', 'country']
    search_fields = ['company_name', 'contact_person', 'phone', 'email']

    def full_phone_display(self, obj):
        return f"{obj.country_code} {obj.phone}"
    full_phone_display.short_description = 'Phone'


# ============================================================
# STOCK ENTRY ADMIN
# ============================================================
class StockEntryItemInline(admin.TabularInline):
    model = StockEntryItem
    extra = 1


@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):
    list_display = ['purchase_invoice_no', 'supplier', 'subtotal', 'tax_amount', 'total_amount', 'entry_date']
    list_filter = ['entry_date']
    inlines = [StockEntryItemInline]


# ============================================================
# INVOICE ADMIN
# ============================================================
class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'grand_total', 'payment_status', 'created_at']
    list_filter = ['payment_status', 'payment_method', 'created_at']
    search_fields = ['invoice_number', 'customer__company_name', 'customer_name']
    inlines = [InvoiceItemInline]


@admin.register(ReturnItem)
class ReturnItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'invoice', 'product', 'quantity', 'condition', 'refund_amount', 'returned_at']
    list_filter = ['condition', 'returned_at']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'module', 'ip_address', 'timestamp']
    list_filter = ['module', 'timestamp']
    search_fields = ['user__username', 'action']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
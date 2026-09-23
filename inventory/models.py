from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


# ============================================================
# SETTINGS (Global Configuration)
# ============================================================
class Settings(models.Model):
    """Global system settings - single row table"""
    CURRENCY_CHOICES = [
        ('PKR', 'Pakistani Rupee (₨)'),
        ('AED', 'UAE Dirham (د.إ)'),
        ('SAR', 'Saudi Riyal (﷼)'),
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
    ]

    COUNTRY_CHOICES = [
        ('PK', 'Pakistan'),
        ('AE', 'United Arab Emirates'),
        ('SA', 'Saudi Arabia'),
        ('US', 'United States'),
        ('GB', 'United Kingdom'),
    ]

    # Company Info
    company_name = models.CharField(max_length=200, default='My Company LLC')
    company_address = models.TextField(blank=True, default='')
    company_phone = models.CharField(max_length=30, blank=True, default='')
    company_email = models.EmailField(blank=True, default='')
    company_trn = models.CharField(max_length=50, blank=True, help_text="Tax Registration Number", default='')
    company_logo = models.ImageField(upload_to='company/', blank=True, null=True)

    # Country & Currency
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default='AE')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='AED')

    # Tax Settings
    tax_name = models.CharField(max_length=20, default='VAT', help_text="VAT, GST, Sales Tax")
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)

    class Meta:
        verbose_name = "Settings"
        verbose_name_plural = "Settings"

    def __str__(self):
        return f"{self.company_name} - {self.currency}"

    @classmethod
    def get_settings(cls):
        """Get or create the single settings instance"""
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    @classmethod
    def get_currency_symbol(cls):
        """Return currency symbol"""
        symbols = {
            'PKR': '₨',
            'AED': 'د.إ',
            'SAR': '﷼',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
        }
        settings_obj = cls.get_settings()
        return symbols.get(settings_obj.currency, '$')


# ============================================================
# CATEGORY
# ============================================================
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


# ============================================================
# SUPPLIER (Company-first)
# ============================================================
class Supplier(models.Model):
    """Supplier - Company name is primary, person name optional"""
    # PRIMARY: Company name
    company_name = models.CharField(max_length=200, help_text="Primary - Company/LLC name")
    
    # SECONDARY: Person name (optional)
    contact_person = models.CharField(max_length=200, blank=True, help_text="Optional - Person name")
    
    # Contact
    country_code = models.CharField(max_length=5, default='+971')
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, help_text="Email address")
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True, default='UAE')
    
    # Business
    trn = models.CharField(max_length=50, blank=True, help_text="Tax Registration Number")
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name

    @property
    def display_name(self):
        if self.contact_person:
            return f"{self.company_name} ({self.contact_person})"
        return self.company_name

    @property
    def full_phone(self):
        return f"{self.country_code} {self.phone}"

    @property
    def total_purchases(self):
        return self.stock_entries.aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0


# ============================================================
# CUSTOMER (Company-first)
# ============================================================
class Customer(models.Model):
    """Customer - Company name is primary, person name optional"""
    # PRIMARY: Company name
    company_name = models.CharField(max_length=200, help_text="Primary - Company/LLC name")
    
    # SECONDARY: Person name (optional)
    contact_person = models.CharField(max_length=200, blank=True, help_text="Optional - Person name")
    
    # Contact
    country_code = models.CharField(max_length=5, default='+971')
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, help_text="Email address")
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True, default='UAE')
    
    # Business
    trn = models.CharField(max_length=50, blank=True, help_text="Tax Registration Number")
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name

    @property
    def display_name(self):
        if self.contact_person:
            return f"{self.company_name} ({self.contact_person})"
        return self.company_name

    @property
    def full_phone(self):
        return f"{self.country_code} {self.phone}"

    @property
    def total_purchases(self):
        return self.invoices.aggregate(
            total=models.Sum('grand_total')
        )['total'] or 0


# ============================================================
# PRODUCT
# ============================================================
class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)
    barcode = models.CharField(max_length=50, blank=True, null=True, unique=True)
    barcode_image = models.ImageField(upload_to='barcodes/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    description = models.TextField(blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.IntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    unit = models.CharField(max_length=20, default='Piece')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku or 'No SKU'})"

    @property
    def stock_value(self):
        return self.purchase_price * self.quantity

    @property
    def is_low_stock(self):
        return 0 < self.quantity <= self.low_stock_threshold

    @property
    def is_out_of_stock(self):
        return self.quantity <= 0

    @property
    def status(self):
        if self.quantity <= 0:
            return 'Out of Stock'
        elif self.quantity <= self.low_stock_threshold:
            return 'Low Stock'
        return 'Available'


# ============================================================
# STOCK MOVEMENT
# ============================================================
class StockMovement(models.Model):
    MOVEMENT_TYPES = (
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUST', 'Adjustment'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    quantity = models.IntegerField()
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity_before = models.IntegerField(default=0)
    quantity_after = models.IntegerField(default=0)
    reference = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.movement_type} ({self.quantity})"


# ============================================================
# STOCK ENTRY (Purchase from Supplier)
# ============================================================
class StockEntry(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='stock_entries')
    purchase_invoice_no = models.CharField(max_length=50, unique=True)
    entry_date = models.DateField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Stock Entries"

    def __str__(self):
        return f"PO-{self.purchase_invoice_no}"


class StockEntryItem(models.Model):
    stock_entry = models.ForeignKey(StockEntry, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_cost * self.quantity
        super().save(*args, **kwargs)


# ============================================================
# INVOICE (Sales to Customer)
# ============================================================
class Invoice(models.Model):
    PAYMENT_STATUS = (
        ('PAID', 'Paid'),
        ('UNPAID', 'Unpaid'),
        ('PARTIAL', 'Partial'),
    )
    PAYMENT_METHODS = (
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('BANK', 'Bank Transfer'),
        ('CREDIT', 'Credit'),
    )
    
    invoice_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    customer_name = models.CharField(max_length=200, blank=True, help_text="Walk-in customer name")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invoices')
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    tax_name = models.CharField(max_length=20, default='VAT')
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PAID')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number}"

    def calculate_totals(self):
        self.subtotal = sum(item.total for item in self.items.all())
        
        if self.discount_percent > 0:
            self.discount = (self.subtotal * self.discount_percent) / Decimal('100')
        
        after_discount = self.subtotal - self.discount
        
        if self.tax_percent > 0:
            self.tax = (after_discount * self.tax_percent) / Decimal('100')
        
        self.grand_total = after_discount + self.tax


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total = (self.price * self.quantity) - self.discount
        super().save(*args, **kwargs)


# ============================================================
# RETURN
# ============================================================
class ReturnItem(models.Model):
    CONDITION_CHOICES = (
        ('RESELLABLE', 'Resellable'),
        ('DAMAGED', 'Damaged'),
    )
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='returns')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reason = models.TextField(blank=True)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='RESELLABLE')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    returned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-returned_at']

    def __str__(self):
        return f"Return #{self.id} - {self.product.name}"


# ============================================================
# ACTIVITY LOG
# ============================================================
class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    module = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.action}"


# ============================================================
# NOTIFICATION
# ============================================================
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
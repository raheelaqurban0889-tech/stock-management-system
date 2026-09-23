from django import forms
from .models import (
    Product, Customer, Supplier, Invoice, Category,
    StockEntry, Settings
)


# ============================================================
# HELPER — Country Codes
# ============================================================
COUNTRY_CODE_CHOICES = [
    ('+971', '🇦🇪 UAE (+971)'),
    ('+92', '🇵🇰 Pakistan (+92)'),
    ('+966', '🇸🇦 Saudi Arabia (+966)'),
    ('+974', '🇶🇦 Qatar (+974)'),
    ('+965', '🇰🇼 Kuwait (+965)'),
    ('+973', '🇧🇭 Bahrain (+973)'),
    ('+968', '🇴🇲 Oman (+968)'),
    ('+1', '🇺🇸 USA (+1)'),
    ('+44', '🇬🇧 UK (+44)'),
]


# ============================================================
# SETTINGS FORM
# ============================================================
class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = [
            'company_name', 'company_address', 'company_phone',
            'company_email', 'company_trn', 'company_logo',
            'country', 'currency', 'tax_name', 'tax_percent'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-input-custom'}),
            'company_address': forms.Textarea(attrs={'class': 'form-input-custom', 'rows': 2}),
            'company_phone': forms.TextInput(attrs={'class': 'form-input-custom'}),
            'company_email': forms.EmailInput(attrs={'class': 'form-input-custom'}),
            'company_trn': forms.TextInput(attrs={'class': 'form-input-custom'}),
            'country': forms.Select(attrs={'class': 'form-input-custom'}),
            'currency': forms.Select(attrs={'class': 'form-input-custom'}),
            'tax_name': forms.TextInput(attrs={'class': 'form-input-custom'}),
            'tax_percent': forms.NumberInput(attrs={'class': 'form-input-custom', 'step': '0.01'}),
        }


# ============================================================
# PRODUCT FORM
# ============================================================
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'barcode', 'category', 'supplier', 'description',
            'purchase_price', 'price', 'quantity', 'low_stock_threshold',
            'unit', 'image'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input-custom', 'placeholder': 'Product name'}),
            'sku': forms.TextInput(attrs={'class': 'form-input-custom', 'placeholder': 'Auto-generated if blank'}),
            'barcode': forms.TextInput(attrs={'class': 'form-input-custom', 'placeholder': 'Auto-generated if blank'}),
            'category': forms.Select(attrs={'class': 'form-input-custom'}),
            'supplier': forms.Select(attrs={'class': 'form-input-custom'}),
            'description': forms.Textarea(attrs={'class': 'form-input-custom', 'rows': 3}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-input-custom', 'step': '0.01'}),
            'price': forms.NumberInput(attrs={'class': 'form-input-custom', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input-custom'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-input-custom'}),
            'unit': forms.TextInput(attrs={'class': 'form-input-custom'}),
        }


# ============================================================
# CUSTOMER FORM (Company-first)
# ============================================================
class CustomerForm(forms.ModelForm):
    country_code = forms.ChoiceField(
        choices=COUNTRY_CODE_CHOICES,
        initial='+971',
        widget=forms.Select(attrs={'class': 'form-input-custom'})
    )

    class Meta:
        model = Customer
        fields = [
            'company_name', 'contact_person',
            'country_code', 'phone', 'email',
            'address', 'city', 'country', 'trn'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-input-custom',
                'placeholder': 'e.g., ABC Trading LLC',
                'required': True
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-input-custom',
                'placeholder': 'Optional — e.g., Ahmed Khan'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input-custom',
                'placeholder': 'e.g., 50 123 4567'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input-custom',
                'placeholder': 'e.g., info@company.com'
            }),
            'address': forms.Textarea(attrs={'class': 'form-input-custom', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-input-custom'}),
            'country': forms.TextInput(attrs={'class': 'form-input-custom'}),
            'trn': forms.TextInput(attrs={'class': 'form-input-custom', 'placeholder': 'Tax Registration Number'}),
        }


# ============================================================
# SUPPLIER FORM (Company-first)
# ============================================================
class SupplierForm(forms.ModelForm):
    country_code = forms.ChoiceField(
        choices=COUNTRY_CODE_CHOICES,
        initial='+971',
        widget=forms.Select(attrs={'class': 'form-input-custom'})
    )

    class Meta:
        model = Supplier
        fields = [
            'company_name', 'contact_person',
            'country_code', 'phone', 'email',
            'address', 'city', 'country', 'trn'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-input-custom',
                'placeholder': 'e.g., XYZ Suppliers LLC',
                'required': True
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-input-custom',
                'placeholder': 'Optional — e.g., Bilal Ahmed'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input-custom',
                'placeholder': 'e.g., 50 987 6543'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input-custom',
                'placeholder': 'e.g., sales@supplier.com'
            }),
            'address': forms.Textarea(attrs={'class': 'form-input-custom', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-input-custom'}),
            'country': forms.TextInput(attrs={'class': 'form-input-custom'}),
            'trn': forms.TextInput(attrs={'class': 'form-input-custom', 'placeholder': 'Tax Registration Number'}),
        }


# ============================================================
# CATEGORY FORM
# ============================================================
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input-custom'}),
            'description': forms.Textarea(attrs={'class': 'form-input-custom', 'rows': 2}),
        }


# ============================================================
# INVOICE FORM
# ============================================================
class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'customer', 'customer_name',
            'discount_percent', 'tax_name', 'tax_percent',
            'payment_method', 'payment_status', 'notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-input-custom'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-input-custom', 'placeholder': 'Walk-in customer name'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-input-custom', 'step': '0.01'}),
            'tax_name': forms.TextInput(attrs={'class': 'form-input-custom', 'placeholder': 'VAT / GST'}),
            'tax_percent': forms.NumberInput(attrs={'class': 'form-input-custom', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-input-custom'}),
            'payment_status': forms.Select(attrs={'class': 'form-input-custom'}),
            'notes': forms.Textarea(attrs={'class': 'form-input-custom', 'rows': 2}),
        }


# ============================================================
# STOCK ENTRY FORM
# ============================================================
class StockEntryForm(forms.ModelForm):
    class Meta:
        model = StockEntry
        fields = ['supplier', 'purchase_invoice_no', 'entry_date', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-input-custom'}),
            'purchase_invoice_no': forms.TextInput(attrs={'class': 'form-input-custom'}),
            'entry_date': forms.DateInput(attrs={'class': 'form-input-custom', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-input-custom', 'rows': 2}),
        }
from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    # ============================================================
    # LANDING PAGE
    # ============================================================
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),
path('notifications/count/', views.notifications_count, name='notifications_count'),
    # ============================================================
    # AUTHENTICATION
    # ============================================================
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ============================================================
    # DASHBOARD
    # ============================================================
    path('dashboard/', views.dashboard, name='dashboard'),

    # ============================================================
    # INVENTORY
    # ============================================================
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.add_inventory, name='add_inventory'),
    path('inventory/edit/<int:product_id>/', views.edit_inventory, name='edit_inventory'),
    path('inventory/delete/<int:product_id>/', views.delete_inventory, name='delete_inventory'),
    path('inventory/stock/<int:product_id>/', views.add_stock, name='add_stock'),
    path('inventory/history/', views.stock_history, name='stock_history'),
    path('inventory/low-stock/', views.low_stock, name='low_stock'),

    # ============================================================
    # STOCK ENTRIES (PURCHASE)
    # ============================================================
    path('stock-entries/', views.stock_entries, name='stock_entries'),
    path('stock-entries/create/', views.create_stock_entry, name='create_stock_entry'),

    # ============================================================
    # INVOICES (SALES)
    # ============================================================
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoice/create/', views.create_invoice, name='create_invoice'),
    path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoice/<int:invoice_id>/print/', views.print_invoice, name='print_invoice'),
    path('invoice/<int:invoice_id>/pdf/', views.download_invoice_pdf, name='download_invoice_pdf'),

    # ============================================================
    # RETURNS
    # ============================================================
    path('returns/', views.returns, name='returns'),

    # ============================================================
    # CUSTOMERS
    # ============================================================
    path('customers/', views.customers, name='customers'),
    path('customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('customers/edit/<int:customer_id>/', views.edit_customer, name='edit_customer'),
    path('customers/delete/<int:customer_id>/', views.delete_customer, name='delete_customer'),

    # ============================================================
    # SUPPLIERS
    # ============================================================
    path('suppliers/', views.suppliers, name='suppliers'),
    path('suppliers/<int:supplier_id>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/edit/<int:supplier_id>/', views.edit_supplier, name='edit_supplier'),
    path('suppliers/delete/<int:supplier_id>/', views.delete_supplier, name='delete_supplier'),

    # ============================================================
    # REPORTS
    # ============================================================
    path('reports/', views.reports, name='reports'),

    # ============================================================
    # USER MANAGEMENT
    # ============================================================
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.create_staff, name='create_staff'),
    path('users/toggle/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),

    # ============================================================
    # ACTIVITY LOGS
    # ============================================================
    path('activity-logs/', views.activity_logs, name='activity_logs'),

    # ============================================================
    # NOTIFICATIONS
    # ============================================================
    path('notifications/', views.notifications, name='notifications'),

    # ============================================================
    # GLOBAL SEARCH
    # ============================================================
    path('search/', views.global_search, name='global_search'),

    # ============================================================
    # DATA BACKUP
    # ============================================================
    path('backup/', views.backup_data, name='backup_data'),

    # ============================================================
    # BARCODE / QR CODE
    # ============================================================
    path('product/<int:product_id>/barcode/', views.product_barcode, name='product_barcode'),
    path('product/<int:product_id>/qr/', views.product_qr, name='product_qr'),
    path('product/<int:product_id>/print-label/', views.print_barcode_labels, name='print_barcode_labels'),
    path('product/<int:product_id>/regenerate/', views.regenerate_barcode_qr, name='regenerate_barcode_qr'),
    path('scan/', views.scan_barcode, name='scan_barcode'),
]
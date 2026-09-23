"""
Barcode and QR Code generation utilities.
Supports Code128 barcodes and QR codes.
"""

import json
import logging

# Safe imports
try:
    import barcode
    from barcode.writer import ImageWriter
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False
    print("WARNING: python-barcode not installed. Run: python -m pip install python-barcode")

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    print("WARNING: qrcode not installed. Run: python -m pip install qrcode[pil]")

from io import BytesIO
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


# ============================================================
# BARCODE GENERATION
# ============================================================

def generate_barcode_image(barcode_number, product_name="Product"):
    """
    Generate a barcode image (Code128 format).
    Returns ContentFile ready to save, or None on failure.
    """
    if not BARCODE_AVAILABLE:
        logger.error("python-barcode not installed. Cannot generate barcode.")
        return None

    try:
        clean_number = str(barcode_number).strip().replace(' ', '')

        if not clean_number:
            logger.warning("Empty barcode number provided")
            return None

        CODE128 = barcode.get_barcode_class('code128')
        code = CODE128(clean_number, writer=ImageWriter())

        buffer = BytesIO()
        code.write(buffer, options={
            'module_width': 0.3,
            'module_height': 15.0,
            'font_size': 10,
            'text_distance': 5.0,
            'background': 'white',
            'foreground': 'black',
            'quiet_zone': 6.5,
        })
        buffer.seek(0)

        filename = f"barcode_{clean_number}.png"
        return ContentFile(buffer.read(), name=filename)

    except Exception as e:
        logger.exception(f"Barcode generation failed for '{barcode_number}': {e}")
        return None


# ============================================================
# QR CODE GENERATION
# ============================================================

def generate_qr_code_image(data, product_name="Product"):
    """
    Generate a QR code image containing product data.
    Returns ContentFile ready to save, or None on failure.
    """
    if not QRCODE_AVAILABLE:
        logger.error("qrcode not installed. Cannot generate QR code.")
        return None

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(str(data))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        safe_name = str(product_name).replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"qr_{safe_name}.png"

        return ContentFile(buffer.read(), name=filename)

    except Exception as e:
        logger.exception(f"QR generation failed: {e}")
        return None


# ============================================================
# QR DATA BUILDER
# ============================================================

def generate_product_qr_data(product):
    """
    Generate QR data string for a product.
    """
    try:
        data = {
            'id': product.id,
            'name': product.name,
            'sku': product.sku or '',
            'barcode': product.barcode or '',
            'price': str(product.price),
            'stock': product.quantity,
        }
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        logger.exception(f"QR data build failed: {e}")
        return str(product.id)


# ============================================================
# COMBINED GENERATOR
# ============================================================

def generate_barcode_for_product(product):
    """
    Generate both barcode and QR code for a product.
    Saves images to the product instance fields.
    """
    success = False

    try:
        if not product.barcode:
            product.barcode = f"{product.id:013d}"

        # Barcode
        barcode_file = generate_barcode_image(product.barcode, product.name)
        if barcode_file:
            try:
                product.barcode_image.save(
                    f"barcode_{product.sku or product.id}.png",
                    barcode_file,
                    save=False
                )
                success = True
            except Exception as e:
                logger.exception(f"Failed to save barcode image: {e}")

        # QR Code
        qr_data = generate_product_qr_data(product)
        qr_file = generate_qr_code_image(qr_data, product.sku or str(product.id))
        if qr_file:
            try:
                product.qr_code.save(
                    f"qr_{product.sku or product.id}.png",
                    qr_file,
                    save=False
                )
                success = True
            except Exception as e:
                logger.exception(f"Failed to save QR image: {e}")

        if success:
            product.save()

        return success

    except Exception as e:
        logger.exception(f"Product barcode/QR generation failed: {e}")
        return False
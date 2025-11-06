"""Utility functions for image processing and file handling."""
import os
import zipfile
from uuid import uuid4
from PIL import Image, ImageEnhance
from io import BytesIO
import magic

def allowed_file(filename, allowed_extensions):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def validate_file(file, allowed_extensions, max_size):
    """Validate uploaded file."""
    if not file:
        raise ValueError("No file provided")
    if not allowed_file(file.filename, allowed_extensions):
        raise ValueError(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
    content = file.read()
    file.seek(0)  # Reset file pointer
    if len(content) > max_size:
        raise ValueError(f"File too large. Maximum size: {max_size/1024/1024}MB")
    mime = magic.from_buffer(content, mime=True)
    if not mime.startswith('image/'):
        raise ValueError(f"Invalid file type: {mime}")
    return True

def apply_watermark(image, watermark, fill_pct, opacity_pct):
    """Apply centered watermark with caching."""
    try:
        img = image.convert("RGBA")
        watermark = watermark.convert("RGBA")

        wm_width = int((fill_pct / 100.0) * img.width)
        aspect_ratio = watermark.width / watermark.height
        wm_height = int(wm_width / aspect_ratio)
        watermark = watermark.resize((wm_width, wm_height), Image.Resampling.LANCZOS)

        alpha = watermark.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity_pct / 100.0)
        watermark.putalpha(alpha)

        # Center the watermark
        pos = ((img.width - wm_width) // 2, (img.height - wm_height) // 2)
        img.paste(watermark, pos, watermark)

        return img
    except Exception as e:
        raise Exception(f"Error applying watermark: {e}")

def resize_image(image, scale_pct):
    """Resize image by percentage."""
    if scale_pct == 100:
        print("[DEBUG] Skipping resize (100%)")
        return image
    width = int(image.width * scale_pct / 100)
    height = int(image.height * scale_pct / 100)
    print(f"[DEBUG] Resizing image to {width}x{height}")
    return image.resize((width, height), Image.Resampling.LANCZOS)

def create_zip(folder_path, zip_folder):
    """Create a zip file from processed images."""
    zip_id = str(uuid4())
    zip_filename = f"{zip_id}.zip"
    zip_path = os.path.join(zip_folder, zip_filename)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                abs_path = os.path.join(root, file)
                arcname = os.path.relpath(abs_path, folder_path)
                zipf.write(abs_path, arcname)

    return zip_filename
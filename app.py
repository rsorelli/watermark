import os
import shutil
import zipfile
from uuid import uuid4
from threading import Thread
from flask import Flask, request, render_template, send_from_directory, jsonify
from PIL import Image, ImageEnhance
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

# Limit to 2 or 3 concurrent threads
executor = ThreadPoolExecutor(max_workers=3)  # Change to 3 if you want 3 threads

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join("static", "output")
ZIP_FOLDER = os.path.join("static", "zips")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ZIP_FOLDER, exist_ok=True)

progress_tracker = {}


def clear_previous_sessions():
    for folder in [UPLOAD_FOLDER, ZIP_FOLDER]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")


def apply_watermark(image, watermark, fill_pct, opacity_pct):
    img = image.convert("RGBA")
    watermark = watermark.convert("RGBA")

    wm_width = int((fill_pct / 100.0) * img.width)
    aspect_ratio = watermark.width / watermark.height
    wm_height = int(wm_width / aspect_ratio)
    watermark = watermark.resize((wm_width, wm_height), Image.Resampling.LANCZOS)

    alpha = watermark.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity_pct / 100.0)
    watermark.putalpha(alpha)

    pos = ((img.width - wm_width) // 2, (img.height - wm_height) // 2)
    img.paste(watermark, pos, watermark)
    return img


def resize_image(image, scale_pct):
    if scale_pct == 100:
        print("[DEBUG] Skipping resize (100%)")
        return image
    width = int(image.width * scale_pct / 100)
    height = int(image.height * scale_pct / 100)
    print(f"[DEBUG] Resizing image to {width}x{height}")
    return image.resize((width, height), Image.Resampling.LANCZOS)


def create_zip(folder_path):
    zip_id = str(uuid4())
    zip_filename = f"{zip_id}.zip"
    zip_path = os.path.join(ZIP_FOLDER, zip_filename)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                abs_path = os.path.join(root, file)
                arcname = os.path.relpath(abs_path, folder_path)
                zipf.write(abs_path, arcname)

    return zip_filename


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        clear_previous_sessions()

        session_id = str(uuid4())
        session_folder = os.path.join(UPLOAD_FOLDER, session_id)
        os.makedirs(session_folder, exist_ok=True)

        image_files = [
            {
                "filename": f.filename,
                "content": f.read()
            }
            for f in request.files.getlist("photos")
        ]

        watermark_file = request.files.get('watermark')
        apply_watermark_flag = 'apply_watermark' in request.form
        reduce_size_flag = 'reduce_size' in request.form
        output_format = request.form.get("format", "jpg").lower()

        if output_format not in ["jpg", "png"]:
            output_format = "jpg"

        fill_pct = int(request.form.get('fill_pct', 0))
        opacity_pct = int(request.form.get('opacity_pct', 0))
        reduce_pct = int(request.form.get('reduce_pct', 100))

        progress_tracker[session_id] = {'total': len(image_files), 'done': 0, 'zip': None}

        watermark_bytes = watermark_file.read() if watermark_file else None

        def process_images():
            for file in image_files:
                try:
                    img = Image.open(BytesIO(file["content"])).convert("RGBA")
                except Exception as e:
                    print(f"Skipping {file['filename']}: {e}")
                    progress_tracker[session_id]['done'] += 1
                    continue

                filename_base = os.path.splitext(os.path.basename(file["filename"]))[0].replace(" ", "_")
                suffix = []

                processed_img = img

                if apply_watermark_flag and watermark_bytes:
                    watermark = Image.open(BytesIO(watermark_bytes))
                    processed_img = apply_watermark(processed_img, watermark, fill_pct, opacity_pct)
                    suffix.append("logo")

                if reduce_size_flag:
                    print(f"[DEBUG] Resizing {file['filename']} to {reduce_pct}%")
                    processed_img = resize_image(processed_img, reduce_pct)
                    suffix.append(f"mini{reduce_pct}")

                suffix_str = f"_{'_'.join(suffix)}" if suffix else ""
                final_name = f"{filename_base}{suffix_str}.{output_format}"
                final_path = os.path.join(session_folder, final_name)

                if output_format == "jpg":
                    processed_img.convert("RGB").save(final_path, format="JPEG", quality=85, optimize=True)
                else:
                    processed_img.save(final_path, format="PNG", optimize=True)

                print(f"[DEBUG] Saved {final_name}")
                progress_tracker[session_id]['done'] += 1

            zip_name = create_zip(session_folder)
            zip_url = f"/static/zips/{zip_name}"
            progress_tracker[session_id]['zip'] = zip_url
            print(f"[DEBUG] Zip ready: {zip_url}")

        #Thread(target=process_images).start()
        executor.submit(process_images)

        return render_template("progress.html", session_id=session_id)

    return render_template("index.html")


@app.route('/progress/<session_id>')
def get_progress(session_id):
    progress = progress_tracker.get(session_id)
    if not progress:
        return jsonify({"status": "not_found"}), 404

    return jsonify({
        "total": progress['total'],
        "done": progress['done'],
        "zip": progress['zip']
    })


@app.route('/static/zips/<path:filename>')
def download_zip(filename):
    return send_from_directory(ZIP_FOLDER, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=4444, debug=True)

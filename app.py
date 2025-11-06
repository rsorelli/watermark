import os
import shutil
import zipfile
import logging
import magic
from uuid import uuid4
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask, request, render_template, send_from_directory, jsonify, session, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from PIL import Image, ImageEnhance
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from flask import session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Translations dictionary
TRANSLATIONS = {
    'en': {
        'title': 'Watermark App',
        'select_images': 'Select Images:',
        'watermark_image': 'Watermark Image:',
        'apply_watermark': 'Apply Watermark',
        'watermark_fill': 'Watermark Fill % (0–100):',
        'opacity': 'Opacity % (0–100):',
        'reduce_size': 'Reduce Size',
        'reduce_size_percent': 'Reduce Size % (1–100):',
        'position': 'Position:',
        'pattern': 'Pattern:',
        'output_format': 'Output Format:',
        'process_images': 'Process Images',
        'center': 'Center',
        'top_left': 'Top Left',
        'top_right': 'Top Right',
        'bottom_left': 'Bottom Left',
        'bottom_right': 'Bottom Right',
        'single': 'Single',
        'grid': 'Grid',
        'diagonal': 'Diagonal',
        'jpg_smaller': 'JPG (Smaller)',
        'png_lossless': 'PNG (Lossless)',
        'gif': 'GIF',
        'language': 'Language:',
        'select_files': 'Select files...',
        'preview': 'Preview',
        'error_no_file': 'Please select at least one image',
        'error_file_too_large': 'File is too large. Maximum size is 16MB',
        'processing_title': 'Processing Images',
        'processing_description': 'Please wait while your images are being processed...',
        'processed_images': 'Processed Images',
        'total_images': 'Total Images',
        'download_ready': 'Your images are ready!',
        'click_download': 'Click here to download your processed images',
        'processing': 'Processing',
        'session_not_found': 'Session not found.',
        'processing_complete': 'Processing complete!',
        'error_checking_progress': 'Error checking progress.',
        'return_to_upload': 'Return to Upload',
        'processing_file': 'Processing file',
        'estimated_time': 'Estimated time remaining',
        'reconnecting': 'Connection lost, attempting to reconnect...',
        'connection_lost': 'Connection lost. Please refresh the page.'
    },
    'pt': {
        'title': 'Aplicativo de Marca d\'água',
        'select_images': 'Selecionar Imagens:',
        'watermark_image': 'Imagem da Marca d\'água:',
        'apply_watermark': 'Aplicar Marca d\'água',
        'watermark_fill': 'Preenchimento da Marca d\'água % (0–100):',
        'opacity': 'Opacidade % (0–100):',
        'reduce_size': 'Reduzir Tamanho',
        'reduce_size_percent': 'Reduzir Tamanho % (1–100):',
        'position': 'Posição:',
        'pattern': 'Padrão:',
        'output_format': 'Formato de Saída:',
        'process_images': 'Processar Imagens',
        'center': 'Centro',
        'top_left': 'Superior Esquerdo',
        'top_right': 'Superior Direito',
        'bottom_left': 'Inferior Esquerdo',
        'bottom_right': 'Inferior Direito',
        'single': 'Único',
        'grid': 'Grade',
        'diagonal': 'Diagonal',
        'jpg_smaller': 'JPG (Menor)',
        'png_lossless': 'PNG (Sem Perda)',
        'gif': 'GIF',
        'language': 'Idioma:',
        'select_files': 'Selecionar arquivos...',
        'preview': 'Visualizar',
        'error_no_file': 'Por favor, selecione pelo menos uma imagem',
        'error_file_too_large': 'Arquivo muito grande. Tamanho máximo é 16MB',
        'processing_title': 'Processando Imagens',
        'processing_description': 'Por favor, aguarde enquanto suas imagens são processadas...',
        'processed_images': 'Imagens Processadas',
        'total_images': 'Total de Imagens',
        'download_ready': 'Suas imagens estão prontas!',
        'click_download': 'Clique aqui para baixar suas imagens processadas',
        'processing': 'Processando',
        'session_not_found': 'Sessão não encontrada.',
        'processing_complete': 'Processamento completo!',
        'error_checking_progress': 'Erro ao verificar progresso.',
        'return_to_upload': 'Voltar para Upload',
        'processing_file': 'Processando arquivo',
        'estimated_time': 'Tempo restante estimado',
        'reconnecting': 'Conexão perdida, tentando reconectar...',
        'connection_lost': 'Conexão perdida. Por favor, atualize a página.'
    }
}

# Initialize Flask app and extensions
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
app.secret_key = 'your-secret-key-here'  # Required for session

# Initialize extensions
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
cache = Cache(app)
executor = ThreadPoolExecutor(max_workers=3)

# Configure folders
UPLOAD_FOLDER = os.path.join("static", "output")
ZIP_FOLDER = os.path.join("static", "zips")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ZIP_FOLDER, exist_ok=True)

# Configure allowed file types
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

progress_tracker = {}

# Define cleanup function first
def clear_previous_sessions():
    """Clean up old files and folders"""
    logger.info("Starting cleanup of previous sessions")
    for folder in [UPLOAD_FOLDER, ZIP_FOLDER]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    # Check if file is older than 24 hours
                    if datetime.now() - datetime.fromtimestamp(os.path.getctime(file_path)) > timedelta(hours=24):
                        os.unlink(file_path)
                elif os.path.isdir(file_path):
                    if datetime.now() - datetime.fromtimestamp(os.path.getctime(file_path)) > timedelta(hours=24):
                        shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {e}")

# Initialize scheduler for cleanup
scheduler = BackgroundScheduler()
scheduler.add_job(func=clear_previous_sessions, trigger="interval", hours=24)
scheduler.start()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file(file):
    if not file:
        raise ValueError("No file provided")
    if not allowed_file(file.filename):
        raise ValueError(f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")
    content = file.read()
    file.seek(0)  # Reset file pointer
    if len(content) > MAX_FILE_SIZE:
        raise ValueError(f"File too large. Maximum size: {MAX_FILE_SIZE/1024/1024}MB")
    mime = magic.from_buffer(content, mime=True)
    if not mime.startswith('image/'):
        raise ValueError(f"Invalid file type: {mime}")
    return True

def clear_previous_sessions():
    """Clean up old files and folders"""
    logger.info("Starting cleanup of previous sessions")
    for folder in [UPLOAD_FOLDER, ZIP_FOLDER]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    # Check if file is older than 24 hours
                    if datetime.now() - datetime.fromtimestamp(os.path.getctime(file_path)) > timedelta(hours=24):
                        os.unlink(file_path)
                elif os.path.isdir(file_path):
                    if datetime.now() - datetime.fromtimestamp(os.path.getctime(file_path)) > timedelta(hours=24):
                        shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {e}")



@cache.memoize(timeout=300)
def apply_watermark(image, watermark, fill_pct, opacity_pct):
    """Apply centered watermark with caching"""
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
        logger.error(f"Error applying watermark: {e}")
        raise


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


@app.route('/language/<lang>', methods=['GET', 'POST'])
def set_language(lang):
    if lang in TRANSLATIONS:
        session['language'] = lang
        if request.method == 'POST':
            return jsonify({
                'status': 'success',
                'translations': TRANSLATIONS[lang]
            })
    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def index():
    # Set default language if not set
    if 'language' not in session:
        session['language'] = 'en'
    
    # Get translations for current language
    translations = TRANSLATIONS[session['language']]
    
    if request.method == 'GET':
        return render_template('index.html', translations=translations)
    
    if request.method == 'POST':
        try:
            # Clear old sessions
            clear_previous_sessions()

            # Create new session
            session_id = str(uuid4())
            session_folder = os.path.join(UPLOAD_FOLDER, session_id)
            os.makedirs(session_folder, exist_ok=True)

            # Validate and process image files
            if not request.files.getlist("photos"):
                return jsonify({"error": "No images uploaded"}), 400

            for f in request.files.getlist("photos"):
                try:
                    validate_file(f)
                except ValueError as e:
                    return jsonify({"error": str(e)}), 400

            image_files = [
                {
                    "filename": f.filename,
                    "content": f.read()
                }
                for f in request.files.getlist("photos")
            ]

            # Validate watermark file
            watermark_file = request.files.get('watermark')
            if watermark_file:
                try:
                    validate_file(watermark_file)
                except ValueError as e:
                    return jsonify({"error": f"Watermark file error: {str(e)}"}), 400

            # Get and validate form parameters
            apply_watermark_flag = 'apply_watermark' in request.form
            reduce_size_flag = 'reduce_size' in request.form
            output_format = request.form.get("format", "jpg").lower()

            # Validate parameters
            if output_format not in ALLOWED_EXTENSIONS:
                return jsonify({"error": f"Invalid output format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return jsonify({"error": "An unexpected error occurred"}), 500

        if output_format not in ["jpg", "png"]:
            output_format = "jpg"

        fill_pct = int(request.form.get('fill_pct', 0))
        opacity_pct = int(request.form.get('opacity_pct', 0))
        reduce_pct = int(request.form.get('reduce_pct', 100))

        progress_tracker[session_id] = {
            'total': len(image_files),
            'done': 0,
            'zip': None,
            'current_file': None,
            'start_time': datetime.now()
        }

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
                progress_tracker[session_id]['current_file'] = file["filename"]
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

        # Get the language from the query parameter or session, default to session language
        lang = request.args.get('lang', session.get('language', 'en'))
        if lang in TRANSLATIONS:
            session['language'] = lang
        
        return render_template(
            "progress.html",
            session_id=session_id,
            translations=TRANSLATIONS,
            lang=session['language']
        )

    return render_template("index.html")


@app.route('/progress/<session_id>')
def get_progress(session_id):
    progress = progress_tracker.get(session_id)
    if not progress:
        return jsonify({"status": "not_found"}), 404

    elapsed_time = None
    if progress.get('start_time'):
        elapsed_time = (datetime.now() - progress['start_time']).total_seconds()

    return jsonify({
        "total": progress['total'],
        "done": progress['done'],
        "zip": progress['zip'],
        "current_file": progress.get('current_file'),
        "elapsed_time": elapsed_time
    })


@app.route('/static/zips/<path:filename>')
def download_zip(filename):
    return send_from_directory(ZIP_FOLDER, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=4444, debug=True)

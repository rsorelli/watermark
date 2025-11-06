"""Application routes and views."""
from flask import render_template, request, jsonify, session, redirect, url_for, send_from_directory, current_app
from uuid import uuid4
from datetime import datetime
from PIL import Image
from io import BytesIO
import os
import logging
from .utils import (
    validate_file,
    apply_watermark,
    resize_image,
    create_zip
)

logger = logging.getLogger(__name__)

# Global progress tracker - shared across all requests
progress_tracker = {}

def register_routes(app):
    """Register all application routes."""
    
    @app.route('/language/<lang>', methods=['GET', 'POST'])
    def set_language(lang):
        if lang in app.config['TRANSLATIONS']:
            session['language'] = lang
            if request.method == 'POST':
                return jsonify({
                    'status': 'success',
                    'translations': app.config['TRANSLATIONS'][lang]
                })
        return redirect(url_for('index'))

    @app.route('/', methods=['GET', 'POST'])
    def index():
        # Set default language if not set
        if 'language' not in session:
            session['language'] = 'en'
        
        translations = app.config['TRANSLATIONS'][session['language']]
        
        if request.method == 'GET':
            return render_template('index.html', translations=translations)
        
        if request.method == 'POST':
            try:
                # Validate files
                files = request.files.getlist('photos')
                if not files or not files[0].filename:
                    return jsonify({"error": translations["error_no_file"]}), 400
                
                for file in files:
                    try:
                        validate_file(
                            file,
                            app.config['ALLOWED_EXTENSIONS'],
                            app.config['MAX_FILE_SIZE']
                        )
                    except ValueError as e:
                        return jsonify({"error": str(e)}), 400
                
                # Generate a session ID for this batch
                session_id = str(uuid4())
                
                # Store files in memory for background processing
                image_files = []
                for file in files:
                    content = file.read()
                    file.seek(0)
                    image_files.append({
                        'filename': file.filename,
                        'content': content
                    })
                
                # Process watermark if provided - ACCEPT ANY FILE TYPE
                watermark_bytes = None
                if 'watermark' in request.files and request.files['watermark'].filename:
                    try:
                        watermark_file = request.files['watermark']
                        # Only check file size for watermark, accept any file type
                        content = watermark_file.read()
                        if len(content) > app.config['MAX_FILE_SIZE']:
                            raise ValueError(f"Watermark file too large. Maximum size: {app.config['MAX_FILE_SIZE']/1024/1024}MB")
                        watermark_bytes = content
                    except Exception as e:
                        return jsonify({"error": f"Watermark error: {str(e)}"}), 400
                
                # Get form parameters
                apply_watermark_flag = 'apply_watermark' in request.form
                fill_pct = float(request.form.get('fill_pct', 30))
                opacity_pct = float(request.form.get('opacity_pct', 50))
                reduce_size_flag = 'reduce_size' in request.form
                reduce_pct = float(request.form.get('reduce_pct', 60))
                output_format = request.form.get('format', 'jpg').lower()
                
                if output_format not in app.config['ALLOWED_EXTENSIONS']:
                    output_format = 'jpg'
                
                # Initialize progress tracker
                progress_tracker[session_id] = {
                    'total': len(image_files),
                    'done': 0,
                    'zip': None,
                    'current_file': None,
                    'start_time': datetime.now(),
                    'failed': 0
                }
                
                # Define background processing function
                def process_images_background():
                    """Background task to process images"""
                    try:
                        # Create session output directory
                        output_dir = os.path.join(app.root_path, 'static', 'output', session_id)
                        zip_dir = os.path.join(app.root_path, 'static', 'zips')
                        os.makedirs(output_dir, exist_ok=True)
                        os.makedirs(zip_dir, exist_ok=True)
                        
                        output_files = []
                        
                        # Load watermark once if needed
                        watermark = None
                        if apply_watermark_flag and watermark_bytes:
                            watermark = Image.open(BytesIO(watermark_bytes))
                        
                        # Process each image
                        for file_data in image_files:
                            try:
                                # Update current file being processed
                                progress_tracker[session_id]['current_file'] = file_data['filename']
                                
                                # Open image
                                img = Image.open(BytesIO(file_data['content']))
                                
                                # Apply watermark if requested
                                if watermark:
                                    img = apply_watermark(img, watermark, fill_pct, opacity_pct)
                                
                                # Resize if requested
                                if reduce_size_flag:
                                    img = resize_image(img, reduce_pct)
                                
                                # Generate output filename
                                base_name = os.path.splitext(file_data['filename'])[0]
                                safe_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).strip()
                                safe_name = safe_name.replace(' ', '_')
                                filename = f"{safe_name}_{str(uuid4())[:8]}.{output_format}"
                                filepath = os.path.join(output_dir, filename)
                                
                                # Save image
                                if output_format == 'jpg':
                                    if img.mode in ('RGBA', 'LA', 'P'):
                                        # Create white background for transparency
                                        background = Image.new('RGB', img.size, (255, 255, 255))
                                        if img.mode == 'P':
                                            img = img.convert('RGBA')
                                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                                        img = background
                                    else:
                                        img = img.convert('RGB')
                                    img.save(filepath, 'JPEG', quality=85, optimize=True)
                                elif output_format == 'png':
                                    img.save(filepath, 'PNG', optimize=True)
                                elif output_format == 'gif':
                                    # Convert to palette mode for GIF
                                    if img.mode != 'P':
                                        img = img.convert('P', palette=Image.ADAPTIVE)
                                    img.save(filepath, 'GIF', optimize=True)
                                
                                output_files.append(filepath)
                                logger.info(f"Successfully processed: {file_data['filename']}")
                                
                            except Exception as e:
                                logger.error(f"Error processing {file_data['filename']}: {str(e)}")
                                progress_tracker[session_id]['failed'] += 1
                            finally:
                                # Update progress
                                progress_tracker[session_id]['done'] += 1
                        
                        # Create zip file
                        if output_files:
                            zip_path = os.path.join(zip_dir, f"{session_id}.zip")
                            create_zip(output_files, zip_path)
                            progress_tracker[session_id]['zip'] = f"/download/{session_id}"
                            logger.info(f"Zip file created: {zip_path}")
                        else:
                            logger.error("No files were successfully processed")
                            
                    except Exception as e:
                        logger.error(f"Error in background processing: {str(e)}")
                        progress_tracker[session_id]['error'] = str(e)
                
                # Submit background task
                app.executor.submit(process_images_background)
                
                # Return progress page immediately
                return render_template(
                    'progress.html',
                    session_id=session_id,
                    translations=app.config['TRANSLATIONS'],
                    lang=session['language']
                )
                
            except Exception as e:
                logger.error(f"Error in index route: {str(e)}")
                return jsonify({"error": translations.get("unexpected_error", "An error occurred")}), 500

    @app.route('/progress/<session_id>')
    def get_progress(session_id):
        """Get progress for a specific session"""
        try:
            if session_id not in progress_tracker:
                return jsonify({"status": "not_found"}), 404
            
            progress = progress_tracker[session_id]
            
            # Calculate elapsed time
            elapsed_time = None
            if progress.get('start_time'):
                elapsed_time = (datetime.now() - progress['start_time']).total_seconds()
            
            return jsonify({
                "total": progress['total'],
                "done": progress['done'],
                "failed": progress.get('failed', 0),
                "zip": progress.get('zip'),
                "current_file": progress.get('current_file'),
                "elapsed_time": elapsed_time,
                "error": progress.get('error')
            })
        except Exception as e:
            logger.error(f"Error getting progress: {str(e)}")
            return jsonify({"error": "Error checking progress"}), 500

    @app.route('/download/<session_id>')
    def download_file(session_id):
        """Download the processed zip file"""
        try:
            zip_dir = os.path.join(app.root_path, 'static', 'zips')
            zip_path = os.path.join(zip_dir, f"{session_id}.zip")
            
            if not os.path.exists(zip_path):
                if 'language' not in session:
                    session['language'] = 'en'
                translations = app.config['TRANSLATIONS'][session['language']]
                return jsonify({"error": translations.get("error", "File not found")}), 404
            
            return send_from_directory(
                zip_dir,
                f"{session_id}.zip",
                as_attachment=True,
                download_name="processed_images.zip"
            )
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return jsonify({"error": "Error downloading file"}), 500

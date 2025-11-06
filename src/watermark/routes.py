"""Application routes and views."""
from flask import render_template, request, jsonify, session, redirect, url_for, send_from_directory
from uuid import uuid4
from datetime import datetime
from PIL import Image
import os
from .utils import (
    validate_file,
    apply_watermark,
    resize_image,
    create_zip
)
from .tasks import clear_previous_sessions

# Global progress tracker
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
                files = request.files.getlist('photos')
                if not files:
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
                
                # Ensure directories exist and get absolute paths
                output_dir = os.path.join(app.root_path, 'static', 'output', session_id)
                zip_dir = os.path.join(app.root_path, 'static', 'zips')
                os.makedirs(output_dir, exist_ok=True)
                os.makedirs(zip_dir, exist_ok=True)
                
                # Process watermark if provided
                watermark = None
                if 'watermark' in request.files and request.files['watermark'].filename:
                    try:
                        watermark_file = request.files['watermark']
                        validate_file(
                            watermark_file,
                            app.config['ALLOWED_EXTENSIONS'],
                            app.config['MAX_FILE_SIZE']
                        )
                        watermark = Image.open(watermark_file)
                    except Exception as e:
                        return jsonify({"error": str(e)}), 400
                
                # Store form data in progress tracker
                progress_tracker[session_id] = {
                    "total": len(files),
                    "processed": 0,
                    "failed": 0,
                    "completed": False
                }
                
                # Get form parameters
                fill_pct = float(request.form.get('fill_pct', 30))
                opacity_pct = float(request.form.get('opacity_pct', 50))
                reduce_size = bool(request.form.get('reduce_size', False))
                reduce_pct = float(request.form.get('reduce_pct', 60))
                output_format = request.form.get('format', 'jpg')
                
                # Process each file
                output_files = []
                for i, file in enumerate(files):
                    try:
                        # Open and process image
                        img = Image.open(file)
                        
                        # Apply watermark if requested and available
                        if 'apply_watermark' in request.form and watermark:
                            img = apply_watermark(img, watermark, fill_pct, opacity_pct)
                            
                        # Resize image if requested
                        if reduce_size:
                            img = resize_image(img, reduce_pct)
                            
                        # Save processed image
                        filename = str(uuid4()) + '.' + output_format
                        filepath = os.path.join(output_dir, filename)
                        
                        if output_format == 'jpg':
                            # Convert to RGB for JPEG
                            if img.mode in ('RGBA', 'P'):
                                img = img.convert('RGB')
                            img.save(filepath, 'JPEG', quality=85)
                        else:
                            img.save(filepath, output_format.upper())
                            
                        output_files.append(filepath)
                        progress_tracker[session_id]["processed"] += 1
                    except Exception as e:
                        app.logger.error(f"Error processing file {file.filename}: {str(e)}")
                        progress_tracker[session_id]["failed"] += 1
                
                # Mark processing as complete
                progress_tracker[session_id]["completed"] = True
                
                # Create zip file with processed images
                zip_path = os.path.join(zip_dir, f"{session_id}.zip")
                create_zip(output_files, zip_path)
                
                return jsonify({
                    "message": translations["success"],
                    "session_id": session_id,
                    "download_url": f"/download/{session_id}"
                })
                
            except Exception as e:
                app.logger.error(f"Error processing request: {str(e)}")
                return jsonify({"error": translations["unexpected_error"]}), 500

    @app.route('/download/<session_id>')
    def download_file(session_id):
        try:
            if 'language' not in session:
                session['language'] = 'en'
                
            translations = app.config['TRANSLATIONS'][session['language']]
            zip_path = os.path.join(app.root_path, 'static', 'zips', f"{session_id}.zip")
            
            if not os.path.exists(zip_path):
                return jsonify({"error": translations["error"]}), 404
                
            return send_from_directory(
                os.path.dirname(zip_path),
                os.path.basename(zip_path),
                as_attachment=True,
                download_name="processed_images.zip"
            )
        except Exception as e:
            app.logger.error(f"Error downloading file: {str(e)}")
            return jsonify({"error": translations["unexpected_error"]}), 500

    @app.route('/progress/<session_id>')
    def get_progress(session_id):
        try:
            if 'language' not in session:
                session['language'] = 'en'
                
            translations = app.config['TRANSLATIONS'][session['language']]
            
            if session_id not in progress_tracker:
                return jsonify({"error": translations["error"]}), 404
                
            progress = progress_tracker[session_id]
            return jsonify({
                "total": progress["total"],
                "processed": progress["processed"],
                "failed": progress["failed"],
                "completed": progress["completed"]
            })
        except Exception as e:
            app.logger.error(f"Error getting progress: {str(e)}")
            return jsonify({"error": translations["unexpected_error"]}), 500
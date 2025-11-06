"""Application routes and views."""
from flask import render_template, request, jsonify, session, redirect, url_for, send_from_directory
from uuid import uuid4
from datetime import datetime
import os
from .utils import (
    validate_file,
    apply_watermark,
    resize_image,
    create_zip,
    clear_previous_sessions
)

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
                # Implementation of file processing logic
                pass
            except Exception as e:
                app.logger.error(f"Error processing request: {str(e)}")
                return jsonify({"error": "An unexpected error occurred"}), 500

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
        return send_from_directory(app.config['ZIP_FOLDER'], filename, as_attachment=True)
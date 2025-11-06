"""Application configuration."""
import os

class Config:
    """Base configuration."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    
    # ✅ INCREASED: Upload size limits to handle larger batches
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB total request size (was 16MB)
    
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300

    # Translations
    TRANSLATIONS = {
        'en': {
            'title': 'Image Watermark Tool',
            'upload_text': 'Choose files or drag and drop here',
            'submit': 'Upload',
            'progress': 'Progress',
            'clear': 'Clear',
            'error': 'Error',
            'success': 'Success',
            'processing': 'Processing...',
            'download': 'Download',
            'max_files': 'Maximum 10 files allowed',
            'invalid_type': 'Invalid file type',
            'file_too_large': 'File is too large',
            'unexpected_error': 'An unexpected error occurred',
            'select_images': 'Select Images',
            'apply_watermark': 'Apply Watermark',
            'watermark_image': 'Select Watermark Image',
            'watermark_fill': 'Watermark Fill Percentage',
            'opacity': 'Opacity',
            'reduce_size': 'Reduce Image Size',
            'reduce_size_percent': 'Size Reduction Percentage',
            'output_format': 'Output Format',
            'process_images': 'Process Images',
            'jpg_smaller': 'JPEG (Smaller file size)',
            'png_lossless': 'PNG (Lossless quality)',
            'gif': 'GIF',
            'error_no_file': 'Please select at least one file',
            'error_file_too_large': 'One or more files are too large (max 20MB per file)',
            'error_total_size': 'Total upload size exceeds 100MB limit',
            'error_loading': 'Error loading files',
            'error_processing': 'Error processing files',
            'error_watermark': 'Error processing watermark',
            'error_download': 'Error downloading file',
            'uploaded_files': 'Uploaded Files:',
            'no_files': 'No files selected',
            'processing_title': 'Processing Images',
            'processing_description': 'Please wait while your images are being processed...',
            'processed_images': 'Processed Images',
            'total_images': 'Total Images',
            'download_ready': 'Your images are ready!',
            'click_download': 'Click here to download your processed images',
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
            'title': 'Ferramenta de Marca D\'água',
            'upload_text': 'Escolha os arquivos ou arraste e solte aqui',
            'submit': 'Enviar',
            'progress': 'Progresso',
            'clear': 'Limpar',
            'error': 'Erro',
            'success': 'Sucesso',
            'processing': 'Processando...',
            'download': 'Baixar',
            'max_files': 'Máximo de 10 arquivos permitidos',
            'invalid_type': 'Tipo de arquivo inválido',
            'file_too_large': 'Arquivo muito grande',
            'unexpected_error': 'Ocorreu um erro inesperado',
            'select_images': 'Selecionar Imagens',
            'apply_watermark': 'Aplicar Marca D\'água',
            'watermark_image': 'Selecionar Imagem de Marca D\'água',
            'watermark_fill': 'Percentual de Preenchimento',
            'opacity': 'Opacidade',
            'reduce_size': 'Reduzir Tamanho da Imagem',
            'reduce_size_percent': 'Percentual de Redução',
            'output_format': 'Formato de Saída',
            'process_images': 'Processar Imagens',
            'jpg_smaller': 'JPEG (Menor tamanho)',
            'png_lossless': 'PNG (Qualidade sem perdas)',
            'gif': 'GIF',
            'error_no_file': 'Selecione pelo menos um arquivo',
            'error_file_too_large': 'Um ou mais arquivos são muito grandes (máx 20MB por arquivo)',
            'error_total_size': 'Tamanho total do upload excede o limite de 100MB',
            'error_loading': 'Erro ao carregar arquivos',
            'error_processing': 'Erro ao processar arquivos',
            'error_watermark': 'Erro ao processar marca d\'água',
            'error_download': 'Erro ao baixar arquivo',
            'uploaded_files': 'Arquivos Enviados:',
            'no_files': 'Nenhum arquivo selecionado',
            'processing_title': 'Processando Imagens',
            'processing_description': 'Por favor, aguarde enquanto suas imagens são processadas...',
            'processed_images': 'Imagens Processadas',
            'total_images': 'Total de Imagens',
            'download_ready': 'Suas imagens estão prontas!',
            'click_download': 'Clique aqui para baixar suas imagens processadas',
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
    
    # Configure folders
    UPLOAD_FOLDER = os.path.join("static", "output")
    ZIP_FOLDER = os.path.join("static", "zips")
    
    # File configurations
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # ✅ INCREASED: Individual file size limit
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB per individual file (was 16MB)
    
    # Optional: Set maximum number of files per upload
    MAX_FILES_PER_UPLOAD = 20  # Reasonable limit to prevent abuse
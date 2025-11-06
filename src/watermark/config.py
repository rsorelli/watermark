"""Application configuration."""
import os

class Config:
    """Base configuration."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
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
            'error_file_too_large': 'One or more files are too large (max 16MB)',
            'error_loading': 'Error loading files',
            'error_processing': 'Error processing files',
            'error_watermark': 'Error processing watermark',
            'error_download': 'Error downloading file',
            'uploaded_files': 'Uploaded Files:',
            'no_files': 'No files selected'
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
            'error_file_too_large': 'Um ou mais arquivos são muito grandes (máx 16MB)',
            'error_loading': 'Erro ao carregar arquivos',
            'error_processing': 'Erro ao processar arquivos',
            'error_watermark': 'Erro ao processar marca d\'água',
            'error_download': 'Erro ao baixar arquivo',
            'uploaded_files': 'Arquivos Enviados:',
            'no_files': 'Nenhum arquivo selecionado'
        }
    }
    
    # Configure folders
    UPLOAD_FOLDER = os.path.join("static", "output")
    ZIP_FOLDER = os.path.join("static", "zips")
    
    # File configurations
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
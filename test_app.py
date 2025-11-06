import pytest
import os
from PIL import Image
from io import BytesIO
from app import app, allowed_file, validate_file, apply_watermark

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_allowed_file():
    assert allowed_file('test.jpg') == True
    assert allowed_file('test.png') == True
    assert allowed_file('test.gif') == True
    assert allowed_file('test.pdf') == False
    assert allowed_file('test') == False

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_upload_no_file(client):
    response = client.post('/')
    assert response.status_code == 400
    assert b"No images uploaded" in response.data

def test_upload_invalid_file(client):
    data = {
        'photos': (BytesIO(b'not an image'), 'test.txt')
    }
    response = client.post('/', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert b"File type not allowed" in response.data

def test_watermark_positions():
    # Create test images
    img = Image.new('RGBA', (100, 100), 'white')
    watermark = Image.new('RGBA', (20, 20), 'black')
    
    # Test different positions
    positions = ['center', 'top-left', 'top-right', 'bottom-left', 'bottom-right']
    for pos in positions:
        result = apply_watermark(img, watermark, 20, 50, position=pos)
        assert isinstance(result, Image.Image)

def test_watermark_patterns():
    # Create test images
    img = Image.new('RGBA', (100, 100), 'white')
    watermark = Image.new('RGBA', (20, 20), 'black')
    
    # Test different patterns
    patterns = ['single', 'grid', 'diagonal']
    for pattern in patterns:
        result = apply_watermark(img, watermark, 20, 50, pattern=pattern)
        assert isinstance(result, Image.Image)
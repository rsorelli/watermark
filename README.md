# Watermark Application

A Flask-based web application for adding watermarks to images.

## Features

- Upload multiple images
- Add watermark with customizable opacity and size
- Resize images
- Multiple output formats (JPG, PNG)
- Progress tracking
- Multi-language support (English and Portuguese)

## Project Structure

```
watermark/
├── src/
│   ├── watermark/
│   │   ├── static/
│   │   │   ├── output/
│   │   │   └── zips/
│   │   ├── templates/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── routes.py
│   │   ├── tasks.py
│   │   └── utils.py
│   └── main.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.synology.yml
├── requirements.txt
├── setup.py
└── README.md
```

## Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Run the application:
   ```bash
   python src/main.py
   ```

## Docker Deployment

### Standard Docker Compose
```bash
docker-compose up --build
```

### Synology NAS Deployment
```bash
docker-compose -f docker-compose.synology.yml up -d
```

## License

MIT License
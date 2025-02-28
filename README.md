# newBackend

## Dependencies

Install all requirements with

```bash
pip install -r requirements.txt
```

## Usage

### Migrations

###### Basic migrations manipulation

```bash
# Edit alembic.ini file to add DB url there

# Initializing migrations
alembic revision --autogenerate -m "init"
# Apply migration
alembic upgrade head
# Creating new migration the same way
alembic revision --autogenerate -m "another message"
```

### Server

###### Basic server usage

```bash
# Production server
uvicorn main:app --host 0.0.0.0 --port 80
# Development server
uvicorn main:app --host 0.0.0.0 --port 80 --reload
```
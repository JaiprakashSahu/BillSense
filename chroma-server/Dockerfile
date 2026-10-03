FROM python:3.11-slim

RUN pip install chromadb

# Chroma data directory
RUN mkdir -p /chroma/data

EXPOSE 8000

CMD ["chroma", "run", "--path", "/chroma/data", "--host", "0.0.0.0", "--port", "8000"]

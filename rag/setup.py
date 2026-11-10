from setuptools import setup, find_packages

setup(
    name="sarkarsetu-rag",
    version="1.0.0",
    description="RAG subsystem for SarkarSetu AI",
    python_requires=">=3.11",
    packages=find_packages(where=".", include=["*"]),
    package_dir={"": "."},
    install_requires=[
        "python-dotenv==1.0.1",
        "pydantic==2.9.0",
        "pydantic-settings==2.5.0",
        "PyMuPDF==2.1",
        "pdfplumber==0.11.10",
        "pytesseract==0.3.13",
        "Pillow==13.0.0",
        "python-multipart==0.0.9",
        "sentence-transformers==3.0.1",
        "faiss-cpu==1.15.1",
        "pandas==2.2.3",
        "numpy==1.26.4",
        "fastapi==0.115.0",
        "uvicorn[standard]==0.32.0",
    ],
)

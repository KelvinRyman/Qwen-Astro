from setuptools import setup, find_packages

setup(
    name="rag-engine",
    version="0.1.1",
    author="Your Name",
    description="A comprehensive RAG engine for various applications.",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "chromadb>=1.0.12",
        "dotenv>=0.9.9",
        "llama-index>=0.12.42",
        "llama-index-llms-google-genai>=0.2.1",
        "llama-index-embeddings-openai-like>=0.1.1",
        "llama-index-vector-stores-chroma>=0.4.2",
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
        ],
    },
)

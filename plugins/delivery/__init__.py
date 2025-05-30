"""
Delivery Plugins for RAG Document Processor.

Delivery plugins handle uploading processed chunks with embeddings to vector databases.
Each plugin implements the DeliveryProvider interface and handles its own dependencies.

Available Delivery Plugins:
- supabase: Upload to Supabase with pgvector
- pinecone: Upload to Pinecone vector database (planned)
- weaviate: Upload to Weaviate vector database (planned)
- chroma: Upload to ChromaDB (planned)
- qdrant: Upload to Qdrant vector database (planned)
"""
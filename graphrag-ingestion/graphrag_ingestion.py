import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
import ollama
import boto3
from pypdf import PdfReader
from neo4j import GraphDatabase

class GraphRAGIngestor:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            "bolt://neo4j.hyperplane-neo4j:7687", 
            auth=("neo4j", "Shakudo312!")
        )
        self.embedding_model = "nomic-embed-text:latest"
        self.chat_model = "granite-3.3-8b-instruct-Q6_K_L:latest"
        self.chunk_size = 1000
        self.chunk_overlap = 200
        
        # Configure Ollama client with custom endpoint
        self.ollama_host = "http://ollama-1.hyperplane-ollama-gpu-1.svc.cluster.local:11434"
    
        username = "shakudo_svc"
        access_key = "PS....."
        secret_key = "C71....."
        endpoint_url = "https://flashblade-data.campbell.com"
        self.s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            verify=False  # disable SSL cert check
        )

    def download_pdfs(self, bucket: str, download_dir: str):
        Path(download_dir).mkdir(parents=True, exist_ok=True)
        response = self.s3.list_objects_v2(Bucket=bucket)
        for obj in response.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith(".pdf"):
                local_path = Path(download_dir) / Path(key).name
                self.s3.download_file(bucket, key, str(local_path))
        return list(Path(download_dir).glob("*.pdf"))
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if not text:
            return []
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk = " ".join(chunk_words)
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama"""
        try:
            response = ollama.embeddings(
                model=self.embedding_model,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return []
    
    def generate_questions(self, chunk_text: str) -> List[str]:
        """Generate 1-2 questions for a chunk using LLM"""
        prompt = f"""Based on the following text chunk, generate 1-2 concise questions that this chunk could answer. Return only the questions, one per line.

Text chunk:
{chunk_text[:500]}..."""
        
        try:
            response = ollama.chat(
                model=self.chat_model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            questions_text = response['message']['content'].strip()
            questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
            return questions[:2]  # Limit to 2 questions
        except Exception as e:
            print(f"Error generating questions: {e}")
            return []
    
    def create_graph_schema(self):
        """Create Neo4j constraints and indexes"""
        with self.driver.session() as session:
            # Create constraints
            session.run("CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE")
            session.run("CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE")
            session.run("CREATE CONSTRAINT question_id IF NOT EXISTS FOR (q:Question) REQUIRE q.id IS UNIQUE")
            
            # Create vector indexes
            try:
                session.run("CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS FOR (c:Chunk) ON c.embedding OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}}")
                session.run("CREATE VECTOR INDEX question_embedding IF NOT EXISTS FOR (q:Question) ON q.embedding OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}}")
            except:
                pass  # Index might already exist
    
    def ingest_document(self, pdf_path: str):
        """Ingest a single PDF document"""
        print(f"Processing {pdf_path}...")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            print(f"No text extracted from {pdf_path}")
            return
        
        # Generate document ID
        doc_id = hashlib.md5(pdf_path.encode()).hexdigest()
        doc_name = Path(pdf_path).stem
        
        # Chunk text
        chunks = self.chunk_text(text)
        print(f"Generated {len(chunks)} chunks")
        
        with self.driver.session() as session:
            # Create document node
            session.run("""
                MERGE (d:Document {id: $doc_id})
                SET d.name = $name, 
                    d.path = $path, 
                    d.text_length = $text_length,
                    d.chunk_count = $chunk_count
            """, doc_id=doc_id, name=doc_name, path=pdf_path, 
                text_length=len(text), chunk_count=len(chunks))
            
            # Process each chunk
            for i, chunk_text in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                
                # Get embedding for chunk
                chunk_embedding = self.get_embedding(chunk_text)
                if not chunk_embedding:
                    continue
                
                # Create chunk node
                session.run("""
                    MERGE (c:Chunk {id: $chunk_id})
                    SET c.text = $text,
                        c.embedding = $embedding,
                        c.chunk_index = $index
                    WITH c
                    MATCH (d:Document {id: $doc_id})
                    MERGE (d)-[:HAS_CHUNK]->(c)
                """, chunk_id=chunk_id, text=chunk_text, 
                    embedding=chunk_embedding, index=i, doc_id=doc_id)
                
                # Generate and process questions
                questions = self.generate_questions(chunk_text)
                for j, question_text in enumerate(questions):
                    question_id = f"{chunk_id}_question_{j}"
                    
                    # Get embedding for question
                    question_embedding = self.get_embedding(question_text)
                    if not question_embedding:
                        continue
                    
                    # Create question node and relationship
                    session.run("""
                        MERGE (q:Question {id: $question_id})
                        SET q.text = $text,
                            q.embedding = $embedding
                        WITH q
                        MATCH (c:Chunk {id: $chunk_id})
                        MERGE (c)-[:HAS_QUESTION]->(q)
                    """, question_id=question_id, text=question_text, 
                        embedding=question_embedding, chunk_id=chunk_id)
                
                print(f"Processed chunk {i+1}/{len(chunks)}")
        
        print(f"Successfully ingested {pdf_path}")
    
    def ingest_all_pdfs(self, folder_path: str = "."):
        """Ingest all PDF files in the folder"""
        pdf_files = list(Path(folder_path).glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {folder_path}")
            return
        
        print(f"Found {len(pdf_files)} PDF files")
        
        # Create graph schema
        self.create_graph_schema()
        
        # Process each PDF
        for pdf_file in pdf_files:
            try:
                self.ingest_document(str(pdf_file))
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
    
    def close(self):
        """Close Neo4j driver"""
        self.driver.close()

def main():
    """Main function to run the ingestion"""
    ingestor = GraphRAGIngestor()
    
    try:
        ingestor.ingest_all_pdfs()
        print("Ingestion completed!")
    except Exception as e:
        print(f"Error during ingestion: {e}")
    finally:
        ingestor.close()

if __name__ == "__main__":
    main() 
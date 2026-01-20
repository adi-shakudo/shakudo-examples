from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from neo4j import GraphDatabase
import os
import uvicorn

app = FastAPI(title="n8n-Neo4j-Bridge")

# Neo4j connection details from Environment Variables
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://neo4j.hyperplane-neo4j.svc.cluster.local:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Shakudo312!")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Updated Data Model
class ChatData(BaseModel):
    session_id: str
    agent_name: str  # e.g., "VOBC Orchestrator"
    topics: list[str] # e.g., ["Decoupling", "Abstraction", "Security"]

def execute_cypher(tx, session_id, agent_name, topics):
    # Updated Schema: (Session)-[:INTERACTED_WITH]->(Agent)-[:DISCUSSED]->(Topic)
    query = """
    MERGE (s:Session {id: $session_id})
    MERGE (a:Agent {name: $agent_name})
    MERGE (s)-[:INTERACTED_WITH]->(a)
    
    WITH a
    UNWIND $topics AS t_name
    MERGE (t:Topic {name: t_name})
    MERGE (a)-[:DISCUSSED]->(t)
    """
    tx.run(query, session_id=session_id, agent_name=agent_name, topics=topics)

@app.post("/graph/ingest")
async def ingest_chat(data: ChatData):
    try:
        with driver.session() as session:
            session.execute_write(execute_cypher, data.session_id, data.agent_name, data.topics)
        return {"status": "success", "session_id": data.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
def shutdown_event():
    driver.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8787)
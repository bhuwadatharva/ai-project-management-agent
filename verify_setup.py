import os
import sys
import logging

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DevPilot-Verify")

def run_checks():
    logger.info("========================================")
    logger.info("DEVPILOT AI - VERIFYING APPLICATION CONFIG")
    logger.info("========================================")
    
    # 1. Environment keys check
    from backend.app.config.settings import settings
    logger.info("Checking configuration keys:")
    logger.info(f"  - Database URL: {settings.DATABASE_URL}")
    logger.info(f"  - OpenAI API Key: {'Set' if settings.OPENAI_API_KEY else 'Not Set'}")
    logger.info(f"  - Google API Key: {'Set' if settings.GOOGLE_API_KEY else 'Not Set'}")
    logger.info(f"  - GitHub Token: {'Set' if settings.GITHUB_TOKEN else 'Not Set'}")
    
    # 2. Database test connection
    from backend.app.db.session import engine, Base
    try:
        logger.info("Connecting to database...")
        Base.metadata.create_all(bind=engine)
        logger.info("Successfully connected to database and provisioned schemas.")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)
        
    # 3. LangGraph compilation test
    try:
        logger.info("Compiling LangGraph Agent Workflow...")
        from backend.app.graph.workflow import compiled_graph
        # Test drawing or inspecting graph
        logger.info("Successfully compiled LangGraph workflow!")
    except Exception as e:
        logger.error(f"Failed to compile LangGraph: {e}")
        sys.exit(1)
        
    # 4. Mock REST client health checks
    try:
        logger.info("Testing REST Server App using FastAPI test client...")
        from fastapi.testclient import TestClient
        from backend.app.main import app
        
        client = TestClient(app)
        res = client.get("/")
        assert res.status_code == 200
        
        health_res = client.get("/api/health")
        assert health_res.status_code == 200
        logger.info(f"REST Health Check Endpoint returned: {health_res.json()}")
        
    except Exception as e:
        logger.error(f"Mock FastAPI endpoints test check failed: {e}")
        sys.exit(1)
        
    logger.info("========================================")
    logger.info("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    logger.info("DevPilot AI is ready for local execution.")
    logger.info("========================================")

if __name__ == "__main__":
    run_checks()

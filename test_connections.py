#!/usr/bin/env python3
"""
SehatAgent - Quick Connection Test
Tests GCP and Database connections
"""

import os
import sys
from pathlib import Path

# Load .env
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("🏥 SehatAgent - Connection Test")
print("=" * 60)

# ============================================================
# 1. SERVICE ACCOUNT
# ============================================================
print("\n1️⃣ Service Account JSON...")

json_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./idea92-975a54751781.json")
abs_path = Path(json_path).absolute()

if not Path(json_path).exists():
    print(f"   ❌ NOT FOUND: {json_path}")
    print(f"   Copy your service account JSON to the project folder!")
    sys.exit(1)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(abs_path)
print(f"   ✅ Found: {json_path}")

# ============================================================
# 2. GCP AUTHENTICATION
# ============================================================
print("\n2️⃣ GCP Authentication...")

try:
    from google.auth import default
    from google.auth.transport.requests import Request
    
    credentials, project = default()
    print(f"   ✅ Authenticated! Project: {project}")
except Exception as e:
    print(f"   ❌ Failed: {e}")

# ============================================================
# 3. DATABASE CONNECTION
# ============================================================
print("\n3️⃣ PostgreSQL Database...")

db_host = os.getenv("DB_HOST", "104.154.190.25")
db_name = os.getenv("DB_NAME", "bitech_sehatagent")
db_user = os.getenv("DB_USER", "postgres")
db_password = os.getenv("DB_PASSWORD", "idea92.superior")

try:
    import psycopg
    
    conn_string = f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}"
    conn = psycopg.connect(conn_string)
    
    # Check tables
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = [t[0] for t in cursor.fetchall()]
    
    print(f"   ✅ Connected to: {db_name}")
    print(f"   📋 Tables found: {tables}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"   ❌ Failed: {e}")

# ============================================================
# 4. VERTEX AI MODEL TEST
# ============================================================
print("\n4️⃣ Vertex AI Model Test...")

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    
    project_id = os.getenv("GCP_PROJECT_ID", "idea92")
    location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    model_name = os.getenv("VERTEX_AI_MODEL", "gemini-2.0-flash-001")
    
    print(f"   Initializing Vertex AI...")
    print(f"   Project: {project_id}")
    print(f"   Location: {location}")
    print(f"   Model: {model_name}")
    
    vertexai.init(project=project_id, location=location)
    model = GenerativeModel(model_name)
    
    print(f"   Sending test request...")
    response = model.generate_content("Reply with exactly: SehatAgent OK")
    
    print(f"   ✅ Response: {response.text.strip()}")
    print(f"   🎉 Vertex AI is working!")
    
except Exception as e:
    print(f"   ❌ Failed: {e}")
    print(f"\n   Possible issues:")
    print(f"   - Service account may not have Vertex AI permissions")
    print(f"   - Model name might be different")
    print(f"   - Try model: gemini-1.5-flash or gemini-1.5-pro")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("📊 SUMMARY")
print("=" * 60)
print("""
If all checks passed ✅, you're ready to run the app:

  uvicorn app.main:app --reload --port 8080

Then test with:

  curl -X POST http://localhost:8080/api/v1/health/analyze \\
    -H "Content-Type: application/json" \\
    -d '{"query": "mujhe bukhar hai", "language": "auto"}'
""")
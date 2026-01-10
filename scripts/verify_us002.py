
import sys
import os
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gym_agent.main import app

def verify():
    print("Verifying US-002 endpoints...")
    # httpx/TestClient will trigger lifespan
    with TestClient(app) as client:
        
        # Test Stats
        print("Testing /api/v1/dashboard/stats ...")
        resp = client.get("/api/v1/dashboard/stats")
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} - {resp.text}")
        assert resp.status_code == 200
        stats = resp.json()
        print("Stats:", stats)
        assert "total_customers" in stats
        
        # Test Customers List Search
        print("Testing search 'John' ...")
        resp = client.get("/api/v1/customers?search=John")
        assert resp.status_code == 200
        customers = resp.json()
        print(f"Found {len(customers)} customers.")
        
        cid = None
        if len(customers) > 0:
            cid = customers[0]["id"]
        else:
            # Fallback to getting all
            print("Fetching all customers to find an ID...")
            resp = client.get("/api/v1/customers")
            all_c = resp.json()
            if all_c:
                cid = all_c[0]["id"]
        
        if cid:
            print(f"Testing conversations for {cid} ...")
            resp = client.get(f"/api/v1/conversations/{cid}")
            assert resp.status_code == 200
            convs = resp.json()
            print(f"Found {len(convs)} conversations.")
            
        print("✅ US-002 Verification Complete!")

if __name__ == "__main__":
    verify()

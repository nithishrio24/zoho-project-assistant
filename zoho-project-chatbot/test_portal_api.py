import asyncio
import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv("../.env", override=True)

user_id = "60073829523"

async def test_api():
    db_path = "./zoho_chatbot.db"
    import aiosqlite
    
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT access_token FROM user_tokens WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            access_token = row[0]
            print(f"✅ Found token for user {user_id}\n")
            
            headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
            
            # Try project endpoints with different portal IDs
            endpoints = [
                ("GET /portal/1/projects/", "https://projectsapi.zoho.in/restapi/portal/1/projects/"),
                ("GET /portal/0/projects/", "https://projectsapi.zoho.in/restapi/portal/0/projects/"),
                ("GET /projects/", "https://projectsapi.zoho.in/restapi/projects/"),
                ("GET /portals/", "https://projectsapi.zoho.in/restapi/portals/"),
                ("GET /portal/portal1/projects/", "https://projectsapi.zoho.in/restapi/portal/portal1/projects/"),
            ]
            
            async with httpx.AsyncClient() as client:
                for label, url in endpoints:
                    try:
                        print(f"Trying: {label}")
                        print(f"  URL: {url}")
                        resp = await client.get(url, headers=headers, timeout=10.0)
                        print(f"  Status: {resp.status_code}")
                        if resp.status_code == 200:
                            data = resp.json()
                            print(f"  ✅ SUCCESS!\n  Response:\n{json.dumps(data, indent=4)}\n")
                        elif resp.status_code == 204:
                            print(f"  Status 204 (No Content)\n")
                        else:
                            try:
                                data = resp.json()
                                print(f"  Error: {data}\n")
                            except:
                                print(f"  Response text: {resp.text}\n")
                    except Exception as e:
                        print(f"  Exception: {e}\n")
        else:
            print(f"❌ No token found for user {user_id}")

asyncio.run(test_api())

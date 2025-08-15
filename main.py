from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
import os

app = FastAPI()

# Database config from environment variables (set these in Render)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "defaultdb")

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

class LicenseCheck(BaseModel):
    mac: str
    license_key: str

class RegisterDevice(BaseModel):
    mac: str
    license_key: str
    email: str

@app.post("/check_license")
def check_license(data: LicenseCheck):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT * FROM licenses WHERE mac_address=%s OR license_key=%s"
    cursor.execute(query, (data.mac, data.license_key))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return {"status": "invalid"}

    conn.close()
    return {"status": "valid", "email": result["email"]}

@app.post("/register_device")
def register_device(data: RegisterDevice):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if license key exists
    cursor.execute("SELECT * FROM licenses WHERE license_key=%s", (data.license_key,))
    license_row = cursor.fetchone()
    
    if not license_row:
        conn.close()
        return {"status": "invalid", "message": "License key not found"}
    
    # Update license row with mac and email
    cursor.execute(
        "UPDATE licenses SET mac_address=%s, email=%s WHERE license_key=%s",
        (data.mac, data.email, data.license_key)
    )
    conn.commit()
    conn.close()
    
    return {"status": "valid", "email": data.email}

@app.get("/")
def root():
    return {"message": "License server running"}

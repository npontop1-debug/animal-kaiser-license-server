from fastapi import FastAPI
from pydantic import BaseModel
import mysql.connector
import os

# Environment variables from Render
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

app = FastAPI()

# Request model for checking a license
class LicenseRequest(BaseModel):
    mac: str
    license_key: str

# Request model for registering a new device
class RegisterRequest(BaseModel):
    mac: str
    license_key: str
    email: str

@app.post("/check_license")
def check_license(req: LicenseRequest):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute(
            "SELECT email FROM device_keys WHERE mac_address = %s AND device_key = %s",
            (req.mac, req.license_key)
        )
        result = cursor.fetchone()
        if result:
            return {"status": "valid", "email": result[0]}
        else:
            return {"status": "invalid"}
    except mysql.connector.Error as err:
        return {"status": "error", "message": str(err)}
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

@app.post("/register_device")
def register_device(req: RegisterRequest):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        # Check if license key exists
        cursor.execute("SELECT device_key FROM device_keys WHERE device_key = %s", (req.license_key,))
        result = cursor.fetchone()
        if not result:

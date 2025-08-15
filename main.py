from fastapi import FastAPI
from pydantic import BaseModel
import mysql.connector
import os

# Get DB credentials from Render Environment Variables
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

app = FastAPI()

class LicenseRequest(BaseModel):
    mac: str
    license_key: str
    email: str = None  # optional, used when registering new MAC

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

        # Check if license exists
        cursor.execute(
            "SELECT email, mac_address FROM device_keys WHERE device_key = %s",
            (req.license_key,)
        )
        result = cursor.fetchone()

        if result:
            db_email, db_mac = result

            if db_mac == req.mac:
                # MAC matches, valid license
                return {"status": "valid", "email": db_email}
            elif db_mac is None:
                # MAC not set yet, register new device
                cursor.execute(
                    "UPDATE device_keys SET mac_address = %s, email = %s WHERE device_key = %s",
                    (req.mac, req.email or db_email, req.license_key)
                )
                conn.commit()
                return {"status": "valid", "email": req.email or db_email}
            else:
                # MAC does not match, invalid
                return {"status": "invalid"}
        else:
            return {"status": "invalid"}

    except mysql.connector.Error as err:
        return {"status": "error", "message": str(err)}

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from databases import Database
import qrcode
import io
import base64
from fastapi.responses import StreamingResponse

app = FastAPI()

DATABASE_URL = "sqlite:///./tickets.db"
database = Database(DATABASE_URL)

class Ticket(BaseModel):
    id: int
    name: str
    email: str
    used: bool = False

async def create_tables():
    query = """
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        used BOOLEAN
    );
    """
    await database.execute(query)

async def generate_ticket(name: str, email: str):
    ticket_id = await database.execute("INSERT INTO tickets (name, email, used) VALUES (:name, :email, :used)", 
                                       values={"name": name, "email": email, "used": False})
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"{ticket_id}")
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)

    img_str = base64.b64encode(buf.read()).decode('utf-8')
    return {"ticket_id": ticket_id, "qr_code": img_str}

async def validate_ticket(ticket_id: int):
    ticket = await database.fetch_one("SELECT * FROM tickets WHERE id = :id", values={"id": ticket_id})
    if ticket:
        if ticket['used']:
            raise HTTPException(status_code=400, detail="Ticket already used")
        await database.execute("UPDATE tickets SET used = :used WHERE id = :id", values={"used": True, "id": ticket_id})
        return {"message": "Ticket is valid"}
    raise HTTPException(status_code=404, detail="Ticket not found")

@app.on_event("startup")
async def startup():
    await database.connect()
    await create_tables()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/generate_ticket/")
async def generate_ticket_endpoint(name: str, email: str):
    return await generate_ticket(name, email)

@app.get("/validate_ticket/{ticket_id}")
async def validate_ticket_endpoint(ticket_id: int):
    return await validate_ticket(ticket_id)

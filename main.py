# main.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from databases import Database
import qrcode
import io
import base64
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

DATABASE_URL = "sqlite:///./tickets.db"
database = Database(DATABASE_URL)

class Ticket(BaseModel):
    id: int
    name: str
    email: str
    used: bool = False

class TicketRequest(BaseModel):
    name: str
    email: str
    password: str

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

async def get_tickets():
    query = "SELECT * FROM tickets"
    tickets = await database.fetch_all(query)
    return tickets

@app.on_event("startup")
async def startup():
    await database.connect()
    await create_tables()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/generate_ticket/")
async def generate_ticket_endpoint(ticket_request: TicketRequest):
    if ticket_request.password != "your_password":
        raise HTTPException(status_code=401, detail="Invalid password")

    return await generate_ticket(ticket_request.name, ticket_request.email)

@app.get("/tickets/")
async def get_tickets_endpoint():
    tickets = await get_tickets()
    return tickets
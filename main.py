from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from databases import Database
import qrcode
import hashlib
import os
import secrets
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
        used BOOLEAN,
        hash TEXT,
        qr_code_path TEXT
    );
    """
    await database.execute(query)

async def generate_ticket(name: str, email: str):
    existing_ticket = await database.fetch_one("SELECT * FROM tickets WHERE email = :email", values={"email": email})
    if existing_ticket:
        raise HTTPException(status_code=400, detail="Email already used for a ticket")

    ticket_hash = hashlib.sha256(secrets.token_bytes(32)).hexdigest()
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(ticket_hash)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    os.makedirs("qr_codes", exist_ok=True)
    image_path = f"qr_codes/{ticket_hash}.png"
    img.save(image_path)

    ticket_id = await database.execute("INSERT INTO tickets (name, email, used, hash, qr_code_path) VALUES (:name, :email, :used, :hash, :qr_code_path)", 
                                       values={"name": name, "email": email, "used": False, "hash": ticket_hash, "qr_code_path": image_path})

    return {"ticket_id": ticket_id, "qr_code_path": image_path}

@app.on_event("startup")
async def startup():
    await database.connect()
    await create_tables()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/generate_ticket/")
async def generate_ticket_endpoint(ticket_request: TicketRequest):
    if ticket_request.password != "your_password":  # Replace with your actual password
        raise HTTPException(status_code=401, detail="Invalid password")

    return await generate_ticket(ticket_request.name, ticket_request.email)

@app.get("/tickets/")
async def get_tickets_endpoint(password: str = Query(...)):
    if password != "your_password":  # Replace with your actual password
        raise HTTPException(status_code=401, detail="Invalid password")
    
    tickets = await database.fetch_all("SELECT * FROM tickets")
    return tickets

@app.delete("/cleanup/")
async def cleanup_database(password: str = Query(...)):
    if password != "your_cleanup_password":  # Replace with your actual cleanup password
        raise HTTPException(status_code=401, detail="Invalid password")
    
    await database.execute("DELETE FROM tickets")
    return {"detail": "All tickets have been deleted"}

@app.get("/validate_ticket/{ticket_hash}")
async def validate_ticket(ticket_hash: str):
    ticket = await database.fetch_one("SELECT * FROM tickets WHERE hash = :hash", values={"hash": ticket_hash})
    if ticket is None:
        return {"message": "Ticket is invalid"}
    if ticket["used"]:
        return {"message": "Ticket has already been used"}
    await database.execute("UPDATE tickets SET used = :used WHERE hash = :hash", values={"used": True, "hash": ticket_hash})
    return {"message": "Ticket is valid"}

app.mount("/qr_codes", StaticFiles(directory="qr_codes"), name="qr_codes")

from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from databases import Database
from passlib.context import CryptContext
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

DATABASE_URL = "mysql://ticket_user:XvJ7!252gi*N@7@localhost/ticketing_system"
database = Database(DATABASE_URL)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TicketRequest(BaseModel):
    name: str
    email: str
    password: str

class User(BaseModel):
    username: str
    password: str

async def create_tables():
    ticket_table_query = """
    CREATE TABLE IF NOT EXISTS tickets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        email VARCHAR(255) UNIQUE,
        used BOOLEAN,
        hash VARCHAR(255),
        qr_code_path VARCHAR(255)
    );
    """
    user_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) UNIQUE,
        password VARCHAR(255)
    );
    """
    await database.execute(ticket_table_query)
    await database.execute(user_table_query)

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

@app.post("/create_user/")
async def create_user(user: User):
    hashed_password = pwd_context.hash(user.password)
    await database.execute("INSERT INTO users (username, password) VALUES (:username, :password)", values={"username": user.username, "password": hashed_password})
    return {"message": "User created successfully"}

@app.post("/token/")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await database.fetch_one("SELECT * FROM users WHERE username = :username", values={"username": form_data.username})
    if not user or not pwd_context.verify(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": form_data.username, "token_type": "bearer"}

app.mount("/qr_codes", StaticFiles(directory="qr_codes"), name="qr_codes")

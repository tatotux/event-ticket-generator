# Event Ticketing System

This repository contains a complete solution for an event ticketing system. The system allows the generation, storage, and validation of tickets for an event, ensuring that each ticket is unique and can only be used once.

## Features

- **Ticket Generation**: Generate unique tickets with QR codes.
- **Ticket Storage**: Store ticket information including buyer's name, email, and usage status.
- **Ticket Validation**: Validate tickets at the event entrance using a web application accessible from an Android phone.

## Technologies Used

- **Backend**: FastAPI, Uvicorn
- **Frontend**: HTML, JavaScript
- **QR Code Generation**: qrcode (Python library)
- **QR Code Scanning**: html5-qrcode (JavaScript library)

## Getting Started

### Prerequisites

- Python 3.7+
- Node.js (for serving the frontend, optional)

### Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/event-ticketing-system.git
    cd event-ticketing-system
    ```

2. **Set up the backend**:
    - Install the required Python packages:
      ```bash
      pip install fastapi uvicorn qrcode[pil]
      ```
    - Run the FastAPI server:
      ```bash
      uvicorn main:app --reload
      ```

3. **Set up the frontend**:
    - Open the `index.html` file in a web browser. Alternatively, you can serve it using a simple HTTP server:
      ```bash
      npx http-server .
      ```

### Usage

1. **Generate a Ticket**:
    - Send a POST request to `/generate_ticket/` with the buyer's name and email:
      ```bash
      curl -X POST "http://localhost:8000/generate_ticket/?name=John Doe&email=johndoe@example.com"
      ```
    - The response will include the ticket ID and a base64-encoded QR code image.

2. **Validate a Ticket**:
    - Open the `index.html` file in a web browser on an Android phone.
    - Click the "Scan QR Code" button to start scanning.
    - Point the camera at the QR code to validate the ticket.
    - The web application will communicate with the FastAPI backend to check if the ticket is valid and not used.

### File Structure

event-ticketing-system/
│
├── main.py # FastAPI application
├── index.html # Frontend web application
├── README.md # Project documentation
└── requirements.txt # Python dependencies

### API Endpoints

- **Generate Ticket**:
  - **URL**: `/generate_ticket/`
  - **Method**: `POST`
  - **Parameters**: `name`, `email`
  - **Response**: `ticket_id`, `qr_code`

- **Validate Ticket**:
  - **URL**: `/validate_ticket/{ticket_id}`
  - **Method**: `GET`
  - **Response**: `message`

### Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

### License

This project is licensed under the MIT License.

### Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [html5-qrcode](https://github.com/mebjas/html5-qrcode)
- [qrcode](https://github.com/lincolnloop/python-qrcode)

---

Feel free to customize this `README.md` file according to your specific requirements.

# FastAPI Demo Project

This is a simple FastAPI demo project for educational purposes.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Make sure you have Python 3.7 or higher installed.

### Installing Dependencies

Create a virtual environment and install the project dependencies.

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
```

### Running the Application

Run the FastAPI application using the following command:

```bash
uvicorn main:app --reload
```

Visit http://127.0.0.1:8000/docs in your browser to access the Swagger documentation and explore the API.

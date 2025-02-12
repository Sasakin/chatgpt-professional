from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Numbers(BaseModel):
    num1: float
    num2: float

@app.post("/add")
def add(numbers: Numbers):
    return {"result": numbers.num1 + numbers.num2}

@app.post("/subtract")
def subtract(numbers: Numbers):
    return {"result": numbers.num1 - numbers.num2}

@app.post("/multiply")
def multiply(numbers: Numbers):
    return {"result": numbers.num1 * numbers.num2}

@app.post("/divide")
def divide(numbers: Numbers):
    if numbers.num2 == 0:
        return {"error": "Division by zero is not allowed"}
    return {"result": numbers.num1 / numbers.num2}

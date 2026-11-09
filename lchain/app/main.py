from fastapi import FastAPI

app = FastAPI()

@app.get('/')
async def hello():
    print('hello world')
    return "hello world"



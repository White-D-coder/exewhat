from fastapi import FastAPI, Response
import uvicorn

app = FastAPI()

@app.head("/")
def health_check_head():
    return Response(content="ok", status_code=200)

@app.get("/")
def health_check_get():
    return Response(content="ok", status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/s3-event")
async def s3_event(request: Request):
    body = await request.json()
    print("📩 Evento recibido desde Lambda/S3:")
    print(body)
    return {"status": "received", "data": body}

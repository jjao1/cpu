from fastapi import FastAPI
import httpx

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Simple URL Request API"}

@app.get("/request")
async def get_url(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return {
            "status": response.status_code,
            "content": response.text
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

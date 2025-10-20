# backend/main.py
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
from model import predict_image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/predict/")
async def predict(
    file: UploadFile = File(...),
    container_width: float = Form(...),
    container_height: float = Form(...),
):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Please upload a JPEG or PNG image.",
        )
    image = Image.open(io.BytesIO(await file.read())).convert("RGB")
    result = predict_image(image, container_width, container_height)
    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)

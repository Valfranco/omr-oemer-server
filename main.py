import os
import tempfile
import glob
import subprocess
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from oemer.downloader import fetch_models

app = FastAPI(title="OMR Oemer Server")

# Permitir peticiones desde tu app web en Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    fetch_models()
except Exception as e:
    print("Estado de modelos Oemer:", e)

@app.get("/")
def home():
    return {"status": "Servidor OMR activo"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input_sheet.png")
        
        content = await file.read()
        with open(input_path, "wb") as f:
            f.write(content)

        try:
            subprocess.run(["oemer", input_path, "-o", tmpdir], check=True)
        except Exception as err:
            raise HTTPException(status_code=500, detail=f"Error en OMR: {str(err)}")

        xml_files = glob.glob(os.path.join(tmpdir, "*.musicxml")) + glob.glob(os.path.join(tmpdir, "*.xml"))
        
        if not xml_files:
            raise HTTPException(status_code=500, detail="No se identificaron notas en la imagen.")

        with open(xml_files[0], "r", encoding="utf-8") as f:
            xml_data = f.read()

        return Response(content=xml_data, media_type="application/xml")

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from ultralytics import YOLO
import io
import base64
from PIL import Image
import os
from typing import List, Dict, Any
import uvicorn
from pathlib import Path

app = FastAPI(
    title="Eggplant Leaf Disease Detection API",
    description="API for detecting diseases in eggplant leaves using YOLOv8",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model path - using the trained model for eggplant leaf diseases
BEST_MODEL_PATH = "best.pt"

# Disease information mapping
DISEASE_INFO = {
    0: {
        "name": "Healthy",
        "description": "The plant exhibits vibrant, green leaves with no signs of disease, pest infestation, or discoloration. It shows robust growth and normal plant characteristics.",
        "severity": "None",
        "recommendation": {
        "priority": "Low",
        "urgency": "None",
        "treatment": "None required.",
        "action": "Continue regular monitoring and care.",
        },
        "treatment": "No treatment necessary.",
        "prevention": "Maintain healthy soil and good growing conditions. Ensure proper sunlight and watering practices. Use disease-free seeds and avoid overcrowding plants."
    },
    2: {
        "name": "Leaf Spot",
        "description": "The leaf spots start as small round yellow flecks, which are slightly sunken. As the spots grow larger, their shape becomes more irregular, and they are surrounded by a yellow halo. These spots may cause the affected leaves to turn yellow and eventually die.",
        "severity": "Medium",
        "recommendation": {
            "priority": "Medium",
            "urgency": "Moderate",
            "treatment": "Use fungicides and remove infected leaves to prevent spread.",
            "action": "Apply fungicides and remove affected plant material immediately",
        },
        "treatment": "Remove and destroy infected plant material. Apply fungicides like copper or chlorothalonil.",
        "prevention": "Avoid overhead irrigation and ensure proper spacing between plants. Use resistant varieties if available. Practice crop rotation and remove debris from the soil."
    },
    3: {
        "name": "Mosaic Virus",
        "description": "Yellow, mosaic-like patterns on leaves, with stunted growth and distorted plant structures. The virus is often spread by aphids or contaminated tools.",
        "severity": "High",
        "recommendation": {
            "priority": "High",
            "urgency": "Immediate action required",
            "treatment": "Remove infected plants and control aphids promptly.",
            "action": "Isolate affected plants and apply insecticides or aphid control measures.",
        },
        "treatment": "Remove and destroy infected plants. Control aphid populations using insecticidal soap or natural predators like ladybugs.",
        "prevention": "Use virus-free seeds and resistant varieties. Control aphid populations through regular inspection and pesticide application. Clean tools regularly to avoid spreading the virus."
    },
    1: {
        "name": "Insect Pest Diseases",
        "description": "Damage caused by various insect pests such as aphids, caterpillars, flea beetles, or whiteflies. These pests cause wilting, discoloration, and the presence of holes in the leaves.",
        "severity": "Medium",
        "recommendation": {
            "priority": "Medium",
            "urgency": "Moderate",
            "treatment": "Use recommended insecticides or introduce natural predators like ladybugs.",
            "action": "Apply appropriate insecticides or biological control methods.",
        },
        "treatment": "Use insecticidal soap, neem oil, or targeted pesticides. Introduce natural predators like ladybugs or predatory beetles.",
        "prevention": "Inspect plants regularly for signs of pests. Use row covers to protect plants from insects. Remove weeds where pests may hide and feed."
    }
}
    

# Load the model once when the app starts
try:
    # Fix for PyTorch 2.6+ weights_only issue
    import torch
    # Set torch.load to use weights_only=False for model loading
    original_load = torch.load
    def patched_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_load(*args, **kwargs)
    torch.load = patched_load
    
    model = YOLO(BEST_MODEL_PATH)
    
    # Restore original torch.load
    torch.load = original_load
    
    print(f"✅ Eggplant Disease Detection Model loaded successfully from {BEST_MODEL_PATH}")
    print(f"📊 Model classes: {model.names}")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main frontend page"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return {"message": "YOLO Object Detection API is running", "status": "healthy", "note": "Frontend not found - API only mode"}

@app.get("/health")
async def health_check():
    """Health check endpoint for API status"""
    return {
        "message": "Eggplant Leaf Disease Detection API is running",
        "status": "healthy",
        "model_loaded": model is not None
    }

@app.get("/model/info")
async def get_model_info():
    """Get information about the loaded model"""
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    return {
        "model_name": "YOLOv8 Eggplant Leaf Disease Detection",
        "model_path": BEST_MODEL_PATH,
        "model_loaded": True,
        "classes": model.names if hasattr(model, 'names') else "Unknown",
        "description": "Trained to detect diseases in eggplant leaves including Bacterial Wilt, Phomopsis Blight, and Verticillium Wilt"
    }

@app.get("/diseases/info")
async def get_diseases_info():
    """Get information about all detectable diseases"""
    return {
        "total_diseases": len(DISEASE_INFO),
        "diseases": DISEASE_INFO
    }

@app.post("/predict_with_image")
async def predict_with_annotated_image(file: UploadFile = File(...)):
    """
    Upload an eggplant leaf image and get predictions with annotated image
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image file
        contents = await file.read()
        
        # Convert to numpy array
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Perform prediction
        results = model.predict(source=image, conf=0.3)
        
        # Extract predictions
        predictions = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls.item())
                    prediction = {
                        "class_id": class_id,
                        "class_name": model.names[class_id],
                        "confidence": float(box.conf.item()),
                        "bbox": {
                            "x1": float(box.xyxy[0][0].item()),
                            "y1": float(box.xyxy[0][1].item()),
                            "x2": float(box.xyxy[0][2].item()),
                            "y2": float(box.xyxy[0][3].item())
                        }
                    }
                    predictions.append(prediction)
        
        # Get annotated image
        annotated_image = results[0].plot()
        
        # Convert to base64
        _, buffer = cv2.imencode('.jpg', annotated_image)
        annotated_image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            "filename": file.filename,
            "predictions": predictions,
            "total_detections": len(predictions),
            "annotated_image": f"data:image/jpeg;base64,{annotated_image_base64}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/diagnose")
async def diagnose_disease(file: UploadFile = File(...)):
    """
    Upload an eggplant leaf image for detailed disease diagnosis with treatment recommendations
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image file
        contents = await file.read()
        
        # Convert to numpy array
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Perform prediction
        results = model.predict(source=image, conf=0.3)
        
        # Extract predictions with detailed diagnosis
        diagnoses = []
        highest_confidence_disease = None
        max_confidence = 0
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls.item())
                    confidence = float(box.conf.item())
                    
                    if confidence > max_confidence:
                        max_confidence = confidence
                        highest_confidence_disease = class_id
                    
                    diagnosis = {
                        "detection": {
                            "class_id": class_id,
                            "class_name": model.names[class_id],
                            "confidence": confidence,
                            "bbox": {
                                "x1": float(box.xyxy[0][0].item()),
                                "y1": float(box.xyxy[0][1].item()),
                                "x2": float(box.xyxy[0][2].item()),
                                "y2": float(box.xyxy[0][3].item())
                            }
                        },
                        "disease_info": DISEASE_INFO.get(class_id, {
                            "name": "Unknown",
                            "description": "Disease information not available",
                            "severity": "Unknown",
                            "treatment": "Consult with agricultural expert",
                            "prevention": "Follow general plant care guidelines"
                        })
                    }
                    diagnoses.append(diagnosis)
                
        return {
            "filename": file.filename,
            "total_detections": len(diagnoses),
            "diagnoses": diagnoses,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

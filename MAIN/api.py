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
    title="Malabar Spinach Leaf Disease Detection API",
    description="API for detecting diseases in malabar spinach leaves using YOLOv8",
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

# Model path - using the trained model for malabar spinach leaf diseases
BEST_MODEL_PATH = "best.pt"

# Disease information mapping
DISEASE_INFO = {
    0: {
        "name": "Healthy",
        "description": "The plant exhibits vibrant green leaves, robust growth, and no visible signs of disease or pest infestation.",
        "severity": "None",
        "recommendation": {
            "priority": "Low",
            "urgency": "None",
            "treatment": "None required.",
            "action": "Continue regular maintenance and monitoring.",
        },
        "treatment": "No treatment necessary.",
        "prevention": "Maintain optimal growing conditions: well-drained soil, adequate sunlight, and proper spacing."
    },
    1: {
        "name": "Anthracnose",
        "description": "Characterized by dark, sunken lesions on leaves and stems, often with a reddish-brown center.",
        "severity": "High",
        "recommendation": {
            "priority": "High",
            "urgency": "Immediate action required",
            "treatment": "Use recommended fungicides and remove infected plant material.",
            "action": "Apply fungicide and remove infected material.",
        },
        "treatment": "Remove and destroy infected plant parts. Apply fungicides containing copper or azoxystrobin.",
        "prevention": "Use disease-free seeds. Practice crop rotation to avoid the buildup of pathogens. Ensure good air circulation and avoid overhead irrigation."
    },
    2: {
        "name": "Bacterial Spot",
        "description": "Small, water-soaked lesions that turn yellow and may have a greasy appearance.",
        "severity": "Medium",
        "recommendation": {
            "priority": "Medium",
            "urgency": "Moderate",
            "treatment": "Use copper-based bactericides and maintain good hygiene.",
            "action": "Apply bactericides and remove infected material.",
        },
        "treatment": "Remove and destroy infected plant parts. Apply bactericides containing copper.",
        "prevention": "Use disease-free seeds and practice crop rotation. Avoid working among wet plants to prevent the spread."
    },
    3: {
        "name": "Downy Mildew",
        "description": "Yellow angular lesions on the upper leaf surface with a grayish-purple mold on the underside.",
        "severity": "High",
        "recommendation": {
            "priority": "High",
            "urgency": "High",
            "treatment": "Use recommended fungicides and adjust watering practices.",
            "action": "Implement fungicide application and improve cultural practices.",
        },
        "treatment": "Remove and destroy infected plant parts. Apply fungicides such as copper or phosphorus acid.",
        "prevention": "Ensure proper spacing for good air circulation. Water early in the day to allow foliage to dry. Avoid overhead irrigation."
    },
    4: {
        "name": "Pest Damage",
        "description": "Damage from insects like aphids, spider mites, or caterpillars, leading to distorted or chewed leaves.",
        "severity": "Medium",
        "recommendation": {
            "priority": "Medium",
            "urgency": "Moderate",
            "treatment": "Use recommended insecticides or introduce beneficial insects.",
            "action": "Apply appropriate pest control measures.",
        },
        "treatment": "Use insecticidal soap or neem oil. Introduce natural predators like ladybugs.",
        "prevention": "Regularly inspect plants for pests. Remove weeds that can harbor pests. Maintain healthy plant vigor to resist pest attacks."
    },
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
    
    print(f"✅ Malabar Spinach Disease Detection Model loaded successfully from {BEST_MODEL_PATH}")
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
        "message": "Malabar Spinach Leaf Disease Detection API is running",
        "status": "healthy",
        "model_loaded": model is not None
    }

@app.get("/model/info")
async def get_model_info():
    """Get information about the loaded model"""
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    return {
        "model_name": "YOLOv8 Malabar Spinach Leaf Disease Detection",
        "model_path": BEST_MODEL_PATH,
        "model_loaded": True,
        "classes": model.names if hasattr(model, 'names') else "Unknown",
        "description": "Trained to detect diseases in malabar spinach leaves including Bacterial Wilt, Phomopsis Blight, and Verticillium Wilt"
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
    Upload an malabar spinach leaf image and get predictions with annotated image
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
    Upload an malabar spinach leaf image for detailed disease diagnosis with treatment recommendations
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
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)

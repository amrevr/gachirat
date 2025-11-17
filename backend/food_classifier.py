import torch
import torchvision.transforms as transforms
import torchvision.models as models
from torchvision.models import ResNet50_Weights
from PIL import Image
import io
import urllib.request
import json
import os
import google.generativeai as genai

# Load pre-trained ResNet50 model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = models.resnet50(weights=None)
weights_path = os.path.join(os.path.dirname(__file__), 'trained_weights')
model.load_state_dict(torch.load(weights_path, map_location=device))
model = model.to(device)
model.eval()

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY: genai.configure(api_key=GEMINI_API_KEY)

# Load ImageNet class labels
try:
    imagenet_labels_url = "https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json"
    with urllib.request.urlopen(imagenet_labels_url) as url:
        imagenet_labels = json.loads(url.read().decode())
    print(f"[DEBUG] Loaded {len(imagenet_labels)} ImageNet labels")
except Exception as e:
    print(f"[DEBUG] Warning: Could not load ImageNet labels: {e}")
    imagenet_labels = []

# Image preprocessing
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Nutrition mapping (health score: 1=very unhealthy, 5=very healthy)
NUTRITION_MAP = {
    # Fruits (4-5)
    'banana': {'health_score': 5, 'category': 'fruit'},
    'apple': {'health_score': 5, 'category': 'fruit'},
    'orange': {'health_score': 5, 'category': 'fruit'},
    'strawberry': {'health_score': 5, 'category': 'fruit'},
    'pineapple': {'health_score': 4, 'category': 'fruit'},
    'lemon': {'health_score': 5, 'category': 'fruit'},
    
    # Vegetables (5)
    'broccoli': {'health_score': 5, 'category': 'vegetable'},
    'mushroom': {'health_score': 5, 'category': 'vegetable'},
    'artichoke': {'health_score': 5, 'category': 'vegetable'},
    'cauliflower': {'health_score': 5, 'category': 'vegetable'},
    'zucchini': {'health_score': 5, 'category': 'vegetable'},
    'cucumber': {'health_score': 5, 'category': 'vegetable'},
    
    # Fast food (1-2)
    'cheeseburger': {'health_score': 1, 'category': 'fast food'},
    'hamburger': {'health_score': 2, 'category': 'fast food'},
    'pizza': {'health_score': 2, 'category': 'fast food'},
    'hotdog': {'health_score': 1, 'category': 'fast food'},
    'french fries': {'health_score': 1, 'category': 'fast food'},
    
    # Desserts (1-2)
    'ice cream': {'health_score': 1, 'category': 'dessert'},
    'chocolate': {'health_score': 2, 'category': 'dessert'},
    'cupcake': {'health_score': 1, 'category': 'dessert'},
    'doughnut': {'health_score': 1, 'category': 'dessert'},
    'tiramisu': {'health_score': 2, 'category': 'dessert'},
    
    # Default for unknown foods
    'unknown': {'health_score': 3, 'category': 'unknown'}
}

def get_nutrition_info(food_name):
    """Get nutrition info for a food item"""
    food_lower = food_name.lower()
    
    # Check for exact match
    if food_lower in NUTRITION_MAP:
        return NUTRITION_MAP[food_lower]
    
    # Check for partial match
    for key in NUTRITION_MAP:
        if key in food_lower or food_lower in key:
            return NUTRITION_MAP[key]
    
    # Default
    return NUTRITION_MAP['unknown']

def classify_food_with_gemini(image_bytes):
    """Fallback classification using Gemini vision model"""
    try:
        print(f"[DEBUG] Using Gemini vision fallback for classification...")
        
        # Load image from bytes
        image = Image.open(io.BytesIO(image_bytes))
        
        # Use Gemini vision model
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = """Identify the main food item in this image. Respond with ONLY the specific food name in lowercase (e.g., 'banana', 'pizza', 'broccoli'). 
        If multiple foods are present, identify the most prominent one. 
        If no food is visible, respond with 'unknown'."""
        
        response = model.generate_content([prompt, image])
        food_name = response.text.strip().lower()
        
        print(f"[DEBUG] Gemini classified as: {food_name}")
        return food_name, 0.75  # Assign a reasonable confidence for Gemini results
        
    except Exception as e:
        print(f"[ERROR] Gemini vision classification failed: {e}")
        import traceback
        traceback.print_exc()
        return "unknown food", 0.0

def classify_food(image_file):
    """Classify food image using ResNet50"""
    try:
        print(f"[DEBUG] Starting classification...")
        print(f"[DEBUG] Image file type: {type(image_file)}")
        
        # Load and preprocess image
        image_bytes = image_file.read()
        print(f"[DEBUG] Read {len(image_bytes)} bytes from image file")
        
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        print(f"[DEBUG] Image loaded successfully: {image.size}")
        
        input_tensor = preprocess(image)
        input_batch = input_tensor.unsqueeze(0).to(device)
        
        # Predict
        with torch.no_grad():
            output = model(input_batch)
        
        # Get top prediction
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top_prob, top_idx = torch.topk(probabilities, 1)
        
        predicted_label = imagenet_labels[top_idx.item()] if imagenet_labels else "unknown food"
        confidence = top_prob.item()
        
        print(f"[DEBUG] Classified as: {predicted_label} with confidence: {confidence:.2f}")
        
        # If confidence is too low, use Gemini vision as fallback
        if confidence < 0.6:
            print(f"[DEBUG] Confidence {confidence:.2f} < 0.6, trying Gemini vision...")
            return classify_food_with_gemini(image_bytes)
        
        return predicted_label, confidence
    except Exception as e:
        print(f"[ERROR] Classification failed: {e}")
        import traceback
        traceback.print_exc()
        # Try Gemini vision as fallback on error
        try:
            image_file.seek(0)
            image_bytes = image_file.read()
            return classify_food_with_gemini(image_bytes)
        except:
            return "unknown food", 0.0

if __name__ == "__main__":
    pass    

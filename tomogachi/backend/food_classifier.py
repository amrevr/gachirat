import torch
import torchvision.transforms as transforms
import torchvision.models as models
from torchvision.models import ResNet50_Weights
from PIL import Image
import io
import urllib.request
import json
import os

# Load pre-trained ResNet50 model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = models.resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
model = model.to(device)
model.eval()

# Image preprocessing
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Load ImageNet labels
LABELS_URL = 'https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json'
try:
    with urllib.request.urlopen(LABELS_URL) as url:
        imagenet_labels = json.loads(url.read().decode())
except Exception as e:
    print(f"Warning: Could not load ImageNet labels: {e}")
    imagenet_labels = []

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
        
        return predicted_label, confidence
    except Exception as e:
        print(f"[ERROR] Classification failed: {e}")
        import traceback
        traceback.print_exc()
        return "unknown food", 0.0

if __name__ == "__main__":
    # Directory with test images
    test_dir = "tomogachi/backend/test_images"

    print(f"Model loaded on device: {device}")
    print(f"ImageNet labels loaded: {len(imagenet_labels)} classes")

    if not os.path.isdir(test_dir):
        print(f"Test images directory not found: {test_dir}")
    else:
        exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        image_files = sorted([os.path.join(test_dir, f) for f in os.listdir(test_dir)
                              if os.path.splitext(f)[1].lower() in exts])

        if not image_files:
            print(f"No image files found in: {test_dir}")
        else:
            for img_path in image_files:
                try:
                    with open(img_path, "rb") as img_file:
                        predicted_label, confidence = classify_food(img_file)

                    nutrition = get_nutrition_info(predicted_label)
                    print(f"{os.path.basename(img_path)} -> {predicted_label} ({confidence*100:.2f}%) "
                          f"health_score={nutrition['health_score']}, category={nutrition['category']}")
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")

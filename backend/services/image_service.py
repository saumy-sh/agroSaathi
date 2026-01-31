import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import numpy as np
import pandas as pd
from pathlib import Path

class MobileNetV2Predictor:
    def __init__(self, model_path, device=None):
        """
        Initialize the MobileNetV2 predictor
        
        Args:
            model_path (str): Path to the saved fine-tuned model
            device (str): Device to run inference on ('cuda' or 'cpu')
        """
        self.model_path = model_path
        self.device = device if device else torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load model and class names
        self._load_model()
        
        # Setup transforms
        self._setup_transforms()
        
        print(f"Model loaded successfully on {self.device}")
        print(f"Number of classes: {len(self.class_names)}")
        print(f"Class names: {self.class_names}")
    
    def _load_model(self):
        """Load the fine-tuned model"""
        try:
            # Load checkpoint
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            # Get class names from checkpoint
            if 'class_names' in checkpoint:
                self.class_names = checkpoint['class_names']
            else:
                # If class names not saved, you'll need to provide them manually
                print("Warning: Class names not found in checkpoint. Using default names.")
                self.class_names = [f'class_{i}' for i in range(len(checkpoint['model_state_dict']['classifier.1.weight']))]
            
            self.num_classes = len(self.class_names)
            
            # Create model architecture
            self.model = models.mobilenet_v2(pretrained=False)
            self.model.classifier = nn.Sequential(
                nn.Dropout(0.2),
                nn.Linear(1280, self.num_classes)
            )
            
            # Load trained weights
            if 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            
            # Move to device and set to eval mode
            self.model = self.model.to(self.device)
            self.model.eval()
            
        except Exception as e:
            raise Exception(f"Error loading model: {e}")
    
    def _setup_transforms(self):
        """Setup image preprocessing transforms"""
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def predict_single_image(self, image_path, return_probabilities=False):
        """
        Predict class for a single image
        
        Args:
            image_path (str): Path to the image
            return_probabilities (bool): Whether to return class probabilities
            
        Returns:
            dict: Prediction results
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            input_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            # Make prediction
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
                confidence, predicted_idx = torch.max(probabilities, 0)
                
                predicted_class = self.class_names[predicted_idx.item()]
                confidence_score = confidence.item()
            
            result = {
                'image_path': image_path,
                'predicted_class': predicted_class,
                'confidence': confidence_score,
                'predicted_index': predicted_idx.item()
            }
            
            if return_probabilities:
                prob_dict = {self.class_names[i]: prob.item() 
                           for i, prob in enumerate(probabilities)}
                result['class_probabilities'] = prob_dict
            
            return result
            
        except Exception as e:
            return {
                'image_path': image_path,
                'error': str(e)
            }

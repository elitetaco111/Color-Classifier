import joblib
import os
import cv2
import numpy as np

#load the model
knn_loaded = joblib.load("color_model.pkl")
print("Model loaded successfully!")

#how to calc mean image color
def extract_color_features(image_path):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) #RGB conversion func
    mean_color = np.mean(image, axis=(0, 1)) #mean the color values
    return mean_color

#how to get central pixel color value
def get_center_pixel_color(image_path):
    image = cv2.imread(image_path) 
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    height, width, _ = image.shape
    center_x, center_y = width // 2, height // 2 

    center_pixel = image[center_y, center_x]
    return center_pixel

#ONLY CHOOSE ONE OF THE ABOVE METHODS (just func defs up here though)

def predict_color(image_path, model):
    center_color = get_center_pixel_color(image_path).reshape(1, -1)  # Reshape for prediction
    predicted_label = model.predict(center_color)
    return predicted_label[0]

image_path = "test_image.jpg"
predicted_color = predict_color(image_path, knn_loaded)
print(f"Predicted Color: {predicted_color}")

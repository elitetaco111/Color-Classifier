import joblib
import os
import cv2
import numpy as np
import pandas as pd

#load the model
knn_loaded = joblib.load("color_modelv2.pkl")
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

#ONLY CHOOSE ONE OF THE ABOVE METHODS (just func defs above here though)

def predict_color(image_path, model):
    center_color = extract_color_features(image_path).reshape(1, -1)  # Reshape for prediction
    predicted_label = model.predict(center_color)
    return predicted_label[0]

def process_images_from_folder(folder_path, model, output_file):
    image_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('jpeg', 'jpg'))]
    results = []
    
    for image_path in image_files:
        image_name = os.path.basename(image_path)
        image_name = image_name.partition('.')[0]
        predicted_color = predict_color(image_path, model)
        results.append((image_name, predicted_color))
    
    df = pd.DataFrame(results, columns=["Name", "Predicted Color"])
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

###########################################

# image_path = "test.jpg"
# predicted_color = predict_color(image_path, knn_loaded)
# print(f"Predicted Color: {predicted_color}")

#single image test ^^^^^^^^
#multi image test vvvvvvvv

image_folder = "test/"  
output_csv = "color_predictions.csv"
process_images_from_folder(image_folder, knn_loaded, output_csv)

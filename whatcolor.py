import joblib
import os
import cv2
import numpy as np
import pandas as pd

os.environ["LOKY_MAX_CPU_COUNT"] = "10"

#load the model
knn_loaded = joblib.load("gray_model.pkl")
print("Model loaded successfully!")

#how to calc mean image color
def extract_color_features(image_path):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) #RGB conversion func
    mean_color = np.mean(image, axis=(0, 1)) #mean the color values
    return mean_color

#calc mean color without white pixels
def extract_color_features_nw(image_path):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  #convert to RGB

    #create a mask for non-white pixels
    mask = ~(np.all(image == [255, 255, 255], axis=-1))

    #extract non-white pixels to mask
    non_white_pixels = image[mask]

    #compute mean color
    if len(non_white_pixels) > 0:
        mean_color = np.mean(non_white_pixels, axis=0)
    else:
        mean_color = [0, 0, 0]  #default to black if no valid pixels

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
    center_color = extract_color_features_nw(image_path).reshape(1, -1)  # Reshape for prediction
    predicted_label = model.predict(center_color)
    return predicted_label[0]

def process_images_from_folder(folder_path, model, output_file):
    image_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('jpeg', 'jpg'))]
    results = []
    
    for image_path in image_files:
        print(f"Processing image: {image_path}")
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

image_folder = "gray_images/"  
output_csv = "gray_predictions.csv"
process_images_from_folder(image_folder, knn_loaded, output_csv)

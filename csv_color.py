import cv2
import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
import joblib  # For saving and loading the model
import os  # To check if the model file exists
import requests  # For downloading images
from io import BytesIO
from PIL import Image

# Number of neighbors to use for KNN
n = 1  # Set to 1 since we want the closest match

# Base URL for constructing image URLs
BASE_URL = 'https://media.rallyhouse.com/homepage/{}-1.jpg?tx=f_auto,c_fit,w_730,h_730'

# Path to save/load the trained model
model_path = "knn_model.joblib"

# Function to calculate mean color without white pixels
def extract_color_features_nw(image):
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)  # Convert PIL image to OpenCV format
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert to RGB

    # Create a mask for non-white pixels
    mask = ~(np.all(image == [255, 255, 255], axis=-1))

    # Extract non-white pixels using the mask
    non_white_pixels = image[mask]

    # Compute mean color
    if len(non_white_pixels) > 0:
        mean_color = np.mean(non_white_pixels, axis=0)
    else:
        mean_color = [0, 0, 0]  # Default to black if no valid pixels

    return mean_color

# Function to download an image from a URL
def download_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        return image
    else:
        raise Exception(f"Failed to download image from {url}")

# Function to train the model
def train_model(csv_path):
    # Load item data from a CSV file
    item_data = pd.read_csv(csv_path)

    # Columns in the CSV: 'Name', 'Parent Color Primary', 'PictureID'
    x = []  # To store RGB features
    y = []  # To store color labels

    for _, row in item_data.iterrows():
        name = row['Name']
        color = row['Parent Color Primary']
        picture_id = row['Picture ID']

        # Try downloading the image using Name first
        try:
            image_url = BASE_URL.format(name)
            image = download_image(image_url)
        except Exception as e1:
            print(f"Failed to download image using Name {name}: {e1}")
            # Fallback to PictureID if Name fails
            try:
                image_url = BASE_URL.format(picture_id)
                image = download_image(image_url)
            except Exception as e2:
                print(f"Failed to download image using PictureID {picture_id}: {e2}")
                continue  # Skip this row if both attempts fail

        # Extract color features
        mean_color = extract_color_features_nw(image)

        # Append features and label
        x.append(mean_color)
        y.append(color)

    # Convert to numpy arrays
    x = np.array(x)
    y = np.array(y)

    # Initialize the KNN classifier
    knn = KNeighborsClassifier(n_neighbors=n)
    knn.fit(x, y)  # Train the model using the extracted features

    # Save the trained model to a file
    joblib.dump(knn, model_path)
    print("Trained and saved the KNN model to file.")

# Function to test the model
def test_model(test_csv_path, output_csv_path):
    # Load the trained model
    if not os.path.exists(model_path):
        raise Exception("Model file not found. Train the model first.")

    knn = joblib.load(model_path)
    print("Loaded the KNN model from file.")

    # Load test data from a CSV file
    test_data = pd.read_csv(test_csv_path)

    # Columns in the CSV: 'Name', 'PictureID', 'Color List'
    results = []

    for _, row in test_data.iterrows():
        name = row['Name']
        picture_id = row['Picture ID']
        original_color_list = row['Color List']  # Get the original color list value

        # Try downloading the image using Name first
        try:
            image_url = BASE_URL.format(name)
            image = download_image(image_url)
        except Exception as e1:
            print(f"Failed to download image using Name {name}: {e1}")
            # Fallback to PictureID if Name fails
            try:
                image_url = BASE_URL.format(picture_id)
                image = download_image(image_url)
            except Exception as e2:
                print(f"Failed to download image using PictureID {picture_id}: {e2}")
                results.append({
                    "Name": name,
                    "Original Color List": original_color_list,
                    "PredictedColor": "Error"
                })
                continue  # Skip this row if both attempts fail

        # Extract color features
        mean_color = extract_color_features_nw(image)

        # Predict the closest color
        predicted_color = knn.predict([mean_color])[0]
        print(f"Predicted color for {name}: {predicted_color}")

        # Append the result
        results.append({
            "Name": name,
            "Original Color List": original_color_list,
            "PredictedColor": predicted_color
        })

    # Save results to a CSV file
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_csv_path, index=False)
    print(f"Results saved to {output_csv_path}")

def main():
    #print("Training the model...")
    #train_model("items.csv")
    #print("Model training completed.")
    print("Testing the model...")
    test_model("test.csv", "predictions.csv")
    print("Model training and testing completed.")
    return 0

if __name__ == "__main__":
    main()
#FILE TO RUN AND TEST MODEL
import cv2
import os
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split

#number of colors to classify
n = 2

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

#define where data is coming from
data_path = "img/" #folder named img with folders of colors
x = []
y = []

#gather test data from the directory of images
for color_label in os.listdir(data_path):
    folder_path = os.path.join(data_path, color_label)
    if not os.path.isdir(folder_path):  #skip non-foldered files
        continue
    
    for img_file in os.listdir(folder_path):
        img_path = os.path.join(folder_path, img_file)
        center_color = extract_color_features(img_path) #Where to choose what center color method to use
        x.append(center_color)
        y.append(color_label)

x = np.array(x)
y = np.array(y)

#split data into test and validation datasets
X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

knn = KNeighborsClassifier(n_neighbors=n)  #set to train using n neighbors
knn.fit(X_train, y_train) #actually train the model

#saving the model
import joblib

# Save the trained model to a file
joblib.dump(knn, "color_modelv1.pkl")
print("Model saved successfully!")

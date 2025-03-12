import os
import requests
import pandas as pd
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
from urllib.parse import urljoin

#constant vars
CSV_FILE = 'data.csv'
FOLDER_NAME = 'scraped_images'
BASE_URL = 'https://media.rallyhouse.com/homepage/{}-1.jpg?tx=f_auto,c_fit,w_730,h_730'

#create the folder to store scraped images
os.makedirs(FOLDER_NAME, exist_ok=True)

#read csv
dataFile = pd.read_csv(CSV_FILE)

#data validation
ITEM_COL = 'Name'

if ITEM_COL not in dataFile.columns:
    raise ValueError(f"'{ITEM_COL}' column not found in the CSV file.")

#put it all together, iterate over skus in the csv
for Name in dataFile[ITEM_COL]:
    img_url = BASE_URL.format(Name)

    
    try:
        #request image
        response = requests.get(img_url, headers={'User-Agent': 'Mozilla/5.0'}, stream = True)
        response.raise_for_status()  # Raise an error for bad responses

        #open and save image
        image = Image.open(BytesIO(response.content))
        image_path = os.path.join(FOLDER_NAME, f"{Name}.jpg")
        image.save(image_path)

        print(f"Downloaded: {image_path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {Name}: {e}")
print('Download Complete')
    
import os
import requests
import pandas as pd
from PIL import Image
from io import BytesIO
import concurrent.futures
import threading

# Constant variables
TEAM_CODE = "haleyyyyyyy"
CSV_FILE = f'Color Import.csv'
FOLDER_NAME = 'to_tag_images'
BASE_URL = 'https://media.rallyhouse.com/homepage/{}-1.jpg?tx=f_auto,c_fit,w_730,h_730'

#TO ADD TO BUCKET: aws s3 cp "C:\Users\DavidNissly\Desktop\Git\AWS\FOLDER" s3://rh-college-logos/FOLDER/ --recursive

# Create the folder to store scraped images
os.makedirs(FOLDER_NAME, exist_ok=True)

# Read CSV
dataFile = pd.read_csv(CSV_FILE, dtype=str)

# Data validation
ITEM_COL = 'Name'
PICTURE_ID_COL = 'Picture ID'

if ITEM_COL not in dataFile.columns or PICTURE_ID_COL not in dataFile.columns:
    raise ValueError(f"'{ITEM_COL}' or '{PICTURE_ID_COL}' column not found in the CSV file.")

failed_downloads = []
failed_lock = threading.Lock()

# Function to download an image
def download_image(identifier, save_as, internal_id):
    extensions = ['jpg', 'jpeg', 'png']
    for ext in extensions:
        image_path = os.path.join(FOLDER_NAME, f"{save_as}.{ext}")
        # Check if the image already exists
        if os.path.exists(image_path):
            print(f"Skipped: {image_path} (already exists)")
            return True  # Already exists, not a failure

        img_url = BASE_URL.format(identifier).replace('.jpg', f'.{ext}')
        try:
            # Request image
            response = requests.get(img_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True)
            response.raise_for_status()  # Raise an error for bad responses

            # Open and save image
            image = Image.open(BytesIO(response.content))

            if image.mode == "P":
                image = image.convert("RGB")

            image.save(image_path)
            print(f"Downloaded: {image_path}")
            return True  # Indicate success
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {save_as} as .{ext}: {e}")
        except Exception as e:
            print(f"Error processing {save_as} as .{ext}: {e}")

    # If all attempts fail
    with failed_lock:
        failed_downloads.append({'Internal ID': internal_id, 'Name': save_as})
    return False  # Indicate failure

# Iterate over rows in the CSV
def main():
    tasks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for _, row in dataFile.iterrows():
            name = row[ITEM_COL]
            picture_id = row[PICTURE_ID_COL]
            internal_id = picture_id  # Or another column if you have a different internal ID
            if name == picture_id:
                # Download using Name
                tasks.append(executor.submit(download_image, name, name, internal_id))
            else:
                # Download using Picture ID
                tasks.append(executor.submit(download_image, picture_id, name, internal_id))
        # Optionally, wait for all tasks to complete and print summary
        concurrent.futures.wait(tasks)

    # Write failed downloads to CSV
    if failed_downloads:
        failed_df = pd.DataFrame(failed_downloads)
        failed_df.to_csv('failed.csv', index=False)
        print(f"Failed downloads written to failed.csv ({len(failed_downloads)} entries)")
    else:
        print("No failed downloads.")

    print('Download Complete')

if __name__ == "__main__":
    main()

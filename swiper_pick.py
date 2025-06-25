import pygame
import os
import csv
import math
import signal
import sys

# === CONFIG ===
IMAGE_FOLDER = "to_tag_images"
INPUT_CSV = "Color Import.csv"
TEAM_COLORS_CSV = "Colors By Team.csv"
OUTPUT_CSV = "tagged_results.csv"
ALL_COLOR_OPTIONS_CSV = "All Color Options.csv"
TO_CREATE_CSV = "to_create.csv"
BASE_WINDOW_HEIGHT = 700
IMAGE_WIDTH = 511

# === SETUP ===
pygame.init()
pygame.font.init()
font = pygame.font.Font(None, 24)

# Load all products from Color Import.csv
products = []
with open(INPUT_CSV, "r", newline='', encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        products.append(row)

# Load all team color options from Colors By Team.csv
team_color_options = {}
with open(TEAM_COLORS_CSV, "r", newline='', encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        team = row["Team"]
        if team not in team_color_options:
            team_color_options[team] = []
        team_color_options[team].append({
            "Name": row["Name"],
            "Item Name Color": row["Item Name Color"]
        })

# Load all color options for DNE dropdown
all_color_options = []
with open(ALL_COLOR_OPTIONS_CSV, "r", newline='', encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        all_color_options.append(row["Name"])

# === RESUME LOGIC ===
processed_names = set()
already_written_names = set()
tagged_results = []
if os.path.isfile(OUTPUT_CSV):
    with open(OUTPUT_CSV, "r", newline='', encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize keys to match the rest of the code
            pname = row.get("Product Name", row.get("product_name", ""))
            tagged_results.append({
                "product_name": pname,
                "image": row.get("Product Image", row.get("image", "")),
                "team": row.get("Team", row.get("team", "")),
                "selected_name": row.get("Selected Name", row.get("selected_name", "")),
                "selected_item_name_color": row.get("Selected Item Name Color", row.get("selected_item_name_color", ""))
            })
            processed_names.add(pname)
            already_written_names.add(pname)

to_create_rows = []
if os.path.isfile(TO_CREATE_CSV):
    with open(TO_CREATE_CSV, "r", newline='', encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize keys to match the rest of the code
            pname = row.get("Product Name", row.get("product_name", ""))
            to_create_rows.append({
                "product_name": pname,
                "team": row.get("Team", row.get("team", "")),
                "selected_name": row.get("Selected Name", row.get("selected_name", ""))
            })
            processed_names.add(pname)
            already_written_names.add(pname)

# Only process products not already tagged or in to_create
products_to_process = [p for p in products if p["Name"] not in processed_names]
data_index = 0
last_selected_idx = 0  # Add this before the main loop

def get_tag_options_for_team(team):
    # Always add DNE as the first option
    options = [{
        "key": 0,
        "name": "DNE",
        "display_name": "DNE (Not in list)",
        "item_name_color": "DNE"
    }]
    for idx, row in enumerate(team_color_options.get(team, []), start=1):
        options.append({
            "key": idx,
            "name": row["Name"],
            "display_name": row["Name"],  # <-- Changed from Item Name Color to Name
            "item_name_color": row["Item Name Color"]
        })
    return options

def calc_column_widths(tag_options):
    column_widths = []
    max_rows_per_group = 20
    column_height = 40
    for col in range(math.ceil(len(tag_options) / max_rows_per_group)):
        max_width = 0
        for i in range(col * max_rows_per_group, min((col + 1) * max_rows_per_group, len(tag_options))):
            text_width, _ = font.size(f"{i % 10}: {tag_options[i]['display_name']}")
            max_width = max(max_width, text_width)
        column_width = max_width + 45
        column_widths.append(column_width)
    return column_widths, max_rows_per_group, column_height

def show_image_with_options(image_path, tag_options, current_index, total_images):
    screen.fill((255, 255, 255))
    image = pygame.image.load(image_path)
    image = pygame.transform.scale(image, (IMAGE_WIDTH, 512))
    screen.blit(image, (0, 0))
    # Only show product image and progress text
    progress_text = font.render(f"Image {current_index + 1} of {total_images}", True, (0, 0, 0))
    screen.blit(progress_text, (10, 520))
    pygame.display.flip()

def save_results():
    # Append only new results to tagged_results.csv
    file_exists = os.path.isfile(OUTPUT_CSV)
    with open(OUTPUT_CSV, "a", newline='', encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Product Name", "Product Image", "Team", "Selected Name", "Selected Item Name Color"])
        for item in tagged_results:
            if item["product_name"] not in already_written_names:
                writer.writerow([
                    item["product_name"],
                    item["image"],
                    item["team"],
                    item["selected_name"],
                    item["selected_item_name_color"]
                ])
                already_written_names.add(item["product_name"])

    # Append only new results to to_create.csv
    file_exists_create = os.path.isfile(TO_CREATE_CSV)
    with open(TO_CREATE_CSV, "a", newline='', encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists_create:
            writer.writerow(["Product Name", "Team", "Selected Name"])
        for item in to_create_rows:
            if item["product_name"] not in already_written_names:
                writer.writerow([item["product_name"], item["team"], item["selected_name"]])
                already_written_names.add(item["product_name"])

def show_dropdown(screen, options, prompt="Select a color option (Up/Down, Enter):", x=100, y=100, selected=0):
    per_page = 15
    scroll = max(0, selected - per_page + 1)
    font_height = 32
    width = 500
    height = min(len(options), per_page) * font_height + 60
    dropdown_surface = pygame.Surface((width, height))
    dropdown_surface.fill((240, 240, 240))
    running = True

    # Key repeat variables
    up_held = False
    down_held = False
    hold_start_time = 0
    repeat_delay = 300  # ms before repeat starts
    repeat_interval = 50  # ms between repeats

    clock = pygame.time.Clock()

    while running:
        dropdown_surface.fill((240, 240, 240))
        prompt_text = font.render(prompt, True, (0, 0, 0))
        dropdown_surface.blit(prompt_text, (10, 10))
        start = scroll
        end = min(scroll + per_page, len(options))
        for i, option in enumerate(options[start:end]):
            color = (0, 0, 0)
            bg = (200, 200, 255) if (start + i) == selected else (240, 240, 240)
            pygame.draw.rect(dropdown_surface, bg, (0, 40 + i * font_height, width, font_height))
            text = font.render(option, True, color)
            dropdown_surface.blit(text, (10, 40 + i * font_height))
        screen.blit(dropdown_surface, (x, y))
        pygame.display.flip()

        dt = clock.tick(60)
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                handle_exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    if selected < len(options) - 1:
                        selected += 1
                        if selected >= scroll + per_page:
                            scroll += 1
                    down_held = True
                    hold_start_time = now
                elif event.key == pygame.K_UP:
                    if selected > 0:
                        selected -= 1
                        if selected < scroll:
                            scroll -= 1
                    up_held = True
                    hold_start_time = now
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    return options[selected], selected
                elif event.key == pygame.K_ESCAPE:
                    return None, selected
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    down_held = False
                elif event.key == pygame.K_UP:
                    up_held = False

        # Handle key repeat for up/down
        if down_held:
            if now - hold_start_time > repeat_delay:
                if (now - hold_start_time) % repeat_interval < dt:
                    if selected < len(options) - 1:
                        selected += 1
                        if selected >= scroll + per_page:
                            scroll += 1
        if up_held:
            if now - hold_start_time > repeat_delay:
                if (now - hold_start_time) % repeat_interval < dt:
                    if selected > 0:
                        selected -= 1
                        if selected < scroll:
                            scroll -= 1

def save_to_create(row):
    # Only add to in-memory list if not already present
    if row["product_name"] not in [item["product_name"] for item in to_create_rows]:
        to_create_rows.append(row)

def handle_exit(*args):
    save_results()
    pygame.quit()
    sys.exit()  # <-- Change exit() to sys.exit()

# Register signal handler for graceful exit
signal.signal(signal.SIGINT, handle_exit)

# === MAIN LOOP ===
while data_index < len(products_to_process):
    current_product = products_to_process[data_index]
    image_path = os.path.join(IMAGE_FOLDER, current_product["Image"])
    team = current_product["Team"]

    if not os.path.isfile(image_path):
        print(f"Image not found: {image_path}. Skipping product {current_product['Name']}.")
        data_index += 1
        continue

    tag_options = get_tag_options_for_team(team)
    if not tag_options:
        print(f"No color options for team: {team}")
        data_index += 1
        continue

    # Find the index of the current product in the original products list
    original_index = next((i for i, p in enumerate(products) if p["Name"] == current_product["Name"]), data_index)

    window_width = IMAGE_WIDTH + 520  # 500 for dropdown + margin
    window_height = max(BASE_WINDOW_HEIGHT, 800)
    WINDOW_SIZE = (window_width, window_height)
    screen = pygame.display.set_mode(WINDOW_SIZE)
    show_image_with_options(image_path, tag_options, original_index, len(products))

    # Prepare dropdown options
    dropdown_options = [opt["display_name"] for opt in tag_options]
    # Ensure last_selected_idx is in range
    if last_selected_idx >= len(dropdown_options):
        last_selected_idx = 0
    selected_display, last_selected_idx = show_dropdown(
        screen, dropdown_options, prompt="Select a color option (Up/Down, Enter):", x=IMAGE_WIDTH + 10, y=10, selected=last_selected_idx
    )
    if selected_display is None:
        continue

    # Map back to the selected tag_option
    selected_idx = dropdown_options.index(selected_display)
    selected_option = tag_options[selected_idx]
    last_selected_idx = selected_idx  # Update for next item

    if selected_option["name"] == "DNE":
        # For DNE, reset to 0 for the DNE dropdown
        selected_color, _ = show_dropdown(
            screen, all_color_options, prompt="Select DNE color (Up/Down, Enter):", x=IMAGE_WIDTH + 10, y=10, selected=0
        )
        if selected_color:
            save_to_create({
                "product_name": current_product["Name"],
                "team": team,
                "selected_name": selected_color
            })
            data_index += 1
    else:
        # Save all info as before
        tagged_results.append({
            "product_name": current_product["Name"],
            "image": current_product["Image"],
            "team": team,
            "selected_name": selected_option["name"],
            "selected_item_name_color": selected_option["item_name_color"]
        })
        data_index += 1

# On normal exit
save_results()
pygame.quit()
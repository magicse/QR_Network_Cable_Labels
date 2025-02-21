import chardet
from io import BytesIO
import csv
import os
import pyqrcode
from PIL import Image, ImageDraw, ImageFont

def detect_file_encoding(csv_filename):
    """
    Detect the encoding of a file using chardet.
    
    Args:
        csv_filename (str): The path to the CSV file.
    
    Returns:
        str: The detected encoding.
    """
    with open(csv_filename, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding']

def generate_qr_code_label(data_qr, data_lab):
    """
    Generate a QR code and create the label image without saving intermediate images to disk.
    
    Args:
        data_qr (str): The data to encode in the QR code.
        data_lab (str): The data to display as a label.
    
    Returns:
        Image: The generated label image.
    """
    version = 8
    scale = 4
    quiet_zone = 5
    font_size = 29 # will be calced later
    font = ImageFont.truetype("arial.ttf", font_size)
    Shift = 40
   
    # Create a QR code with UTF-8 encoding
    qr = pyqrcode.create(data_qr, encoding='utf-8', version=version)

    # Generate the QR code as PNG and save to a BytesIO object
    qr_png = BytesIO()
    qr.png(qr_png, scale=scale, quiet_zone = quiet_zone)
    qr_png.seek(0)  # Reset the pointer to the beginning of the file-like object

    # Convert the PNG from BytesIO to a PIL Image
    qr_img = Image.open(qr_png)
    qr_img_width, qr_img_height = qr_img.size

    # Create a new image with a larger width
    new_img_width = qr_img_width * 5
    new_img_height = qr_img_height
    new_img = Image.new('RGB', (new_img_width, new_img_height), color=(255, 255, 255))    

    # Add the QR code to the new image
    new_img.paste(qr_img, (0, (new_img_height - qr_img_height) // 2))

    # Create a drawing context
    draw = ImageDraw.Draw(new_img)

    # Function to draw rounded rectangles (borders)
    def draw_rounded_rectangle(draw, xy, radius, color, width=1):
        x1, y1, x2, y2 = xy
        draw.line([(x1 + radius, y1), (x2 - radius, y1)], fill=color, width=width)
        draw.line([(x1 + radius, y2), (x2 - radius, y2)], fill=color, width=width)
        draw.line([(x1, y1 + radius), (x1, y2 - radius)], fill=color, width=width)
        draw.line([(x2, y1 + radius), (x2, y2 - radius)], fill=color, width=width)
        draw.arc([x1, y1, x1 + 2 * radius, y1 + 2 * radius], start=180, end=270, fill=color, width=width)
        draw.arc([x2 - 2 * radius, y1, x2, y1 + 2 * radius], start=270, end=360, fill=color, width=width)
        draw.arc([x1, y2 - 2 * radius, x1 + 2 * radius, y2], start=90, end=180, fill=color, width=width)
        draw.arc([x2 - 2 * radius, y2 - 2 * radius, x2, y2], start=0, end=90, fill=color, width=width)

    # Split the data into lines
    lines = data_lab.split("\n")

    # Calculate line height
    line_height = draw.textbbox((0, 0), "Ay", font=font)[3]  # Use textbbox to get height
    
    # Calculate total text height and maximum text width
    total_text_height = len(lines) * line_height
    total_text_width = max(draw.textbbox((0, 0), line, font=font)[2] for line in lines)    

    # Define maximum allowed dimensions
    max_width = new_img_width - (qr_img_width + scale * quiet_zone ) - Shift
    max_height = new_img_height - 20 

    # Calculate scale factor to fit text within the rectangle
    scale_factor = min(max_width / total_text_width, max_height / total_text_height)

    # If scaling is needed, adjust font size
    if scale_factor != 1:
        adjusted_font_size = int(font_size * scale_factor)
        font = ImageFont.truetype("arial.ttf", adjusted_font_size)
        line_height = draw.textbbox((0, 0), "Ay", font=font)[3]  # Use textbbox to get height

    
    # Draw each line of text
    for i, line in enumerate(lines):
        draw.text((qr_img_width, 10 + i * line_height), line, font = font, fill=(0, 0, 0))

    # Add a rounded border
    border_padding = 1
    draw_rounded_rectangle(draw, (0, 0, new_img_width - 1, new_img_height - 1), 20, (0, 0, 0), width=border_padding)

    return new_img

def draw_dotted_lines(draw, start_x, start_y, end_x, end_y, dash_length=5, gap_length=10):
    """
    Draw dotted lines between two points.

    Args:
        draw (ImageDraw): The drawing context.
        start_x (int): The starting x-coordinate.
        start_y (int): The starting y-coordinate.
        end_x (int): The ending x-coordinate.
        end_y (int): The ending y-coordinate.
        dash_length (int): The length of each dash.
        gap_length (int): The length of the gap between dashes.
    """
    total_length = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
    dashes = int(total_length // (dash_length + gap_length))
    
    for i in range(dashes):
        start = i * (dash_length + gap_length)
        end = start + dash_length
        x = start_x + (end_x - start_x) * (start / total_length)
        y = start_y + (end_y - start_y) * (start / total_length)
        x_end = start_x + (end_x - start_x) * (end / total_length)
        y_end = start_y + (end_y - start_y) * (end / total_length)
        draw.line([(x, y), (x_end, y_end)], fill=(0, 0, 0), width=1)

def place_labels_on_a4_sheet(labels, output_filename):
    """
    Place labels on an A4 sheet.

    Args:
        labels (list): A list of label images.
        output_filename (str): The filename to save the A4 sheet to.
    """
    # A4 sheet dimensions in pixels
    a4_width = 2480
    a4_height = 3508

    # Create a new image for the A4 sheet
    a4_sheet = Image.new('RGB', (a4_width, a4_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(a4_sheet)

    # Open the first label image to get its dimensions
    label_img = labels[0]
    label_width, label_height = label_img.size

    # Calculate the number of rows and columns for the labels
    num_cols = 2
    num_rows = 12
    
    # Calculate the spacing between labels
    cell_width = a4_width // num_cols
    label_spacing_x = (cell_width - label_width) // 2
    label_spacing_y = (a4_height - (num_rows * label_height)) // (num_rows + 1)
    
    sheet_index = 1

    # Place the labels on the A4 sheet
    for label_index, label_img in enumerate(labels):
        # Calculate the position of the label
        row = (label_index // num_cols) % num_rows
        col = label_index % num_cols
        x = label_spacing_x + (col * (label_width + label_spacing_x * 2))
        y = label_spacing_y + (row * (label_height + label_spacing_y))

        # Create a new A4 sheet if necessary
        if label_index % (num_cols * num_rows) == 0 and label_index != 0:
            for i in range(0, num_rows + 1):
                y_line = label_spacing_y + (i * (label_height + label_spacing_y)) - label_spacing_y // 2
                draw_dotted_lines(draw, 0, y_line, a4_width, y_line)
            for i in range(1, num_cols):
                x_line = label_spacing_x + (i * (label_width + label_spacing_x * 2)) - label_spacing_x 
                draw_dotted_lines(draw, x_line, 0, x_line, a4_height)

            a4_sheet.save(f'{output_filename}_{sheet_index}.png')
            sheet_index += 1
            a4_sheet = Image.new('RGB', (a4_width, a4_height), color=(255, 255, 255))
            draw = ImageDraw.Draw(a4_sheet)

        a4_sheet.paste(label_img, (x, y))

    # Draw the final dotted lines
    for i in range(0, num_rows + 1):
        y_line = label_spacing_y + (i * (label_height + label_spacing_y)) - label_spacing_y // 2
        draw_dotted_lines(draw, 0, y_line, a4_width, y_line)
    for i in range(1, num_cols):
        x_line = label_spacing_x + (i * (label_width + label_spacing_x * 2)) - label_spacing_x
        draw_dotted_lines(draw, x_line, 0, x_line, a4_height)

    a4_sheet.save(f'{output_filename}_{sheet_index}.png')

def process_csv_file(csv_filename, output_dir):
    """
    Process a CSV file and generate labels.

    Args:
        csv_filename (str): The filename of the CSV file.
        output_dir (str): The directory to save the generated labels.
    """
    labels = []
    
    # Detect the encoding of the file dynamically
    encoding = detect_file_encoding(csv_filename)
    print(f"Detected encoding: {encoding}")
    
    with open(csv_filename, 'r', encoding=encoding) as csv_file:
        reader = csv.DictReader(csv_file, delimiter=';', quotechar='|')
        
        # Read all rows into a list
        rows = list(reader)

        # Sort the rows first by 'Division' and then by 'Name'
        sorted_rows = sorted(rows, key=lambda row: (row['Division'], row['City'], row['Name']))
        
        for row in sorted_rows:
            # Extract the data from the CSV row
            name = row['Name']
            id = row['ID']
            ip = row['IP']
            pidr = row['Division'] # Підрозділ
            misto = row['City'] # Населений пункт
            print(name,id,ip)

            # Create the data for the QR code and label
            data_qr = f"Name: {name}\r\nIP: {ip}"
            #data_qr = f"NAME: {name}\nIP: {ip}\nID: {id}"
            data_lab = f"{pidr}\nName: {name}\nID: {id}"

            # Generate the label image
            label_img = generate_qr_code_label(data_qr, data_lab)

            # Add the label image to the list of labels
            labels.append(label_img)

    # Place the labels on an A4 sheet only if there are labels
    if labels:
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, "labels_a4_sheet.png")
        place_labels_on_a4_sheet(labels, output_filename)
    else:
        print("No records found.")

csv_filename = 'test.csv'
output_dir = 'labels'
process_csv_file(csv_filename, output_dir)

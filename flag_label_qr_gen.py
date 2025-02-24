import chardet
from io import BytesIO
import csv
import os
import pyqrcode
from PIL import Image, ImageDraw, ImageFont, ImageColor

# Define conversion factor (1 mm = 11.81 pixels at 300 DPI)
PPI = 300
#inch = 25.4 mm
#MM_TO_PIXELS = 11.81
MM_TO_PIXELS = PPI / 25.4

font_type = "arial.ttf"
font_type = "consolab.ttf"

# Define label dimensions in mm
LABEL_WIDTH = 57 #37
TOTAL_LABEL_WIDTH = 104 #84 
LABEL_HEIGHT = 13
TOTAL_LABEL_HEIGHT = LABEL_HEIGHT * 2
 
TAIL_WIDTH = 10
TAIL_SHIFT = 2
LINE_WIDTH = 1

LABEL_COLOR = 'yellow'
LABEL_COLOR = (255,255,186)

CORNER_RADIUS = 0.5 * MM_TO_PIXELS  # Adjust corner roundness
TOTAL_LABEL_WIDTH_PX = TOTAL_LABEL_WIDTH * MM_TO_PIXELS
TOTAL_LABEL_HEIGHT_PX = TOTAL_LABEL_HEIGHT * MM_TO_PIXELS

def convert_color(color):
    if isinstance(color, str):
        return ImageColor.getrgb(color)  # Convert color name to RGB tuple
    return color  # If already an RGB tuple, return as is

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


def create_arc_points(x, y, radius, start_angle, end_angle, segments=16):
    """Create points for an arc using multiple line segments"""
    from math import sin, cos, pi
    
    points = []
    for i in range(segments + 1):
        angle = start_angle + (end_angle - start_angle) * i / segments
        angle_rad = angle * pi / 180
        points.append((
            x + radius * cos(angle_rad),
            y + radius * sin(angle_rad)
        ))
    return points

def draw_label(data_lab_a, data_lab_b, data_qr_a = '', data_qr_b = ''):
    # Create a blank white image
    img = Image.new("RGBA", (int(TOTAL_LABEL_WIDTH_PX), int(TOTAL_LABEL_HEIGHT_PX)), "white")
    draw = ImageDraw.Draw(img)
    
    # Convert measurements to pixels
    w = TOTAL_LABEL_WIDTH_PX - 1 
    #print(w)
    h = TOTAL_LABEL_HEIGHT_PX -1
    #print(h)
    split_x = LABEL_WIDTH * MM_TO_PIXELS
    split_y1 = TAIL_SHIFT * MM_TO_PIXELS
    split_y2 = (TAIL_SHIFT + TAIL_WIDTH) * MM_TO_PIXELS
    r = CORNER_RADIUS
    
    # Create the complete path points
    path_points = []
    
    # Start from top-left corner
    path_points.extend(create_arc_points(r, r, r, 180, 270))  # Top-left corner
    path_points.append((split_x, 0))  # Top edge
    path_points.append((split_x, split_y1))  # Right edge of first section
    path_points.append((w - r, split_y1))  # Top edge of middle section
    path_points.extend(create_arc_points(w - r, split_y1 + r, r, 270, 360))  # Top-right corner
    path_points.append((w, split_y2 - r))  # Right edge
    path_points.extend(create_arc_points(w - r, split_y2 - r, r, 0, 90))  # Bottom-right corner
    path_points.append((split_x, split_y2))  # Bottom edge of middle section
    path_points.append((split_x , h))  # Right edge of bottom section
    path_points.append((r, h))  # Bottom edge
    path_points.extend(create_arc_points(r, h - r, r, 90, 180))  # Bottom-left corner
    path_points.append((0, r))  # Left edge
    
    # Draw the filled shape
    draw.polygon(path_points, fill = LABEL_COLOR, outline="black", width = LINE_WIDTH)
    
    # Draw dashed line
    x1, y1 = 0, LABEL_HEIGHT * MM_TO_PIXELS
    x2, y2 = LABEL_WIDTH * MM_TO_PIXELS, LABEL_HEIGHT * MM_TO_PIXELS
    dash_length = 3
    gap_length = 3
    current_x = x1
    while current_x < x2:
        next_x = min(current_x + dash_length, x2)
        draw.line([(current_x, y1), (next_x, y2)], fill="black", width=1)
        current_x += dash_length + gap_length

    # QR Generation
    #Low (L): Recovers 7% of data. Medium (M): Recovers 15% of data. Quartile (Q): Recovers 25% of data. High (H): Recovers 30% of data.
    version = 8
    scale = 2
    quiet_zone = 4
    qr_background = convert_color(LABEL_COLOR)
    # Create a QR code with UTF-8 encoding
    qr_a = pyqrcode.create(data_qr_a, encoding='utf-8', version=version, error='M')
    qr_b = pyqrcode.create(data_qr_b, encoding='utf-8', version=version, error='M')
    # Generate the QR code as PNG and save to a BytesIO object
    qr_png_a = BytesIO()
    qr_png_b = BytesIO()
    qr_a.png(qr_png_a, scale=scale, quiet_zone = quiet_zone, background = qr_background)
    qr_b.png(qr_png_b, scale=scale, quiet_zone = quiet_zone, background = qr_background)
    qr_png_a.seek(0)  # Reset the pointer to the beginning of the file-like object
    qr_png_b.seek(0)  # Reset the pointer to the beginning of the file-like object    
    # Convert the PNG from BytesIO to a PIL Image
    qr_img_a = Image.open(qr_png_a)
    qr_img_b = Image.open(qr_png_b)
    qr_img_width, qr_img_height = qr_img_a.size
    
    # Add the QR code to the new image
    img.paste(qr_img_a, (round(1 * MM_TO_PIXELS), round(1 * MM_TO_PIXELS)))  

    
    font_type = "arial.ttf"
    font_type = "consolab.ttf"
    # Split both sets of data into lines
    a_lines = data_lab_a.split("\n")
    b_lines = data_lab_b.split("\n")
    # Combine both sets of lines
    all_lines = a_lines + b_lines
    
    font_size = 29
    font = ImageFont.truetype(font_type, font_size)
    # Calculate line height
    line_height = draw.textbbox((0, 0), "Ay", font = font)[3]  # Use textbbox to get height
    # Calculate total text height and maximum text width
    total_text_height = max(len(a_lines) * line_height, len(b_lines) * line_height)
    total_text_width = max(draw.textbbox((0, 0), line, font=font)[2] for line in all_lines)
    # Define maximum allowed dimensions
    max_width = LABEL_WIDTH * MM_TO_PIXELS - 4 * MM_TO_PIXELS - qr_img_width
    max_height = LABEL_HEIGHT * MM_TO_PIXELS - 2 * MM_TO_PIXELS
    # Calculate scale factor to fit text within the rectangle
    scale_factor = min(max_width / total_text_width, max_height / total_text_height)    
    # If scaling is needed, adjust font size
    if scale_factor != 1:
        adjusted_font_size = int(font_size * scale_factor)
        font = ImageFont.truetype(font_type, adjusted_font_size)
        #line_height = draw.textsize("Ay", font=font)[1]  # Recalculate line height
        line_height = draw.textbbox((0, 0), "Ay", font=font)[3]  # Use textbbox to get height

    # Draw each line of text
    for i, line in enumerate(a_lines):
        draw.text((2 * MM_TO_PIXELS + qr_img_width, 1 * MM_TO_PIXELS + i * line_height), line, font=font, fill=(0, 0, 0))

    # Create a separate image for the flipped text
    flipped_img = Image.new("RGBA", (round(max_width + qr_img_width + 2 * MM_TO_PIXELS), round(max_height)), (255, 255, 255, 0))
    flipped_draw = ImageDraw.Draw(flipped_img)

    # Add the QR code to the new image
    flipped_img.paste(qr_img_b, (0, 0)) 

    # Draw text on the separate image
    for i, line in enumerate(b_lines):
        flipped_draw.text((1 * MM_TO_PIXELS + qr_img_width, i * line_height), line, font=font, fill=(0, 0, 0))

    # Rotate the image 180 degrees
    flipped_img = flipped_img.rotate(180, expand=True)

    # Paste the rotated text onto the main label
    img.paste(flipped_img, (round(1 * MM_TO_PIXELS), round((LABEL_HEIGHT + 1) * MM_TO_PIXELS)), flipped_img) 


    # Draw each line of text
    #for i, line in enumerate(b_lines):
    #    draw.text((2 * MM_TO_PIXELS, (LABEL_HEIGHT + 1) * MM_TO_PIXELS + i * line_height), line, font=font, fill=(0, 0, 0))
    
    return img


def draw_dotted_lines(draw, start_x, start_y, end_x, end_y, dash_length=5, gap_length=5):
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
    #a4_width = 2480
    #a4_height = 3508

    a4_width = round(210 * MM_TO_PIXELS)
    a4_height = round(297 * MM_TO_PIXELS)
    

    # Create a new image for the A4 sheet
    a4_sheet = Image.new('RGB', (a4_width, a4_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(a4_sheet)

    # Open the first label image to get its dimensions
    label_img = labels[0]
    label_width, label_height = label_img.size

    # Calculate the number of rows and columns for the labels
    num_cols = 2
    num_rows = 11
    
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

    a4_sheet.save(f'{output_filename}_{sheet_index}.png', dpi=(PPI, PPI))

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
        sorted_rows = sorted(rows, key=lambda row: (row['SrcPort']))
        
        for row in sorted_rows:
            # Extract the data from the CSV row
            sport = row['SrcPort']
            sname = row['SrcName']
            tname = row['TrgName']
            tport = row['TrgPort']
            sip = row['SrcIP']
            tip = row['TrgIP']
            print(sip, sport,tname,tip,tport)

            # Create the data for the QR code and label
            data_qr_a = f"{sname}\nIP: {sip}\nPort: {sport}"
            data_lab_a = f"-=Source=-\n{sname}\nIP: {sip}\nPORT: {sport}"
            data_qr_b = f"{tname}\nIP: {tip}\nPort: {tport}"
            data_lab_b = f"-=Destination=-\n{tname}\nIP: {tip}\nPORT: {tport}"

            # Generate the label image
            #label_img = generate_qr_code_label(data_qr_left, data_qr_right, data_lab_left, data_lab_right)
            label_img = draw_label(data_lab_a, data_lab_b, data_qr_a, data_qr_b)
            

            # Add the label image to the list of labels
            labels.append(label_img)

    # Place the labels on an A4 sheet only if there are labels
    if labels:
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, "labels_a4_sheet")
        place_labels_on_a4_sheet(labels, output_filename)
    else:
        print("No records found.")

# Example usage
csv_filename = 'temp2.csv'
output_dir = 'labels'
process_csv_file(csv_filename, output_dir)    

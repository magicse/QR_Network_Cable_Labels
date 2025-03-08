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
PIXELS_TO_MM = 25.4 / PPI

BACK_COLOR = (230,230,230)
LABEL_COLOR = 'yellow'
#LABEL_COLOR = 'white'
LABEL_WIDTH = 51
LABEL_HEIGHT = 17
LINE_WIDTH = 1
# If 0 the middle part will be 2mm, if 2 then middle part will be 6mm 
MIDDLE_PART_WIDTH = 4
# A4 Left Right side mergin. 
SIDE_MERGIN = 4 # mm


TOTAL_LABEL_WIDTH = LABEL_WIDTH * 2
TOTAL_LABEL_HEIGHT = LABEL_HEIGHT

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

def draw_rounded_rectangle_color(draw, xy, radius, fill_color, stroke_color, width=1):
    # Extract coordinates from the xy tuple
    x1, y1, x2, y2 = xy
    
    # Draw the filled rounded rectangle
    # Draw the main body of the rectangle with the fill color
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill_color)  # Fill the central part
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill_color)  # Fill the sides

    # Draw the rounded corners with the fill color
    draw.pieslice([x1, y1, x1 + 2 * radius, y1 + 2 * radius], start=180, end=270, fill=fill_color)
    draw.pieslice([x2 - 2 * radius, y1, x2, y1 + 2 * radius], start=270, end=360, fill=fill_color)
    draw.pieslice([x1, y2 - 2 * radius, x1 + 2 * radius, y2], start=90, end=180, fill=fill_color)
    draw.pieslice([x2 - 2 * radius, y2 - 2 * radius, x2, y2], start=0, end=90, fill=fill_color)
    
    # Now draw the stroke (outline) over the filled area
    draw.line([(x1 + radius, y1), (x2 - radius, y1)], fill=stroke_color, width=width)
    draw.line([(x1 + radius, y2), (x2 - radius, y2)], fill=stroke_color, width=width)
    draw.line([(x1, y1 + radius), (x1, y2 - radius)], fill=stroke_color, width=width)
    draw.line([(x2, y1 + radius), (x2, y2 - radius)], fill=stroke_color, width=width)
    draw.arc([x1, y1, x1 + 2 * radius, y1 + 2 * radius], start=180, end=270, fill=stroke_color, width=width)
    draw.arc([x2 - 2 * radius, y1, x2, y1 + 2 * radius], start=270, end=360, fill=stroke_color, width=width)
    draw.arc([x1, y2 - 2 * radius, x1 + 2 * radius, y2], start=90, end=180, fill=stroke_color, width=width)
    draw.arc([x2 - 2 * radius, y2 - 2 * radius, x2, y2], start=0, end=90, fill=stroke_color, width=width)

def draw_rounded_rectangle(draw, xy, radius, color, width=1):
    # Convert each element of xy to mm
    x1, y1, x2, y2 = xy
    draw.line([(x1 + radius, y1), (x2 - radius, y1)], fill=color, width=width)
    draw.line([(x1 + radius, y2), (x2 - radius, y2)], fill=color, width=width)
    draw.line([(x1, y1 + radius), (x1, y2 - radius)], fill=color, width=width)
    draw.line([(x2, y1 + radius), (x2, y2 - radius)], fill=color, width=width)
    draw.arc([x1, y1, x1 + 2 * radius, y1 + 2 * radius], start=180, end=270, fill=color, width=width)
    draw.arc([x2 - 2 * radius, y1, x2, y1 + 2 * radius], start=270, end=360, fill=color, width=width)
    draw.arc([x1, y2 - 2 * radius, x1 + 2 * radius, y2], start=90, end=180, fill=color, width=width)
    draw.arc([x2 - 2 * radius, y2 - 2 * radius, x2, y2], start=0, end=90, fill=color, width=width)


def generate_qr_code_label(data_qr_left, data_qr_right, data_lab_left, data_lab_right):
    """
    Generate a QR code and create the label image without saving intermediate images to disk.
    
    Args:
        data_qr (str): The data to encode in the QR code.
        data_lab (str): The data to display as a label.
    
    Returns:
        Image: The generated label image.
    """
    
    # Calculate the font size based on the image height
    font_size = 29
    font_type = "arial.ttf"
    font_type = "consolab.ttf"
    font = ImageFont.truetype(font_type, font_size)    
    
    #Low (L): Recovers 7% of data. Medium (M): Recovers 15% of data. Quartile (Q): Recovers 25% of data. High (H): Recovers 30% of data.
    version = 8
    scale = 3
    quiet_zone = 5
    Shift = round(1 * MM_TO_PIXELS)
    lb_fill_color = convert_color(LABEL_COLOR)
    
    # Create a QR code with UTF-8 encoding
    qr_left = pyqrcode.create(data_qr_left, encoding='utf-8', version=version, error='M')
    qr_right = pyqrcode.create(data_qr_right, encoding='utf-8', version=version, error='M')
    

    # Generate the QR code as PNG and save to a BytesIO object
    qr_png_left = BytesIO()
    qr_png_right = BytesIO()
    qr_left.png(qr_png_left, scale=scale, quiet_zone=quiet_zone, background = lb_fill_color)
    qr_right.png(qr_png_right, scale=scale, quiet_zone=quiet_zone, background = lb_fill_color)
    qr_png_left.seek(0)  # Reset the pointer to the beginning of the file-like object
    qr_png_right.seek(0)  # Reset the pointer to the beginning of the file-like object

    # Convert the PNG from BytesIO to a PIL Image
    qr_img_a = Image.open(qr_png_left)
    qr_img_b = Image.open(qr_png_right)

    qr_img_width, qr_img_height = qr_img_a.size


    # Create a blank white image
    img_base = Image.new("RGBA", (int(TOTAL_LABEL_WIDTH_PX), int(TOTAL_LABEL_HEIGHT_PX)), BACK_COLOR)
    draw_base = ImageDraw.Draw(img_base)   
    
    new_img_width = round((LABEL_WIDTH - 2 - MIDDLE_PART_WIDTH) * MM_TO_PIXELS)
    new_img_height = round(LABEL_HEIGHT * MM_TO_PIXELS) - 1

    a_img = Image.new('RGBA', (new_img_width, new_img_height), color = BACK_COLOR)
    b_img = Image.new('RGBA', (new_img_width, new_img_height), color = BACK_COLOR)    

    # Create a drawing context
    a_draw = ImageDraw.Draw(a_img)
    b_draw = ImageDraw.Draw(b_img)

   

    # Split both sets of data into lines
    lines_a = data_lab_left.split("\n")
    lines_b = data_lab_right.split("\n")

    # Combine both sets of lines
    all_lines = lines_a + lines_b

    # Split the data into lines
    lines = data_lab_left.split("\n")
  
    # Calculate line height
    line_height = a_draw.textbbox((0, 0), "Ay", font=font)[3]  # Use textbbox to get height
    
    # Calculate total text height and maximum text width
    total_text_height = len(lines) * line_height
    total_text_width = max(a_draw.textbbox((0, 0), line, font=font)[2] for line in all_lines)
    
    # Define maximum allowed dimensions
    max_width = new_img_width  - (qr_img_width + 2 * MM_TO_PIXELS + Shift)
    max_height = new_img_height - 2 * MM_TO_PIXELS    
    
    
    # Calculate scale factor to fit text within the rectangle
    scale_factor = min(max_width / total_text_width, max_height / total_text_height)

    # If scaling is needed, adjust font size
    if scale_factor != 1:
        adjusted_font_size = int(font_size * scale_factor)
        font = ImageFont.truetype(font_type, adjusted_font_size)
        line_height = a_draw.textbbox((0, 0), "Ay", font=font)[3]  # Use textbbox to get height

    draw_rounded_rectangle_color(a_draw, (0, 0, new_img_width - 1, new_img_height - 1), 20, lb_fill_color, (0, 0, 0) ,width = LINE_WIDTH)
    draw_rounded_rectangle_color(b_draw, (0, 0, new_img_width - 1, new_img_height - 1), 20, lb_fill_color, (0, 0, 0) ,width = LINE_WIDTH)
    

    # Add the QR code to the new image
    a_img.paste(qr_img_a, (Shift, Shift))
    b_img.paste(qr_img_b, (Shift, Shift))

    # Draw each line of text
    for i, line in enumerate(lines_a):
        a_draw.text((qr_img_width + Shift, i * line_height + 1 * MM_TO_PIXELS), line, font=font, fill=(0, 0, 0))

    # Draw each line of text
    for i, line in enumerate(lines_b):
        b_draw.text((qr_img_width + Shift, i * line_height + 1 * MM_TO_PIXELS), line, font=font, fill=(0, 0, 0))

    img_base.paste(a_img, (round(1 * MM_TO_PIXELS), 0))
    img_base.paste(b_img, (round((LABEL_WIDTH + 1 + MIDDLE_PART_WIDTH) * MM_TO_PIXELS), 0))   

    # Add a rounded border
    border_padding = 1
    draw_base.line([(TOTAL_LABEL_WIDTH_PX/2, 0), (TOTAL_LABEL_WIDTH_PX/2, new_img_height)], fill=(0, 0, 0), width = LINE_WIDTH)
    return img_base

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
    
    # margin from left right edge
    side_mergin_px = SIDE_MERGIN * MM_TO_PIXELS
    
    # Create a new image for the A4 sheet
    a4_sheet = Image.new('RGB', (a4_width, a4_height), color = BACK_COLOR)
    draw = ImageDraw.Draw(a4_sheet)

    # Open the first label image to get its dimensions
    label_img = labels[0]
    label_width, label_height = label_img.size

    # Calculate the number of rows and columns for the labels
    num_cols = 2
    num_rows = 15 # 12
    
    # Calculate the spacing between labels
    cell_width = round((a4_width - side_mergin_px) // num_cols)
    label_spacing_x = (cell_width - label_width) // 2
    label_spacing_y = (a4_height - (num_rows * label_height)) // (num_rows + 1)
    
    sheet_index = 1

    # Place the labels on the A4 sheet
    for label_index, label_img in enumerate(labels):
        # Calculate the position of the label
        row = (label_index // num_cols) % num_rows
        col = label_index % num_cols
        x = round(side_mergin_px // 2 + label_spacing_x + (col * (label_width + label_spacing_x * 2)))
        y = label_spacing_y + (row * (label_height + label_spacing_y))

        # Create a new A4 sheet if necessary
        if label_index % (num_cols * num_rows) == 0 and label_index != 0:
            for i in range(0, num_rows + 1):
                y_line = label_spacing_y + (i * (label_height + label_spacing_y)) - label_spacing_y // 2
                draw_dotted_lines(draw, 0, y_line, a4_width, y_line)
            for i in range(1, num_cols):
                x_line = side_mergin_px // 2 + label_spacing_x + (i * (label_width + label_spacing_x * 2)) - label_spacing_x 
                draw_dotted_lines(draw, x_line, 0, x_line, a4_height)

            a4_sheet.save(f'{output_filename}_{sheet_index}.png')
            sheet_index += 1
            a4_sheet = Image.new('RGB', (a4_width, a4_height), color = BACK_COLOR)
            draw = ImageDraw.Draw(a4_sheet)

        a4_sheet.paste(label_img, (x, y))

    # Draw the final dotted lines
    for i in range(0, num_rows + 1):
        y_line = label_spacing_y + (i * (label_height + label_spacing_y)) - label_spacing_y // 2
        draw_dotted_lines(draw, 0, y_line, a4_width, y_line)
    for i in range(0, num_cols + 1):
        x_line = side_mergin_px // 2 + label_spacing_x + (i * (label_width + label_spacing_x * 2)) - label_spacing_x
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
        sorted_rows = sorted(rows, key=lambda row: (row['SrcPort']))
        
        #for row in sorted_rows:
        for row in rows:
            # Extract the data from the CSV row
            sport = row['SrcPort']
            sname = row['SrcName']
            tname = row['TrgName']
            tport = row['TrgPort']
            sip = row['SrcIP']
            tip = row['TrgIP']
            
            # Check if 'SrcODF' and 'TrgODF' columns exist
            src_odf = row.get('SrcODF', '')  # Get value or empty string if not present
            trg_odf = row.get('TrgODF', '')  # Get value or empty string if not present
            
            print(sip, sport,tname,tip,tport)

            # Create the data for the QR code and label
            data_qr_left = f"{sname}\r\nIp: {sip}\r\nPort: {sport}"
            data_lab_left = f"-=Source=-\n{sname}\nIp: {sip}\nPort: {sport}"
            data_qr_right = f"{tname}\r\nIp: {tip}\r\nPort: {tport}"
            data_lab_right = f"-=Destination=-\n{tname}\nIp: {tip}\nPort: {tport}"

            # Modify labels if SrcODF and TrgODF are present and non-empty
            if src_odf != '':
                data_lab_left += f"\nODF: {src_odf}"
            
            if trg_odf != '':
                data_lab_right += f"\nODF: {trg_odf}"

            # Generate the label image
            label_img = generate_qr_code_label(data_qr_left, data_qr_right, data_lab_left, data_lab_right)

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
csv_filename = 'temp.csv'

output_dir = 'cable_labels'
process_csv_file(csv_filename, output_dir)

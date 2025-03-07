# Label Generator for Network Devices and Cables.

## Overview
This Python scripts processes a CSV file containing structured data, generates QR codes, and places them alongside formatted labels. The labels are then arranged on an A4 sheet for easy printing.

<img src="https://github.com/user-attachments/assets/c84ad850-7584-42c2-a839-79bf95d968f1" width=70% height=70%>


## Features
- Detects CSV file encoding dynamically using `chardet`.
- Generates QR codes with encoded information.
- Creates labels with formatted text.
- Places multiple labels onto A4-sized sheets.
- Supports automatic sorting by Division, City, and Name.
- Includes dotted lines for easy cutting of labels.

## Dependencies
Make sure you have the following Python libraries installed:

```bash
pip install chardet pyqrcode pypng pillow
```

## Usage
### 1. Prepare the CSV File
For labels_qr_gen.py the CSV file should contain the following columns:
- `ID`
- `Name`
- `IP`
- `Division` (Subdivision)
- `City`
  
For flag_label_qr_gen.py the CSV file should contain the following columns:
- `SrcName`
- `SrcIP`
- `SrcPort`
- `TrgName`  
- `TrgIP`
- `TrgPort`

The file should use `;` as the delimiter and `|` as the quote character.

### 2. Run the Script
Modify the filename in the script and execute it:

```python
csv_filename = 'your_file.csv'
output_dir = 'labels'
process_csv_file(csv_filename, output_dir)
```

### 3. Output
- QR code labels will be arranged on A4 sheets.
- Output files will be saved in the specified directory.
- The generated images will have dotted lines for easy cutting.

## Example Output
The script will generate files like `labels_a4_sheet_1.png`, `labels_a4_sheet_2.png`, etc.

## License
This project is open-source and available under the MIT License.


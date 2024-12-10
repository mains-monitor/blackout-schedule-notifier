from collections import defaultdict
from datetime import time, datetime, timedelta
import cv2
import numpy as np
import pytesseract

# Number of blackout groups
num_groups = 6
num_hours = 24

def recognize(image_path):
    image = cv2.imread(image_path)

    # Preprocess the image: Convert to grayscale and threshold
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary_image = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)

    # Detect external contours only
    external_contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    external_contours = [c for c in external_contours if cv2.contourArea(c) > 200]

    # Detect all contours
    contours, hierarchy = cv2.findContours(binary_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    id_to_contour = [(i, c) for i, c in enumerate(contours)]

    # Filter out small contours
    min_contour_area = 100  # Minimum contour area to keep
    id_to_filtered_contours = [c for c in id_to_contour if cv2.contourArea(c[1]) > min_contour_area]

    # Find the biggest contour by its area
    id_to_table_contour = max(id_to_filtered_contours, key=lambda c: cv2.contourArea(c[1]))
    table_contour = id_to_table_contour[1]

    _, table_y, _, _ = cv2.boundingRect(table_contour)
    external_contours_above_table = [c for c in external_contours if cv2.boundingRect(c)[1] < table_y]
    external_contours_above_table = sorted(external_contours_above_table, key=lambda c: cv2.boundingRect(c)[0], reverse=True)
    date_time_box_contour = external_contours_above_table[0]

    # Extract the portion of the image denoted by date_time_box_contour
    x, y, w, h = cv2.boundingRect(date_time_box_contour)
    date_time_box_image = image[y:y + h, x:x + w]

    # Recognize the text inside the extracted portion using pytesseract
    date_time_text = pytesseract.image_to_string(date_time_box_image, config='--psm 6').strip()

    # Find internal contours
    id_to_internal_contours = [(i, contours[i]) for i in range(0, hierarchy.shape[1]) if hierarchy[0, i][3] == id_to_table_contour[0]]

    # Filter out small contours
    id_to_internal_contours = [c for c in id_to_internal_contours if cv2.contourArea(c[1]) > min_contour_area]

    bounding_rects = [cv2.boundingRect(c) for _, c in id_to_internal_contours]
    x_sorted_bounding_rects = sorted(bounding_rects, key=lambda r: (r[0], r[1]))

    first_column_rects = x_sorted_bounding_rects[1:7]
    first_column_y_diffs = [r2[1] - r1[1] for r1, r2 in zip(first_column_rects, first_column_rects[1:])]

    # Check we really found a cells in the first column
    assert all(diff > 10 for diff in first_column_y_diffs)

    # Check for anomalies in first_column_y_diffs
    mean_diff = np.mean(first_column_y_diffs)
    std_diff = np.std(first_column_y_diffs)
    anomalies = [diff for diff in first_column_y_diffs if abs(diff - mean_diff) > 3 * std_diff]

    assert len(anomalies) == 0, f"Anomalies detected in first_column_y_diffs: {anomalies}"

    y_sorted_bounding_rects = sorted(bounding_rects, key=lambda r: (r[1], r[0]))

    first_row_rects = y_sorted_bounding_rects[1:25]
    first_row_x_diffs = [r2[0] - r1[0] for r1, r2 in zip(first_row_rects, first_row_rects[1:])]

    # Check we really found a cells in the first row
    assert all(diff > 10 for diff in first_row_x_diffs)

    # Check for anomalies in first_column_y_diffs
    mean_diff = np.mean(first_row_x_diffs)
    std_diff = np.std(first_row_x_diffs)
    anomalies = [diff for diff in first_row_x_diffs if abs(diff - mean_diff) > 3 * std_diff]

    assert len(anomalies) == 0, f"Anomalies detected in first_row_x_diffs: {anomalies}"

    row_heights = [r[3] for r in first_column_rects]
    col_widths = [r[2] for r in first_row_rects]
    col_x_coords = [r[0] for r in first_row_rects]
    col_y_coords = [r[1] for r in first_column_rects]

    start_time = None
    blackouts = defaultdict(list)

    for row in range(0, num_groups):
        for col in range(0, num_hours):
            cell_w = col_widths[col]
            cell_h = row_heights[row]
            cell_x = col_x_coords[col]
            cell_y = col_y_coords[row]
            rect = binary_image[cell_y:cell_y + cell_h, cell_x:cell_x + cell_w]
            avg_color = np.median(rect)

            # Determine if the average color is white
            is_white = avg_color > 240

            if is_white:
                if start_time is None:
                    start_time = datetime.combine(datetime.now().date(), time(hour=col, minute=0))

            if not is_white and start_time is not None:
                blackouts[row + 1].append(
                    dict(start=start_time, end=datetime.combine(datetime.now().date(), time(hour=col, minute=0)))
                )
                start_time = None

        if start_time is not None:
            end = datetime.combine(datetime.now().date(), time(hour=col, minute=0)) + timedelta(hours=1)
            blackouts[row + 1].append(dict(start=start_time, end=end))
            start_time = None
    
    return dict(date_time=date_time_text, blackouts=blackouts)

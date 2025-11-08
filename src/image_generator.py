import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import os

logger = logging.getLogger(__name__)


def generate_schedule_table_image(schedule, output_path, groups=None):
    """
    Generates a table image with blackout schedule.
    
    Args:
        schedule: Dictionary with schedule in format:
            {
                "date_time": "30.10.2025 08:12",
                "blackouts": {
                    "1.1": [{"start": datetime, "end": datetime}, ...],
                    "2.1": [...]
                }
            }
            or with bit_masks:
            {
                "date_time": "30.10.2025 08:12",
                "bit_masks": {
                    "1.1": "000000000000000000000000",
                    "2.1": "000000000000000000000000"
                }
            }
        output_path: Path to save the image
    
    Returns:
        str: Path to the saved image
    """
    
    # Table parameters
    CELL_WIDTH = 40
    CELL_HEIGHT = 50
    HEADER_HEIGHT = 60
    GROUP_COLUMN_WIDTH = 80
    BORDER_WIDTH = 2
    TITLE_Y = 10
    
    # Get groups
    if "bit_masks" in schedule:
        if not groups:
            groups = sorted(schedule["bit_masks"].keys())
        use_bitmasks = True
    else:
        if not groups:
            groups = sorted(schedule["blackouts"].keys())
        use_bitmasks = False
    
    hours = list(range(24))
    
    # Calculate image dimensions
    width = GROUP_COLUMN_WIDTH + len(hours) * CELL_WIDTH + BORDER_WIDTH
    height = HEADER_HEIGHT + len(groups) * CELL_HEIGHT + BORDER_WIDTH + TITLE_Y + 10
    
    # Create image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to load font
    try:
        # For macOS
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        header_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        cell_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except:
        try:
            # Alternative font for macOS
            title_font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 20)
            header_font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 16)
            cell_font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 14)
        except:
            # If font loading fails, use default
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            cell_font = ImageFont.load_default()
    
    # Draw header with date
    date_time_str = schedule.get("date_time", "")
    draw.text((width // 2, TITLE_Y), date_time_str, fill='black', 
              font=title_font, anchor='mt')
    
    # Draw hour headers
    for i, hour in enumerate(hours):
        x = GROUP_COLUMN_WIDTH + i * CELL_WIDTH
        y = HEADER_HEIGHT - 30 + TITLE_Y
        hour_text = f"{hour:02d}"
        draw.text((x + CELL_WIDTH // 2, y), hour_text, fill='black', 
                  font=header_font, anchor='mm')
    
    # Convert schedule to bitmasks for convenience
    group_bitmasks = {}
    
    if use_bitmasks:
        for group in groups:
            mask_str = schedule["bit_masks"][group]
            group_bitmasks[group] = [int(bit) for bit in mask_str[::-1]]
    else:
        # Convert blackouts to bitmasks
        for group in groups:
            bitmask = [0] * 24
            if group in schedule["blackouts"]:
                for blackout in schedule["blackouts"][group]:
                    start_hour = blackout["start"].hour
                    end_hour = blackout["end"].hour
                    
                    # If end is at 00:00 next day
                    if end_hour == 0 and blackout["end"].date() > blackout["start"].date():
                        end_hour = 24
                    
                    for hour in range(start_hour, end_hour):
                        if hour < 24:
                            bitmask[hour] = 1
            
            group_bitmasks[group] = bitmask
    
    # Draw table
    for row_idx, group in enumerate(groups):
        y_start = HEADER_HEIGHT + row_idx * CELL_HEIGHT
        
        # Draw group name
        draw.text((GROUP_COLUMN_WIDTH // 2, y_start + CELL_HEIGHT // 2), 
                  group, fill='black', font=cell_font, anchor='mm')
        
        # Draw vertical line after group name
        draw.line([(GROUP_COLUMN_WIDTH, y_start), 
                   (GROUP_COLUMN_WIDTH, y_start + CELL_HEIGHT)], 
                  fill='gray', width=1)
        
        # Draw cells for each hour
        bitmask = group_bitmasks[group]
        for col_idx, is_blackout in enumerate(bitmask):
            x_start = GROUP_COLUMN_WIDTH + col_idx * CELL_WIDTH
            
            # Determine cell color
            if is_blackout:
                cell_color = 'black'
            else:
                cell_color = 'white'
            
            # Draw cell
            draw.rectangle(
                [(x_start, y_start), 
                 (x_start + CELL_WIDTH, y_start + CELL_HEIGHT)],
                fill=cell_color,
                outline='gray',
                width=1
            )
    
    # Draw horizontal line under header
    draw.line([(0, HEADER_HEIGHT), (width, HEADER_HEIGHT)], 
              fill='gray', width=2)
    
    # Draw outer border
    draw.rectangle([(0, 0), (width - 1, height - 1)], 
                   outline='black', width=BORDER_WIDTH)
    
    # Save image
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    img.save(output_path)
    logger.info(f"Schedule table image saved to: {output_path}")
    
    return output_path

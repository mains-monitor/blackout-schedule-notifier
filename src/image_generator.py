import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import os
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Europe/Kyiv timezone
KYIV_TZ = ZoneInfo("Europe/Kyiv")


def generate_schedule_table_image(schedule, output_path, groups=None):
    """
    Generates a table image with blackout schedule.
    Supports half-hour granularity - cells can be filled fully, half (left or right), or not at all.
    
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
    
    if not groups:
        groups = sorted(schedule["blackouts"].keys())
    
    hours = list(range(24))
    
    # Calculate image dimensions
    width = GROUP_COLUMN_WIDTH + len(hours) * CELL_WIDTH + BORDER_WIDTH
    height = HEADER_HEIGHT + len(groups) * CELL_HEIGHT + BORDER_WIDTH + TITLE_Y + 10
    
    # Create image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    
    title_font = ImageFont.load_default(20)
    header_font = ImageFont.load_default(16)
    cell_font = ImageFont.load_default(14)
    
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
    
    # Convert schedule to half-hour bitmasks for convenience
    # Each hour has 2 half-hour periods: 0 = no blackout, 1 = first half, 2 = second half, 3 = full hour
    group_half_hour_masks = {}
    
    # Convert blackouts to half-hour bitmasks
    for group in groups:
        # Store as list of 24 values, each 0-3 representing state of that hour
        half_hour_mask = [0] * 24
        
        if group in schedule["blackouts"]:
            for blackout in schedule["blackouts"][group]:
                start_dt = blackout["start"]
                end_dt = blackout["end"]
                
                # Calculate start half-hour slot (0-47)
                start_half_hour = start_dt.hour * 2 + (1 if start_dt.minute >= 30 else 0)
                
                # Calculate end half-hour slot (0-48, where 48 = midnight next day)
                if end_dt.date() > start_dt.date() and end_dt.hour == 0 and end_dt.minute == 0:
                    end_half_hour = 48
                else:
                    end_half_hour = end_dt.hour * 2 + (1 if end_dt.minute >= 30 else 0)
                
                # Mark affected hours
                for half_hour_slot in range(start_half_hour, end_half_hour):
                    if half_hour_slot < 48:
                        hour_index = half_hour_slot // 2
                        is_first_half = (half_hour_slot % 2 == 0)
                        
                        if is_first_half:
                            # Mark first half (add 1)
                            half_hour_mask[hour_index] |= 1
                        else:
                            # Mark second half (add 2)
                            half_hour_mask[hour_index] |= 2
        
        group_half_hour_masks[group] = half_hour_mask
    
    # Draw table
    for row_idx, group in enumerate(groups):
        y_start = HEADER_HEIGHT + row_idx * CELL_HEIGHT
        
        # Draw group name
        draw.text((GROUP_COLUMN_WIDTH // 2, y_start + CELL_HEIGHT // 2), 
                  group, fill='black', font=title_font, anchor='mm')
        
        # Draw vertical line after group name
        draw.line([(GROUP_COLUMN_WIDTH, y_start), 
                   (GROUP_COLUMN_WIDTH, y_start + CELL_HEIGHT)], 
                  fill='gray', width=1)
        
        # Draw cells for each hour
        half_hour_mask = group_half_hour_masks[group]
        for col_idx, hour_state in enumerate(half_hour_mask):
            x_start = GROUP_COLUMN_WIDTH + col_idx * CELL_WIDTH
            
            # hour_state: 0 = no blackout, 1 = first half only, 2 = second half only, 3 = full hour
            
            if hour_state == 0:
                # No blackout - white cell
                draw.rectangle(
                    [(x_start, y_start), 
                     (x_start + CELL_WIDTH, y_start + CELL_HEIGHT)],
                    fill='white',
                    outline='gray',
                    width=1
                )
            elif hour_state == 3:
                # Full hour blackout - black cell
                draw.rectangle(
                    [(x_start, y_start), 
                     (x_start + CELL_WIDTH, y_start + CELL_HEIGHT)],
                    fill='black',
                    outline='gray',
                    width=1
                )
            elif hour_state == 1:
                # First half blackout - left half black, right half white
                # Draw white background
                draw.rectangle(
                    [(x_start, y_start), 
                     (x_start + CELL_WIDTH, y_start + CELL_HEIGHT)],
                    fill='white',
                    outline='gray',
                    width=1
                )
                # Draw black left half
                draw.rectangle(
                    [(x_start, y_start), 
                     (x_start + CELL_WIDTH // 2, y_start + CELL_HEIGHT)],
                    fill='black',
                    outline=None
                )
                # Redraw left border
                draw.line([(x_start, y_start), (x_start, y_start + CELL_HEIGHT)], 
                          fill='gray', width=1)
            elif hour_state == 2:
                # Second half blackout - left half white, right half black
                # Draw white background
                draw.rectangle(
                    [(x_start, y_start), 
                     (x_start + CELL_WIDTH, y_start + CELL_HEIGHT)],
                    fill='white',
                    outline='gray',
                    width=1
                )
                # Draw black right half
                draw.rectangle(
                    [(x_start + CELL_WIDTH // 2, y_start), 
                     (x_start + CELL_WIDTH, y_start + CELL_HEIGHT)],
                    fill='black',
                    outline=None
                )
                # Redraw right border
                draw.line([(x_start + CELL_WIDTH, y_start), 
                          (x_start + CELL_WIDTH, y_start + CELL_HEIGHT)], 
                          fill='gray', width=1)
    
    # Draw horizontal line under header
    draw.line([(0, HEADER_HEIGHT), (width, HEADER_HEIGHT)], 
              fill='gray', width=2)
    
    # Draw outer border
    draw.rectangle([(0, 0), (width - 1, height - 1)], 
                   outline='black', width=BORDER_WIDTH)
    
    # Save image
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    if date_time_str:
        # Parse date_time and format for filename
        try:
            dt = datetime.strptime(date_time_str, "%d.%m.%Y").replace(tzinfo=KYIV_TZ)
            timestamp = dt.strftime("%Y%m%d_%H%M")
            # Insert timestamp before file extension
            base, ext = os.path.splitext(output_path)
            output_path = f"{base}_{timestamp}{ext}"
        except ValueError:
            logger.warning(f"Could not parse date_time: {date_time_str}")
    
    img.save(output_path)
    logger.info(f"Schedule table image saved to: {output_path}")
    
    return output_path

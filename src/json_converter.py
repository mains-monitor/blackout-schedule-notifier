import json
import logging
from datetime import datetime, time, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


def convert_supplier_json_to_internal(json_path):
    """
    Convert supplier JSON format to internal format.
    
    Supplier format:
    {
        "data": {
            "timestamp": {
                "GPV1.1": {"1": "yes", "2": "yes", ...},
                ...
            }
        },
        "update": "DD.MM.YYYY HH:MM",
        "today": timestamp
    }
    
    Internal format:
    {
        "date_time": "DD.MM.YYYY HH:MM",
        "blackouts": {
            "1.1": [{"start": datetime, "end": datetime}, ...],
            ...
        }
    }
    """
    logger.info(f"Converting supplier JSON from: {json_path}")
    
    with open(json_path, 'r') as f:
        supplier_data = json.load(f)

    last_updated = supplier_data.get("update", "")

    results = []

    for timestamp, day_data in supplier_data.get("data", {}).items():
        date_time = datetime.fromtimestamp(int(timestamp)).date().strftime("%d.%m.%Y")
        # Convert timestamp to date for datetime objects
        base_date = datetime.fromtimestamp(int(timestamp)).date()
        # Build internal format
        blackouts = defaultdict(list)
        bit_masks = {}
        
        # Process each group
        for group_key, hours in day_data.items():
            # Convert "GPV1.1" to "1.1"
            internal_group = group_key.replace("GPV", "")
            
            # Track blackout periods
            start_time = None
            group_bit_mask = 0
            
            for hour_str in sorted(hours.keys(), key=int):
                hour = int(hour_str)
                status = hours[hour_str]
                
                # "yes" means power is available (no blackout)
                # "no" or "maybe" means blackout
                has_power = status == "yes"

                if not has_power:
                    group_bit_mask |= (1 << (hour - 1))
                    # Blackout starts or continues
                    if start_time is None:
                        # Hour strings are 1-24, but datetime hours are 0-23
                        start_time = datetime.combine(base_date, time(hour=(hour - 1) % 24, minute=0))
                        if hour == 24:
                            start_time += timedelta(days=1)
                else:
                    # Power is available
                    if start_time is not None:
                        # End the blackout period
                        end_time = datetime.combine(base_date, time(hour=(hour - 1) % 24, minute=0))
                        if hour == 24:
                            end_time += timedelta(days=1)
                        
                        blackouts[internal_group].append({
                            "start": start_time,
                            "end": end_time
                        })
                        start_time = None
            
            # Close any open blackout period at the end of the day
            if start_time is not None:
                end_time = datetime.combine(base_date, time(hour=23, minute=59)) + timedelta(minutes=1)
                blackouts[internal_group].append({
                    "start": start_time,
                    "end": end_time
                })
            bit_masks[internal_group] = format(group_bit_mask, '024b')
        
        internal_format = {
            "date_time": date_time,
            "blackouts": dict(blackouts),
            "bit_masks": bit_masks,
            "last_updated": last_updated
        }
        results.append(internal_format)

    logger.info(f"Converted schedule data from supplier JSON")
    return results

import logging
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
import argparse
import os
import glob
import json
import hashlib
from schedule_handler import handle_schedule_change
from json_converter import convert_supplier_json_to_internal
from config import config
from datetime import timedelta

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='Process schedule data from image or JSON.')
    parser.add_argument('--input_dir', type=str, required=True, help='Directory containing the input images')
    parser.add_argument('--src', type=str, required=True, help='Source image or JSON file')
    parser.add_argument('--out_dir', type=str, required=True, help='Directory to save the json schedule')
    parser.add_argument('--group_log', type=str, required=True,
                        help='Service directory for tracking group schedule changes')
    parser.add_argument('--mode', type=str, choices=['image', 'json', 'cleanup'], default='image',
                        help='Processing mode: "image" for image recognition, "json" for supplier JSON conversion')
    return parser.parse_args()


def remove_old_files(directory, exceptions=None, cutoff_days=2):
    logger.info(f"Removing old files in directory: {directory}, cutoff_days: {cutoff_days}")
    resolved_exceptions = []
    if exceptions:
        resolved_exceptions = [os.path.join(directory, exc) for exc in exceptions]
    files = glob.glob(os.path.join(directory, '*'))
    current_time = datetime.now()
    cutoff_time = current_time - timedelta(days=cutoff_days)
    logger.info(f"Cutoff time: {cutoff_time}, timestamp: {cutoff_time.timestamp()}")
    logger.info(f"Total files found: {len(files)}")
    files = [f for f in files if os.path.getmtime(f) < cutoff_time.timestamp()]
    logger.info(f"Files to be removed: {len(files)}")
    for file in files:
        if file in resolved_exceptions:
            continue
        logger.info(f"Removing old file: {file}")
        os.remove(file)


def time_converter(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%H:%M")
    raise TypeError("Type not serializable")


def dump_json_to_file(json_data, directory):
    json_str = json.dumps(json_data, sort_keys=True, default=time_converter)
    md5_hash = hashlib.md5(json_str.encode()).hexdigest()
    file_name = f"{md5_hash}.json"
    file_path = os.path.join(directory, file_name)
    logger.info(f"Saving schedule to: {file_path}")

    if os.path.exists(file_path):
        logger.info(f"File already exists: {file_path}")
        return file_name

    with open(file_path, 'w') as json_file:
        json_file.write(json_str)

    logger.info(f"Schedule saved to: {file_path}")
    return file_name


def dump_meta_info(meta_info, out_dir):
    meta_file_path = os.path.join(out_dir, 'meta_info.json')
    if os.path.exists(meta_file_path):
        with open(meta_file_path, 'r') as f:
            existing_meta = json.load(f)
        existing_meta.update(meta_info)
        dates = [datetime.strptime(schedule_date, "%d.%m.%Y") for schedule_date in existing_meta.keys()]
        dates.sort()
        latest_dates = dates[-3:]
        meta_info = {date.strftime("%d.%m.%Y"): existing_meta[date.strftime("%d.%m.%Y")] for date in latest_dates}
    with open(meta_file_path, 'w') as f:
        json.dump(meta_info, f, indent=2)
    logger.info(f"Meta info saved to: {meta_file_path}")


if __name__ == "__main__":
    args = parse_args()
    input_dir = args.input_dir
    src = args.src
    out_dir = args.out_dir
    group_log = args.group_log
    mode = args.mode
    
    # Initialize global config
    config.initialize(input_dir, src, out_dir, group_log, mode)

    logger.info(f"Input dir: {input_dir}")
    logger.info(f"Source: {src}")
    logger.info(f"Output dir: {out_dir}")
    logger.info(f"Group log: {group_log}")
    logger.info(f"Mode: {mode}")

    if mode == 'cleanup':
        logger.info("Running cleanup mode")
        remove_old_files(input_dir)
        remove_old_files(out_dir, exceptions=['meta_info.json', 'telegram-meta-v2.json'])
        remove_old_files(group_log)
        exit(0)
    elif mode == 'image':
        logger.info("Processing image with OCR recognition")
        # schedule = recognize(src)
        raise NotImplementedError("Image recognition mode is not implemented yet.")
    elif mode == 'json':
        logger.info("Processing supplier JSON file")
        schedule = convert_supplier_json_to_internal(src)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    meta_info = {}

    if isinstance(schedule, list):
        for single_schedule in schedule:
            file_name = dump_json_to_file(single_schedule, out_dir)
            meta_info[single_schedule["date_time"]] = file_name
            if file_name:
                # if 'bit_masks' in single_schedule:
                #     handle_schedule_changes_with_masks(single_schedule, src, group_log)
                # else:
                handle_schedule_change(single_schedule, src, group_log) 
    else:
        file_name = dump_json_to_file(schedule, out_dir)
        meta_info[schedule["date_time"]] = file_name
        if file_name:
            # if 'bit_masks' in schedule:
            #     handle_schedule_changes_with_masks(schedule, src, group_log)
            # else:
            handle_schedule_change(schedule, src, group_log)

    dump_meta_info(meta_info, out_dir)

    remove_old_files(input_dir)
    remove_old_files(out_dir, exceptions=['meta_info.json', 'telegram-meta-v2.json'])
    remove_old_files(group_log)
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
from recognizer import recognize

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='Process some images.')
    parser.add_argument('--input_dir', type=str, required=True, help='Directory containing the input images')
    parser.add_argument('--src', type=str, required=True, help='Source image')
    parser.add_argument('--out_dir', type=str, required=True, help='Directory to save the json schedule')
    parser.add_argument('--group_log', type=str, required=True,
                        help='Service directory for tracking group schedule changes')
    return parser.parse_args()


def remove_old_files(directory, max_files=10):
    files = glob.glob(os.path.join(directory, '*'))
    files.sort(key=os.path.getmtime, reverse=True)
    for file in files[max_files:]:
        logger.info(f"Removing old file: {file}")
        os.remove(file)


def time_converter(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%H:%M")
    raise TypeError("Type not serializable")


def dump_json_to_file(json_data, directory):
    json_str = json.dumps(json_data, sort_keys=True, default=time_converter)
    md5_hash = hashlib.md5(json_str.encode()).hexdigest()
    file_path = os.path.join(directory, f"{md5_hash}.json")
    logger.info(f"Saving schedule to: {file_path}")

    if os.path.exists(file_path):
        logger.info(f"File already exists: {file_path}")
        return False

    with open(file_path, 'w') as json_file:
        json_file.write(json_str)

    logger.info(f"Schedule saved to: {file_path}")
    return True


if __name__ == "__main__":
    args = parse_args()
    input_dir = args.input_dir
    src = args.src
    out_dir = args.out_dir
    group_log = args.group_log

    logger.info(f"Input dir: {input_dir}")
    logger.info(f"Source image: {src}")
    logger.info(f"Output dir: {out_dir}")
    logger.info(f"Group log: {group_log}")

    remove_old_files(input_dir)
    remove_old_files(out_dir)
    remove_old_files(group_log)

    logger.info("Recognizing the schedule")
    schedule = recognize(src)

    if dump_json_to_file(schedule, out_dir):
        handle_schedule_change(schedule, src, group_log)

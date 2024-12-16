import hashlib
import logging
from datetime import datetime, timedelta
import os
import json
from tg import post_message_with_image

logger = logging.getLogger(__name__)

CHAT_ID_TO_BLACKOUT_GROUPS = json.loads(
    os.getenv('CHAT_ID_TO_BLACKOUT_GROUPS') or '{}')

def generate_markdown(date_time, groups, blackouts):
    message = f"""
🗓 Графік на {date_time}. {', '.join(groups)} {'група' if len(groups) == 1 else 'групи'}:

{blackouts}
"""
    return message


def time_converter(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%H:%M")
    raise TypeError("Type not serializable")


def _store_hash_if_not_exist(directory, json_data):
    json_str = json.dumps(json_data, sort_keys=True, default=time_converter)
    md5_hash = hashlib.md5(json_str.encode()).hexdigest()
    file_path = os.path.join(directory, f"{md5_hash}")

    if os.path.exists(file_path):
        logger.info(f"File already exists: {file_path}")
        return False

    with open(file_path, 'w') as f:
        f.write('')

    return True


def handle_schedule_change(schedule, image_path, group_log):
    for chant_id, groups in CHAT_ID_TO_BLACKOUT_GROUPS.items():
        logger.info(
            f"Handling schedule change for chant_id: {chant_id} and groups: {groups}")
        if len(groups) == 1:
            logger.info("Handling single group")
            date_time = schedule["date_time"]
            group_schedule = schedule["blackouts"][int(groups[0])]
            if not _store_hash_if_not_exist(group_log, group_schedule):
                logger.info("No changes in the schedule for the group")
                continue
            schedule_text_block = '\n'.join(
                [f"◾️ {item['start'].strftime('%H:%M')} - {item['end'].strftime('%H:%M')}" for item in group_schedule])
            message = generate_markdown(
                date_time, groups, schedule_text_block)
            logger.info(
                f"Posting message with image: {image_path} and message: {message}")
            post_message_with_image(chant_id, image_path, message)
        else:
            logger.info("Handling multiple groups")
            date_time = schedule["date_time"]
            time_line = []
            for group in groups:
                for blackout in schedule["blackouts"][group]:
                    time_line.append((blackout['start'], group, 'start'))
                    time_line.append((blackout['end'], group, 'end'))
            
            time_line.sort(key=lambda x: x[0])
            num_groups = len(groups)
            merged_schedule = []
            stack = []
            possible_switches = []

            if not _store_hash_if_not_exist(group_log, time_line):
                logger.info(
                    f"No changes in the schedule for the groups {groups}")
                continue
            for time_point, group, event in time_line:
                if event == 'start':
                    stack.append((time_point, group))
                    if len(stack) < num_groups:
                        possible_switches.append(
                            {'start': time_point, 'end': time_point + timedelta(minutes=30)})
                else:
                    start_time, _ = stack.pop()
                    if len(stack) == num_groups - 1:
                        if start_time != time_point:
                            merged_schedule.append(
                                {'start': start_time, 'end': time_point})
                        else:
                            possible_switches.append(
                                {'start': time_point, 'end': time_point + timedelta(minutes=30)})

            texts = []
            if merged_schedule:
                schedule_text_block = 'Відключення:\n' + \
                    '\n'.join(
                        [f"◾️ {item['start'].strftime('%H:%M')} - {item['end'].strftime('%H:%M')}" for item in merged_schedule])
                texts.append(schedule_text_block + '\n')
            if possible_switches:
                possible_switches_text_block = 'Можливе перемикання:\n' + \
                    '\n'.join(
                        [f"🔀{item['start'].strftime('%H:%M')} - {item['end'].strftime('%H:%M')}" for item in possible_switches])
                texts.append(possible_switches_text_block)
            message = generate_markdown(
                date_time, groups, '\n'.join(texts))
            logger.info(
                f"Posting message with image: {image_path} and message: {message}")
            post_message_with_image(chant_id, image_path, message)

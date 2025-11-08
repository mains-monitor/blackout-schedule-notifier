import hashlib
import logging
from datetime import datetime, timedelta
import os
import json
from tg import post_message_with_image
from image_generator import generate_schedule_table_image

logger = logging.getLogger(__name__)

CHAT_ID_TO_BLACKOUT_GROUPS = json.loads(
    os.getenv('CHAT_ID_TO_BLACKOUT_GROUPS') or '{}')

def generate_markdown(date_time, groups, blackouts):
    message = f"""
🗓 Графік на {date_time}\n\n{', '.join(groups)} {'група' if len(groups) == 1 else 'групи'}

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
    # Generate table image
    
    for chant_id, groups in CHAT_ID_TO_BLACKOUT_GROUPS.items():
        logger.info(
            f"Handling schedule change for chant_id: {chant_id} and groups: {groups}")
        table_image_path = image_path.replace('.json', '_table.png').replace('.jpg', '_table.png').replace('.png', '_table.png')
        generate_schedule_table_image(schedule, table_image_path, groups)
        if len(groups) == 1:
            logger.info("Handling single group")
            date_time = schedule["date_time"]
            group_schedule = schedule["blackouts"][groups[0]]
            if not _store_hash_if_not_exist(group_log, group_schedule):
                logger.info("No changes in the schedule for the group")
                continue
            schedule_text_block = '\n'.join(
                [f"◾️ {item['start'].strftime('%H:%M')} - {item['end'].strftime('%H:%M')}" for item in group_schedule])
            message = generate_markdown(
                date_time, groups, schedule_text_block)
            logger.info(
                f"Posting message with image: {table_image_path} and message: {message}")
            post_message_with_image(chant_id, table_image_path, message)
        else:
            logger.info("Handling multiple groups")
            date_time = schedule["date_time"]
            time_line = []
            for group in groups:
                if group in schedule["blackouts"]:
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
                    last_start_time = stack[-1][0] if len(stack) > 0 else None
                    stack.append((time_point, group))
                    if last_start_time and time_point > last_start_time:
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
            if not merged_schedule and not possible_switches:
                texts.append('💡 Відключення не заплановані')
            message = generate_markdown(
                date_time, groups, '\n'.join(texts))
            logger.info(
                f"Posting message with image: {table_image_path} and message: {message}")
            post_message_with_image(chant_id, table_image_path, message)

def handle_schedule_changes_with_masks(schedule, image_path, group_log):
    for chant_id, groups in CHAT_ID_TO_BLACKOUT_GROUPS.items():
        logger.info(
            f"Handling schedule change for chant_id: {chant_id} and groups: {groups}")
        table_image_path = image_path.replace('.json', '_table.png').replace('.jpg', '_table.png').replace('.png', '_table.png')
        generate_schedule_table_image(schedule, table_image_path, groups)
        combined_mask = (1 << 24) - 1  # All 24 bits set
        possible_switches_mask = 0
        for group in groups:
            if group in schedule["bit_masks"]:
                group_mask_str = schedule["bit_masks"][group]
                group_mask = int(group_mask_str, 2)
                combined_mask &= group_mask
                possible_switches_mask ^= group_mask
        if not _store_hash_if_not_exist(group_log, [schedule["bit_masks"][group] for group in groups]):
            logger.info("No changes in the schedule for the groups")
            continue
        if combined_mask == 0 and possible_switches_mask == 0:
            post_message_with_image(chant_id, table_image_path, '💡 Відключення не заплановані')
            continue
        blackout_periods = []
        possible_switches_periods = []
        start_time = None
        for hour in range(24):
            if (combined_mask >> hour) & 1:
                if not start_time:
                    start_time = datetime.combine(
                        datetime.now().date(), datetime.min.time()) + timedelta(hours=hour)
            else:
                if start_time:
                    end_time = datetime.combine(
                            datetime.now().date(), datetime.min.time()) + timedelta(hours=hour)
                    blackout_periods.append(
                        {'start': start_time, 'end': end_time})
                    start_time = None
        if start_time:
            end_time = datetime.combine(
                datetime.now().date(), datetime.min.time()) + timedelta(hours=24)
            blackout_periods.append(
                {'start': start_time, 'end': end_time})
        
        if possible_switches_mask != 0:
            group_detect_masks = [possible_switches_mask ^ int(schedule["bit_masks"][group],2) for group in groups if group in schedule["bit_masks"]]
            switching_period_continues = False
            for hour in range(24):
                if (possible_switches_mask >> hour) & 1 and not switching_period_continues:
                    start_time = datetime.combine(
                        datetime.now().date(), datetime.min.time()) + timedelta(hours=hour)
                    end_time = start_time + timedelta(minutes=30)
                    possible_switches_periods.append(
                        {'start': start_time, 'end': end_time})
                    switching_period_continues = True
                elif not (possible_switches_mask >> hour) & 1:
                    switching_period_continues = False

        schedule_text_block = '\n'.join(
            [f"◾️ {item['start'].strftime('%H:%M')} - {item['end'].strftime('%H:%M')}" for item in blackout_periods])
        
        if possible_switches_periods:
            schedule_text_block += 'Можливе перемикання:\n' + '\n'.join(
                [f"🔀 {item['start'].strftime('%H:%M')} - {item['end'].strftime('%H:%M')}" for item in possible_switches_periods])

        message = generate_markdown(
            schedule["date_time"], groups, schedule_text_block)
        logger.info(
            f"Posting message with image: {table_image_path} and message: {message}")
        post_message_with_image(chant_id, table_image_path, message)

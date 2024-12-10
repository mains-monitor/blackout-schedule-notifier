from datetime import datetime, timedelta
import os
import json
from tg import post_message_with_image

CHAT_ID_TO_BLACKOUT_GROUPS = json.loads(os.getenv('CHAT_ID_TO_BLACKOUT_GROUPS'))

def generate_markdown(date_time, groups, blackouts):
    message = f"""
🗓 Графік на {date_time}. {', '.join(groups)} {'група' if len(groups) == 1 else 'групи'}:

{blackouts}
"""
    return message


def handle_schedule_change(schedule, image_path):
    for chant_id, groups in CHAT_ID_TO_BLACKOUT_GROUPS.items():
        if len(groups) == 1:
            date_time = schedule["date_time"]
            group_schedule = schedule["blackouts"][int(groups[0])]
            schedule_text_block = '\n'.join([f"◾️ {item['start'].strftime('%H:%M')} - {item['end'].strftime('%H:%M')}" for item in group_schedule])
            message = generate_markdown(date_time, groups, schedule_text_block)
            post_message_with_image(chant_id, image_path, message)
        else:
            date_time = schedule["date_time"]
            time_line = []
            for group in groups:
                for blackout in schedule["blackouts"][int(group)]:
                    time_line.append((blackout['start'], group, 'start'))
                    time_line.append((blackout['end'], group, 'end'))
            
            time_line.sort(key=lambda x: x[0])
            num_groups = len(groups)
            merged_schedule = []
            stack = []
            possible_switches = []

            for time_point, group, event in time_line:
                if event == 'start':
                    stack.append((time_point, group))
                    if len(stack) < num_groups:
                        possible_switches.append({'start': time_point, 'end': time_point + timedelta(minutes=30)})
                else:
                    start_time, _ = stack.pop()
                    if len(stack) == num_groups - 1:
                        merged_schedule.append({'start': start_time, 'end': time_point})
            
            texts = []
            if merged_schedule:
                schedule_text_block = 'Відключення:\n' + '\n'.join([f"◾️ {item['start'].strftime('%H:%M')} - {item['end'].strftime('%H:%M')}" for item in merged_schedule])
                texts.append(schedule_text_block+ '\n')
            if possible_switches:
                possible_switches_text_block = 'Можливе перемикання:\n' + '\n'.join([f"🔀{item['start'].strftime('%H:%M')} - {item['end'].strftime('%H:%M')}" for item in possible_switches])
                texts.append(possible_switches_text_block)
            message = generate_markdown(date_time, groups, '\n'.join(texts))
            post_message_with_image(chant_id, image_path, message)
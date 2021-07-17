def send_message_to_id(dst_id, message):
    #send message to dst_id
    pass
def send_message_to_group_of_ids(dst_ids, message):
    for id in dst_ids:
        send_message_to_id(id, message)
def handle_chat(dst_id, message):
    pass
import boto3
from logger_setup import setup_logger
import os
import uuid
from datetime import datetime, timezone
from datetime import datetime
import random
import yaml
from decimal import Decimal
from dotenv import load_dotenv
import logging

boto3.set_stream_logger('botocore', level=logging.DEBUG)

logger = setup_logger()
load_dotenv()


aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_DEFAULT_REGION')


dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)



table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))

with open("bot.yml", "r") as ymlfile:
    bot_data = yaml.load(ymlfile, Loader=yaml.FullLoader)

def db_create_entry(chat_id, **kwargs):
    '''Initialize a new entry in the table'''
    item = {
        "chat_id": chat_id,
        "created": datetime.now(timezone.utc).isoformat(),
        "messages": [],  # list of dicts with keys "sender", "text", "timestamp", "widget_type", "widget_config"
        "issue_messages": [],  # subset list of messages that are the users issue, emotions, and explanations for emotions
        "completed": 0,  # 0 if the chat is not completed, 1 if the chat is completed,
        "state": "begin",
        "ip_address": "",
        "emotions": [],  # list of len 1-3 where each element is a dict with keys emotion. 
        "vals": [],  # list of len 15 with dicts with keys "value_text", "value_num", "value_rating"
        "reappraisals": [],  # list of len 3 with dicts with keys "reap_text", "reap_num", "value_text", "value_rank", "value_rating", "reap_efficacy"
        # "pid": "",
        # "person_values": {"v" + str(i+1): int(-99) for i in range(16)},
        # "issue": "",
        # "issue_summary_bot": "",
        # "issue_summary": "",
        # "crisis_input": "",
    }
    item.update(kwargs)
    table.put_item(Item=item)
    return chat_id

def db_add_message(chat_id, sender, data):
    '''Add a message to the messages list in the table'''
    if sender not in ["user", "bot"]:
        raise ValueError("Sender must be 'user' or 'bot'")
    msg = {
        "sender": sender,
        "response": data['response'],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "widget_type": data['widget_type'],
        "widget_config": data.get("widget_config", {})
    }
    db_append_list(chat_id, "messages", msg)

def db_add_messages(chat_id, sender, data: list):
    '''Add a message to the messages list in the table'''
    if sender not in ["user", "bot"]:
        raise ValueError("Sender must be 'user' or 'bot'")
    msgs = []
    for msg in data:
        entry = {
            "sender": sender,
            "response": msg['response'],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "widget_type": msg['widget_type'],
            "widget_config": msg.get("widget_config", {})
        }
        msgs.append(entry)
    db_append_list(chat_id, "messages", msgs)
        

def db_get_entry(chat_id):
    '''Get an entry from the table'''
    response = table.get_item(Key={'chat_id': str(chat_id)})
    item = response['Item']
    return item

def db_update_entry(chat_id, key, value):
    '''Update a simple entry in the table, allowing for various data types (e.g., dict, list, etc.)'''
    # Ensure key and value retain their original types
    table.update_item(
        Key={
            'chat_id': str(chat_id)
        },
        UpdateExpression=f"set #key = :val",
        ExpressionAttributeNames={
            '#key': key  
        },
        ExpressionAttributeValues={
            ':val': value  
        },
        ReturnValues="UPDATED_NEW"
    )
    
def db_update_nested_field(chat_id, list_name, index, field, new_value):
    '''Update a specific field within a list of dictionaries at a given index.'''
    # Update the specific field in a nested list of dictionaries
    table.update_item(
        Key={
            'chat_id': str(chat_id)
        },
        UpdateExpression=f"set #{list_name}[{index}].{field} = :val",
        ExpressionAttributeNames={
            f'#{list_name}': list_name  # Ensure the list field is recognized
        },
        ExpressionAttributeValues={
            ':val': new_value  # New value to update
        },
        ReturnValues="UPDATED_NEW"
    )

def db_append_list(chat_id, key, value):
    '''Append any value (str, dict, etc.) or extend a list of values to an existing list in the DynamoDB table'''

    # Ensure the value is a list
    if not isinstance(value, list):
        value = [value]
    
    table.update_item(
        Key={
            'chat_id': str(chat_id)
        },
        UpdateExpression=f"SET {key} = list_append(if_not_exists({key}, :empty_list), :val)",
        ExpressionAttributeValues={
            ':val': value,
            ':empty_list': []  # Fallback to an empty list if the key doesn't exist
        },
        ReturnValues="UPDATED_NEW"
    )


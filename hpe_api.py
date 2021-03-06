from havenondemand.hodclient import *
import json
import parsedatetime
from datetime import datetime
from pprint import pprint

client = HODClient("2ce81803-a67f-423b-84be-68661802991d", version="v1")

# with open('chat.json') as data:
# 	chat_data = json.load(data)

def extract_branch_messages(branch, chat_data):
	msg = branch
	branch_msg = chat_data[branch]["messages"]
	for item in branch_msg:
		msg += ' '
		msg += item["message"]
	data = {'text': msg}
	return data

def get_entities(branch, chat_data):
	params = extract_branch_messages(branch, chat_data)
	params["entity_type"] = ["films_eng"]
	response = client.get_request(params, HODApps.ENTITY_EXTRACTION, async=False)
	entities = []
	for item in response['entities']:
		if item['normalized_text'] not in entities:
			entities.append(item['normalized_text'])
		else:
			continue
	return entities

def get_concepts(branch, chat_data):
	params = extract_branch_messages(branch, chat_data)
	response = client.get_request(params, HODApps.EXTRACT_CONCEPTS, async=False)
	return response['concepts']

def get_message(item): 
	return item["message"]

def unix_time_sec(dt):
	epoch = datetime.utcfromtimestamp(0)
	sec = (dt - epoch).total_seconds()
	return int(sec)

def get_date_time_occurrences(branch, chat_data):
	data = {}
	messages = [branch]
	messages.extend(list(map(get_message, chat_data[branch]["messages"])))
	cal = parsedatetime.Calendar()
	seq = 0;
	for message in messages:
		curr = {}
		time_struct, parse_status = cal.parse(message)
		if (parse_status > 0):
			datetimevalue = datetime(*time_struct[:6])
			sec = unix_time_sec(datetimevalue)
			if sec in data.keys():
				curr["seq"] = data[sec]["seq"]
				curr["occurrences"] = data[sec]["occurrences"] + 1
				curr["type"] = "datetime"
			else:
				curr["seq"] = seq
				curr["occurrences"] = 1
				curr["type"] = "datetime"
				seq += 1
			data[sec] = curr
	result = []
	for key in data.keys():
		curr = data[key]
		curr["entity"] = key
		result.append(curr)
	return result

def get_relevant_entities(branch, chat_data):
	data = []
	entities = get_entities(branch, chat_data)
	for item in get_concepts(branch, chat_data):
		curr = {}
		if item['concept'] in entities:
			curr['entity'] = item['concept']
			curr['occurrences'] = item['occurrences']
			curr['type'] = 'films'
			data.append(curr)
		elif "cinema" in item['concept'].lower():
			curr['entity'] = item['concept']
			curr['type'] = 'location'
			curr['occurrences'] = item['occurrences']
			data.append(curr)
		else:
			continue
	data.extend(get_date_time_occurrences(branch, chat_data))
	return data

def normalize_user_msg(branch, chat_data):
	data = {}
	for item in chat_data[branch]["messages"]:
		username = item['username']
		message = item['message']
		if username not in data.keys():
			data[username] = ''
		data[username] += ' '
		data[username] += message
	return data

def get_user_sentiments(branch, chat_data):
	data = {}
	user_data = normalize_user_msg(branch, chat_data)
	for user in user_data.keys():
		params = {'text': user_data[user]}
		response = client.get_request(params, HODApps.ANALYZE_SENTIMENT, async=False)
		data[user] = response
	return data

# pprint(get_user_sentiments("Shall we watch Finding Dory tonight?", chat_data))
# def get_summary(branch):
# pprint(get_entities("Shall we watch Finding Dory tonight?"))
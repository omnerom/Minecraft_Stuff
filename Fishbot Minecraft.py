from pythmc import ChatLink
import time
import re
import traceback
from collections import deque
from openai import OpenAI
import tiktoken
import threading
import pyperclip

print("Starting in 3 seconds...")
time.sleep(1)
print("2...")
time.sleep(1)
print("1...")
time.sleep(1)

# Define constants
MAX_TOKENS = 30
MESSAGE_COOLDOWN = 1.5
QUESTION_COOLDOWN = 20
RECENT_LINES_COUNT = 3
CONTEXT_LINES_COUNT = 10

chat = ChatLink()

# File paths
file_path = r'C:\Users\saved\AppData\Roaming\PrismLauncher\instances\1.21 mods\.minecraft\logs\latest.log'
welcome_players = r'C:\Users\saved\PycharmProjects\Minecraft_stuff\welcome_mc_players'
INSTRUCTIONS_PATH = r'C:\Users\saved\PycharmProjects\Minecraft_stuff\mc_instructions.txt'
API_KEY_PATH = r'C:\Users\saved\OneDrive\Documents\Python stuff\API_KEY.txt'

with open(API_KEY_PATH, 'r', encoding='utf-8') as file:
    api_key = file.read().strip()

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Initialize global variables
recent_lines = deque(maxlen=RECENT_LINES_COUNT)
context_lines = deque(maxlen=CONTEXT_LINES_COUNT)
last_question = ""
last_question_time = 0
last_message_time = 0

# List of valid mining resources
valid_resources = ["copper", "lead", "beryllium", "sand", "coal", "graphite", "scrap", "titanium"]

# Initialize the tiktoken encoder
encoding = tiktoken.get_encoding("cl100k_base")

# Load instructions
def load_instructions(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip()]
            if not lines:
                print("No instructions found in the file.")
            return lines
    except FileNotFoundError:
        print(f"File not found: {path}")
        return []
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return []

instructions = load_instructions(INSTRUCTIONS_PATH)

# Function to send instructions to ChatGPT
def send_instructions():
    """Send the instructions to ChatGPT."""
    if not instructions:
        print("No instructions to send.")
        return

    messages = [{"role": "system", "content": "\n".join(instructions)}]
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=30  # Adjust as necessary
        )
        print(f"Instructions sent: {response}")
    except Exception as e:
        print(f"Error sending instructions: {e}")

# Function to count tokens using tiktoken
def count_tokens(messages):
    tokens = sum(len(encoding.encode(message["content"])) for message in messages)
    return tokens

# Function to generate and send a personalized message
def send_personalized_message(question, context):
    # Filter context lines to include only relevant information
    filtered_context = [line for line in context if "relevant" in line.lower()]  # Adjust filter criteria as needed

    messages = [{"role": "user", "content": question}]
    messages.extend({"role": "system", "content": instruction} for instruction in instructions)
    messages.extend({"role": "system", "content": line} for line in filtered_context)

    print(f"T: {count_tokens(messages)}")

    while True:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=MAX_TOKENS,
                messages=messages
            )
            assistant_response = response.choices[0].message.content.strip()

            if assistant_response.lower().startswith("fishbot:"):
                assistant_response = assistant_response[len("fishbot:"):].strip()

            assistant_response = f"{assistant_response}"

            # Send the message using ChatLink
            chat.send(assistant_response)

            # Ensure the message fits within the token limit
            if len(assistant_response.split()) <= MAX_TOKENS:
                print("R:", assistant_response)
                print(f"T: {len(encoding.encode(assistant_response))}")
                break
        except Exception as e:
            print(f"Error sending message: {e}")

# Function to clean the message by removing "[I] [Chat] " prefix
def clean_message(message):
    return message.replace("[I] [Chat] ", "")

# Function to send a message
send_message_lock = threading.Lock()
def send_message(message):
    global last_message_time
    current_time = time.time()

    with send_message_lock:
        # Check if the cooldown period has passed
        time_since_last_message = current_time - last_message_time
        if time_since_last_message < MESSAGE_COOLDOWN:
            wait_time = MESSAGE_COOLDOWN - time_since_last_message
            print(f"Cooldown in effect. Waiting for {wait_time:.2f} seconds...")
            time.sleep(wait_time)
            current_time = time.time()  # Update current_time after waiting

        # Send the message using ChatLink
        try:
            chat.send(message)
            print(f"Message sent: {message}")
        except Exception as e:
            print(f"Error sending message: {e}")

        # Update the last message time
        last_message_time = current_time
        print(f"Updated last_message_time to {last_message_time}")

# Function to send "Fishbot is online" message
def send_online_message():
    send_message("FishBot is online.")
    print("Fishbot is online")

# Function to handle the response to a question
def handle_question_response(question_text):
    global last_question, last_question_time

    current_time = time.time()
    if question_text == last_question and current_time - last_question_time < QUESTION_COOLDOWN:
        return

    last_question = question_text
    last_question_time = current_time

    print(f"Q: {question_text}")

    # Handle different commands or questions
    if re.search(r'\bhey fishbot mine\b', question_text, re.IGNORECASE):
        # Example command handling
        if re.search(r'\bhey fishbot mine (everything|all)\b', question_text, re.IGNORECASE):
            send_message("[gold]Mining everything")
            time.sleep(0.5)
            send_message("!miner * 1000000")
            return

        resources = [resource for resource in valid_resources if resource in question_text.lower()]
        if resources:
            resource_list = ", ".join(resources)
            send_message(f"[gold]Mining {resource_list}")
            time.sleep(0.5)
            send_message(f"!miner {' '.join(resources)} 1000000")
            return

    # Send personalized message using the clipboard
    send_personalized_message(question_text, list(context_lines))

# Function to load a list of players from a file
def load_list_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            players = [line.strip() for line in file if line.strip()]
            if not players:
                print(f"No players found in the file: {file_path}")
            return players
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return []

# Function to detect questions and new player connections in the log file
def detect_fishbot_questions(file_path):
    fishbot_pattern = re.compile(r'\bhey fishbot\b', re.IGNORECASE)
    connected_pattern = re.compile(r'is swimming with us!', re.IGNORECASE)
    with open(file_path, 'r', encoding='latin-1') as file:
        file.seek(0, 2)

        while True:
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue

            recent_lines.append(line.strip())

            if '[Chat]' in line:
                cleaned_line = clean_message(line.strip())
                context_lines.append(cleaned_line)

            if fishbot_pattern.search(line):
                if not any(fishbot_pattern.search(recent_line) for recent_line in recent_lines):
                    print("Q:")

                handle_question_response(clean_message(line.strip()))

            if connected_pattern.search(line):
                for welcome_player in load_list_from_file(welcome_players):
                    if welcome_player.lower() in line.lower():
                        time.sleep(1)
                        welcome_message = f"&eWelcome, {welcome_player}."
                        send_message(welcome_message)
                        break

# Main function
def main():
    try:
        send_online_message()
        send_instructions()  # Send instructions only once at the start

        # Start monitoring the log file
        detect_fishbot_questions(file_path)
    except KeyboardInterrupt:
        print("Script stopped by user.")

if __name__ == "__main__":
    main()

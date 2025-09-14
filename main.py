from skills import process_text
import time

def speak(text):
    """
    Outputs the text directly in the chat.
    """
    if text:
        print(f"JARVIS🤖: {text}")

def process_and_send_command(command_text):
    """
    Processes a given command and outputs the result directly.
    """
    if command_text:
        result = process_text(command_text)
        speak(result)

if __name__ == "__main__":
    print("Jarvis is online!")
    while True:
        command_from_text = input().strip()
        if command_from_text.lower() == 'q':
            print("Shutting down Jarvis.")
            break
        process_and_send_command(command_from_text)
        time.sleep(0.1)

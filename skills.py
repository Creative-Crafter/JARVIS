import subprocess
from datetime import datetime
import pyperclip
import re
import webbrowser
from urllib.parse import urlparse
import dateparser
from ics import Calendar, Event
import tempfile
import os
import requests

def ask_deepseek(prompt: str) -> str:
    try:
        r = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": "deepseek-v2:16b", "prompt": prompt, "stream": False},
            timeout=60
        )
        return r.json().get("response", "").strip() if r.ok else f"Error {r.status_code}: {r.text}"
    except Exception as e:
        return f"Request failed: {e}"

def ask_ollama(prompt: str) -> str:
    try:
        r = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": "alientelligence/jarvisv2", "prompt": prompt, "stream": False},
            timeout=60
        )
        return r.json().get("response", "").strip() if r.ok else f"Error {r.status_code}: {r.text}"
    except Exception as e:
        return f"Request failed: {e}"
    
def ask_deepseekcoder(prompt: str) -> str:
    try:
        r = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": "deepseek-coder-v2:16b", "prompt": prompt, "stream": False},
            timeout=60
        )
        return r.json().get("response", "").strip() if r.ok else f"Error {r.status_code}: {r.text}"
    except Exception as e:
        return f"Request failed: {e}"


def process_text(command):
    command = command.lower()
    print("command: ", command)

    if "time" in command:
        now = datetime.now()
        current_time = now.strftime("%I:%M %p")  # z.B. 03:45 PM
        return f"The current time is {current_time}."

    elif "date" in command:
        today = datetime.now()
        current_date = today.strftime("%A, %B %d, %Y")  # z.B. Tuesday, June 7, 2025
        return f"Today is {current_date}."

    elif "weather" in command:
        return "Sorry, weather functionality is not available right now."

    elif "code" in command or "program" in command:
        print("found code or program word")
        code = ask_deepseekcoder("Do not text me any explanation, only the code. That's what you should make: " + command)
        pyperclip.copy(code)
        new_code = extract_triple_quote_blocks(code)
        return ask_ollama("Describe this code. Only describe it. Code:\n\n" + str(code))

    elif "mail" in command or ("messege" in command and "to" in command):
        mail = ask_deepseek("Only write the messenge . nothing else" + command)
        subject = ask_deepseek("write a very short subject for this email: " + mail)
        webbrowser.open(f"mailto:example@example.com?subject={subject}&body={mail}")
        return mail

    elif "call" in command:
        phone_numbers = extract_all_phone_numbers(command)
        if phone_numbers:
            tel_link = f"tel:{phone_numbers[0]}"
            print("Opening phone link:", tel_link)
            webbrowser.open(tel_link)
            return f"Opening phone app with: {phone_numbers[0]}"
        else:
            return "No phone number found in your command."

    elif "deadline" in command:
        create_and_open_calendar_event(command)
        return "✅ Event created and opened in your calendar app."

    elif "website" in command or "webpage" in command:
        return open_website_from_command(command)

    else:
        return ask_ollama(command)


def extract_triple_quote_blocks(text):
    pattern = r"```([^\n]*)\n(.*?)\n?```"
    matches = re.findall(pattern, text, re.DOTALL)

    code_blocks = []
    for i, (lang, code) in enumerate(matches, 1):
        lang = lang.strip().lower()
        print(lang, code)
        if lang == "python":
            ext = ".py"
        elif lang == "html":
            ext = ".html"
        elif lang in ("js", "javascript"):
            ext = ".js"
        elif lang == "css":
            ext = ".css"
        else:
            ext = ".txt"

        filename = f"codeblock_{i}_{lang}{ext}"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(code.strip())
        print(f"Datei gespeichert: {filename}")
        code_blocks.append(code.strip())

    return code_blocks


def extract_all_phone_numbers(text):
    if not isinstance(text, str):
        raise ValueError("Input must be a string.")
    pattern = r'(?:(?:\+|00)[1-9]\d{0,2})?[\s\-]?(?:\(?\d+\)?[\s\-]?){4,}'
    matches = re.findall(pattern, text)
    return [re.sub(r'[\s\-\(\)]', '', m) for m in matches]


def open_website_from_command(command):
    print("fsdfjas")
    match = re.search(r"https?://[^\s]+", command)

    if match:
        url = match.group(0)
        parsed = urlparse(url)
        domain = parsed.netloc

        chrome_path = "C:/Programme/Google/Chrome/Application/chrome.exe %s"

        try:
            browser = webbrowser.get(chrome_path)
            browser.open(url)
        except webbrowser.Error:
            webbrowser.open(url)

        return "Successfully opened: " + domain


def extract_event_details(command):
    title_match = re.search(r"(name it|called)\s+(.*?)[\.\n]?$", command, re.IGNORECASE)
    title = title_match.group(2).strip() if title_match else "Untitled Event"

    time_match = re.search(r"(from|between)\s+(.*?)\s+(to|and)\s+(.*?)([\.\n]|$)", command, re.IGNORECASE)
    if not time_match:
        return None

    start_time_str = time_match.group(2).strip()
    end_time_str = time_match.group(4).strip()

    date_match = re.search(r"(on\s+\w+ \d+|tomorrow|today|next \w+)", command, re.IGNORECASE)
    date_context = date_match.group(0) if date_match else "today"

    start_dt = dateparser.parse(f"{date_context} at {start_time_str}")
    end_dt = dateparser.parse(f"{date_context} at {end_time_str}")

    if not start_dt or not end_dt:
        return None

    return {
        "title": title,
        "start_dt": start_dt,
        "end_dt": end_dt
    }


def create_and_open_calendar_event(command):
    event_data = extract_event_details(command)
    if not event_data:
        print("⚠️  Could not extract event details.")
        return

    cal = Calendar()
    e = Event()
    e.name = event_data["title"]
    e.begin = event_data["start_dt"]
    e.end = event_data["end_dt"]
    cal.events.add(e)

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ics")
    filepath = tmp_file.name
    tmp_file.close()

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(str(cal))

    print(f"📂 Created calendar file: {filepath}")

    if os.name == "nt":  # Windows
        os.startfile(filepath)
    elif os.uname().sysname == "Darwin":  # macOS
        os.system(f"open '{filepath}'")
    else:  # Linux
        os.system(f"xdg-open '{filepath}'")

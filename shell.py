import requests
import sys
import time
import threading
import signal
import re
import subprocess
import configparser

# flag for mode switching
useLLM = True

# initialize config.ini
config = configparser.ConfigParser()
config.read("config.ini")

url = "http://" + config["settings"]["host"] + ":" + config["settings"]["port"] + "/generate"  # Server URL

def handle_exit_signal(signal, frame):
    print("\nExiting...")
    sys.exit(0)

def generate_text(input_text, max_length=50, temperature=0.7, top_k=50):
    # Prepare the data for the POST request
    payload = {
        "text": input_text,
        # "max_length": max_length,
        # "temperature": temperature,
        # "top_k": top_k
    }

    # Send POST request to the Flask server
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("generated_text")
        else:
            return f"Error: {response.status_code}, {response.text}"
    
    except requests.exceptions.RequestException as e:
        return f"Error during request: {str(e)}"

def show_loader(stop_event):
    # Show a simple loading spinner
    while not stop_event.is_set():
        for spinner in ['|', '/', '-', '\\']:
            sys.stdout.write(f'\rLoading... {spinner}')
            sys.stdout.flush()
            time.sleep(0.1)

def parse_command(generated_text):
    pattern = r"```(?:cmd|bash|shell|powershell)?(.*?)```"
    match = re.search(pattern, generated_text, re.DOTALL)  # Use re.DOTALL to match across newlines
    command = match.group(1).strip() if match else None
    return command

# to do: handle <None> command
def run_command(command):
    result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if(result.stdout):
        print(f"\n{result.stdout}")
    if(result.stderr):
        print(f"Errors:\n{result.stderr}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit_signal)
    print("Welcome to the first intelligent terminal!")
    print("- Type 'exit' to quit.")
    print("- Type 'manual' for executing shell commands directly.")
    print("- Type 'assist' for magic.")

    while True:
        try:
            input_text = input("$ ").strip()

            if input_text.lower() == "exit":
                print("Exiting...")
                break
            
            # handle blank spaces
            if input_text == "":
                print("There are other keys as well you know.")
                continue

            if input_text.lower() == "manual":
                print("Starting manual mode...")
                useLLM = False
                continue

            if input_text.lower() == "assist":
                print("Starting assisted mode...")
                useLLM = True
                continue
            
            if useLLM:
                stop_event = threading.Event()
                loader_thread = threading.Thread(target=show_loader, args=(stop_event,))
                loader_thread.start()

                input_text = "Give the linux command to " + input_text 
                generated_text = generate_text(input_text, max_length=100, temperature=0.8, top_k=50)

                stop_event.set()
                loader_thread.join()

                sys.stdout.write("\r")  # Clear the loading spinner
                sys.stdout.flush()

                command = parse_command(generated_text)

                # print(generated_text)
                skip = input(f"The following command will be executed: <{command}>")
                if skip != "":  # If user pressed anything other than Enter
                    print("Cool you the human here.")
                    continue

                run_command(command)

            # directly run shell command that user provides
            else:
                run_command(input_text)

        except KeyboardInterrupt:
            # Catch the Ctrl+C signal and exit
            handle_exit_signal(None, None)

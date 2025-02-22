import requests
url = "http://localhost:5000/generate"  # Server URL
import sys
import time
import threading
import signal
import re
import subprocess



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

def run_command(command):
    result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if(result.stdout):
        print(f"\n{result.stdout}")
    if(result.stderr):
        print(f"Errors:\n{result.stderr}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit_signal)
    print("Welcome to the first intelligent terminal!")
    print("Type 'exit' to quit.")

    while True:
        try:
            input_text = input("$ ")

            if input_text.lower() == "exit":
                print("Exiting...")
                break
            
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

        except KeyboardInterrupt:
            # Catch the Ctrl+C signal and exit
            handle_exit_signal(None, None)
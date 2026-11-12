"""Watchdog script to run the Dragon S1 agent and restart it if it crashes."""
import subprocess
import time
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [Watchdog] %(message)s")

def main():
    agent_script = "main.py"
    while True:
        logging.info(f"Starting {agent_script}...")
        try:
            process = subprocess.Popen([sys.executable, agent_script])
            process.wait()
            
            if process.returncode != 0:
                logging.warning(f"Agent crashed with exit code {process.returncode}. Restarting in 5 seconds...")
                time.sleep(5)
            else:
                logging.info("Agent exited normally.")
                break
        except Exception as e:
            logging.error(f"Error starting agent: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()

from imports.email_multiple_helper import *

from datetime import datetime
import os
import sys
import signal

print(f"\n\n\n\n\n{datetime.now()} : {os.path.basename(__file__)} has been initiated.\n")


try:
    for retry in range(max_retries):
        observer = None # This ensures that the observer variable exists incase the script exits before it is properly set,
                        # allowing the "finally" block to check if the observer has been set
        try:
            LOCK_FILE = "/tmp/email_watcher.lock"

            def sig_handler(signum, frame):
                sys.exit(0)

            signal.signal(signal.SIGINT, sig_handler)   # For Ctrl+C or kill -SIGINT
            signal.signal(signal.SIGTERM, sig_handler)

            # Checks if this script is already a running process
            if os.path.exists(LOCK_FILE):
                print(f"{datetime.now()} : Observer already running. Exiting.\n")
                sys.exit(0)


            # Set up and start observer
            if __name__ == "__main__":
                print(f"{datetime.now()} : Watching folder : {WATCHED_FOLDER} for new PDFs...\n")
                event_handler = PDFHandler()
                observer = Observer()
                observer.schedule(event_handler, WATCHED_FOLDER, recursive=False)
                observer.start()
                open(LOCK_FILE, "w").close() # Only once watchdog starts successfully does the file lock enable, preventing more than one 
                                             # version of this script to run concurrently (avoids sending duplicate emails)

                while observer.is_alive():
                    time.sleep(1)

        except Exception:
            if observer:
                observer.stop()
                observer.join()
            time.sleep(retry_delay)
            print(f"{datetime.now()} : Attempt no. {retry+1} failed, trying again...\n")

            if retry == max_retries - 1:
                print(f"{datetime.now()} : Maximum retries have been reached, aborting script...\n\n\n\n\n")
                sys.exit(2)
            continue

finally:
    if observer:
        observer.stop()
        observer.join()

    # Once the script exits, remove the file lock (if it has been set)
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
    

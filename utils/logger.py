import logging

# Configure logging
logging.basicConfig(
    filename="chatbot_logs.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def log_event(message, level="INFO"):
    """Logs messages for debugging and performance tracking."""
    if level == "INFO":
        logging.info(message)
    elif level == "WARNING":
        logging.warning(message)
    elif level == "ERROR":
        logging.error(message)

if __name__ == "__main__":
    log_event("Chatbot started successfully.")

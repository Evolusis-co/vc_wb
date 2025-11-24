"""
Simple startup script for Web Chatbot without debug reloader
"""
import os
import sys

# Disable Flask debug mode to prevent reloader issues
os.environ['FLASK_DEBUG'] = 'false'

# Change to chatbot directory
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_chatbot-main'))

# Import and run
from app import app, logger

if __name__ == '__main__':
    port = 5001
    logger.info("=" * 60)
    logger.info("🚀 Starting Web Chatbot Application")
    logger.info("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False
    )

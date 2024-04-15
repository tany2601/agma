# Clone the Repository
git clone https://github.com/myselflohith/firebase_data.git

# Create a Virtual Environment
cd <project-directory>
python -m venv .venv

# Activate the Virtual Environment
# On Windows
cd .venv\Scripts
.\activate

# On macOS/Linux
source .venv/bin/activate

# Install Required Libraries
pip install -r requirements.txt

# Run the Cron Job Script
python cronjob.py &

# Run the Flask Application
python app.py &

# Update Environment Variables
# Open the .env file and update the variables according to your environment.

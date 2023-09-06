help:
    @echo "Interact with the database and models.\n"
    @echo "Commands:"
    @echo "  isntall  Install Python dependencies."
    @echo "  describe  Describe the status of the database and models."
    @echo "  setup  Setup the database and models."

install:
    @pip install -r requirements.txt

describe:
    @python cli/main.py database describe
    @python cli/main.py models describe

setup:
    @python cli/main.py database create
    @python cli/main.py database write
    @python cli/main.py models create
    @python cli/main.py models write

delete:
    @python cli/main.py database delete
    @python cli/main.py models delete

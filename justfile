# uncomment to load .env file
# set dotenv-load

# run server
run:
    (cd ..; source ditto/bin/activate; cd nlp_server; python main.py)

# create venv and install requirements
install:
    (cd ..; python -m venv ditto; source ditto/bin/activate; cd nlp_server; pip install -r requirements.txt)

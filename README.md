# Columbia-CSEE-W4119

## Running the Streamlit Application (DEV)

1. To run the application, create a virtual environment using `python3 -m venv venv`
2. Activate the virtual environment. For Mac users: `source venv/bin/activate`
3. Install project dependencies from the root repository. For Mac users: `pip install -r requirements.txt`.
4. Run the Streamlit Application. Note that `client_ui.py` contains the UI and `client.py` will serve as the main entry point for the client side application. Run the following command `streamlit run client.py <peer.py port> <streamlit_ui_port> <addr> <tracker_port> <addr>`.

   Example: `streamlit run client.py 8080 8081 127.0.0.1 8000 127.0.0.1`

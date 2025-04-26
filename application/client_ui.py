
import streamlit as st

class ClientUi:
    def __init__(self, port, address, peer=None):
        self.port = port
        self.address = address
        self.peer = peer

    def run_ui(self):
        st.title("Decentralized Voting App")
        
        # Only display the possible options 
        if not self.peer.options:
            st.spinner(text="Awaiting ballot from tracker...")
        else: 
            self.display_blockchain()
            self.display_voting_options(self.peer.options)
    
    def display_blockchain(self):
        return

    def display_voting_options(self, options):
        # options can be a list of options
        with st.form("ballot"):
            st.write("Cast your vote:")

            voter_id = st.text_input("Enter your vote ID:")
            selected_candidate = st.pills("Select candidate:", options, selection_mode = "single")

            submitted = st.form_submit_button("Submit")
            if submitted:
                st.success('Ballot submitted. Initiating mining + broadcaasting...', icon=":material/check:")
                # self.peer.submit_vote(vote_id, canadiate_id) 

# Below is only for testing purposes during development
if __name__ == '__main__':
    client_ui = ClientUi()
    client_ui.run_ui()
    
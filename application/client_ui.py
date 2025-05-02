import streamlit as st
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from blockchain_layer.transaction import Transaction

class ClientUi:
    def __init__(self):
        pass

    def run_ui(self):

        st.set_page_config(
            page_title="Decentralized Voting App",
            page_icon="🗳️",
        )
        
        st.title(":orange[:material/How_To_Vote: Decentralized Voting App]")
        st.subheader("Secure Peer-to-Peer Blockchain Voting")

        with st.container():
            col1, col2 = st.columns(2)
            with col1: 
                st.markdown("""
                            Voters can submit ballots securely through a peer-to-peer (P2P) blockchain network with this app. 
                            Ballots are requested from a server. 
                            Each vote is recorded as a block, mined, added to the local blockchain, and broadcasted to all peers.""")
            with col2:
                st.markdown("""
                            <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
                            <ul style="list-style-type: none; padding-left: 0;">
                                <li><span class="material-icons" style="vertical-align: middle;">ballot</span>  Cast your vote securely and anonymously.</li>
                                <li><span class="material-icons" style="vertical-align: middle;">polyline</span>  View the local blockchain of votes.</li>
                                <li><span class="material-icons" style="vertical-align: middle;">query_stats</span>  See real-time aggregated voting results.</li>
                            </ul>
                            """, unsafe_allow_html=True)

        st.write('')

        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1: 
                st.write(f"**Peer Port:** {st.session_state['client'].peer_port}")
            with col2:
                st.write(f"**Peer IP Address:** {st.session_state['client'].peer_addr}")

        self.display_blockchain()
            
        col1, col2 = st.columns(2)
        with st.container():
            with col1:
                self.display_total_votes()
            with col2:
                self.display_voting_options()

    @st.fragment(run_every="0.5s")
    def display_total_votes(self):
        with st.container(border=True):
            st.write("**:material/Query_Stats: Total votes**")

            votes = st.session_state['client'].peer.blockchain
            if not votes: 
                st.info("No votes yet.")
                return

            df = pd.DataFrame({
                'Candidates': list(votes.keys()),
                'Votes': list(votes.values())
            })

            st.bar_chart(df.set_index('Candidates'), horizontal = True, color=['#fb6c56'])

    @st.fragment(run_every="0.5s")
    def display_blockchain(self):
        hex_colors = ['#555555','#ff4b4b'] # Gray, Orange

        with st.container(border=True):

            st.write("**:material/Polyline: Local Blockchain**")

            blockchain_data = st.session_state['client'].peer.blockchain_obj.get_chain_data()
            if not blockchain_data:
                st.info("Blockchain is empty.")
                return

            blockchain_html = """<div style="display: flex; overflow-x: auto; padding: 1rem;">"""
            for i, block_data in enumerate(blockchain_data):
                block_html = self.get_block_html(block_data, hex_colors[i%2], hex_colors[(i+1)%2])
                blockchain_html += block_html
                if i < len(blockchain_data) - 1: # Add lines between blocks
                    blockchain_html += """
<div style='flex: 0 0 auto; width: 20px; height: 2.5px; background-color: #ccc; margin: 0 0.5rem; align-self: center;'></div>
"""

            blockchain_html += "</div>"
            # Render
            st.markdown(blockchain_html, unsafe_allow_html=True)
    
    def get_block_html(self, block, prev_hash_color, hash_color):

        # TODO: Add in the transaction information
        return f"""
<div style='flex: 0 0 auto; width: 200px; border: 0px solid #ccc; padding: 1rem; border-radius: 12.5px; background-color: #f0f2f6;'>
    <p><b>Block {block['index']}</b></p>
    <p><b>Timestamp:</b> {block['timestamp']}</p>
    <p><b>Nonce:</b> {block['nonce']}</p>
    <p><b>Prev Hash:</b> <span style='color: {prev_hash_color};'>{block['previous_hash']}</span></p>
    <p><b>Curr Hash:</b> <span style='color: {hash_color};'>{block['hash']}</span></p>
</div>
        """
    
    def display_voting_options(self):
        options = st.session_state['client'].ballot_options # list of options

        with st.form("ballot"):
            st.write("**:material/Ballot: Cast your vote**")

            voter_id = st.text_input("Enter your vote ID:")
            selected_candidate = st.pills("Select candidate:", options, selection_mode = "single")

            if not options:
                st.info("Awaiting ballot options...")

            submitted = st.form_submit_button("Submit")
            if submitted:
                if not options:
                    st.error("Ballot not available yet.")
                elif not voter_id:
                    st.error("Voter ID is required.")
                elif not selected_candidate:
                    st.error("Select a candidate.")
                else:
                    st.toast('Ballot submitted. Initiating mining + broadcasting...', icon=":material/check:")
                    transaction = Transaction(voter_id, selected_candidate)
                    # TODO: Submit the vote
                    st.session_state['client'].peer.submit_vote(transaction) 

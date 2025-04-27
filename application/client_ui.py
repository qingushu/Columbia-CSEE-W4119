import streamlit as st
import pandas as pd
import time 

class ClientUi:
    def __init__(self, peer_port, peer_addr, ballot_options=None, blockchain=None, peer=None):
        self.peer_port = peer_port
        self.peer_addr = peer_addr
        self.ballot_options = ballot_options
        self.blockchain = blockchain
        self.peer = peer

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
        # self.ballot_options = None

        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1: 
                st.write(f"**Peer Port:** {self.peer_port}")
            with col2:
                st.write(f"**Peer IP Address:** {self.peer_addr}")
        while not self.ballot_options:
            with st.spinner(text="Awaiting ballot from tracker..."):
                time.sleep(100) # Run spinner until ballot arrives
        else: 
            with st.container(border=True):
                self.display_blockchain()
            
            col1, col2 = st.columns(2)
            with st.container():
                with col1:
                    with st.container(border=True):
                        self.display_total_votes()
                with col2:
                    self.display_voting_options(self.ballot_options)
        
    def display_total_votes(self):
        st.write("**:material/Query_Stats: Total votes**")
        # TODO: Remove dummy block chain once ready
        # votes = self.blockchain.get_vote_count()  # returns a dict of all ballot options and their vote counts based on the blockchain
        dummy_votes = {
            'A' : 3,
            'B' : 4,
            'C' : 2,
        }

        # votes = None    
        votes = dummy_votes 
        if not votes: 
            st.info("No votes yet.")
            return

        df = pd.DataFrame({
            'Candidates': list(votes.keys()),
            'Votes': list(votes.values())
        })

        st.bar_chart(df.set_index('Candidates'), horizontal = True, color=['#fb6c56'])

    def display_blockchain(self):
        hex_colors = ['#555555','#ff4b4b'] # Gray, Orange

        st.write("**:material/Polyline: Local Blockchain**")

        dummy_blockchain = [
            {
                'index': 0,
                'voter_id': '12345',
                'selected_candidate': 'Alice',
                'previous_hash': None,
                'hash': 'abcd1234'
            },
            {
                'index': 1,
                'voter_id': '67890',
                'selected_candidate': 'Bob',
                'previous_hash': 'abcd1234',
                'hash': 'efgh5678'
            },
            {
                'index': 2,
                'voter_id': '54321',
                'selected_candidate': 'Charlie',
                'previous_hash': 'efgh5678',
                'hash': 'ijkl91011'
            },
            {
                'index': 3,
                'voter_id': '98765',
                'selected_candidate': 'Alice',
                'previous_hash': 'ijkl91011',
                'hash': 'mnop1213'
            },
            {
                'index': 4,
                'voter_id': '19283',
                'selected_candidate': 'Bob',
                'previous_hash': 'mnop1213',
                'hash': 'qrst1415'
            },
            {
                'index': 5,
                'voter_id': '74829',
                'selected_candidate': 'Charlie',
                'previous_hash': 'qrst1415',
                'hash': 'uvwx1617'
            }
        ]

        self.blockchain = dummy_blockchain

        if not self.blockchain:
            st.info("Blockchain is empty.")
            return

        blockchain_html = """<div style="display: flex; overflow-x: auto; padding: 1rem;">"""

        for i, block_data in enumerate(self.blockchain):
            block_html = self.get_block_html(block_data, hex_colors[i%2], hex_colors[(i+1)%2])
            blockchain_html += block_html
            if i < len(self.blockchain) - 1: # Add lines between blocks
                blockchain_html += """
<div style='flex: 0 0 auto; width: 20px; height: 2.5px; background-color: #ccc; margin: 0 0.5rem; align-self: center;'></div>
"""

        blockchain_html += "</div>"
        # Render
        st.markdown(blockchain_html, unsafe_allow_html=True)
    
    def get_block_html(self, block, prev_hash_color, hash_color):

        return f"""
<div style='flex: 0 0 auto; width: 200px; border: 0px solid #ccc; padding: 1rem; border-radius: 12.5px; background-color: #f0f2f6;'>
    <p><b>Block {block['index']}</b></p>
    <p><b>Voter ID:</b> {block['voter_id']}</p>
    <p><b>Candidate:</b> {block['selected_candidate']}</p>
    <p><b>Prev Hash:</b> <span style='color: {prev_hash_color};'>{block['previous_hash']}</span></p>
    <p><b>Curr Hash:</b> <span style='color: {hash_color};'>{block['hash']}</span></p>
</div>
        """
    
    def display_voting_options(self, options):
        # options can be a list of options
        with st.form("ballot"):
            st.write("**:material/Ballot: Cast your vote**")

            voter_id = st.text_input("Enter your vote ID:")
            selected_candidate = st.pills("Select candidate:", options, selection_mode = "single")

            submitted = st.form_submit_button("Submit")
            if submitted:
                if not voter_id:
                    st.error("Voter ID is required.")
                elif not selected_candidate:
                    st.error("Select a candidate.")
                else:
                    st.success('Ballot submitted. Initiating mining + broadcaasting...', icon=":material/check:")
                # self.peer.submit_vote(vote_id, selected_candidate) 

from flask import Flask, render_template, request, redirect, url_for, session, flash
import secrets
import decimal
import hashlib
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key

# Blockchain and Wallet logic
decimal.getcontext().prec = 18
DIFFICULTY = 4
TOTAL_SUPPLY = decimal.Decimal(10_000_000)
MINING_REWARD = decimal.Decimal(50)
UNLOCKED_SUPPLY = decimal.Decimal(1_000_000)

class Transaction:
    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = decimal.Decimal(amount)
        self.timestamp = time.time()

    def to_dict(self):
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': str(self.amount),
            'timestamp': self.timestamp
        }

class Block:
    def __init__(self, previous_hash, transactions, nonce=0):
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = None

    def compute_hash(self):
        block_string = str({
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine_block(self, difficulty):
        self.nonce = 0
        computed_hash = self.compute_hash()
        while not computed_hash.startswith('0' * difficulty):
            self.nonce += 1
            computed_hash = self.compute_hash()
        self.hash = computed_hash

    def finalize_block(self, difficulty):
        self.mine_block(difficulty)

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_supply = UNLOCKED_SUPPLY
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(previous_hash="0", transactions=[])
        genesis_block.finalize_block(DIFFICULTY)
        self.chain.append(genesis_block)

    def add_block(self, transactions, miner_wallet):
        previous_hash = self.chain[-1].hash
        new_block = Block(previous_hash=previous_hash, transactions=transactions)
        new_block.finalize_block(DIFFICULTY)

        if self.is_valid_block(new_block):
            self.chain.append(new_block)
            self.reward_miner(miner_wallet)
            return True
        return False

    def reward_miner(self, miner_wallet):
        if self.current_supply < TOTAL_SUPPLY:
            reward = min(MINING_REWARD, TOTAL_SUPPLY - self.current_supply)
            miner_wallet.deposit(reward)
            self.current_supply += reward

    def is_valid_block(self, block):
        return block.hash.startswith('0' * DIFFICULTY) and block.hash == block.compute_hash()

    def display_chain(self):
        chain_info = ""
        for block in self.chain:
            chain_info += f"Block Hash: {block.hash}\n"
            chain_info += f"Previous Hash: {block.previous_hash}\n"
            chain_info += "Transactions:\n"
            for tx in block.transactions:
                chain_info += f"  {tx.to_dict()}\n"
            chain_info += "-" * 30 + "\n"
        return chain_info

class Wallet:
    def __init__(self, full_name, public_key, private_key, balance=0):
        self.full_name = full_name
        self.public_key = public_key
        self.private_key = private_key
        self.balance = decimal.Decimal(balance)

    def deposit(self, amount):
        self.balance += decimal.Decimal(amount)

    def withdraw(self, amount):
        if decimal.Decimal(amount) > self.balance:
            return False
        self.balance -= decimal.Decimal(amount)
        return True

    def check_credentials(self, public_key, private_key):
        return self.public_key == public_key and self.private_key == private_key

def generate_key_pair():
    public_key = secrets.token_hex(16)
    private_key = secrets.token_hex(32)
    return public_key, private_key

def transfer_funds(sender, receiver, amount, blockchain):
    if sender.withdraw(amount):
        receiver.deposit(amount)
        transaction = Transaction(sender=sender.public_key, receiver=receiver.public_key, amount=amount)
        if blockchain.add_block([transaction], miner_wallet=sender):
            return True
    return False

# Initialize Blockchain and Wallets
blockchain = Blockchain()

# Abacus Wallet Initialization
abacus_wallet = Wallet(
    full_name="Abacus Wallet",
    public_key="84a1651a95e3e92d6b4dfb3e0e79fdb5",
    private_key="d97f0af4e834c5ae82f2ed6b962b952259f5c810f3b14cf6528dd06ae9aed599",
    balance=1_000_000
)
wallets = [abacus_wallet]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        public_key = request.form['public_key']
        private_key = request.form['private_key']
        global logged_in_wallet
        logged_in_wallet = None
        for wallet in wallets:
            if wallet.check_credentials(public_key, private_key):
                logged_in_wallet = wallet
                session['public_key'] = public_key
                return redirect(url_for('user_menu'))
        flash("Invalid Public Key or Private Key.")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form['full_name']
        public_key, private_key = generate_key_pair()
        new_wallet = Wallet(full_name=full_name, public_key=public_key, private_key=private_key, balance=0)
        wallets.append(new_wallet)
        flash(f"Account created. Public Key: {public_key}, Private Key: {private_key}. Save these keys securely!")
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/user_menu')
def user_menu():
    if 'public_key' not in session:
        return redirect(url_for('index'))
    wallet = find_wallet_by_public_key(session['public_key'])
    return render_template('user_menu.html', wallet=wallet)

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if request.method == 'POST':
        recipient_public_key = request.form['recipient_public_key']
        amount = decimal.Decimal(request.form['amount'])
        sender = find_wallet_by_public_key(session['public_key'])
        recipient_wallet = find_wallet_by_public_key(recipient_public_key)
        if recipient_wallet and transfer_funds(sender, recipient_wallet, amount, blockchain):
            flash(f"Successfully transferred {amount} ABCs to {recipient_wallet.full_name}.")
        else:
            flash("Transfer failed. Check recipient wallet and amount.")
    return render_template('transfer.html')

@app.route('/mine')
def mine():
    wallet = find_wallet_by_public_key(session['public_key'])
    if wallet:
        transactions = []
        if blockchain.add_block(transactions, miner_wallet=wallet):
            flash("Block successfully mined!")
        else:
            flash("Mining failed.")
    return redirect(url_for('user_menu'))

@app.route('/view_blockchain')
def view_blockchain():
    chain_info = blockchain.display_chain()
    return render_template('blockchain.html', chain_info=chain_info)

def find_wallet_by_public_key(public_key):
    for wallet in wallets:
        if wallet.public_key == public_key:
            return wallet
    return None

if __name__ == '__main__':
    app.run(debug=True)

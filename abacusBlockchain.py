import tkinter as tk
from tkinter import messagebox, PhotoImage
import secrets
import decimal
import hashlib
import time

# Configure the decimal module for high precision
decimal.getcontext().prec = 18

DIFFICULTY = 4  # Number of leading zeros required in the hash
TOTAL_SUPPLY = decimal.Decimal(10_000_000)  # Total cap of ABCs
MINING_REWARD = decimal.Decimal(50)  # Reward per mined block (can be adjusted)
UNLOCKED_SUPPLY = decimal.Decimal(1_000_000)  # Initially unlocked ABCs

# Define color scheme
BG_COLOR = "#1e2b39"  # Dark Blue
BUTTON_COLOR = "#ff8c00"  # Orange
FONT_COLOR = "#ffffff"  # White
HIGHLIGHT_COLOR = "#ff4500"  # Highlight Orange

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
        self.hash = None  # Initialize with None, will be set after creation

    def compute_hash(self):
        block_string = str({
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine_block(self, difficulty):
        # Mining: finding a hash with a specific number of leading zeros
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

class CryptoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Abacus Cryptocurrency")
        self.root.configure(bg=BG_COLOR)

        # Blockchain and wallets initialization
        self.blockchain = Blockchain()
        self.wallets = []
        self.logged_in_wallet = None

        # Abacus Wallet Initialization
        self.abacus_wallet = Wallet(
            full_name="Abacus Wallet",
            public_key="84a1651a95e3e92d6b4dfb3e0e79fdb5",
            private_key="d97f0af4e834c5ae82f2ed6b962b952259f5c810f3b14cf6528dd06ae9aed599",
            balance=1_000_000
        )
        self.wallets.append(self.abacus_wallet)

        # Load icons/images
        self.logo = PhotoImage(file="logo.png")  # Make sure you have a logo image file
        self.coin_icon = PhotoImage(file="coin.png")  # Make sure you have a coin image file

        # Main Menu
        self.main_menu()

    def main_menu(self):
        self.clear_screen()

        tk.Label(self.root, text="Welcome to Abacus", font=("Helvetica", 24, "bold"), fg=HIGHLIGHT_COLOR, bg=BG_COLOR).pack(pady=20)
        tk.Label(self.root, image=self.logo, bg=BG_COLOR).pack()

        login_button = tk.Button(self.root, text="Log-in", command=self.login_screen, bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 16))
        login_button.pack(pady=10)

        signup_button = tk.Button(self.root, text="Sign up", command=self.signup_screen, bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 16))
        signup_button.pack(pady=10)

        view_blockchain_button = tk.Button(self.root, text="View Blockchain", command=self.view_blockchain, bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 16))
        view_blockchain_button.pack(pady=10)

        exit_button = tk.Button(self.root, text="Exit", command=self.root.quit, bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 16))
        exit_button.pack(pady=10)

    def login_screen(self):
        self.clear_screen()

        tk.Label(self.root, text="Log in to your account", font=("Helvetica", 20, "bold"), fg=HIGHLIGHT_COLOR, bg=BG_COLOR).pack(pady=20)

        tk.Label(self.root, text="Public Key:", font=("Helvetica", 14), fg=FONT_COLOR, bg=BG_COLOR).pack()
        public_key_entry = tk.Entry(self.root)
        public_key_entry.pack(pady=5)

        tk.Label(self.root, text="Private Key:", font=("Helvetica", 14), fg=FONT_COLOR, bg=BG_COLOR).pack()
        private_key_entry = tk.Entry(self.root, show="*")
        private_key_entry.pack(pady=5)

        login_button = tk.Button(self.root, text="Log-in", command=lambda: self.login(public_key_entry.get(), private_key_entry.get()), bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 16))
        login_button.pack(pady=20)

        back_button = tk.Button(self.root, text="Back", command=self.main_menu, bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 14))
        back_button.pack(pady=10)

    def signup_screen(self):
        self.clear_screen()

        tk.Label(self.root, text="Create a new account", font=("Helvetica", 20, "bold"), fg=HIGHLIGHT_COLOR, bg=BG_COLOR).pack(pady=20)

        tk.Label(self.root, text="Full Name:", font=("Helvetica", 14), fg=FONT_COLOR, bg=BG_COLOR).pack()
        name_entry = tk.Entry(self.root)
        name_entry.pack(pady=5)

        signup_button = tk.Button(self.root, text="Sign up", command=lambda: self.create_account(name_entry.get()), bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 16))
        signup_button.pack(pady=20)

        back_button = tk.Button(self.root, text="Back", command=self.main_menu, bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 14))
        back_button.pack(pady=10)

    def create_account(self, full_name):
        if not full_name:
            messagebox.showerror("Error", "Full name is required.")
            return

        public_key, private_key = generate_key_pair()
        new_wallet = Wallet(full_name=full_name, public_key=public_key, private_key=private_key, balance=0)
        self.wallets.append(new_wallet)

        messagebox.showinfo("Account Created", f"Your account has been created.\nPublic Key: {public_key}\nPrivate Key: {private_key}\nSave these keys securely!")
        self.main_menu()

    def login(self, public_key, private_key):
        for wallet in self.wallets:
            if wallet.check_credentials(public_key, private_key):
                self.logged_in_wallet = wallet
                self.user_menu()
                return
        messagebox.showerror("Error", "Invalid Public Key or Private Key.")
        self.login_screen()

    def user_menu(self):
        self.clear_screen()

        tk.Label(self.root, text=f"Welcome, {self.logged_in_wallet.full_name}", font=("Helvetica", 20, "bold"), fg=HIGHLIGHT_COLOR, bg=BG_COLOR).pack(pady=20)
        tk.Label(self.root, image=self.coin_icon, bg=BG_COLOR).pack()

        balance_button = tk.Button(self.root, text="Check Balance", command=self.display_balance, bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 16))
        balance_button.pack(pady=10)

        transfer_button = tk.Button(self.root, text="Transfer ABCs", command=self.transfer_screen, bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 16))
        transfer_button.pack(pady=10)

        view_blockchain_button = tk.Button(self.root, text="View Blockchain", command=self.view_blockchain, bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 16))
        view_blockchain_button.pack(pady=10)

        mine_button = tk.Button(self.root, text="Mine Block", command=self.mine_block, bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 16))
        mine_button.pack(pady=10)

        logout_button = tk.Button(self.root, text="Log-out", command=self.main_menu, bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 16))
        logout_button.pack(pady=10)

    def display_balance(self):
        messagebox.showinfo("Balance", f"Current Balance: {self.logged_in_wallet.balance} ABCs")

    def transfer_screen(self):
        self.clear_screen()

        tk.Label(self.root, text="Recipient's Public Key:", font=("Helvetica", 14), fg=FONT_COLOR, bg=BG_COLOR).pack()
        recipient_entry = tk.Entry(self.root)
        recipient_entry.pack(pady=5)

        tk.Label(self.root, text="Amount to Transfer:", font=("Helvetica", 14), fg=FONT_COLOR, bg=BG_COLOR).pack()
        amount_entry = tk.Entry(self.root)
        amount_entry.pack(pady=5)

        transfer_button = tk.Button(self.root, text="Transfer", command=lambda: self.transfer_funds(recipient_entry.get(), amount_entry.get()), bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 16))
        transfer_button.pack(pady=20)

        back_button = tk.Button(self.root, text="Back", command=self.user_menu, bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 14))
        back_button.pack(pady=10)

    def transfer_funds(self, recipient_public_key, amount):
        recipient_wallet = self.find_wallet_by_public_key(recipient_public_key)
        if recipient_wallet:
            try:
                amount = decimal.Decimal(amount)
                if amount <= 0:
                    raise ValueError
            except:
                messagebox.showerror("Error", "Invalid amount.")
                return

            if transfer_funds(self.logged_in_wallet, recipient_wallet, amount, self.blockchain):
                messagebox.showinfo("Success", f"Successfully transferred {amount} ABCs to {recipient_wallet.full_name}.")
                self.user_menu()
            else:
                messagebox.showerror("Error", "Insufficient funds or transfer failed.")
        else:
            messagebox.showerror("Error", "Recipient wallet does not exist.")

    def mine_block(self):
        if self.logged_in_wallet:
            transactions = []
            if self.blockchain.add_block(transactions, miner_wallet=self.logged_in_wallet):
                messagebox.showinfo("Mining Successful", "Block successfully mined!")
            else:
                messagebox.showerror("Mining Failed", "Mining failed. Try again.")
        self.user_menu()

    def find_wallet_by_public_key(self, public_key):
        for wallet in self.wallets:
            if wallet.public_key == public_key:
                return wallet
        return None

    def view_blockchain(self):
        self.clear_screen()
        chain_info = self.blockchain.display_chain()
        tk.Label(self.root, text=chain_info, justify="left", fg=FONT_COLOR, bg=BG_COLOR, font=("Courier", 12)).pack()

        back_button = tk.Button(self.root, text="Back", command=self.main_menu, bg=BUTTON_COLOR, fg=FONT_COLOR, font=("Helvetica", 14))
        back_button.pack(pady=10)

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoApp(root)
    root.mainloop()

import secrets
import decimal
import hashlib
import time

decimal.getcontext().prec = 18

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
    def __init__(self, previous_hash, transactions):
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.hash = None 

    def compute_hash(self):
        block_string = str({
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash
        }).encode()
        return hashlib.sha256(block_string).hexdigest()

    def finalize_block(self):
        self.hash = self.compute_hash()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(previous_hash="0", transactions=[])
        genesis_block.finalize_block()
        self.chain.append(genesis_block)

    def add_block(self, transactions):
        previous_hash = self.chain[-1].hash
        new_block = Block(previous_hash=previous_hash, transactions=transactions)
        new_block.finalize_block() 
        self.chain.append(new_block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            if current_block.hash != current_block.compute_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True

    def display_chain(self):
        for block in self.chain:
            print(f"Block Hash: {block.hash}")
            print(f"Previous Hash: {block.previous_hash}")
            print("Transactions:")
            for tx in block.transactions:
                print(tx.to_dict())
            print("-" * 30)

class Wallet:
    def __init__(self, name, username, password, public_key=None, private_key=None):
        self.name = name
        self.username = username
        self.password = password
        self.public_key = public_key
        self.private_key = private_key
        self.balance = decimal.Decimal(0)

    def deposit(self, amount):
        self.balance += decimal.Decimal(amount)

    def withdraw(self, amount):
        if decimal.Decimal(amount) > self.balance:
            print(f"Not enough balance in {self.name}.")
            return False
        self.balance -= decimal.Decimal(amount)
        return True

    def check_credentials(self, username, password):
        return self.username == username and self.password == password

def generate_key_pair():
    public_key = secrets.token_hex(16)
    private_key = secrets.token_hex(32)
    return public_key, private_key

def transfer_funds(sender, receiver, amount, blockchain):
    if sender.withdraw(amount):
        receiver.deposit(amount)
        transaction = Transaction(sender=sender.public_key, receiver=receiver.public_key, amount=amount)
        blockchain.add_block([transaction])
        print(f"Transferred {amount} ABCs from {sender.name} to {receiver.name}. Transaction recorded on blockchain.")
    else:
        print(f"Transfer failed. Not enough balance in {sender.name}.")

def display_balance(wallet):
    print(f"{wallet.name} Balance: {wallet.balance} ABCs")

def create_wallet(wallets):
    username = input("Enter username for the new wallet: ").strip()
    password = input("Enter password for the new wallet: ").strip()
    email = input("Enter email for the new wallet: ").strip()

    if any(wallet.username == username for wallet in wallets):
        print("Username already exists. Please choose a different username.")
        return

    public_key, private_key = generate_key_pair()
    new_wallet = Wallet(name=f"Wallet {username}", username=username, password=password, public_key=public_key, private_key=private_key)
    wallets.append(new_wallet)
    print(f"Account created successfully. Public Key: {public_key}")

def find_wallet_by_public_key(wallets, public_key):
    for wallet in wallets:
        if wallet.public_key == public_key:
            return wallet
    return None

def login(wallets):
    logged_in_wallet = None
    while logged_in_wallet is None:
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()
        
        for wallet in wallets:
            if wallet.check_credentials(username, password):
                logged_in_wallet = wallet
                break
        if logged_in_wallet is None:
            print("Invalid credentials, please try again.")
    return logged_in_wallet

def main_menu(wallets, blockchain):
    while True:
        print("Please choose an option:")
        print("1. Log-in")
        print("2. Sign up")
        print("3. View Blockchain")
        print("4. Exit")

        option = input("Enter your choice: ").strip()

        if option == '1':
            logged_in_wallet = login(wallets)
            user_menu(logged_in_wallet, wallets, blockchain)
        elif option == '2':
            create_wallet(wallets)
        elif option == '3':
            blockchain.display_chain()
        elif option == '4':
            return
        else:
            print("Invalid choice. Please try again.")

def user_menu(logged_in_wallet, wallets, blockchain):
    while True:
        print("\nMenu:")
        print("1. Display Balance")
        print("2. Transfer Funds")
        print("3. Logout")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            display_balance(logged_in_wallet)
        elif choice == '2':
            to_public_key = input("Enter the public key of the wallet to transfer to: ").strip()
            to_wallet = find_wallet_by_public_key(wallets, to_public_key)
            
            if to_wallet:
                amount = input(f"Enter amount to transfer from {logged_in_wallet.name} to {to_wallet.name} (e.g., 0.5): ").strip()
                try:
                    transfer_funds(logged_in_wallet, to_wallet, amount, blockchain)
                except decimal.InvalidOperation:
                    print("Invalid amount format. Please enter a valid number.")
            else:
                print("No wallet exists with the provided public key.")
        elif choice == '3':
            print("Logging out...")
            main_menu(wallets, blockchain)
            break
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    blockchain = Blockchain()

    abacus_wallet = Wallet("Wallet Abacus", "abacus", "abacus", public_key="default_abacus_public_key", private_key="default_abacus_private_key")
    
    total_abcs = decimal.Decimal(200000)
    abacus_wallet.deposit(total_abcs)

    wallets = [abacus_wallet]

    main_menu(wallets, blockchain)

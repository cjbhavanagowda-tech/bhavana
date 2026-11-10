

import hashlib
import json
import os
import random
from datetime import datetime

DATA_FILE = "bank_data.json"
MIN_BALANCE = 0  



def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_amount(prompt: str) -> float:
    """Keep asking until a positive number is entered."""
    while True:
        try:
            value = float(input(prompt))
            if value <= 0:
                print("Amount must be greater than zero.")
                continue
            return round(value, 2)
        except ValueError:
            print("Invalid amount. Please enter a number.")



class Transaction:
    def __init__(self, kind, amount, balance_after, note="", timestamp=None):
        self.kind = kind
        self.amount = amount
        self.balance_after = balance_after
        self.note = note
        self.timestamp = timestamp or now()

    def to_dict(self):
        return self.__dict__.copy()

    @staticmethod
    def from_dict(d):
        return Transaction(d["kind"], d["amount"], d["balance_after"],
                           d.get("note", ""), d["timestamp"])

    def __str__(self):
        return (f"{self.timestamp} | {self.kind:<12} | "
                f"{self.amount:>10.2f} | Bal: {self.balance_after:>10.2f} | {self.note}")


class Account:
    def __init__(self, acc_no, name, phone, pin_hash, balance=0.0,
                 transactions=None, created=None):
        self.acc_no = acc_no
        self.name = name
        self.phone = phone
        self.pin_hash = pin_hash
        self.balance = balance
        self.transactions = transactions or []
        self.created = created or now()

    
    def deposit(self, amount):
        self.balance += amount
        self.transactions.append(Transaction("DEPOSIT", amount, self.balance))

    def withdraw(self, amount):
        if self.balance - amount < MIN_BALANCE:
            raise ValueError(
                f"Insufficient funds. Minimum balance of {MIN_BALANCE:.2f} must be maintained.")
        self.balance -= amount
        self.transactions.append(Transaction("WITHDRAWAL", amount, self.balance))

    def transfer_out(self, amount, to_acc):
        if self.balance - amount < MIN_BALANCE:
            raise ValueError(
                f"Insufficient funds. Minimum balance of {MIN_BALANCE:.2f} must be maintained.")
        self.balance -= amount
        self.transactions.append(
            Transaction("TRANSFER OUT", amount, self.balance, f"To {to_acc}"))

    def transfer_in(self, amount, from_acc):
        self.balance += amount
        self.transactions.append(
            Transaction("TRANSFER IN", amount, self.balance, f"From {from_acc}"))

    def check_pin(self, pin):
        return self.pin_hash == hash_pin(pin)

    
    def to_dict(self):
        return {
            "acc_no": self.acc_no, "name": self.name, "phone": self.phone,
            "pin_hash": self.pin_hash, "balance": self.balance,
            "created": self.created,
            "transactions": [t.to_dict() for t in self.transactions],
        }

    @staticmethod
    def from_dict(d):
        return Account(d["acc_no"], d["name"], d["phone"], d["pin_hash"],
                       d["balance"],
                       [Transaction.from_dict(t) for t in d["transactions"]],
                       d["created"])


class Bank:
    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.accounts = {}
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    data = json.load(f)
                self.accounts = {k: Account.from_dict(v) for k, v in data.items()}
            except (json.JSONDecodeError, KeyError):
                print("Warning: data file corrupted. Starting with empty data.")
                self.accounts = {}

    def save(self):
        with open(self.filename, "w") as f:
            json.dump({k: a.to_dict() for k, a in self.accounts.items()}, f, indent=2)

    def generate_acc_no(self):
        while True:
            acc_no = str(random.randint(10**9, 10**10 - 1))
            if acc_no not in self.accounts:
                return acc_no

    def register(self, name, phone, pin, opening_deposit):
        acc_no = self.generate_acc_no()
        acc = Account(acc_no, name, phone, hash_pin(pin))
        acc.deposit(opening_deposit)
        acc.transactions[-1].note = "Opening deposit"
        self.accounts[acc_no] = acc
        self.save()
        return acc

    def login(self, acc_no, pin):
        acc = self.accounts.get(acc_no)
        if acc and acc.check_pin(pin):
            return acc
        return None

    def transfer(self, sender, to_acc_no, amount):
        receiver = self.accounts.get(to_acc_no)
        if receiver is None:
            raise ValueError("Receiver account not found.")
        if receiver.acc_no == sender.acc_no:
            raise ValueError("Cannot transfer to your own account.")
        sender.transfer_out(amount, to_acc_no)
        receiver.transfer_in(amount, sender.acc_no)
        self.save()



def register_customer(bank):
    print("\n--- Customer Registration ---")
    name = input("Full name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return
    phone = input("Phone (10 digits): ").strip()
    if not (phone.isdigit() and len(phone) == 10):
        print("Invalid phone number.")
        return
    pin = input("Set 4-digit PIN: ").strip()
    if not (pin.isdigit() and len(pin) == 4):
        print("PIN must be exactly 4 digits.")
        return
    opening = read_amount(f"Opening deposit (min {MIN_BALANCE:.2f}): ")
    if opening < MIN_BALANCE:
        print("Opening deposit below the minimum balance.")
        return
    acc = bank.register(name, phone, pin, opening)
    print(f"\nAccount created successfully! Your account number is {acc.acc_no}")


def account_menu(bank, acc):
    while True:
        print(f"\n--- Welcome, {acc.name} (A/C {acc.acc_no}) ---")
        print("1. Account Details\n2. Deposit\n3. Withdraw\n4. Fund Transfer")
        print("5. Mini Statement (last 5)\n6. Transaction History\n7. Change PIN\n8. Logout")
        choice = input("Choose: ").strip()
        try:
            if choice == "1":
                print(f"Name: {acc.name}\nAccount No: {acc.acc_no}\nPhone: {acc.phone}")
                print(f"Opened: {acc.created}\nBalance: {acc.balance:.2f}")
            elif choice == "2":
                acc.deposit(read_amount("Amount to deposit: "))
                bank.save()
                print(f"Deposited. New balance: {acc.balance:.2f}")
            elif choice == "3":
                acc.withdraw(read_amount("Amount to withdraw: "))
                bank.save()
                print(f"Please collect your cash. New balance: {acc.balance:.2f}")
            elif choice == "4":
                to = input("Receiver account number: ").strip()
                bank.transfer(acc, to, read_amount("Amount to transfer: "))
                print(f"Transfer successful. New balance: {acc.balance:.2f}")
            elif choice == "5":
                print("\n--- Mini Statement ---")
                for t in acc.transactions[-5:]:
                    print(t)
            elif choice == "6":
                print("\n--- Transaction History ---")
                for t in acc.transactions:
                    print(t)
            elif choice == "7":
                old = input("Current PIN: ").strip()
                if not acc.check_pin(old):
                    print("Incorrect PIN.")
                    continue
                new = input("New 4-digit PIN: ").strip()
                if new.isdigit() and len(new) == 4:
                    acc.pin_hash = hash_pin(new)
                    bank.save()
                    print("PIN changed.")
                else:
                    print("PIN must be exactly 4 digits.")
            elif choice == "8":
                print("Logged out.")
                return
            else:
                print("Invalid choice.")
        except ValueError as e:
            print(f"Error: {e}")


def main():
    bank = Bank()
    while True:
        print("\n===== ONLINE BANKING SYSTEM =====")
        print("1. Register\n2. Login\n3. Exit")
        choice = input("Choose: ").strip()
        if choice == "1":
            register_customer(bank)
        elif choice == "2":
            acc_no = input("Account number: ").strip()
            pin = input("PIN: ").strip()
            acc = bank.login(acc_no, pin)
            if acc:
                account_menu(bank, acc)
            else:
                print("Invalid account number or PIN.")
        elif choice == "3":
            print("Thank you for banking with us!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()

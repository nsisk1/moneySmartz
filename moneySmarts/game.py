import os
import random
import logging
import sys  # added for interactivity check
import pygame
from moneySmarts.models import Player, BankAccount, Card, Loan, Asset
from moneySmarts.event_manager import EventBus
from moneySmarts.config_manager import Config
from moneySmarts.exceptions import GameError, BankAccountError
from moneySmarts.utils import compute_net_worth
from moneySmarts.quest import QuestManager  # NEW
from moneySmarts.cloud_storage import get_storage, LocalFileStorage

SAVEGAME_VERSION = 1

# --- Random event effect helpers ---
def tax_refund_effect():
    return random.randint(100, 1000)

def birthday_gift_effect():
    return random.randint(20, 200)

def found_money_effect():
    return random.randint(5, 50)

def bonus_effect(game):
    return int(game.player.salary * random.uniform(0.01, 0.1)) if game.player.salary else 0

def car_repair_effect(game):
    return -random.randint(100, 2000) if any(a.asset_type == "Car" for a in game.player.assets) else 0

def medical_bill_effect():
    return -random.randint(50, 5000)

def lost_wallet_effect(game):
    return -min(50, game.player.cash)

def phone_repair_effect():
    return -random.randint(50, 300)

# --- Console helpers ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_choice(prompt, choices):
    print("\n{prompt}")
    for i, c in enumerate(choices):
        print("{i+1}. {c}")
    sel = 0
    while sel < 1 or sel > len(choices):
        try:
            # noinspection PyCompatibility
            sel = int(input(f"Enter choice (1-{len(choices)}): "))
        except ValueError:
            print("Enter a valid number.")
    return choices[sel-1]

class Game:
    def __init__(self):
        self.player = None
        self.current_month = 1
        self.current_year = 0  # offset from 2023
        self.game_over = False
        self.events = self.initialize_events()
        self.gui_manager = None
        self.paused = False
        self.quests = QuestManager(self)  # NEW quest manager
        self.quest_notifications = []  # recent completed quest titles
        self.met_mentor = False  # NPC mentor interaction flag

    # Convenience wrapper so quests can call net worth
    def compute_net_worth(self):
        if not self.player:
            return 0
        return compute_net_worth(self.player)

    # --- Event setup ---
    def initialize_events(self):
        return {
            "positive": [
                {"name": "Tax Refund", "description": "You received a tax refund!", "cash_effect": tax_refund_effect},
                {"name": "Birthday Gift", "description": "You received money as a birthday gift!", "cash_effect": birthday_gift_effect},
                {"name": "Found Money", "description": "You found money on the ground!", "cash_effect": found_money_effect},
                {"name": "Bonus", "description": "You received a bonus at work!", "cash_effect": lambda: bonus_effect(self)},
            ],
            "negative": [
                {"name": "Car Repair", "description": "Your car needs repairs.", "cash_effect": lambda: car_repair_effect(self)},
                {"name": "Medical Bill", "description": "Unexpected medical expenses.", "cash_effect": medical_bill_effect},
                {"name": "Lost Wallet", "description": "You lost your wallet!", "cash_effect": lambda: lost_wallet_effect(self)},
                {"name": "Phone Repair", "description": "Phone screen cracked.", "cash_effect": phone_repair_effect},
            ]
        }

    # --- Text mode start ---
    def start_game(self):
        clear_screen()
        print("="*60)
        print("WELCOME TO MONEY SMARTZ")
        print("="*60)
        try:
            name = input("Enter your name: ").strip()
            if not name:
                raise GameError("Name cannot be empty")
            self.player = Player(name)
        except Exception as e:
            logging.error("Init error: {e}")
            print("Error starting game.")
            return
        print("Welcome, {self.player.name}! You're 16 and beginning your financial journey.")
        try:
            if get_choice("Open a bank account?", ["Yes", "No"]) == "Yes":
                self.player.bank_account = BankAccount()
                self.player.bank_account.deposit(50)
                print("Opened checking with $50 start.")
                if get_choice("Get a debit card?", ["Yes", "No"]) == "Yes":
                    self.player.debit_card = Card("Debit")
                    print("Debit card issued.")
        except BankAccountError as e:
            logging.error("Bank error: {e}")
        input("Press Enter to begin...")
        self.game_loop()

    # --- Core loops ---
    def game_loop(self):
        while not self.game_over:
            self.advance_month()
            if random.random() < 0.3:
                self.trigger_random_event()
            self.check_life_stage_events()
            self.display_status()
            self.get_player_action()
            if self.player.age >= Config.get("retirement_age", 65):
                self.end_game("retirement")

    def advance_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
            self.player.age += 1
            if self.player.bank_account and self.player.bank_account.account_type == "Savings":
                self.player.bank_account.apply_interest()
            for asset in self.player.assets:
                asset.age_asset()
        # Monthly investment returns
        for inv in self.player.investments:
            inv.apply_monthly_return()
        self.process_monthly_finances()

    def process_monthly_finances(self):
        # Income
        if self.player.job:
            monthly_income = self.player.salary / 12
            self.player.cash += monthly_income
            if self.player.bank_account:
                auto = monthly_income * 0.8
                self.player.bank_account.deposit(auto)
                self.player.cash -= auto
        # Loans
        for loan in self.player.loans:
            pay = loan.monthly_payment
            if self.player.cash >= pay:
                self.player.cash -= pay
                loan.make_payment(pay)
            elif self.player.bank_account and self.player.bank_account.balance >= pay:
                self.player.bank_account.withdraw(pay)
                loan.make_payment(pay)
            elif self.player.credit_card and self.player.credit_card.balance + pay <= self.player.credit_card.limit:
                self.player.credit_card.charge(pay)
                loan.make_payment(pay)
            else:
                self.player.credit_score -= 30
                print("Missed {loan.loan_type} payment.")
        # Credit card minimum
        if self.player.credit_card and self.player.credit_card.balance > 0:
            min_pay = max(25, self.player.credit_card.balance * 0.05)
            if self.player.cash >= min_pay:
                self.player.cash -= min_pay
                self.player.credit_card.pay(min_pay)
            elif self.player.bank_account and self.player.bank_account.balance >= min_pay:
                self.player.bank_account.withdraw(min_pay)
                self.player.credit_card.pay(min_pay)
            else:
                self.player.credit_score -= 50
                print("Missed credit card payment.")
        # Living expenses
        living = Config.get("base_living_expenses", 1000)
        if any(a.asset_type == "House" for a in self.player.assets):
            living += Config.get("homeowner_expenses", 500)
        if any(a.asset_type == "Car" for a in self.player.assets):
            living += Config.get("car_expenses", 200)
        if self.player.family:
            living += Config.get("family_expenses_per_member", 500) * len(self.player.family)
        infl = Config.get("inflation_rate", 0.02)
        living *= (1 + infl) ** self.current_year
        if self.player.cash >= living:
            self.player.cash -= living
        elif self.player.bank_account and self.player.bank_account.balance >= living:
            self.player.bank_account.withdraw(living)
        elif self.player.credit_card and self.player.credit_card.balance + living <= self.player.credit_card.limit:
            self.player.credit_card.charge(living)
        else:
            self.player.credit_score -= 20
            print("Could not cover living expenses.")
        # Recurring bills
        for bill in self.player.recurring_bills:
            amt = bill['amount']
            paid = False
            if bill.get('source') == 'bank_or_credit':
                if self.player.bank_account and self.player.bank_account.balance >= amt:
                    self.player.bank_account.withdraw(amt); paid = True
                elif self.player.credit_card and self.player.credit_card.balance + amt <= self.player.credit_card.limit:
                    self.player.credit_card.charge(amt); paid = True
            if not paid and self.player.cash >= amt:
                self.player.cash -= amt; paid = True
            if not paid:
                self.player.credit_score -= 10
                print("Missed bill: {bill['name']}")
        # Utilities
        for util in self.player.utility_bills:
            amt = util['amount']; paid = False
            if self.player.bank_account and self.player.bank_account.balance >= amt:
                self.player.bank_account.withdraw(amt); paid = True
            elif self.player.credit_card and self.player.credit_card.balance + amt <= self.player.credit_card.limit:
                self.player.credit_card.charge(amt); paid = True
            if not paid and self.player.cash >= amt:
                self.player.cash -= amt; paid = True
            if not paid:
                self.player.credit_score -= 5
                print("Missed utility: {util['name']}")
        # After finances, check quest progress
        newly = self.quests.check_all()
        if newly:
            self.quest_notifications.extend(["Quest Completed: {q.title}" for q in newly])
            # limit backlog
            self.quest_notifications = self.quest_notifications[-5:]

    # --- Random events ---
    def trigger_random_event(self):
        etypes = [t for t in ["positive", "negative"] if self.events.get(t) and len(self.events[t])]
        if not etypes:
            return  # no events defined
        etype = random.choice(etypes)
        event_list = self.events[etype]
        event = random.choice(event_list)
        effect = event['cash_effect']()
        # Apply effect (single application) with source priority for negatives
        if effect > 0:
            self.player.cash += effect
        elif effect < 0:
            cost = -effect
            if self.player.cash >= cost:
                self.player.cash -= cost
            elif self.player.bank_account and self.player.bank_account.balance >= cost:
                self.player.bank_account.withdraw(cost)
            elif self.player.credit_card and self.player.credit_card.balance + cost <= self.player.credit_card.limit:
                self.player.credit_card.charge(cost)
            else:
                self.player.credit_score -= 15
        EventBus.publish("random_event", event=event, effect=effect, player=self.player)
        if effect == 0:
            return
        if self.gui_manager is not None:
            from moneySmarts.screens.random_event_screens import RandomEventScreen
            self.gui_manager.set_screen(RandomEventScreen(self, event, effect))
            return
        clear_screen()
        print("\n!"*30)
        print("EVENT: {event['name']}")
        print(event['description'])
        if effect > 0:
            print("You gained ${effect}")
        else:
            print("You paid ${-effect}")
        print("!"*30)
        # Only prompt for Enter if running interactively (avoid pytest capture OSError)
        if sys.stdin and sys.stdin.isatty():
            try:
                input("Press Enter...")
            except Exception:
                pass

    # --- Life events (text) ---
    def check_life_stage_events(self):
        if self.player.age == 18 and self.player.education == "High School":
            self.high_school_graduation_event()
        if self.player.age == 22 and self.player.education == "College (In Progress)":
            self.college_graduation_event()
        if self.player.age == 22 and not self.player.job and self.player.education != "College (In Progress)":
            self.job_opportunity_event()
        if self.player.age == 20 and not any(a.asset_type == "Car" for a in self.player.assets):
            self.car_purchase_opportunity()
        if self.player.age == 30 and not any(a.asset_type == "House" for a in self.player.assets) and self.player.job:
            self.house_purchase_opportunity()
        if self.player.age >= 28 and not self.player.family and self.player.job and random.random() < 0.1:
            self.family_planning_opportunity()

    def high_school_graduation_event(self):
        clear_screen()
        print("\n" + "=" * 60)
        print("LIFE EVENT: HIGH SCHOOL GRADUATION")
        print("=" * 60)
        print("\nCongratulations! You've graduated from high school.")
        print("It's time to make some important decisions about your future.")

        choices = ["Go to college (costs $20,000/year for 4 years)",
                  "Go to trade school (costs $10,000 for 2 years)",
                  "Start working full-time"]

        choice = get_choice("What would you like to do?", choices)

        if choice == choices[0]:  # College
            print("\nYou've decided to go to college. This is a significant investment")
            print("in your future that could lead to higher-paying jobs.")

            # Check if player can afford college
            annual_cost = 20000
            if self.player.cash >= annual_cost:
                print("\nYou pay the first year's tuition of ${annual_cost} in cash.")
                self.player.cash -= annual_cost
            elif self.player.bank_account and self.player.bank_account.balance >= annual_cost:
                print("\nYou pay the first year's tuition of ${annual_cost} from your bank account.")
                self.player.bank_account.withdraw(annual_cost)
            else:
                # Need a student loan
                print("\nYou don't have enough money to pay for college upfront.")
                print("You'll need to take out student loans.")

                loan_amount = 80000  # 4 years of college
                loan = Loan("Student", loan_amount, 0.05, 20)  # 5% interest, 20-year term
                self.player.loans.append(loan)

                print("\nYou've taken out a student loan for ${loan_amount}.")
                print("Your monthly payment will be ${loan.monthly_payment:.2f} for 20 years.")

            self.player.education = "College (In Progress)"
            print("\nYou're now a college student! Your education will take 4 years.")

        elif choice == choices[1]:  # Trade school
            print("\nYou've decided to go to trade school. This is a practical choice")
            print("that will give you specific skills for certain careers.")

            # Check if player can afford trade school
            cost = 10000
            if self.player.cash >= cost:
                print("\nYou pay the trade school tuition of ${cost} in cash.")
                self.player.cash -= cost
            elif self.player.bank_account and self.player.bank_account.balance >= cost:
                print("\nYou pay the trade school tuition of ${cost} from your bank account.")
                self.player.bank_account.withdraw(cost)
            else:
                # Need a student loan
                print("\nYou don't have enough money to pay for trade school upfront.")
                print("You'll need to take out a student loan.")

                loan = Loan("Student", cost, 0.05, 10)  # 5% interest, 10-year term
                self.player.loans.append(loan)

                print("\nYou've taken out a student loan for ${cost}.")
                print("Your monthly payment will be ${loan.monthly_payment:.2f} for 10 years.")

            self.player.education = "Trade School"
            print("\nYou're now a trade school student! Your education will take 2 years.")

        else:  # Start working
            print("\nYou've decided to start working full-time without further education.")
            print("You'll start with entry-level positions, but can work your way up.")

            self.player.education = "High School Graduate"
            self.job_opportunity_event()

        input("\nPress Enter to continue...")

    def college_graduation_event(self):
        clear_screen()
        print("\n" + "=" * 60)
        print("LIFE EVENT: COLLEGE GRADUATION")
        print("=" * 60)
        print("\nCongratulations! You've graduated from college with a bachelor's degree.")
        print("Your education will open up better job opportunities.")

        self.player.education = "College Graduate"
        self.player.credit_score += 20  # Education boosts credit score

        print("\nYour credit score has increased due to your educational achievement.")
        print("Your credit score is now {self.player.credit_score}.")

        # Offer job opportunities
        print("\nWith your new degree, you have access to better job opportunities.")
        self.job_opportunity_event()

        input("\nPress Enter to continue...")

    def job_opportunity_event(self):
        clear_screen()
        print("\n" + "=" * 60)
        print("LIFE EVENT: JOB OPPORTUNITY")
        print("=" * 60)

        # Generate job options based on education
        job_options = []

        if self.player.education == "High School Graduate":
            job_options = [
                {"title": "Retail Associate", "salary": 25000},
                {"title": "Food Service Worker", "salary": 22000},
                {"title": "Warehouse Worker", "salary": 28000},
            ]
        elif self.player.education == "Trade School":
            job_options = [
                {"title": "Electrician Apprentice", "salary": 35000},
                {"title": "Plumber Assistant", "salary": 32000},
                {"title": "HVAC Technician", "salary": 38000},
            ]
        elif self.player.education == "College Graduate":
            job_options = [
                {"title": "Entry-Level Accountant", "salary": 50000},
                {"title": "Marketing Coordinator", "salary": 45000},
                {"title": "Software Developer", "salary": 65000},
            ]

        # Display job options
        print("\nThe following job opportunities are available to you:")
        for i, job in enumerate(job_options):
            print("{i+1}. {job['title']} - ${job['salary']}/year")

        # Get player choice
        choice = 0
        while choice < 1 or choice > len(job_options):
            try:
                choice = int(input("\nWhich job would you like to take? (1-{len(job_options)}): "))
            except ValueError:
                print("Please enter a valid number.")

        # Apply job
        selected_job = job_options[choice-1]
        self.player.job = selected_job["title"]
        self.player.salary = selected_job["salary"]

        print("\nCongratulations! You are now a {self.player.job} earning ${self.player.salary}/year.")
        print("Your monthly income is ${self.player.salary/12:.2f}.")

        input("\nPress Enter to continue...")

    def car_purchase_opportunity(self):
        clear_screen()
        print("\n" + "=" * 60)
        print("LIFE EVENT: CAR PURCHASE OPPORTUNITY")
        print("=" * 60)
        print("\nYou're now at an age where having your own car could be beneficial.")
        print("Would you like to look at some car options?")

        choice = get_choice("Do you want to buy a car?", ["Yes", "No"])

        if choice == "Yes":
            # Car options
            car_options = [
                {"name": "Used Economy Car", "value": 5000},
                {"name": "New Economy Car", "value": 18000},
                {"name": "Used Luxury Car", "value": 15000},
                {"name": "New Luxury Car", "value": 35000},
            ]

            print("\nHere are your car options:")
            for i, car in enumerate(car_options):
                print("{i+1}. {car['name']} - ${car['value']}")

            # Get player choice
            car_choice = 0
            while car_choice < 1 or car_choice > len(car_options):
                try:
                    car_choice = int(input("\nWhich car would you like to buy? (1-{len(car_options)}): "))
                except ValueError:
                    print("Please enter a valid number.")

            selected_car = car_options[car_choice-1]

            # Payment options
            print("\nYou've selected the {selected_car['name']} for ${selected_car['value']}.")
            print("How would you like to pay?")

            payment_options = ["Cash"]
            if self.player.bank_account and self.player.bank_account.balance >= selected_car['value']:
                payment_options.append("Bank Account")
            payment_options.append("Auto Loan")

            payment_choice = get_choice("Select payment method:", payment_options)

            if payment_choice == "Cash" and self.player.cash >= selected_car['value']:
                self.player.cash -= selected_car['value']
                print("\nYou paid ${selected_car['value']} in cash for your new car.")
            elif payment_choice == "Bank Account":
                self.player.bank_account.withdraw(selected_car['value'])
                print("\nYou paid ${selected_car['value']} from your bank account for your new car.")
            else:  # Auto Loan
                # Determine loan terms based on credit score
                if self.player.credit_score >= 700:
                    interest_rate = 0.03  # 3%
                elif self.player.credit_score >= 650:
                    interest_rate = 0.05  # 5%
                else:
                    interest_rate = 0.08  # 8%

                loan = Loan("Auto", selected_car['value'], interest_rate, 5)  # 5-year auto loan
                self.player.loans.append(loan)

                print("\nYou've taken out an auto loan for ${selected_car['value']}.")
                print(
                    "Your interest rate is {interest_rate*100:.1f}% based on your credit score of {self.player.credit_score}.")
                print("Your monthly payment will be ${loan.monthly_payment:.2f} for 5 years.")

            # Add car to assets
            self.player.assets.append(Asset("Car", selected_car['name'], selected_car['value']))
            print("\nCongratulations on your new {selected_car['name']}!")

        else:
            print("\nYou've decided not to buy a car at this time.")

        input("\nPress Enter to continue...")

    def house_purchase_opportunity(self):
        clear_screen()
        print("\n" + "=" * 60)
        print("LIFE EVENT: HOUSE PURCHASE OPPORTUNITY")
        print("=" * 60)
        print("\nYou're now at a stage in life where buying a house could be a good investment.")
        print("Would you like to look at some housing options?")

        choice = get_choice("Do you want to buy a house?", ["Yes", "No"])

        if choice == "Yes":
            # House options
            house_options = [
                {"name": "Small Starter Home", "value": 150000},
                {"name": "Mid-size Family Home", "value": 250000},
                {"name": "Large Luxury Home", "value": 500000},
                {"name": "Urban Condo", "value": 200000},
            ]

            print("\nHere are your housing options:")
            for i, house in enumerate(house_options):
                print("{i+1}. {house['name']} - ${house['value']}")

            # Get player choice
            house_choice = 0
            while house_choice < 1 or house_choice > len(house_options):
                try:
                    house_choice = int(input("\nWhich house would you like to buy? (1-{len(house_options)}): "))
                except ValueError:
                    print("Please enter a valid number.")

            selected_house = house_options[house_choice-1]

            # Calculate down payment (20% is standard)
            down_payment = selected_house['value'] * 0.2
            loan_amount = selected_house['value'] - down_payment

            print("\nYou've selected the {selected_house['name']} for ${selected_house['value']}.")
            print("A standard mortgage requires a 20% down payment of ${down_payment}.")

            # Check if player can afford down payment
            if self.player.cash < down_payment and (not self.player.bank_account or self.player.bank_account.balance < down_payment):
                print("\nYou don't have enough money for the down payment.")
                print("You'll need to save up more money before buying a house.")
                input("\nPress Enter to continue...")
                return

            # Down payment options
            payment_options = []
            if self.player.cash >= down_payment:
                payment_options.append("Cash")
            if self.player.bank_account and self.player.bank_account.balance >= down_payment:
                payment_options.append("Bank Account")

            payment_choice = get_choice("How would you like to pay the down payment?", payment_options)

            if payment_choice == "Cash":
                self.player.cash -= down_payment
                print("\nYou paid ${down_payment} in cash for your down payment.")
            else:  # Bank Account
                self.player.bank_account.withdraw(down_payment)
                print("\nYou paid ${down_payment} from your bank account for your down payment.")

            # Determine mortgage terms based on credit score
            if self.player.credit_score >= 750:
                interest_rate = 0.035  # 3.5%
            elif self.player.credit_score >= 700:
                interest_rate = 0.04   # 4.0%
            elif self.player.credit_score >= 650:
                interest_rate = 0.045  # 4.5%
            else:
                interest_rate = 0.055  # 5.5%

            loan = Loan("Mortgage", loan_amount, interest_rate, 30)  # 30-year mortgage
            self.player.loans.append(loan)

            print("\nYou've taken out a mortgage for ${loan_amount}.")
            print(
                "Your interest rate is {interest_rate*100:.1f}% based on your credit score of {self.player.credit_score}.")
            print("Your monthly payment will be ${loan.monthly_payment:.2f} for 30 years.")

            # Add house to assets
            self.player.assets.append(Asset("House", selected_house['name'], selected_house['value']))
            print("\nCongratulations on your new {selected_house['name']}!")

        else:
            print("\nYou've decided not to buy a house at this time.")

        input("\nPress Enter to continue...")

    def family_planning_opportunity(self):
        clear_screen()
        print("\n" + "=" * 60)
        print("LIFE EVENT: FAMILY PLANNING")
        print("=" * 60)
        print("\nYou've reached a stage in life where starting a family might be a consideration.")
        print("Starting a family will increase your monthly expenses but can bring joy to your life.")

        choice = get_choice("Would you like to start a family?", ["Yes", "No"])

        if choice == "Yes":
            # Add a spouse
            spouse_age = self.player.age - random.randint(-3, 3)  # Spouse age is close to player age
            self.player.family.append({"relation": "Spouse", "age": spouse_age})

            print("\nCongratulations! You've gotten married.")
            print("Your spouse is {spouse_age} years old.")

            # Chance for dual income
            if random.random() < 0.7:  # 70% chance of spouse having a job
                spouse_income = int(self.player.salary * random.uniform(0.5, 1.5))  # Spouse income relative to player
                self.player.salary += spouse_income  # Add spouse income to family income
                print("Your spouse has a job that adds ${spouse_income}/year to your family income.")
                print("Your combined family income is now ${self.player.salary}/year.")
            else:
                print("Your spouse doesn't currently have a job.")

            # Ask about children
            child_choice = get_choice("Would you like to have children?", ["Yes", "No"])

            if child_choice == "Yes":
                num_children = random.randint(1, 3)  # Random number of children

                for i in range(num_children):
                    child_name = "Child {i+1}"  # Placeholder name
                    child_age = 0  # Newborn
                    self.player.family.append({"relation": "Child", "name": child_name, "age": child_age})

                print("\nCongratulations! You now have {num_children} {'child' if num_children == 1 else 'children'}.")
                print("Having children will increase your monthly expenses.")

                # Adjust expenses for children
                print("\nYour monthly expenses have increased to account for your growing family.")

        else:
            print("\nYou've decided not to start a family at this time.")

        input("\nPress Enter to continue...")

    # --- Status & actions (text mode) ---
    def display_status(self):
        clear_screen()
        print("MONTH: {self.current_month}/YEAR: {2023 + self.current_year} | AGE: {self.player.age}")
        print("-"*60)
        print("Name: {self.player.name}  Education: {self.player.education}")
        job = self.player.job or 'Unemployed'
        print("Job: {job}  Salary: ${self.player.salary}/yr" if self.player.job else "Job: {job}")
        print("Cash: ${self.player.cash:.2f}")
        if self.player.bank_account:
            print("Checking/Savings: ${self.player.bank_account.balance:.2f} ({self.player.bank_account.account_type})")
        if self.player.credit_card:
            print("Credit Card: ${self.player.credit_card.balance:.2f}/{self.player.credit_card.limit:.2f}")
        print("Credit Score: {self.player.credit_score}")
        if self.player.loans:
            print("Loans:")
            for ln in self.player.loans:
                print("  {ln.loan_type}: ${ln.current_balance:.2f} @ ${ln.monthly_payment:.2f}/mo")
        if self.player.assets:
            print("Assets:")
            for asset in self.player.assets:
                print("  {asset.name}: ${asset.current_value:.2f} ({asset.condition})")
        nw = compute_net_worth(self.player)
        print("Net Worth: ${nw:.2f}")
        print("-"*60)

    def get_player_action(self):
        actions = ["Continue"]
        if not self.player.bank_account:
            actions.append("Open Bank Account")
        else:
            actions += ["View Account", "Deposit", "Withdraw"]
            if not self.player.debit_card:
                actions.append("Get Debit Card")
        if not self.player.credit_card and self.player.age >= 18:
            actions.append("Apply Credit Card")
        elif self.player.credit_card:
            actions.append("View Credit Card")
            if self.player.credit_card.balance > 0:
                actions.append("Pay Credit Card")
        if self.player.loans:
            actions += ["View Loans", "Extra Loan Payment"]
        if self.player.assets:
            actions.append("View Assets")
        if not self.player.job and self.player.age >= 16:
            actions.append("Job Search")
        elif self.player.job and random.random() < 0.1:
            actions.append("Job Search")
        for i,a in enumerate(actions):
            print("{i+1}. {a}")
        sel = 0
        while sel < 1 or sel > len(actions):
            try:
                sel = int(input("Choose action: "))
            except ValueError:
                print("Invalid.")
        act = actions[sel-1]
        if act == "Continue":
            return
        if act == "Open Bank Account":
            self.open_bank_account()
        elif act == "View Account":
            self.view_bank_account()
        elif act == "Deposit":
            self.deposit_to_bank()
        elif act == "Withdraw":
            self.withdraw_from_bank()
        elif act == "Get Debit Card":
            self.get_debit_card()
        elif act == "Apply Credit Card":
            self.apply_for_credit_card()
        elif act == "View Credit Card":
            self.view_credit_card()
        elif act == "Pay Credit Card":
            self.pay_credit_card()
        elif act == "View Loans":
            self.view_loans()
        elif act == "Extra Loan Payment":
            self.make_extra_loan_payment()
        elif act == "View Assets":
            self.view_assets()
        elif act == "Job Search":
            self.look_for_job()
        input("Press Enter...")

    # --- Basic financial actions (text stubs) ---
    def open_bank_account(self):
        t = get_choice("Account type?", ["Checking", "Savings"])
        self.player.bank_account = BankAccount(t)
        dep = 0
        while dep <= 0:
            try:
                dep = float(input("Initial deposit: $"))
            except ValueError:
                print("Enter number")
        self.player.cash -= dep
        self.player.bank_account.deposit(dep)

    def view_bank_account(self):
        ba = self.player.bank_account
        print("Type: {ba.account_type} Balance: ${ba.balance:.2f}")

    def deposit_to_bank(self):
        amt = float(input("Deposit amount: $"))
        if 0 < amt <= self.player.cash:
            self.player.cash -= amt
            self.player.bank_account.deposit(amt)

    def withdraw_from_bank(self):
        amt = float(input("Withdraw amount: $"))
        if 0 < amt <= self.player.bank_account.balance:
            self.player.bank_account.withdraw(amt)
            self.player.cash += amt

    def get_debit_card(self):
        if not self.player.debit_card and self.player.bank_account:
            self.player.debit_card = Card("Debit")

    def apply_for_credit_card(self):
        if not self.player.credit_card:
            limit = 2000 if self.player.credit_score < 680 else 5000
            self.player.credit_card = Card("Credit", limit=limit)

    def view_credit_card(self):
        cc = self.player.credit_card
        print("Credit Card Balance: ${cc.balance:.2f} / Limit ${cc.limit:.2f}")

    def pay_credit_card(self):
        cc = self.player.credit_card
        if cc.balance <= 0:
            return
        min_pay = max(25, cc.balance * 0.05)
        pay = float(input("Payment amount (min ${min_pay:.2f}): $"))
        if min_pay <= pay <= self.player.cash and pay <= cc.balance:
            self.player.cash -= pay
            cc.pay(pay)

    def view_loans(self):
        for ln in self.player.loans:
            print("{ln.loan_type}: ${ln.current_balance:.2f} / ${ln.monthly_payment:.2f}/mo")

    def make_extra_loan_payment(self):
        if not self.player.loans:
            return
        ln = self.player.loans[0]
        extra = float(input("Extra payment: $"))
        if 0 < extra <= self.player.cash:
            self.player.cash -= extra
            ln.make_payment(extra)

    def view_assets(self):
        for a in self.player.assets:
            print("{a.name}: ${a.current_value:.2f} ({a.condition})")

    def look_for_job(self):
        # Simple job assignment stub
        options = [
            {"title": "Retail Associate", "salary": 25000},
            {"title": "Technician", "salary": 38000},
            {"title": "Software Dev", "salary": 65000},
        ]
        job = random.choice(options)
        self.player.job = job['title']
        self.player.salary = job['salary']
        print("New job: {job['title']} at ${job['salary']}/yr")

    # --- GUI support methods ---
    def check_life_stage_events_gui(self):
        triggered = False
        if self.player.age == 18 and self.player.education == "High School":
            from moneySmarts.screens.life_event_screens import HighSchoolGraduationScreen
            self.gui_manager.set_screen(HighSchoolGraduationScreen(self)); return True
        if self.player.age == 22 and self.player.education == "College (In Progress)":
            from moneySmarts.screens.life_event_screens import CollegeGraduationScreen
            self.gui_manager.set_screen(CollegeGraduationScreen(self)); return True
        if self.player.age == 22 and not self.player.job and self.player.education != "College (In Progress)":
            from moneySmarts.screens.financial_screens import JobSearchScreen
            self.gui_manager.set_screen(JobSearchScreen(self)); return True
        if self.player.age == 20 and not any(a.asset_type=="Car" for a in self.player.assets):
            from moneySmarts.screens.life_event_screens import CarPurchaseScreen
            self.gui_manager.set_screen(CarPurchaseScreen(self)); return True
        if self.player.age == 30 and not any(a.asset_type=="House" for a in self.player.assets) and self.player.job:
            from moneySmarts.screens.life_event_screens import HousingScreen
            self.gui_manager.set_screen(HousingScreen(self)); return True
        if self.player.age >= 28 and not self.player.family and self.player.job and random.random() < 0.1:
            from moneySmarts.screens.life_event_screens import FamilyPlanningScreen
            self.gui_manager.set_screen(FamilyPlanningScreen(self)); return True
        return triggered

    def end_game(self, reason):
        clear_screen()
        print("GAME OVER - {reason}")
        print("Final Net Worth: ${compute_net_worth(self.player):.2f}")
        self.game_over = True

    def end_game_gui(self, reason):
        self.game_over = True
        try:
            from moneySmarts.screens.base_screens import EndGameScreen  # lazy import
            if self.gui_manager:
                self.gui_manager.set_screen(EndGameScreen(self, reason))
        except Exception as e:
            logging.debug("GUI end screen unavailable: {e}")

    # --- Persistence ---
    def _serialize_state(self):
        return {
            'player': self.player,
            'current_month': self.current_month,
            'current_year': self.current_year,
            'game_over': self.game_over,
            'quests': self.quests.serialize() if hasattr(self, 'quests') else [],
            'met_mentor': self.met_mentor,
            'quest_notifications': self.quest_notifications[-5:],
        }

    def _deserialize_state(self, data):
        self.player = data['player']
        self.current_month = data['current_month']
        self.current_year = data['current_year']
        self.game_over = data['game_over']
        self.met_mentor = data.get('met_mentor', False)
        if hasattr(self, 'quests'):
            try:
                self.quests.restore(data.get('quests', []))
            except Exception:
                pass
        self.quest_notifications = data.get('quest_notifications', [])

    def save_state(self, filename="savegame.dat"):
        """Saves the current game state, trying cloud then local storage."""
        payload = {'version': SAVEGAME_VERSION, 'game_state': self._serialize_state()}
        storage = get_storage()
        loading_prev = None
        # If we have a GUI manager, show the loading screen briefly
        if getattr(self, 'gui_manager', None):
            try:
                from moneySmarts.screens.loading_screen import LoadingScreen
                loading_prev = self.gui_manager.current_screen
                loading = LoadingScreen(self, message="Saving game...")
                self.gui_manager.set_screen(loading)
                # Force one frame so the player sees the loading screen
                try:
                    pygame.display.flip()
                    self.gui_manager.clock.tick(30)
                except Exception:
                    pass
            except Exception:
                loading_prev = None
        try:
            storage.save(payload, filename=filename)
            logging.info("Game state saved to {0}.".format(type(storage).__name__))
        except Exception as e:
            logging.error("Save failed with primary backend {0}: {1}".format(type(storage).__name__, e))
            if not isinstance(storage, LocalFileStorage):
                logging.info("Attempting fallback to local storage.")
                try:
                    fallback_storage = LocalFileStorage()
                    fallback_storage.save(payload, filename=filename)
                    logging.info("Game state saved to local fallback.")
                except Exception as e2:
                    logging.error("Local save fallback also failed: {0}".format(e2))
                    # Chain removed for compatibility with some static checkers
                    raise GameError("Failed to save game to both cloud and local storage.")
            else:
                raise GameError("Failed to save game to local storage.")
        finally:
            # Restore previous screen if possible
            if getattr(self, 'gui_manager', None) and loading_prev is not None:
                try:
                    self.gui_manager.set_screen(loading_prev)
                except Exception:
                    pass

    def load_state(self, filename="savegame.dat"):
        """Loads the game state, trying cloud then local storage."""
        storage = get_storage()
        data = None
        loading_prev = None
        # Show loading screen if we have a GUI manager
        if getattr(self, 'gui_manager', None):
            try:
                from moneySmarts.screens.loading_screen import LoadingScreen
                loading_prev = self.gui_manager.current_screen
                loading = LoadingScreen(self, message="Loading game...")
                self.gui_manager.set_screen(loading)
                try:
                    pygame.display.flip()
                    self.gui_manager.clock.tick(30)
                except Exception:
                    pass
            except Exception:
                loading_prev = None
        try:
            data = storage.load(filename=filename)
            logging.info("Game state loaded from {0}.".format(type(storage).__name__))
        except Exception as e:
            logging.error("Load failed with primary backend {0}: {1}".format(type(storage).__name__, e))
            if not isinstance(storage, LocalFileStorage):
                logging.info("Attempting fallback to local storage.")
                try:
                    fallback_storage = LocalFileStorage()
                    data = fallback_storage.load(filename=filename)
                    logging.info("Game state loaded from local fallback.")
                except Exception as e2:
                    logging.error("Local load fallback also failed: {0}".format(e2))
                    raise GameError("Failed to load game from both cloud and local storage.")
            else:
                raise GameError("Failed to load game from local storage.")

        if not data:
            # Restore previous screen before raising so UI isn't left on loading screen
            if getattr(self, 'gui_manager', None) and loading_prev is not None:
                try:
                    self.gui_manager.set_screen(loading_prev)
                except Exception:
                    pass
            raise GameError("No valid save file found.")

        self._deserialize_state(data['game_state'])
        # If we have a GUI manager, switch to the in-game screen so the
        # loaded player's state is immediately visible to the user.
        if getattr(self, 'gui_manager', None):
            try:
                from moneySmarts.screens.game_screen import GameScreen
                self.gui_manager.set_screen(GameScreen(self))
            except Exception:
                logging.exception("Failed to set GameScreen after loading state")
            finally:
                # no-op: GameScreen set above; if it failed, restore previous
                if getattr(self, 'gui_manager', None) and loading_prev is not None and not getattr(self, 'player', None):
                    try:
                        self.gui_manager.set_screen(loading_prev)
                    except Exception:
                        pass

    # --- Control ---
    def quit(self):
        # Prefer to return to the main menu when running under the GUI.
        try:
            if getattr(self, 'gui_manager', None):
                # Clear current player state so TitleScreen shows new-game flow
                self.player = None
                from moneySmarts.screens.base_screens import TitleScreen
                try:
                    self.gui_manager.set_screen(TitleScreen(self))
                    # keep the GUI loop running
                    return
                except Exception:
                    # Fall through and stop the GUI if we cannot restore title screen
                    pass
        except Exception:
            pass
        # Fallback: mark game over and stop loop
        self.game_over = True
        if self.gui_manager:
            self.gui_manager.running = False

    def restart(self):
        self.__init__()
        if self.gui_manager:
            try:
                from moneySmarts.screens.base_screens import TitleScreen
                self.gui_manager.set_screen(TitleScreen(self))
            except Exception as e:
                logging.error("Restart screen failed: {e}")

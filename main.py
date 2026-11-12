from dataclasses import dataclass
from drafter import *

set_website_title("Safety Toolkit")
hide_debug_information()  # remove this line to debugging
add_website_css("body", "background-color: black; color: white;")


@dataclass
class State:
    password_feedback: str
    email_feedback: str
    quiz_score: int
    quiz_feedback: str
    checklist_feedback: str


Goal = ("Safety and security is our goal\nWith the usage of this tool, we hope you can better your online security!"
)

Privacy_Security = (
    "We do not store any data. All data stays local and will disapear on a refresh of the site."
)


def nav() -> list:
    return [
        Button("Home", index),
        Button("Checker", checker_page),
        Button("Quiz", quiz_page),
        Button("Checklist", checklist_page),
        Button("About", about_page),
        HorizontalRule(),
    ]


@route
def index(state: State) -> Page:
    return Page(
        state,
        nav()
        + [
            Header("Welcome to the Safety Toolkit", 1),
            "Pick a tool from the buttons above:",
            BulletedList(
                [
                    "Checker: test a password and validate an email",
                    "Quiz: test your online safety knowledge",
                    "Checklist: review your security habits",
                    "About: learn more about this project",
                ]
            ),
        ],
    )


@route
def checker_page(state: State) -> Page:
    return Page(
        state,
        nav()
        + [
            Header("Password & Email Checker", 1),
            Header("Password", 2),
            "Enter a password to test (don't use a real one!):",
            TextBox("password", ""),
            state.password_feedback,
            Header("Email", 2),
            "Enter an email address:",
            TextBox("email", ""),
            state.email_feedback,
            LineBreak(),
            Button("Check Both", run_checks),
        ],
    )


def evaluate_password(password: str) -> str:
    if not password:
        return "Please enter a password."
    problems = []
    if len(password) < 12:
        problems.append("at least 12 characters")
    if not any(c.isupper() for c in password):
        problems.append("an uppercase letter")
    if not any(c.islower() for c in password):
        problems.append("a lowercase letter")
    if not any(c.isdigit() for c in password):
        problems.append("a digit")
    if all(c.isalnum() for c in password):
        problems.append("a symbol (e.g. !, @, #)")
    if not problems:
        return "Strong password!"
    return "Needs: " + ", ".join(problems)


def evaluate_email(email: str) -> str:
    email = email.strip()
    if not email:
        return "Please enter an email."
    if " " in email:
        return "Email cannot contain spaces."
    if email.count("@") != 1:
        return "Must contain exactly one '@'."
    local, domain = email.split("@")
    if not local:
        return "Missing the part before '@'."
    if "." not in domain or domain.startswith(".") or domain.endswith("."):
        return "Domain must look like 'example.com'."
    return "Looks like a valid email format."


@route
def run_checks(state: State, password: str, email: str) -> Page:
    state.password_feedback = evaluate_password(password)
    state.email_feedback = evaluate_email(email)
    return checker_page(state)


@route
def quiz_page(state: State) -> Page:
    return Page(
        state,
        nav()
        + [
            Header("Online Safety Quiz", 1),
            "1. What is phishing?",
            SelectBox(
                "q1",
                [
                    "A fishing hobby",
                    "A fraudulent attempt to steal info",
                    "A type of firewall",
                ],
            ),
            "2. Which is the safest practice?",
            SelectBox(
                "q2",
                [
                    "Reuse one strong password",
                    "Use a password manager",
                    "Write passwords on a sticky note",
                ],
            ),
            "3. What does 2FA stand for?",
            SelectBox(
                "q3",
                [
                    "Two-Factor Authentication",
                    "Two-File Archive",
                    "Twice-Fast Access",
                ],
            ),
            Button("Submit", grade_quiz),
            state.quiz_feedback,
        ],
    )


@route
def grade_quiz(state: State, q1: str, q2: str, q3: str) -> Page:
    state.quiz_score = 0
    if q1 == "A fraudulent attempt to steal info":
        state.quiz_score += 1
    if q2 == "Use a password manager":
        state.quiz_score += 1
    if q3 == "Two-Factor Authentication":
        state.quiz_score += 1
    state.quiz_feedback = f"You scored {state.quiz_score}/3."
    return quiz_page(state)


@route
def checklist_page(state: State) -> Page:
    return Page(
        state,
        nav()
        + [
            Header("Security Checklist", 1),
            CheckBox("unique", False),
            " I use unique passwords for each account",
            LineBreak(),
            CheckBox("mfa", False),
            " I have two-factor authentication enabled",
            LineBreak(),
            CheckBox("updates", False),
            " My software is up to date",
            LineBreak(),
            CheckBox("backup", False),
            " I back up important files",
            LineBreak(),
            Button("Review", review_checklist),
            state.checklist_feedback,
        ],
    )


@route
def review_checklist(state: State, unique: bool, mfa: bool, updates: bool, backup: bool) -> Page:
    done = sum([unique, mfa, updates, backup])
    state.checklist_feedback = f"{done}/4 complete."
    if done == 4:
        state.checklist_feedback += " Great job!"
    return checklist_page(state)


@route
def about_page(state: State) -> Page:
    return Page(
        state,
        nav()
        + [
            Header("About This Project", 1),
            Header("Our Goal", 2),
            Goal,
            Header("How It Works", 2),
            Privacy_Security,
        ],
    )


start_server(State("", "", 0, "", ""))

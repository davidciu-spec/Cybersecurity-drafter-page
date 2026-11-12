

from dataclasses import dataclass
from bakery import assert_equal
from drafter import *

set_site_information(
    author = "David Ciupei",
    description = "Cybersecurity",
    sources = "LLM use for the template, ",
    planning = "",
    links = ["https://t3.chat/share/4jor4lmt84","https://t3.chat/share/tfl3i1erc","https://t3.chat/share/td1jvtzswf"]
    )

@dataclass
class SafetyTip:
    """
    Creates a safteytip
    args:
        title (str) - the name of the safety tip
        advice (str) - the advice that is a part of the tip (the description)
        completed (bool) - a checklist change if the tip has been completed 
    """
    title: str
    advice: str
    completed: bool


@dataclass
class State:
    """
    Session state
    args:
        tips: list[SafetyTip] - creates the list of safety tips for the checklist
        quiz_score: int - the total score a user gets on the quiz 
        
    """
    tips: list[SafetyTip]
    quiz_score: int
    quiz_attempts: int
    recommendations: list[str]
    focus: str


QUESTIONS = (
    ("Do you use a different password for every account?",
     "Replace reused passwords with unique passwords, starting with email."),
    ("Do you use long, randomly generated passwords or passphrases?",
     "Use a password manager to generate long random passwords (16+ characters)."),
    ("Do you use a password manager?",
     "Choose a reputable password manager and protect it with MFA."),
    ("Have you enabled multifactor authentication on important accounts?",
     "Enable MFA on email, banking and social accounts; prefer passkeys or security keys."),
    ("Do you verify unexpected messages using a trusted contact method?",
     "Open the official app or contact the sender independently before acting."),
    ("Do you install security updates promptly?",
     "Enable automatic updates for your phone, computer and browser."),
    ("Do you keep backups and check that you can restore them?",
     "Back up important files and practice restoring a file."),
    ("Do you lock your devices with a PIN, password or biometrics?",
     "Enable a screen lock and automatic locking when your device is idle."),
    ("Do you review app permissions and remove apps you no longer use?",
     "Review permissions and remove unnecessary apps and browser extensions."),
    ("Do you know how to recover your most important accounts?",
     "Review recovery options and keep recovery codes somewhere secure."),
)
CHOICES = ("Choose an answer", "Yes", "Sometimes", "No")


def initial_state() -> State:
    """Create independent progress for a new visit."""
    return State([
        SafetyTip("Unique passwords", QUESTIONS[0][1], False),
        SafetyTip("Multifactor authentication", QUESTIONS[3][1], False),
        SafetyTip("Phishing awareness", QUESTIONS[4][1], False),
        SafetyTip("Software updates", QUESTIONS[5][1], False),
        SafetyTip("Reliable backups", QUESTIONS[6][1], False),
        SafetyTip("Account recovery", QUESTIONS[9][1], False),
    ], 0, 0, [], "Accounts")


def shell(state: State, title: str, content: list) -> Page:
    """Wrap each page with consistent navigation and source attribution."""
    return Page(state, [
        Div(Link("CYBER COMPASS", "index"), Link("Tools", "password_tools"),
            Link("Checklist", "checklist"), Link("Quiz", "quiz"),
            Link("About", "about"), classes="navigation"),
        Div("PERSONAL CYBERSECURITY / CISC 106", classes="eyebrow"),
        Header(title), *content,
        Div("Learn. Check. Build better habits.  ",
            Link("Sources & privacy", "about"), classes="footer"),
    ])


def tile(number: str, title: str, description: str, target: str) -> Div:
    """Make a navigable home card with its entire surface clickable."""
    return Div(Span(number, classes="tile-number"), Header(title, 2),
               description, Link("Open " + title + " →", target), classes="tile")


@route
def index(state: State) -> Page:
    """Show four tiles leading to the site's four main areas."""
    return shell(state, "A safer digital life starts here.", [
        Div("Small actions. Stronger protection.", classes="intro"),
        "Explore your habits, check for known exposure, and build a practical plan.",
        Div(
            tile("01", "Password & breach tools", "Check passwords and email exposure.", "password_tools"),
            tile("02", "Safety checklist", "Turn advice into six everyday habits.", "checklist"),
            tile("03", "Your security checkup", "Ten questions. A plan based on your answers.", "quiz"),
            tile("04", "About & privacy", "Understand the project and where your data goes.", "about"),
            classes="tiles"),
    ])


@route
def password_tools(state: State) -> Page:
    """Stack independent private password and email checkers on one page."""
    return shell(state, "Password & email checks", [
        Header("Check a password", 2),
        "Try a sample password. The length check is educational, not a security guarantee.",
        RawHTML('''<section class="panel private-tools">
        <label for="private-password">Password to check</label>
        <input id="private-password" type="password" maxlength="256"
          autocomplete="new-password" spellcheck="false">
        <p>Press Enter or Check password. Only the first five characters
        of its SHA-1 hash go to Have I Been Pwned. The field clears immediately.</p>
        <button type="button" data-private="password">Check password</button>
        <p id="password-result" class="private-result" role="status" aria-live="polite"></p></section>'''),
        Link("Password data: Have I Been Pwned", "https://haveibeenpwned.com/Passwords"),
        Header("Check email exposure", 2),
        *email_content(),
    ])


@route
def email_tools(state: State) -> Page:
    """Keep the email-only route available for direct navigation."""
    return shell(state, "Has your email appeared in a breach?", email_content())


def email_content() -> list:
    """Build the reusable email panel with its own consent and result area."""
    return [
        "This free check uses XposedOrNot, a separate database from Have I Been Pwned.",
        RawHTML('''<section class="panel private-tools">
        <label for="private-email">Your email address</label>
        <input id="private-email" type="email" maxlength="254" autocomplete="off">
        <label class="consent"><input id="private-consent" type="checkbox">
        I own this address or have permission to check it. I agree to send the full
        address to XposedOrNot for this search.</label>
        <p>XposedOrNot receives your email and network information. Its privacy
        practices apply. We do not save the address or results to a database.</p>
        <p>Press Enter in the email box or choose Check email exposure.</p>
        <button type="button" data-private="email">Check email exposure</button>
        <p id="email-result" class="private-result" role="status" aria-live="polite"></p></section>'''),
        Link("Breach data and service: XposedOrNot", "https://xposedornot.com"),
        Link("Provider privacy policy", "https://xposedornot.com/privacy"),
    ]


@route
def checklist(state: State) -> Page:
    """Loop over tip objects and show their attributes and saved progress."""
    content = []
    completed = 0
    for position, tip in enumerate(state.tips):
        if tip.completed:
            completed += 1
        field = CheckBox("tip" + str(position), tip.completed)
        content.append(Div(Header(tip.title, 2), tip.advice,
                           Label("I have done this", field), field,
                           classes="panel"))
    focus_field = SelectBox("focus", ["Accounts", "Devices", "Awareness"], state.focus)
    return shell(state, "Your safety checklist", [
        str(completed) + " of 6 habits completed. Progress lasts for this open session.",
        *content, Label("My current focus", focus_field), focus_field,
        Button("Save my progress", "save_checklist"),
    ])


@route
def save_checklist(state: State, tip0: bool, tip1: bool, tip2: bool,
                   tip3: bool, tip4: bool, tip5: bool, focus: str) -> Page:
    """Meaningfully update the list of SafetyTip instances and focus field."""
    choices = [tip0, tip1, tip2, tip3, tip4, tip5]
    for position, tip in enumerate(state.tips):
        tip.completed = choices[position]
    if focus in ["Accounts", "Devices", "Awareness"]:
        state.focus = focus
    return checklist(state)


@route
def quiz(state: State) -> Page:
    """Ask ten non-sensitive questions about existing security habits."""
    content = ["Answer honestly. This is a habit check, not a technical security audit."]
    for position, question in enumerate(QUESTIONS):
        field = SelectBox("q" + str(position), list(CHOICES))
        content.append(Div(Label(str(position + 1) + ". " + question[0],
                               field), field, classes="panel"))
    return shell(state, "How are your everyday habits?", content + [Button("Get my action plan", "score_quiz")])


@route
def score_quiz(state: State, q0: str, q1: str, q2: str, q3: str, q4: str,
               q5: str, q6: str, q7: str, q8: str, q9: str) -> Page:
    """Validate every answer before changing score, attempts or recommendations."""
    answers = [q0, q1, q2, q3, q4, q5, q6, q7, q8, q9]
    for answer in answers:
        if answer not in CHOICES[1:]:
            page = quiz(state)
            page.content.insert(3, "Please answer all ten questions before submitting.")
            return page
    state.quiz_score = 0
    state.recommendations = []
    for position, answer in enumerate(answers):
        if answer == "Yes":
            state.quiz_score += 2
        elif answer == "Sometimes":
            state.quiz_score += 1
            state.recommendations.append(QUESTIONS[position][1])
        else:
            state.recommendations.append(QUESTIONS[position][1])
    state.quiz_attempts += 1
    return results(state)


@route
def results(state: State) -> Page:
    """Explain the score and show specific suggestions for missed habits."""
    if state.quiz_attempts == 0:
        return shell(state, "Your action plan", ["Take the quiz to build your plan.", Button("Start quiz", "quiz")])
    if state.quiz_score >= 16:
        message = "A solid foundation. Keep these habits consistent."
    elif state.quiz_score >= 10:
        message = "You have a start. Choose one improvement to make today."
    else:
        message = "Start with your email account: a unique password and MFA."
    suggestions = state.recommendations or ["Keep reviewing your security habits as your accounts change."]
    return shell(state, "Your next steps", [
        Header(str(state.quiz_score) + " / 20 habit points", 2), message,
        "This score reflects your answers; it does not measure your risk of being hacked.",
        *[Div(suggestion, classes="panel") for suggestion in suggestions],
        Button("Turn advice into action", "checklist"), Button("Retake quiz", "quiz"),
    ])


@route
def about(state: State) -> Page:
    """Explain scope, data flows, limitations and source attribution."""
    return shell(state, "Know the tools. Know the limits.", [
        Header("Our goal", 2),
        "Cyber Compass helps students learn practical cybersecurity habits and respond to known exposure.",
        Header("Your data", 2),
        "No accounts, analytics, database, cookies or browser storage are added by this project. "
        "Checklist and quiz progress live in Drafter's browser session and page history. Reload to clear them.",
        "Password and email inputs bypass Drafter State and route history. They clear when submitted. "
        "Results are transient page text. Browsers, extensions and operating systems may retain memory; "
        "we cannot promise forensic erasure or control third-party logging.",
        "Passwords are hashed locally with Web Crypto. Only a five-character SHA-1 prefix is sent to HIBP "
        "over HTTPS; matching happens locally. SHA-1 here is a lookup format, not password storage.",
        "Email searches send the full address directly to XposedOrNot after consent. That provider can "
        "process or log the request under its own policies. Neither address nor results are stored by this app.",
        Header("What a result means", 2),
        "A match means known exposure, not proof your current account is compromised. No match is not "
        "proof of safety. Change exposed or reused passwords, enable MFA, and review account activity.",
        Header("Sources", 2),
        Link("Have I Been Pwned API documentation", "https://haveibeenpwned.com/API/V3"),
        Link("XposedOrNot free API", "https://xposedornot.com/api_doc"),
        Link("CISA Secure Our World", "https://www.cisa.gov/secure-our-world"),
        Link("FBI online safety advice", "https://www.fbi.gov/how-we-can-help-you/online-safety/"
             "stay-safe-online-simple-tips-for-adults"),
        Button("Clear checklist and quiz progress", "reset_progress"),
    ])


@route
def reset_progress(state: State) -> Page:
    """Replace current progress; browser Back may still show older session pages."""
    return shell(initial_state(), "Progress reset", [
        "Current progress has been reset. Reload the browser to clear older Drafter history too.",
        Button("Return home", "index"),
    ])


def run_bakery_tests() -> None:
    """Test every application function using independent, non-sensitive state.

    Browser JavaScript and live API responses need browser checks rather than
    Python Bakery assertions. No network requests are made by these tests.
    Test variables stay local so they cannot become global application state.
    """
    state = initial_state()
    assert_equal(len(state.tips), 6)
    assert_equal(state.quiz_score, 0)
    assert_equal(state.quiz_attempts, 0)
    assert_equal(state.recommendations, [])
    assert_equal(state.focus, "Accounts")
    assert_equal(state.tips[0].completed, False)
    assert_equal("Example title" in str(shell(state, "Example title", []).content), True)
    assert_equal("Open Example" in str(tile("01", "Example", "Description", "quiz")), True)
    assert_equal("private-consent" in str(email_content()), True)
    assert_equal("A safer digital life" in str(index(state).content), True)
    assert_equal("private-password" in str(password_tools(state).content), True)
    assert_equal("private-email" in str(password_tools(state).content), True)
    assert_equal("private-email" in str(email_tools(state).content), True)
    assert_equal("0 of 6" in str(checklist(state).content), True)
    assert_equal("10. " in str(quiz(state).content), True)
    assert_equal("Take the quiz" in str(results(state).content), True)
    assert_equal("Your data" in str(about(state).content), True)
    saved = save_checklist(state, True, False, True, False, True, False, "Devices")
    assert_equal([tip.completed for tip in saved.state.tips], [True, False, True, False, True, False])
    assert_equal(saved.state.focus, "Devices")
    assert_equal("3 of 6" in str(saved.content), True)
    save_checklist(state, False, False, False, False, False, False, "Invalid")
    assert_equal(state.focus, "Devices")
    assert_equal([tip.completed for tip in state.tips], [False] * 6)
    for answer, expected_score, expected_count in [("Yes", 20, 0), ("Sometimes", 10, 10), ("No", 0, 10)]:
        scored = score_quiz(state, *([answer] * 10))
        assert_equal(scored.state.quiz_score, expected_score)
        assert_equal(len(scored.state.recommendations), expected_count)
        assert_equal(str(expected_score) + " / 20" in str(results(state).content), True)
    assert_equal(state.quiz_attempts, 3)
    invalid = score_quiz(state, *(["Yes"] * 9 + ["Choose an answer"]))
    assert_equal("Please answer all ten" in str(invalid.content), True)
    assert_equal(state.quiz_attempts, 3)
    assert_equal(state.quiz_score, 0)
    assert_equal(state.recommendations, [question[1] for question in QUESTIONS])
    reset = reset_progress(state)
    assert_equal(reset.state, initial_state())
    assert_equal(reset.state is state, False)
    assert_equal("Progress reset" in str(reset.content), True)
    assert_equal(initial_state().tips[0].completed, False)


assert_equal(run_bakery_tests(), None)

set_website_title("Cyber Compass | CISC 106")
set_website_style("none")
set_website_framed(False)
hide_debug_information()
add_website_css_file("style.css")
add_website_js_file("private-tools.js")

start_server(initial_state(), port=8001, host="127.0.0.1", open_browser=True)


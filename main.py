import sys
from dataclasses import dataclass
from bakery import assert_equal
from drafter import *

set_site_information(
    author = "David Ciupei",
    description = "Cybersecurity",
    sources = "LLM use for the template, CSS, JS. Used APIs (documented below). ",
    planning = "",
    links = ["https://t3.chat/share/4jor4lmt84","https://t3.chat/share/tfl3i1erc","https://t3.chat/share/td1jvtzswf","https://chatgpt.com/s/cx_6af6414a64648191b9246e67444c59a1","https://xposedornot.com/api_doc","https://chatgpt.com/s/cx_6af66e1f8aec81918e07b21fb18fc6b9","https://www.cisa.gov/secure-our-world","https://www.fbi.gov/how-we-can-help-you/online-safety/stay-safe-online-simple-tips-for-adults",
            "https://docs.google.com/document/d/1o9OBWE1hz9fVb5NnTaveS_2FcbgzdIhejqWtBFjfDXM/edit?usp=sharing - CISC Design", "https://docs.google.com/document/d/1xgStWdQnBjMmXmBvU1YjNi4mfz141Jlq5g5pE_L4B5k/edit?usp=sharing - CISC 106 Selection"]
    )

@dataclass
class SafetyTip:
    """
    Creates a safety tip
    args:
        title (str) - the name of the safety tip
        advice (str) - the advice that is a part of the tip (the description)
        completed (bool) - whether the tip has been completed on the checklist
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
        quiz_attempts: int - the number of completed quizzes
        recommendations: list[str] - the advice based on the user's quiz answers
        focus: str - the area the user wants to focus on
        priority_tips: list[int] - positions of the checklist tips that match weak quiz answers
        highlight: bool - whether the checklist currently highlights the priority tips
    """
    tips: list[SafetyTip]
    quiz_score: int
    quiz_attempts: int
    recommendations: list[str]
    focus: str
    priority_tips: list[int]
    highlight: bool


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
# Position of the checklist tip each quiz question relates to (None = no matching tip)
QUESTION_TIPS = (0, 0, 0, 1, 2, 3, 4, None, None, 5)
# Positions of the checklist tips that matter most for each focus area
FOCUS_TIPS = {"Accounts": [0, 1, 5], "Devices": [3, 4], "Awareness": [2]}


def initial_state() -> State:
    """
    Creates the starting progress for a new visit
    args:
        None
    returns:
        State - the starting safety tips, quiz progress, recommendations, and focus
    """
    return State([
        SafetyTip("Unique passwords", QUESTIONS[0][1], False),
        SafetyTip("Multifactor authentication", QUESTIONS[3][1], False),
        SafetyTip("Phishing awareness", QUESTIONS[4][1], False),
        SafetyTip("Software updates", QUESTIONS[5][1], False),
        SafetyTip("Reliable backups", QUESTIONS[6][1], False),
        SafetyTip("Account recovery", QUESTIONS[9][1], False),
    ], 0, 0, [], "Accounts", [], False)


def shell(state: State, title: str, content: list, lead: str = "",
          active: str = "", hero: bool = False) -> Page:
    """
    Creates a page with navigation links, a heading, and a footer
    args:
        state (State) - the current session state
        title (str) - the heading shown on the page
        content (list) - the text and components shown on the page
        lead (str) - a short sentence shown under the heading (empty for none)
        active (str) - the navigation link for this section ("Tools", "Checklist", "Quiz", "About", or "")
        hero (bool) - whether to show the large home page heading
    returns:
        Page - the page with the shared layout
    """
    links = [Link("Cyber Compass", "index", classes="brand")]
    for name, target in [("Tools", "password_tools"), ("Checklist", "checklist"),
                         ("Quiz", "quiz"), ("About", "about")]:
        if name == active:
            links.append(Link(name, target, classes="active"))
        else:
            links.append(Link(name, target))
    heading = [Header(title)]
    if lead:
        heading.append(Div(lead, classes="lead"))
    head_classes = "page-head"
    if hero:
        head_classes = "page-head hero"
    footer = FooterContent(
        Div("Cyber Compass · CISC 106 · by David Ciupei"),
        Div("No accounts, cookies or tracking. Nothing you enter is stored."),
        classes="site-footer")
    return Page(state, [
        Div(*links, classes="navigation"),
        Div(*heading, classes=head_classes),
        *content,
        footer,
    ])


def tile(icon: str, number: str, title: str, description: str, target: str) -> Div:
    """
    Creates a card with a link to another page
    args:
        icon (str) - the icon name for the card (key, checklist, quiz, or shield)
        number (str) - the number shown on the card
        title (str) - the name of the card
        description (str) - the description of the page the card links to
        target (str) - the route the card links to
    returns:
        Div - the card with its icon, number, title, description, and link
    """
    return Div(Span("", classes="tile-icon icon-" + icon), Span(number, classes="tile-number"),
               Header(title, 2), description, Link("Open " + title + " →", target), classes="tile")


@route
def index(state: State) -> Page:
    """
    Shows the home page with links to the four main areas
    args:
        state (State) - the current session state
    returns:
        Page - the home page with the four cards
    """
    return shell(state, "Cyber Compass", [
        Div(
            tile("key", "01", "Password & breach tools", "Check passwords and email exposure.", "password_tools"),
            tile("checklist", "02", "Cyber Safety checklist", "Turn advice into six everyday habits.", "checklist"),
            tile("quiz", "03", "Cyber Safety Quiz", "Ten questions. A plan based on your answers.", "quiz"),
            tile("shield", "04", "About & privacy", "Understand the project and where your data goes.", "about"),
            classes="tiles"),
    ], "Learn practical cybersecurity habits, one small step at a time.", hero=True)


@route
def password_tools(state: State) -> Page:
    """
    Shows the email and password checking tools
    args:
        state (State) - the current session state
    returns:
        Page - the page with the email checker and password checker
    """
    return shell(state, "Password & email checks", [
        Header("Check email exposure", 2),
        *email_content(),
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
    ], "See if a password or email address has shown up in a known data breach.", "Tools")


@route
def email_tools(state: State) -> Page:
    """
    Shows the email checker on its own page
    args:
        state (State) - the current session state
    returns:
        Page - the page with the email checker
    """
    return shell(state, "Has your email appeared in a breach?", email_content(),
                 "A quick, private look at known breaches.", "Tools")


def email_content() -> list:
    """
    Creates the content for the email checker
    args:
        None
    returns:
        list - the email input, consent checkbox, and result area
    """
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
    ]


@route
def checklist(state: State) -> Page:
    """
    Shows the safety tips and the user's saved progress, without highlights
    args:
        state (State) - the current session state with the safety tips and focus
    returns:
        Page - the checklist page with checkboxes, a focus selection, and a save button
    """
    state.highlight = False
    return checklist_page(state)


@route
def action_plan(state: State) -> Page:
    """
    Shows the checklist with the tips that match the user's quiz results highlighted
    args:
        state (State) - the current session state with the quiz results
    returns:
        Page - the checklist page with the matching tips highlighted
    """
    state.highlight = True
    return checklist_page(state)


def checklist_page(state: State) -> Page:
    """
    Creates the checklist page, highlighting priority tips when state.highlight is True
    args:
        state (State) - the current session state with the safety tips and focus
    returns:
        Page - the checklist page with checkboxes, a focus selection, and a save button
    """
    content = []
    completed = 0
    flagged = []
    for position, tip in enumerate(state.tips):
        if tip.completed:
            completed += 1
        field = CheckBox("tip" + str(position), tip.completed)
        classes = "panel tip"
        name = tip.title
        if position in FOCUS_TIPS.get(state.focus, []):
            name = "★ " + name
        title = Header(name, 2)
        if tip.completed:
            classes = "panel tip done"
        elif state.highlight and position in state.priority_tips:
            classes = "panel tip priority"
            flagged.append(tip.title)
            title = Header(name + " · Recommended from your quiz", 2)
        content.append(Div(title, tip.advice,
                           Div(field, Label("I have done this", field), classes="tip-check"),
                           classes=classes))
    intro = []
    if state.highlight and flagged:
        intro.append(Div("Based on your quiz, start with: " + ", ".join(flagged) + ".",
                         classes="panel priority-note"))
    elif state.highlight:
        intro.append(Div("Your quiz answers don't point to any unfinished checklist habits. "
                         "Keep it up.", classes="panel priority-note"))
    intro.append(Div("★ marks the habits that matter most for your current focus: " + state.focus +
                     ". Change your focus below and save to update the stars.", classes="focus-note"))
    focus_field = SelectBox("focus", ["Accounts", "Devices", "Awareness"], state.focus)
    progress = Div(Div(str(completed) + " of 6 habits completed", classes="progress-label"),
                   ProgressBar(completed, max=6, classes="progress"),
                   Div("Progress lasts for this open session.", classes="progress-note"),
                   classes="panel progress-card")
    return shell(state, "Your safety checklist", [
        progress, *intro, *content, Label("My current focus", focus_field), focus_field,
        Button("Save my progress", "save_checklist"),
    ], "Six everyday habits. Tick them off as you go.", "Checklist")


@route
def save_checklist(state: State, tip0: bool, tip1: bool, tip2: bool,
                   tip3: bool, tip4: bool, tip5: bool, focus: str) -> Page:
    """
    Saves the completed safety tips and the user's selected focus
    args:
        state (State) - the current session state to update
        tip0 (bool) - whether the unique passwords tip has been completed
        tip1 (bool) - whether the multifactor authentication tip has been completed
        tip2 (bool) - whether the phishing awareness tip has been completed
        tip3 (bool) - whether the software updates tip has been completed
        tip4 (bool) - whether the reliable backups tip has been completed
        tip5 (bool) - whether the account recovery tip has been completed
        focus (str) - the selected focus, saved if it is Accounts, Devices, or Awareness
    returns:
        Page - the checklist page with the updated progress
    """
    choices = [tip0, tip1, tip2, tip3, tip4, tip5]
    for position, tip in enumerate(state.tips):
        tip.completed = choices[position]
    if focus in ["Accounts", "Devices", "Awareness"]:
        state.focus = focus
    return checklist_page(state)


@route
def quiz(state: State) -> Page:
    """
    Shows ten questions about the user's cybersecurity habits
    args:
        state (State) - the current session state
    returns:
        Page - the quiz page with answer selections and a submit button
    """
    content = ["Answer honestly. This is a habit check, not a technical security audit."]
    for position, question in enumerate(QUESTIONS):
        field = SelectBox("q" + str(position), list(CHOICES))
        content.append(Div(Span(str(position + 1), classes="q-number"),
                           Label(question[0], field), field, classes="panel question"))
    return shell(state, "How are your everyday habits?", content + [Button("Get my action plan", "score_quiz")],
                 "Ten quick questions. Nothing is saved.", "Quiz")


@route
def score_quiz(state: State, q0: str, q1: str, q2: str, q3: str, q4: str,
               q5: str, q6: str, q7: str, q8: str, q9: str) -> Page:
    """
    Checks the answers and updates the quiz score, attempts, and recommendations
    args:
        state (State) - the current session state to update after all answers are valid
        q0 (str) - the answer about using different passwords for each account
        q1 (str) - the answer about using long random passwords or passphrases
        q2 (str) - the answer about using a password manager
        q3 (str) - the answer about enabling multifactor authentication
        q4 (str) - the answer about verifying unexpected messages
        q5 (str) - the answer about installing security updates
        q6 (str) - the answer about keeping and checking backups
        q7 (str) - the answer about locking devices
        q8 (str) - the answer about reviewing app permissions and removing unused apps
        q9 (str) - the answer about knowing how to recover important accounts
    returns:
        Page - the results page, or the quiz with a message if any answer is invalid
    """
    answers = [q0, q1, q2, q3, q4, q5, q6, q7, q8, q9]
    for answer in answers:
        if answer not in CHOICES[1:]:
            page = quiz(state)
            page.content.insert(3, Div("Please answer all ten questions before submitting.", classes="panel alert"))
            return page
    state.quiz_score = 0
    state.recommendations = []
    state.priority_tips = []
    state.highlight = False
    for position, answer in enumerate(answers):
        if answer == "Yes":
            state.quiz_score += 2
            continue
        if answer == "Sometimes":
            state.quiz_score += 1
        state.recommendations.append(QUESTIONS[position][1])
        tip_position = QUESTION_TIPS[position]
        if tip_position is not None and tip_position not in state.priority_tips:
            state.priority_tips.append(tip_position)
    state.quiz_attempts += 1
    return results(state)


@route
def results(state: State) -> Page:
    """
    Shows the quiz score and advice based on the user's answers
    args:
        state (State) - the current session state with the quiz results
    returns:
        Page - the results and recommendations, or a message to take the quiz first
    """
    if state.quiz_attempts == 0:
        return shell(state, "Your action plan", ["Take the quiz to build your plan.", Button("Start quiz", "quiz")],
                     "Your results will appear here after the quiz.", "Quiz")
    if state.quiz_score >= 16:
        message = "A solid foundation. Keep these habits consistent."
    elif state.quiz_score >= 10:
        message = "You have a start. Choose one improvement to make today."
    else:
        message = "Start with your email account: a unique password and MFA."
    suggestions = state.recommendations or ["Keep reviewing your security habits as your accounts change."]
    score_card = Div(
        Div(Span(str(state.quiz_score), classes="score-value"), Span("/ 20", classes="score-max"),
            classes="score-number"),
        Div(Header(str(state.quiz_score) + " / 20 habit points", 2), message,
            "This score reflects your answers; it does not measure your risk of being hacked.",
            classes="score-text"),
        ProgressBar(state.quiz_score, max=20, classes="progress"),
        classes="panel score-card " + score_band(state.quiz_score))
    return shell(state, "Your next steps", [
        score_card, Header("Your next steps", 2), NumberedList(suggestions, classes="steps"),
        Button("Turn advice into action", "action_plan"), Button("Retake quiz", "quiz", classes="secondary"),
    ], "Small changes add up. Start with the first step.", "Quiz")


def score_band(score: int) -> str:
    """
    Chooses the style class that matches a quiz score
    args:
        score (int) - the quiz score from 0 to 20
    returns:
        str - "score-high" for 16 or more, "score-mid" for 10 to 15, otherwise "score-low"
    """
    if score >= 16:
        return "score-high"
    if score >= 10:
        return "score-mid"
    return "score-low"


@route
def about(state: State) -> Page:
    """
    Shows the project's purpose, privacy information, limitations, and sources
    args:
        state (State) - the current session state
    returns:
        Page - the information page with source links and a reset button
    """
    return shell(state, "Know the tools. Know the limits.", [
        Header("Our goal", 2),
        "Cyber Compass helps students learn practical cybersecurity habits and respond to known exposure.",
        Header("Your data", 2),
        "Cyber Compass does not store any of your data. There are no accounts, databases, cookies or "
        "analytics. Checklist and quiz progress only last while the page is open and clear when you reload.",
        "The site only contacts outside services when you press a check button on the Tools page:",
        Div(Header("Password check: Have I Been Pwned", 3),
            "Your password is hashed in your browser, and only the first five characters of that hash are "
            "sent to the Pwned Passwords API. The API sends back a list of matching hashes and the comparison "
            "happens on your device, so your password never leaves it.", classes="panel"),
        Div(Header("Email check: XposedOrNot", 3),
            "With your consent, the email address is sent to the XposedOrNot API, which replies with any known "
            "breaches it appears in. XposedOrNot handles that request under its own privacy policy; this site "
            "does not keep the address or the results.", classes="panel"),
        Header("What a result means", 2),
        "A match means known exposure, not proof your current account is compromised. No match is not "
        "proof of safety. Change exposed or reused passwords, enable MFA, and review account activity.",
        Header("Sources", 2),
        BulletedList([
            Link("Have I Been Pwned API documentation", "https://haveibeenpwned.com/API/V3"),
            Link("XposedOrNot free API", "https://xposedornot.com/api_doc"),
            Link("CISA Secure Our World", "https://www.cisa.gov/secure-our-world"),
            Link("FBI online safety advice", "https://www.fbi.gov/how-we-can-help-you/online-safety/"
                 "stay-safe-online-simple-tips-for-adults"),
        ], classes="sources"),
        Button("Clear checklist and quiz progress", "reset_progress", classes="danger"),
    ], "What this site does, what it never stores, and where its advice comes from.", "About")


@route
def reset_progress(state: State) -> Page:
    """
    Creates a new state to reset the checklist and quiz progress
    args:
        state (State) - the current session state being replaced
    returns:
        Page - the reset confirmation page with a new starting state
    """
    return shell(initial_state(), "Progress reset", [
        "Current progress has been reset. Reload the browser to clear older Drafter history too.",
        Button("Return home", "index", classes="secondary"),
    ], "Your checklist and quiz answers are cleared.", "About")


def run_bakery_tests() -> None:
    """
    Tests the application functions using separate example state
    args:
        None
    returns:
        None - checks the expected results using Bakery assertions.
        """
    state = initial_state()
    assert_equal(len(state.tips), 6)
    assert_equal(state.quiz_score, 0)
    assert_equal(state.quiz_attempts, 0)
    assert_equal(state.recommendations, [])
    assert_equal(state.focus, "Accounts")
    assert_equal(state.tips[0].completed, False)
    assert_equal("Example title" in str(shell(state, "Example title", []).content), True)
    assert_equal("Open Example" in str(tile("key", "01", "Example", "Description", "quiz")), True)
    assert_equal("icon-key" in str(tile("key", "01", "Example", "Description", "quiz")), True)
    assert_equal("site-footer" in str(shell(state, "Example title", []).content), True)
    assert_equal("classes='active'" in str(shell(state, "Example", []).content), False)
    assert_equal("page-head hero" in str(index(state).content), True)
    assert_equal("Take the quiz" in str(index(state).content), False)
    assert_equal("classes='lead'" in str(index(state).content), True)
    assert_equal(score_band(0), "score-low")
    assert_equal(score_band(9), "score-low")
    assert_equal(score_band(10), "score-mid")
    assert_equal(score_band(15), "score-mid")
    assert_equal(score_band(16), "score-high")
    assert_equal(score_band(20), "score-high")
    assert_equal("private-consent" in str(email_content()), True)
    assert_equal("Cyber Compass" in str(index(state).content), True)
    assert_equal("private-password" in str(password_tools(state).content), True)
    assert_equal("private-email" in str(password_tools(state).content), True)
    assert_equal("private-email" in str(email_tools(state).content), True)
    assert_equal("0 of 6" in str(checklist(state).content), True)
    assert_equal("Link('Checklist', 'checklist', classes='active')" in str(checklist(state).content), True)
    assert_equal("Link('Quiz', 'quiz', classes='active')" in str(quiz(state).content), True)
    assert_equal("Link('Tools', 'password_tools', classes='active')" in str(email_tools(state).content), True)
    assert_equal("Link('About', 'about', classes='active')" in str(about(state).content), True)
    assert_equal("Link('Cyber Compass', 'index', classes='brand')" in str(index(state).content), True)
    assert_equal("ProgressBar(0, 6" in str(checklist(state).content), True)
    assert_equal("Span('10', classes='q-number')" in str(quiz(state).content), True)
    assert_equal(str(quiz(state).content).count("classes='panel question'"), 10)
    assert_equal("classes='danger'" in str(about(state).content), True)
    assert_equal("classes='sources'" in str(about(state).content), True)
    assert_equal("site-footer" in str(about(state).content), True)
    assert_equal("Take the quiz" in str(results(state).content), True)
    assert_equal("Your data" in str(about(state).content), True)
    saved = save_checklist(state, True, False, True, False, True, False, "Devices")
    assert_equal([tip.completed for tip in saved.state.tips], [True, False, True, False, True, False])
    assert_equal(saved.state.focus, "Devices")
    assert_equal("3 of 6" in str(saved.content), True)
    assert_equal(str(saved.content).count("classes='panel tip done'"), 3)
    assert_equal(str(saved.content).count("classes='panel tip'"), 3)
    assert_equal(str(saved.content).count("★ "), 3)
    assert_equal("★ Software updates" in str(saved.content), True)
    assert_equal("★ Reliable backups" in str(saved.content), True)
    assert_equal("★ Unique passwords" in str(saved.content), False)
    assert_equal("current focus: Devices" in str(saved.content), True)
    assert_equal("★ Unique passwords" in str(checklist(initial_state()).content), True)
    assert_equal("★ Account recovery" in str(checklist(initial_state()).content), True)
    save_checklist(state, False, False, False, False, False, False, "Invalid")
    assert_equal(state.focus, "Devices")
    assert_equal([tip.completed for tip in state.tips], [False] * 6)
    for answer, expected_score, expected_count, band in [("Yes", 20, 0, "score-high"),
                                                         ("Sometimes", 10, 10, "score-mid"),
                                                         ("No", 0, 10, "score-low")]:
        scored = score_quiz(state, *([answer] * 10))
        assert_equal(scored.state.quiz_score, expected_score)
        assert_equal(len(scored.state.recommendations), expected_count)
        assert_equal("panel score-card " + band in str(scored.content), True)
        assert_equal("Link('Quiz', 'quiz', classes='active')" in str(scored.content), True)
        assert_equal(str(expected_score) + " / 20" in str(results(state).content), True)
    assert_equal(state.quiz_attempts, 3)
    invalid = score_quiz(state, *(["Yes"] * 9 + ["Choose an answer"]))
    assert_equal("Please answer all ten" in str(invalid.content), True)
    assert_equal("classes='panel alert'" in str(invalid.content), True)
    assert_equal("Link('Quiz', 'quiz', classes='active')" in str(invalid.content), True)
    assert_equal(state.quiz_attempts, 3)
    assert_equal(state.quiz_score, 0)
    assert_equal(state.recommendations, [question[1] for question in QUESTIONS])
    assert_equal(state.priority_tips, [0, 1, 2, 3, 4, 5])
    assert_equal("priority" in str(checklist(state).content), False)
    assert_equal(str(action_plan(state).content).count("Recommended from your quiz"), 6)
    state.tips[0].completed = True
    assert_equal(str(action_plan(state).content).count("Recommended from your quiz"), 5)
    assert_equal(str(action_plan(state).content).count("classes='panel tip priority'"), 5)
    assert_equal(str(action_plan(state).content).count("classes='panel tip done'"), 1)
    state.tips[0].completed = False
    score_quiz(state, "Yes", "Yes", "Yes", "No", "Yes", "Yes", "Yes", "No", "Yes", "Yes")
    assert_equal(state.priority_tips, [1])
    assert_equal("★ Multifactor authentication · Recommended" in str(action_plan(state).content), False)
    assert_equal("Multifactor authentication · Recommended" in str(action_plan(state).content), True)
    assert_equal("Unique passwords · Recommended" in str(action_plan(state).content), False)
    assert_equal(save_checklist(state, False, False, False, False, False, False, "Devices").state.highlight, True)
    assert_equal(checklist(state).state.highlight, False)
    score_quiz(state, *(["Yes"] * 10))
    assert_equal("don't point to any" in str(action_plan(state).content), True)
    score_quiz(state, *(["No"] * 10))
    reset = reset_progress(state)
    assert_equal(reset.state, initial_state())
    assert_equal(reset.state is state, False)
    assert_equal("Progress reset" in str(reset.content), True)
    assert_equal("site-footer" in str(reset.content), True)
    assert_equal(initial_state().tips[0].completed, False)


# Run the tests on your computer and during deployment, but not in the
# visitor's browser ("emscripten"), where each assertion looks up main.py
# over the network and slows down the first page load.
if sys.platform != "emscripten":
    assert_equal(run_bakery_tests(), None)

set_website_title("Cyber Compass | CISC 106")
set_website_style("none")
# The site is already dark, so ask the Dark Reader extension not to restyle it
# (it rewrites colours and breaks the dropdown arrow's position).
add_website_header('<meta name="darkreader-lock">')
set_website_framed(False)
hide_debug_information()
add_website_css_file("style.css")
add_website_js_file("private-tools.js")

start_server(initial_state(), port=8001, host="127.0.0.1", open_browser=True)


import random
import sys
from dataclasses import dataclass
from bakery import assert_equal
from drafter import *

set_site_information(
    author = "David Ciupei",
    description = "Cybersecurity",
    sources = "LLM use for the template, CSS, JS, speeding up rendering on open, and reworking the UI. Used APIs (documented below). ",
    planning = "",
    links = ["https://t3.chat/share/4jor4lmt84","https://t3.chat/share/tfl3i1erc","https://t3.chat/share/td1jvtzswf","https://chatgpt.com/s/cx_6af6414a64648191b9246e67444c59a1","https://xposedornot.com/api_doc","https://chatgpt.com/s/cx_6af66e1f8aec81918e07b21fb18fc6b9","https://www.cisa.gov/secure-our-world","https://www.fbi.gov/how-we-can-help-you/online-safety/stay-safe-online-simple-tips-for-adults",
            "https://docs.google.com/document/d/1o9OBWE1hz9fVb5NnTaveS_2FcbgzdIhejqWtBFjfDXM/edit?usp=sharing - CISC Design", "https://docs.google.com/document/d/1xgStWdQnBjMmXmBvU1YjNi4mfz141Jlq5g5pE_L4B5k/edit?usp=sharing - CISC 106 Selection","https://docs.google.com/document/d/1phvccYCsgnMsVA6A5drGUkAhZ2-wECBYbReHJv_oJho/edit?usp=sharing - Overflow conversations that did not have links"]
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
        focus: str - the area the user wants to focus on ("" when none is chosen)
        priority_tips: list[int] - positions of the checklist tips that match weak quiz answers
        highlight: bool - whether the checklist currently highlights the priority tips
        phish_position: int - how many Spot the Phish messages have been moved past in this round
        phish_score: int - the number of Spot the Phish messages answered correctly
        phish_guess: str - the answer for the current message ("" when not answered yet)
        phish_order: list[int] - the positions in MESSAGES, shuffled into the order they are shown
        exposures: list[str] - the kinds of data the user said a breach exposed
        platform: str - the device chosen on the device setup page ("" when none is chosen)
    """
    tips: list[SafetyTip]
    quiz_score: int
    quiz_attempts: int
    recommendations: list[str]
    focus: str
    priority_tips: list[int]
    highlight: bool
    phish_position: int
    phish_score: int
    phish_guess: str
    phish_order: list[int]
    exposures: list[str]
    platform: str


@dataclass
class SampleMessage:
    """
    Creates a practice message for the Spot the Phish activity
    args:
        kind (str) - how the message arrived ("Email" or "Text message")
        sender (str) - who the message says it is from
        subject (str) - the subject line ("" for a text message)
        body (str) - the main text of the message
        link (str) - the web address the message shows ("" for none); it is never clickable
        is_phish (bool) - whether the message is a phishing attempt
        clues (list[str]) - the signs that show whether the message is phishing
    """
    kind: str
    sender: str
    subject: str
    body: str
    link: str
    is_phish: bool
    clues: list[str]


@dataclass
class GuideStep:
    """
    Creates one step of the breach or device guides
    args:
        title (str) - what to do
        where (str) - where to find the setting ("" when there is no setting to find)
        why (str) - how to do it and why it helps
    """
    title: str
    where: str
    why: str


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
FOCUS_CHOICES = ("Choose a focus", "Accounts", "Devices", "Awareness")

# Spot the Phish: practice messages. Every company and address here is made up.
MESSAGES = (
    SampleMessage(
        "Email", "SwiftShip Delivery <alerts@swiftship-redelivery.net>",
        "Action required: your parcel is on hold",
        "We tried to deliver your parcel today, but an unpaid customs fee of $1.99 is due. "
        "Pay within 24 hours or your parcel will be returned to the sender.",
        "swiftship-redelivery.net/pay-fee", True,
        ["The sender's domain isn't the delivery company's own website. Scammers register "
         "lookalike names.",
         "A tiny fee with a 24-hour deadline is a common trick to collect card details quickly.",
         "To check a real parcel, type its tracking number into the company's official app or site."]),
    SampleMessage(
        "Email", "IT Service Desk <servicedesk@yourschool.edu>",
        "Planned email maintenance this Saturday",
        "Email will be unavailable on Saturday from 2 a.m. to 4 a.m. while we install updates. "
        "You don't need to do anything. Status updates will be posted on the IT page of the "
        "student portal.",
        "", False,
        ["It comes from the school's real domain and matches what IT normally sends.",
         "It asks for nothing: no sign-in, no download and no reply.",
         "It sends you to a place you already know, the student portal, instead of a link."]),
    SampleMessage(
        "Text message", "+1 (302) 555-0148", "",
        "First Harbor Bank: we blocked an unusual sign-in to your account. If this wasn't you, "
        "verify your identity now to avoid suspension.",
        "firstharbor-secure-login.co/verify", True,
        ["Banks don't text you links asking you to sign in or verify your identity.",
         "The link adds words like 'secure' and 'login' to look official, and it isn't the "
         "bank's real website.",
         "The threat of suspension is there to rush you. Open the bank's app or call the number "
         "on your card instead."]),
    SampleMessage(
        "Text message", "StreamBox", "",
        "Your StreamBox sign-in code is 482913. It expires in 10 minutes. StreamBox will never "
        "ask you for this code.",
        "", False,
        ["You'd expect this code if you just signed in, and it only asks you to type it yourself.",
         "It warns you never to share the code. Scammers often call pretending to be support "
         "and ask for it.",
         "If a code arrives when you didn't sign in, someone may know your password. Change it "
         "in the official app."]),
    SampleMessage(
        "Email", "Webmail Admin <admin@yourschool-mail.support>",
        "Mailbox 99% full: messages will be deleted",
        "Dear user, your mailbox has reached its storage limit. New messages will be rejected "
        "and older ones deleted in 12 hours. Sign in below to keep your email.",
        "yourschool-mail.support/keep-my-mail", True,
        ["The address looks like the school's, but yourschool-mail.support is a different website.",
         "A generic greeting ('Dear user') and a short deadline are classic phishing signs.",
         "The link leads to a fake sign-in page that collects passwords. Check your storage by "
         "signing in the way you normally do."]),
    SampleMessage(
        "Email", "Prof. Lee <prof.lee.office@gmail.com>", "Quick favour?",
        "Are you free? I'm stuck in meetings all day and need a favour for a student event. "
        "Please buy four $100 gift cards and email me photos of the codes. I'll pay you back "
        "this week. Please keep this between us for now.",
        "", True,
        ["Requests to buy gift cards are almost always scams, because the money can't be traced "
         "or returned.",
         "It uses a personal email address instead of the school address professors normally use.",
         "Urgency and secrecy are pressure tactics. Check with the professor through the school "
         "directory or in person."]),
    SampleMessage(
        "Email", "OneFile Drive <no-reply@onefile-docs-share.com>",
        "Dana shared \"Payroll Adjustments 2026.pdf\" with you",
        "Dana has shared a document with you. This file will be available for 48 hours. Sign in "
        "with your school email and password to view it.",
        "onefile-docs-share.com/view-document", True,
        ["You weren't expecting a file, and the title is chosen to make you curious about money.",
         "The domain isn't the file-sharing service's real website, even though the name looks "
         "close.",
         "Asking for your school password to open a document is how fake sign-in pages steal "
         "accounts. Ask the sender through another channel if the file is real."]),
    SampleMessage(
        "Email", "Campus Library <library@yourschool.edu>",
        "Reminder: 2 books due this Friday",
        "Two items on your library account are due this Friday. You can renew them from My "
        "Account on the library website or at the front desk. If you've already returned them, "
        "you don't need to do anything.",
        "", False,
        ["It comes from the school's real domain and matches something you actually did, "
         "borrowing books.",
         "It asks for nothing sensitive: no password, no payment and no attachment.",
         "It sends you to the library website or the front desk, places you already know, "
         "instead of a link."]),
    SampleMessage(
        "Text message", "+1 (415) 555-0193", "",
        "MetroPass Tolls: you have an unpaid toll balance of $4.35. Pay today to avoid a $50 "
        "late fee and suspension of your driving licence.",
        "metropass-tollpay.info/pay", True,
        ["Unpaid toll texts are one of the most common scams. They're sent to huge numbers of "
         "people, drivers or not.",
         "The threat is far out of proportion to a $4.35 charge. That's meant to scare you into "
         "paying quickly.",
         "The link isn't the toll agency's real website. Check any balance by typing the "
         "official address yourself."]),
    SampleMessage(
        "Text message", "PineCrest Pharmacy", "",
        "PineCrest Pharmacy: your prescription is ready for pickup at our Main Street store. "
        "Bring photo ID. Reply STOP to stop these alerts.",
        "", False,
        ["You'd expect this if you recently asked for a prescription to be filled.",
         "It has no link and doesn't ask for personal details, payment or a reply with "
         "information.",
         "If you're unsure, call the store using the number on your prescription label or "
         "their official website."]),
    SampleMessage(
        "Email", "Campus Careers Team <campus.careers.hiring@outlook.com>",
        "Remote assistant role: $500 a week, 5 hours",
        "Congratulations, your profile was selected for a flexible remote assistant job. We'll "
        "mail you a cheque to buy office equipment. Deposit it, keep $500 for your first week, "
        "and send the rest to our equipment vendor by gift card or wire transfer.",
        "", True,
        ["The pay is far too high for very little work, and you never applied for the job.",
         "Real school career offices use the school's domain, not a free personal email account.",
         "Depositing a cheque and sending part of it back is a fake-cheque scam. The cheque "
         "bounces later and you lose the money you sent."]),
    SampleMessage(
        "Email", "Northleaf Bank <statements@northleafbank.com>",
        "Your October statement is ready",
        "Your October statement is now available. To view it, open the Northleaf Bank app or "
        "type northleafbank.com into your browser and sign in. We will never ask for your "
        "password, PIN or sign-in codes by email.",
        "", False,
        ["It's a routine notice you'd expect each month, with no deadline or threat.",
         "It has no link. It tells you to open the app or type the address yourself, which is "
         "the safe way to sign in.",
         "It asks for nothing and reminds you the bank will never ask for your password or "
         "codes."]),
    SampleMessage(
        "Email", "Account Services <accounts@yourschool.edu.password-renew.com>",
        "Your password expires today",
        "Your school password expires at midnight. To keep access to email and the student "
        "portal, confirm your current password using the secure link below.",
        "yourschool.edu.password-renew.com/confirm", True,
        ["The real website is the last part before the first slash: password-renew.com. "
         "'yourschool.edu' at the start is only there to fool you.",
         "No real IT team asks you to confirm your current password through an email link.",
         "If you think your password is expiring, sign in through the student portal the way "
         "you normally do."]),
    SampleMessage(
        "Text message", "+1 (614) 555-0127", "",
        "Hi Mum, I dropped my phone and this is my new number. I can't get into my banking app. "
        "Can you send $350 to my friend's account for rent? I'll pay you back tomorrow.",
        "", True,
        ["A family member writing from a new number and asking for money straight away is a "
         "well-known scam.",
         "The excuse explains why they can't call or use their own account, so you can't check.",
         "Call the family member on the number you already have before sending anything."]),
    SampleMessage(
        "Email", "Revenue Refunds <refunds@revenue-services-online.com>",
        "You are owed a tax refund of $428.60",
        "After a review of your account we found you are owed a refund of $428.60. To receive "
        "it, enter your bank card number, expiry date and security code on our refund page "
        "within 3 days.",
        "revenue-services-online.com/claim-refund", True,
        ["Tax agencies don't email you about refunds and ask for card details.",
         "A refund never needs your card's security code. That's only used to make payments.",
         "Check for a real refund by typing the tax agency's official address yourself or "
         "calling them."]),
    SampleMessage(
        "Email", "Accounts Payable <billing@quickledger-invoices.biz>",
        "OVERDUE: Invoice #88231 – final notice",
        "Please find the attached overdue invoice for services provided. Payment is now 30 days "
        "late. Open the attachment Invoice_88231.zip and enable editing to view the full "
        "amount.",
        "", True,
        ["You don't recognise the company, and it doesn't say what the services were.",
         "Zip files and requests to 'enable editing' are common ways to install malware.",
         "Don't open unexpected attachments. If you think you might owe money, contact the "
         "company using details you find yourself."]),
    SampleMessage(
        "Text message", "+1 (205) 555-0166", "",
        "ShopMart: Congratulations! You've been selected to receive a $1,000 gift card. Claim "
        "yours in the next 2 hours before it goes to the next winner.",
        "shopmart-rewards.win/claim", True,
        ["You can't win a prize you never entered.",
         "The two-hour limit is there to stop you thinking it through.",
         "The '.win' link isn't the store's real website. These pages ask for personal "
         "details or a 'shipping fee'."]),
    SampleMessage(
        "Email", "SecureGuard Billing <billing@secureguard-renewals.com>",
        "Your subscription renewed: $399.99 charged",
        "Thank you for renewing SecureGuard Total Protection for 3 years. $399.99 has been "
        "charged to your account. If you didn't approve this, call our cancellation line at "
        "1-800-555-0177 within 24 hours for a refund.",
        "", True,
        ["A large charge for something you don't remember buying is meant to make you panic.",
         "Instead of a link, it pushes you to call. The 'support' agent will ask for remote "
         "access to your computer or your bank details.",
         "Check your bank or card statement directly. Only call numbers you find on the "
         "official website."]),
    SampleMessage(
        "Email", "PhotoGram Support <support@photogram-appeals.help>",
        "Your account will be disabled: copyright violation",
        "We received a copyright complaint about one of your posts. Your account will be "
        "permanently disabled in 24 hours unless you submit an appeal and confirm your login "
        "details.",
        "photogram-appeals.help/appeal", True,
        ["The '.help' domain isn't the social media app's real website.",
         "The threat of losing your account in 24 hours is meant to rush you.",
         "Real warnings appear inside the app's own settings or notifications. Check there "
         "instead of signing in through a link."]),
    SampleMessage(
        "Email", "Financial Aid Office <finaid.office@yourschool-grants.org>",
        "You qualify for a $2,500 student grant",
        "Good news! You have been pre-approved for a $2,500 student grant. To release the "
        "funds, pay a one-time $49 processing fee by card on the link below.",
        "yourschool-grants.org/release-funds", True,
        ["Real grants and scholarships don't charge a fee to release money.",
         "The address isn't the school's real domain. It just includes the school's name.",
         "Contact the financial aid office through the student portal or in person to check."]),
    SampleMessage(
        "Email", "Oakview Property Management <rent@oakview-properties.co>",
        "Important: new bank details for rent payments",
        "Please note our bank account has changed. From this month, send your rent to the new "
        "account below and not the old one. Payments to the old account will be returned. "
        "Please don't call the office, as we are moving phone systems.",
        "", True,
        ["Messages that change where you send money are a favourite trick, because the money "
         "is very hard to get back.",
         "The domain ends in '.co' instead of the address your landlord normally uses.",
         "Telling you not to call is a big warning sign. Always confirm new payment details by "
         "phone or in person."]),
    SampleMessage(
        "Email", "StreamBox <no-reply@streambox.com>",
        "Reset your StreamBox password",
        "We received a request to reset your password. If this was you, use the link below "
        "within 1 hour. If you didn't ask for this, you can ignore this email and your password "
        "won't change.",
        "streambox.com/account/reset", False,
        ["This is safe if you just clicked 'forgot password' yourself. You expected it.",
         "The link goes to the company's own website, and it tells you that ignoring it is fine.",
         "If you didn't ask for a reset, don't click. Someone may have typed your email by "
         "mistake, or may be trying to get in."]),
    SampleMessage(
        "Text message", "Bright Smile Dental", "",
        "Bright Smile Dental: reminder of your appointment on Tuesday at 3:00 p.m. Reply C to "
        "confirm or call the office to reschedule.",
        "", False,
        ["You'd expect this if you have an appointment booked.",
         "It has no link and doesn't ask for any personal or payment details.",
         "Replying 'C' only confirms the time. If anything seems off, call the office on the "
         "number you already have."]),
    SampleMessage(
        "Email", "Larkspur Outfitters <orders@larkspuroutfitters.com>",
        "Your order #40219 has shipped",
        "Good news! Your order of 1 rain jacket has shipped and should arrive Thursday. You can "
        "track it from Your Orders on our website.",
        "larkspuroutfitters.com/orders", False,
        ["It matches an order you actually placed, with the right item.",
         "It comes from the store's real domain and the link goes to the same website.",
         "It doesn't ask for payment or a password. You can also open the website yourself to "
         "check."]),
    SampleMessage(
        "Email", "Office of the Registrar <registrar@yourschool.edu>",
        "Spring registration opens Monday",
        "Registration for spring classes opens Monday at 8 a.m. Check your registration time "
        "and any holds on your account in the student portal before then.",
        "", False,
        ["It comes from the school's real domain and arrives at the time of year you'd expect.",
         "It asks for nothing and has no link or attachment.",
         "It points you to the student portal, which you already know how to reach."]),
    SampleMessage(
        "Text message", "First Harbor Bank", "",
        "First Harbor Bank: did you try to make a $62.10 purchase at Corner Grocery? Reply YES "
        "or NO. We will never ask for your PIN, password or codes by text.",
        "", False,
        ["It only asks for a simple YES or NO. There's no link and no request for details.",
         "Banks do send fraud checks like this when a purchase looks unusual.",
         "If you're unsure, call the number on the back of your card instead of replying."]),
    SampleMessage(
        "Email", "StreamBox <security@streambox.com>",
        "New sign-in on a Windows computer",
        "We noticed a new sign-in to your StreamBox account on a Windows computer. If this was "
        "you, you don't need to do anything. If not, open the StreamBox app and change your "
        "password from Settings.",
        "", False,
        ["It comes from the company's real domain and doesn't ask you to click anything.",
         "It tells you to use the app you already have to make changes.",
         "If you didn't sign in, follow its advice through the app: change your password and "
         "turn on MFA."]),
    SampleMessage(
        "Email", "Maya Chen <mchen@yourschool.edu>",
        "Notes from today's group meeting",
        "Hi all, I've put the notes from today's meeting in our group folder on the course "
        "page. Can everyone add their part of the outline before Thursday? Thanks!",
        "", False,
        ["It's from a classmate's school address about a project you're working on.",
         "It asks for nothing unusual: no money, password or secrecy.",
         "It points to the course page you already use instead of an unknown link or "
         "attachment."]),
    SampleMessage(
        "Text message", "SwiftShip", "",
        "SwiftShip: your parcel will be delivered today between 2 p.m. and 5 p.m. Track it in "
        "the SwiftShip app.",
        "", False,
        ["It matches a parcel you're expecting and asks for nothing.",
         "There's no link, no fee and no deadline, unlike the fake delivery message.",
         "It tells you to use the official app, which is the safe way to check."]),
    SampleMessage(
        "Email", "IT Service Desk <servicedesk@yourschool.edu>",
        "Reminder: turn on multifactor authentication by December 15",
        "To protect your account, multifactor authentication will be required from December "
        "15. Set it up from the Security page in the student portal. IT will never ask for your "
        "password or sign-in codes.",
        "", False,
        ["It comes from the school's real domain and gives a reasonable deadline.",
         "It sends you to the student portal instead of a link.",
         "It reminds you that IT will never ask for your password or codes, which is true of "
         "real IT teams."]),
)
PHISH_CHOICES = ("Phishing", "Legitimate")
PHISH_RED_FLAGS = (
    "A sender or link that is close to, but not exactly, the real company's address",
    "Urgency, threats or short deadlines",
    "Requests for passwords, sign-in codes, payments or gift cards",
    "A generic greeting, or an unusual request from someone you know",
    "When in doubt, ignore the message's link. Open the official app or website yourself.",
)

# Breach next steps: (key, checkbox label, section heading)
EXPOSURE_TYPES = (
    ("password", "A password", "If a password was exposed"),
    ("email", "My email address", "If your email address was exposed"),
    ("financial", "Card or bank details", "If card or bank details were exposed"),
    ("identity", "An ID number, such as a Social Security number", "If an ID number was exposed"),
)
FIRST_STEPS = (
    GuideStep("Go to the source yourself", "",
              "Don't click links in breach-notice emails or texts. Open the company's website or app "
              "yourself to read what happened."),
    GuideStep("Secure your email first", "",
              "Your email can reset every other account, so give it a unique password and turn on MFA."),
    GuideStep("Watch for follow-up scams", "",
              "Scammers use breach news to send convincing phishing. Practise on the Spot the Phish page."),
)
BREACH_STEPS = {
    "password": [
        GuideStep("Change the exposed password", "",
                  "Replace it with a new, unique password, ideally one generated by a password manager."),
        GuideStep("Change it everywhere you reused it", "",
                  "Attackers try leaked passwords on other sites. Start with email, banking and shopping."),
        GuideStep("Turn on multifactor authentication", "",
                  "MFA blocks most sign-ins that use a stolen password."),
        GuideStep("Sign out other sessions", "",
                  "In the account's security settings, sign out devices you don't recognise and review "
                  "recent activity."),
    ],
    "email": [
        GuideStep("Expect targeted phishing", "",
                  "Messages may mention the breached service by name. Treat them with extra suspicion."),
        GuideStep("Check whether a password leaked too", "",
                  "Read the company's breach notice. If passwords were included, follow the password "
                  "steps as well."),
        GuideStep("Watch for password resets you didn't request", "",
                  "They can mean someone is trying to get into your accounts."),
    ],
    "financial": [
        GuideStep("Call your bank or card issuer", "",
                  "Use the number on the back of your card and ask whether you need a replacement card."),
        GuideStep("Review recent transactions", "",
                  "Look for charges you don't recognise, even small ones, and report them straight away."),
        GuideStep("Turn on transaction alerts", "",
                  "Most banking apps can notify you about every purchase."),
    ],
    "identity": [
        GuideStep("Freeze your credit", "",
                  "A freeze stops new accounts being opened in your name. It is free with each of the "
                  "three credit bureaus: Equifax, Experian and TransUnion."),
        GuideStep("Check your credit reports", "",
                  "Get free reports at AnnualCreditReport.com and look for accounts you didn't open."),
        GuideStep("Report identity theft", "",
                  "If someone has used your information, report it at IdentityTheft.gov to get a "
                  "recovery plan."),
    ],
}

# Device setup: the five settings that matter most on each kind of device
PLATFORMS = ("Choose a device", "Windows", "Mac", "iPhone", "Android")
DEVICE_GUIDES = {
    "Windows": [
        GuideStep("Lock your screen", "Settings > Accounts > Sign-in options",
                  "Set up a PIN or Windows Hello, and ask Windows to require sign-in every time "
                  "you've been away."),
        GuideStep("Install updates automatically", "Settings > Windows Update",
                  "Check for updates and turn on getting the latest updates as soon as they're available."),
        GuideStep("Back up your files", "Settings > Accounts > Windows backup",
                  "Back up your folders to OneDrive, or use File History with an external drive."),
        GuideStep("Turn on Find my device", "Settings > Privacy & security > Find my device",
                  "Lets you locate and lock a lost laptop. It needs a Microsoft account."),
        GuideStep("Encrypt your drive", "Settings > Privacy & security > Device encryption",
                  "Keeps your files unreadable if the laptop is stolen. Windows Pro calls this BitLocker."),
    ],
    "Mac": [
        GuideStep("Lock your screen", "System Settings > Lock Screen",
                  "Require your password immediately after the screen saver starts or the display "
                  "turns off."),
        GuideStep("Install updates automatically", "System Settings > General > Software Update",
                  "Turn on automatic updates, including security responses and system files."),
        GuideStep("Back up with Time Machine", "System Settings > General > Time Machine",
                  "Add an external drive as a backup disk. iCloud Drive can also keep your documents."),
        GuideStep("Turn on Find My Mac", "System Settings > [your name] > iCloud",
                  "Lets you locate, lock or erase a lost Mac."),
        GuideStep("Turn on FileVault", "System Settings > Privacy & Security > FileVault",
                  "Encrypts your disk so a stolen Mac doesn't expose your files."),
    ],
    "iPhone": [
        GuideStep("Use a strong passcode", "Settings > Face ID & Passcode",
                  "Use a passcode of at least six digits, and set Auto-Lock in Settings > Display & "
                  "Brightness."),
        GuideStep("Install updates automatically", "Settings > General > Software Update > Automatic Updates",
                  "Turn on automatic download and installation of iOS updates and security responses."),
        GuideStep("Back up to iCloud", "Settings > [your name] > iCloud > iCloud Backup",
                  "A lost or broken phone then doesn't mean losing your photos and messages."),
        GuideStep("Turn on Find My iPhone", "Settings > [your name] > Find My",
                  "Lets you locate, lock or erase a lost iPhone."),
        GuideStep("Turn on Stolen Device Protection", "Settings > Face ID & Passcode",
                  "Requires Face ID or Touch ID for sensitive changes away from familiar places, even "
                  "if a thief knows your passcode."),
    ],
    "Android": [
        GuideStep("Set a screen lock", "Settings > Security & privacy > Screen lock",
                  "Choose a PIN, password or pattern, and add fingerprint or face unlock if you like."),
        GuideStep("Install updates", "Settings > System > Software updates",
                  "Install system updates and Google Play system updates when they're offered."),
        GuideStep("Back up your phone", "Settings > Google > Backup",
                  "Saves your photos, contacts and settings to your Google account."),
        GuideStep("Turn on Find Hub", "Settings > Google > Find Hub (formerly Find My Device)",
                  "Lets you locate, lock or erase a lost phone."),
        GuideStep("Keep Play Protect on", "Play Store > your profile picture > Play Protect",
                  "Scans apps for harmful behaviour. Install apps only from the Play Store."),
    ],
}
DEVICE_SOURCES = {
    "Windows": [("Microsoft: Windows help and learning", "https://support.microsoft.com/en-us/windows"),
                ("Microsoft: Find and lock a lost Windows device",
                 "https://support.microsoft.com/en-us/account-billing/find-and-lock-a-lost-windows-device-"
                 "890bf25e-b8ba-d3fe-8253-e98a12f26316")],
    "Mac": [("Apple: Mac User Guide", "https://support.apple.com/guide/mac-help/welcome/mac")],
    "iPhone": [("Apple: iPhone User Guide", "https://support.apple.com/guide/iphone/welcome/ios")],
    "Android": [("Google: Find, secure, or erase a lost Android device",
                 "https://support.google.com/android/answer/6160491"),
                ("Google: Back up or restore data on your Android device",
                 "https://support.google.com/android/answer/2819582")],
}


def initial_state() -> State:
    """
    Creates the starting progress for a new visit
    args:
        None
    returns:
        State - the starting safety tips, quiz progress, recommendations, focus, and page choices
    """
    return State([
        SafetyTip("Unique passwords", QUESTIONS[0][1], False),
        SafetyTip("Multifactor authentication", QUESTIONS[3][1], False),
        SafetyTip("Phishing awareness", QUESTIONS[4][1], False),
        SafetyTip("Software updates", QUESTIONS[5][1], False),
        SafetyTip("Reliable backups", QUESTIONS[6][1], False),
        SafetyTip("Account recovery", QUESTIONS[9][1], False),
    ], 0, 0, [], "", [], False, 0, 0, "", shuffled_order(), [], "")


def shuffled_order() -> list[int]:
    """
    Creates a random order for the Spot the Phish messages
    args:
        None
    returns:
        list[int] - every position in MESSAGES exactly once, in a random order
    """
    order = list(range(len(MESSAGES)))
    random.shuffle(order)
    return order


def ensure_phish_order(state: State) -> None:
    """
    Starts a fresh Spot the Phish round if the saved message order is not a full shuffle
    args:
        state (State) - the current session state to check and repair
    returns:
        None
    """
    if sorted(state.phish_order) != list(range(len(MESSAGES))):
        state.phish_order = shuffled_order()
        state.phish_position = 0
        state.phish_score = 0
        state.phish_guess = ""


def current_message(state: State) -> SampleMessage:
    """
    Finds the Spot the Phish message the user is currently on
    args:
        state (State) - the current session state with the message order and position
    returns:
        SampleMessage - the message at the current position of the shuffled order
    """
    return MESSAGES[state.phish_order[state.phish_position]]


def shell(state: State, title: str, content: list, lead: str = "",
          active: str = "", hero: bool = False) -> Page:
    """
    Creates a page with navigation links, a heading, and a footer
    args:
        state (State) - the current session state
        title (str) - the heading shown on the page
        content (list) - the text and components shown on the page
        lead (str) - a short sentence shown under the heading (empty for none)
        active (str) - the navigation link for this section ("Tools", "Phishing", "Devices",
                       "Checklist", "Quiz", "About", or "")
        hero (bool) - whether to show the large home page heading
    returns:
        Page - the page with the shared layout
    """
    links = [Link("Cyber Compass", "index", classes="brand")]
    for name, target in [("Tools", "password_tools"), ("Phishing", "phish_spotter"),
                         ("Devices", "device_guide"), ("Checklist", "checklist"),
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
        icon (str) - the icon name for the card (key, alert, checklist, quiz, mail, or device)
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
    Shows the home page with links to the six main areas
    args:
        state (State) - the current session state
    returns:
        Page - the home page with the six cards
    """
    return shell(state, "Cyber Compass", [
        Div(
            tile("key", "01", "Password & breach tools", "Check passwords and email exposure.", "password_tools"),
            tile("alert", "02", "After a breach", "Clear next steps when your data shows up in a leak.",
                 "breach_steps"),
            tile("checklist", "03", "Cyber Safety checklist", "Turn advice into six everyday habits.", "checklist"),
            tile("quiz", "04", "Cyber Safety Quiz", "Ten questions. A plan based on your answers.", "quiz"),
            tile("mail", "05", "Spot the Phish", str(len(MESSAGES)) + " practice messages. Can you tell which are fake?",
                 "phish_spotter"),
            tile("device", "06", "Device setup", "Lock down your laptop or phone, step by step.", "device_guide"),
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
        breach_link(),
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
    return shell(state, "Has your email appeared in a breach?", email_content() + [breach_link()],
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


def breach_link() -> Div:
    """
    Creates a card that points to the breach next steps page
    args:
        None
    returns:
        Div - the card with a short note and a link to the breach steps
    """
    return Div(Span("Found a match?", classes="next-step-title"),
               Link("See what to do after a breach →", "breach_steps"), classes="panel next-step")


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
        Page - the checklist page with the matching tips highlighted (plain before any quiz)
    """
    state.highlight = state.quiz_attempts > 0
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
    if state.focus:
        focus_note = ("★ marks the habits that matter most for your current focus: " + state.focus +
                      ". Change your focus and save to update the stars.")
    else:
        focus_note = "Choose a focus and save to star the habits that matter most for it."
    focus_field = SelectBox("focus", list(FOCUS_CHOICES), state.focus or FOCUS_CHOICES[0])
    focus_card = Div(Label("My current focus", focus_field), focus_field,
                     Div(focus_note, classes="focus-note"), classes="panel focus-card")
    progress = Div(Div(str(completed) + " of " + str(len(state.tips)) + " habits completed",
                       classes="progress-label"),
                   ProgressBar(completed, max=len(state.tips), classes="progress"),
                   Div("Progress lasts for this open session.", classes="progress-note"),
                   classes="panel progress-card")
    return shell(state, "Your safety checklist", [
        progress, HorizontalRule(classes="divider"), focus_card, *intro, *content,
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
        focus (str) - the selected focus: Accounts, Devices, or Awareness, or "Choose a focus" to clear it
    returns:
        Page - the checklist page with the updated progress
    """
    choices = [tip0, tip1, tip2, tip3, tip4, tip5]
    for position, tip in enumerate(state.tips):
        tip.completed = choices[position]
    if focus in FOCUS_CHOICES[1:]:
        state.focus = focus
    elif focus == FOCUS_CHOICES[0]:
        state.focus = ""
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
        classes="panel score-card " + score_band(state.quiz_score, 20))
    return shell(state, "Your next steps", [
        score_card, Header("Your next steps", 2), NumberedList(suggestions, classes="steps"),
        Button("Turn advice into action", "action_plan"), Button("Retake quiz", "quiz", classes="secondary"),
    ], "Small changes add up. Start with the first step.", "Quiz")


def score_band(score: int, total: int) -> str:
    """
    Chooses the style class that matches a score
    args:
        score (int) - the score, from 0 to total
        total (int) - the highest possible score
    returns:
        str - "score-high" for 80% or more, "score-mid" for 50% or more, otherwise "score-low"
    """
    if score * 5 >= total * 4:
        return "score-high"
    if score * 2 >= total:
        return "score-mid"
    return "score-low"


def message_card(message: SampleMessage, position: int) -> Div:
    """
    Creates a card that looks like an email or text message
    args:
        message (SampleMessage) - the practice message to show
        position (int) - how many messages came before this one in the current round
    returns:
        Div - the card with the sender, subject, body, and any link shown as plain text
    """
    rows = [Div(Span(message.kind, classes="message-kind"),
                Span("Message " + str(position + 1) + " of " + str(len(MESSAGES))),
                classes="message-meta"),
            Div(Span("From", classes="message-label"), Span(message.sender), classes="message-row")]
    if message.subject:
        rows.append(Div(Span("Subject", classes="message-label"), Span(message.subject),
                        classes="message-row"))
    rows.append(Div(message.body, classes="message-body"))
    if message.link:
        rows.append(Div(Span("Link", classes="message-label"), Span(message.link, classes="fake-link"),
                        classes="message-row"))
    return Div(*rows, classes="panel message")


@route
def phish_spotter(state: State) -> Page:
    """
    Shows the current practice message, its feedback once answered, or the final score
    args:
        state (State) - the current session state with the Spot the Phish progress
    returns:
        Page - the message with answer buttons, the feedback for an answer, or the summary
    """
    ensure_phish_order(state)
    if state.phish_position >= len(MESSAGES):
        return phish_summary(state)
    message = current_message(state)
    content = []
    if state.phish_position == 0 and not state.phish_guess:
        content.append("Each message is made up but based on real scams, and they appear in a random "
                       "order each time. Decide whether it's phishing or legitimate. Links are shown "
                       "as text only, so nothing here can be clicked.")
    else:
        answered = state.phish_position
        if state.phish_guess:
            answered += 1
        content.append(Div("Score so far: " + str(state.phish_score) + " of " + str(answered),
                           classes="phish-score"))
    content.append(message_card(message, state.phish_position))
    if not state.phish_guess:
        content.append(Div(
            Button("It's phishing", "check_phish", [Argument("guess", PHISH_CHOICES[0])]),
            Button("It's legitimate", "check_phish", [Argument("guess", PHISH_CHOICES[1])],
                   classes="secondary"),
            classes="phish-choices"))
    else:
        correct = (state.phish_guess == PHISH_CHOICES[0]) == message.is_phish
        if message.is_phish:
            answer = "This message is phishing."
            clue_heading = "What gives it away"
        else:
            answer = "This message is legitimate."
            clue_heading = "Why it can be trusted"
        if correct:
            content.append(Div(Header("Correct. " + answer, 2), classes="panel verdict correct"))
        else:
            content.append(Div(Header("Not quite. " + answer, 2), classes="panel verdict incorrect"))
        content.append(Header(clue_heading, 2))
        content.append(BulletedList(message.clues, classes="clues"))
        if state.phish_position + 1 < len(MESSAGES):
            content.append(Button("Next message", "next_phish"))
        else:
            content.append(Button("See my score", "next_phish"))
    return shell(state, "Spot the Phish", content,
                 str(len(MESSAGES)) + " messages in a random order. Which ones would you trust?", "Phishing")


@route
def check_phish(state: State, guess: str) -> Page:
    """
    Records the user's answer for the current message and updates the score
    args:
        state (State) - the current session state to update
        guess (str) - the user's answer: "Phishing" or "Legitimate"
    returns:
        Page - the current message with feedback, or the unchanged page if the answer is invalid
    """
    ensure_phish_order(state)
    if guess in PHISH_CHOICES and state.phish_position < len(MESSAGES) and not state.phish_guess:
        state.phish_guess = guess
        if (guess == PHISH_CHOICES[0]) == current_message(state).is_phish:
            state.phish_score += 1
    return phish_spotter(state)


@route
def next_phish(state: State) -> Page:
    """
    Moves on to the next practice message once the current one is answered
    args:
        state (State) - the current session state to update
    returns:
        Page - the next message, or the summary after the last one
    """
    if state.phish_guess:
        state.phish_position += 1
        state.phish_guess = ""
    return phish_spotter(state)


@route
def restart_phish(state: State) -> Page:
    """
    Starts the Spot the Phish activity again with the messages in a new random order
    args:
        state (State) - the current session state to reset
    returns:
        Page - the first practice message
    """
    state.phish_order = shuffled_order()
    state.phish_position = 0
    state.phish_score = 0
    state.phish_guess = ""
    return phish_spotter(state)


@route
def complete_phishing(state: State) -> Page:
    """
    Ticks off the phishing awareness habit after a Spot the Phish round
    args:
        state (State) - the current session state to update
    returns:
        Page - the checklist with phishing awareness completed
    """
    for tip in state.tips:
        if tip.title == "Phishing awareness":
            tip.completed = True
    state.highlight = False
    return checklist_page(state)


def phish_summary(state: State) -> Page:
    """
    Creates the final Spot the Phish page with the score and the red flags to remember
    args:
        state (State) - the current session state with the final score
    returns:
        Page - the summary page with the score, red flags, and next steps
    """
    total = len(MESSAGES)
    band = score_band(state.phish_score, total)
    if band == "score-high":
        message = "Sharp eyes. You can spot the common tricks."
    elif band == "score-mid":
        message = "Good instincts. Review the red flags below."
    else:
        message = "These messages are designed to fool people. The red flags below are worth remembering."
    score_card = Div(
        Div(Span(str(state.phish_score), classes="score-value"), Span("/ " + str(total), classes="score-max"),
            classes="score-number"),
        Div(Header(str(state.phish_score) + " of " + str(total) + " spotted correctly", 2), message,
            classes="score-text"),
        ProgressBar(state.phish_score, max=total, classes="progress"),
        classes="panel score-card " + band)
    return shell(state, "Your phishing score", [
        score_card,
        Header("Red flags to remember", 2),
        BulletedList(list(PHISH_RED_FLAGS), classes="clues"),
        Header("Got a real one?", 2),
        "Don't reply or click. Use your email app's report option, tell your school's IT team, then delete it.",
        BulletedList([Link("CISA: Recognize and report phishing",
                           "https://www.cisa.gov/secure-our-world/recognize-and-report-phishing")],
                     classes="sources"),
        Button("Tick off phishing awareness", "complete_phishing"),
        Button("Try again", "restart_phish", classes="secondary"),
    ], "Phishing works by rushing you. Slowing down is the best defence.", "Phishing")


def guide_steps(steps: list[GuideStep]) -> NumberedList:
    """
    Creates a numbered list of guide steps
    args:
        steps (list[GuideStep]) - the steps to show, in order
    returns:
        NumberedList - each step's title, where to find the setting (if any), and why it helps
    """
    items = []
    for step in steps:
        parts = [Header(step.title, 3)]
        if step.where:
            parts.append(Div(step.where, classes="settings-path"))
        parts.append(Div(step.why))
        items.append(Div(*parts))
    return NumberedList(items, classes="steps")


@route
def breach_steps(state: State) -> Page:
    """
    Shows what to do after a breach, with extra steps for each kind of exposed data
    args:
        state (State) - the current session state with the kinds of exposed data chosen
    returns:
        Page - the breach page with checkboxes and the matching steps
    """
    boxes = []
    for key, label, heading in EXPOSURE_TYPES:
        field = CheckBox(key, key in state.exposures)
        boxes.append(Div(field, Label(label, field), classes="tip-check"))
    content = [
        Div(Header("What was exposed?", 2), "Tick everything the breach notice or the Tools check mentioned.",
            *boxes, Button("Show my steps", "breach_plan"), classes="panel exposure-card"),
        Header("Start here", 2),
        guide_steps(list(FIRST_STEPS)),
    ]
    for key, label, heading in EXPOSURE_TYPES:
        if key in state.exposures:
            content.append(Header(heading, 2))
            content.append(guide_steps(BREACH_STEPS[key]))
    content += [
        Header("Official help", 2),
        BulletedList([
            Link("IdentityTheft.gov: Data breaches", "https://www.identitytheft.gov/databreach"),
            Link("AnnualCreditReport.com: free credit reports", "https://www.annualcreditreport.com/"),
            Link("CISA: Turn on multifactor authentication", "https://www.cisa.gov/secure-our-world/turn-mfa"),
        ], classes="sources"),
        Button("Check a password or email", "password_tools", classes="secondary"),
    ]
    return shell(state, "Your data was in a breach. Now what?", content,
                 "A calm, ordered list of what to do first.", "Tools")


@route
def breach_plan(state: State, password: bool, email: bool, financial: bool, identity: bool) -> Page:
    """
    Saves which kinds of data were exposed and shows the matching steps
    args:
        state (State) - the current session state to update
        password (bool) - whether a password was exposed
        email (bool) - whether an email address was exposed
        financial (bool) - whether card or bank details were exposed
        identity (bool) - whether an ID number was exposed
    returns:
        Page - the breach page with the matching steps, or a message if nothing was ticked
    """
    choices = [password, email, financial, identity]
    state.exposures = []
    for position, (key, label, heading) in enumerate(EXPOSURE_TYPES):
        if choices[position]:
            state.exposures.append(key)
    page = breach_steps(state)
    if not state.exposures:
        page.content.insert(3, Div("Tick at least one kind of data to see the steps for it.",
                                   classes="panel alert"))
    return page


@route
def device_guide(state: State) -> Page:
    """
    Shows the device picker and the setup steps for the chosen device
    args:
        state (State) - the current session state with the chosen device
    returns:
        Page - the device page with a device selection and the matching steps
    """
    field = SelectBox("platform", list(PLATFORMS), state.platform or PLATFORMS[0])
    content = [Div(Label("My device", field), field, Button("Show steps", "device_steps"),
                   classes="panel device-card")]
    if not state.platform:
        content.append("Choose a device to see the five settings that protect it most.")
        return shell(state, "Set up your device safely", content,
                     "Five settings, a few minutes each.", "Devices")
    content.append(Header("Your " + state.platform + " checklist", 2))
    if state.platform == "Android":
        content.append(Div("Menus vary between phone makers. If a setting isn't where it's listed, "
                           "search for it in Settings.", classes="panel priority-note"))
    content.append(guide_steps(DEVICE_GUIDES[state.platform]))
    sources = []
    for name, url in DEVICE_SOURCES[state.platform]:
        sources.append(Link(name, url))
    content += [
        Header("Official guides", 2),
        BulletedList(sources, classes="sources"),
        "Updates and backups are two of your checklist habits. Tick them off once they're set up.",
        Button("Go to my checklist", "checklist"),
    ]
    return shell(state, "Set up your device safely", content,
                 "Five settings, a few minutes each.", "Devices")


@route
def device_steps(state: State, platform: str) -> Page:
    """
    Saves the chosen device and shows its setup steps
    args:
        state (State) - the current session state to update
        platform (str) - the chosen device: Windows, Mac, iPhone, or Android, or "Choose a device" to clear it
    returns:
        Page - the device page with the matching steps
    """
    if platform in PLATFORMS[1:]:
        state.platform = platform
    elif platform == PLATFORMS[0]:
        state.platform = ""
    return device_guide(state)


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
        "analytics. Checklist and quiz progress only last while the page is open and clear when you reload. "
        "The one thing remembered is the colour theme you pick, saved in your own browser.",
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
            Link("CISA: Recognize and report phishing",
                 "https://www.cisa.gov/secure-our-world/recognize-and-report-phishing"),
            Link("IdentityTheft.gov: Data breaches", "https://www.identitytheft.gov/databreach"),
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
    assert_equal(state.focus, "")
    assert_equal("★" in str(checklist(state).content), False)
    assert_equal("Choose a focus and save" in str(checklist(state).content), True)
    assert_equal("SelectBox('focus', ['Choose a focus'" in str(checklist(state).content), True)
    assert_equal("HorizontalRule(classes='divider')" in str(checklist(state).content), True)
    assert_equal(state.tips[0].completed, False)
    assert_equal("Example title" in str(shell(state, "Example title", []).content), True)
    assert_equal("Open Example" in str(tile("key", "01", "Example", "Description", "quiz")), True)
    assert_equal("icon-key" in str(tile("key", "01", "Example", "Description", "quiz")), True)
    assert_equal("site-footer" in str(shell(state, "Example title", []).content), True)
    assert_equal("classes='active'" in str(shell(state, "Example", []).content), False)
    assert_equal("page-head hero" in str(index(state).content), True)
    assert_equal("Take the quiz" in str(index(state).content), False)
    assert_equal("classes='lead'" in str(index(state).content), True)
    assert_equal(score_band(0, 20), "score-low")
    assert_equal(score_band(9, 20), "score-low")
    assert_equal(score_band(10, 20), "score-mid")
    assert_equal(score_band(15, 20), "score-mid")
    assert_equal(score_band(16, 20), "score-high")
    assert_equal(score_band(20, 20), "score-high")
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
    assert_equal("colour theme you pick" in str(about(state).content), True)
    saved = save_checklist(state, True, False, True, False, True, False, "Devices")
    assert_equal([tip.completed for tip in saved.state.tips], [True, False, True, False, True, False])
    assert_equal(saved.state.focus, "Devices")
    assert_equal("3 of 6" in str(saved.content), True)
    assert_equal(str(saved.content).count("classes='panel tip done'"), 3)
    assert_equal(str(saved.content).count("classes='panel tip'"), 3)
    assert_equal(str(saved.content).count("★ Software updates"), 1)
    assert_equal(str(saved.content).count("★ Reliable backups"), 1)
    # Exactly those two tips are starred for the "Devices" focus
    assert_equal(sum(str(saved.content).count("★ " + tip.title) for tip in saved.state.tips), 2)
    assert_equal("★ Software updates" in str(saved.content), True)
    assert_equal("★ Reliable backups" in str(saved.content), True)
    assert_equal("★ Unique passwords" in str(saved.content), False)
    assert_equal("current focus: Devices" in str(saved.content), True)
    accounts = save_checklist(initial_state(), False, False, False, False, False, False, "Accounts")
    assert_equal("★ Unique passwords" in str(accounts.content), True)
    assert_equal("★ Account recovery" in str(accounts.content), True)
    assert_equal(save_checklist(accounts.state, False, False, False, False, False, False,
                                "Choose a focus").state.focus, "")
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
    # The Spot the Phish order is random, so compare everything else against a fresh start
    expected = initial_state()
    expected.phish_order = reset.state.phish_order
    assert_equal(reset.state, expected)
    assert_equal(sorted(reset.state.phish_order), list(range(len(MESSAGES))))
    assert_equal(reset.state is state, False)
    assert_equal("Progress reset" in str(reset.content), True)
    assert_equal("site-footer" in str(reset.content), True)
    assert_equal(initial_state().tips[0].completed, False)
    run_new_page_tests()


def run_new_page_tests() -> None:
    """
    Tests the Spot the Phish, breach steps, and device setup pages using separate example state
    args:
        None
    returns:
        None - checks the expected results using Bakery assertions.
    """
    state = initial_state()
    assert_equal(str(index(state).content).count("classes='tile'"), 6)
    assert_equal("icon-mail" in str(index(state).content), True)
    assert_equal("Link('Phishing', 'phish_spotter')" in str(index(state).content), True)
    assert_equal("Link('Devices', 'device_guide')" in str(index(state).content), True)
    assert_equal("breach_steps" in str(password_tools(state).content), True)
    assert_equal("breach_steps" in str(email_tools(state).content), True)
    assert_equal(score_band(4, 6), "score-mid")
    assert_equal(score_band(5, 6), "score-high")
    assert_equal(score_band(2, 6), "score-low")
    # Spot the Phish: messages, answers, scoring, and moving on
    assert_equal(len(MESSAGES), 30)
    for message in MESSAGES:
        assert_equal(len(message.clues), 3)
    # Every round shows each message exactly once, in a random order
    assert_equal(sorted(state.phish_order), list(range(30)))
    assert_equal(sorted(shuffled_order()), list(range(30)))
    shuffled = initial_state()
    shuffled.phish_order = [2] + [n for n in range(30) if n != 2]
    assert_equal(current_message(shuffled), MESSAGES[2])
    assert_equal("Message 1 of 30" in str(phish_spotter(shuffled).content), True)
    assert_equal(MESSAGES[2].sender in str(phish_spotter(shuffled).content), True)
    check_phish(shuffled, "Phishing")
    assert_equal(shuffled.phish_score, 1)
    broken = initial_state()
    broken.phish_order = [0, 1]
    phish_spotter(broken)
    assert_equal(sorted(broken.phish_order), list(range(30)))
    # Use the original order so the walkthrough below is predictable
    state.phish_order = list(range(30))
    first = phish_spotter(state)
    assert_equal("Link('Phishing', 'phish_spotter', classes='active')" in str(first.content), True)
    assert_equal("Message 1 of 30" in str(first.content), True)
    assert_equal("swiftship-redelivery.net" in str(first.content), True)
    assert_equal("Link('swiftship" in str(first.content), False)
    assert_equal("check_phish" in str(first.content), True)
    assert_equal("Score so far" in str(first.content), False)
    assert_equal("Subject" in str(message_card(MESSAGES[2], 2)), False)
    answered = check_phish(state, "Phishing")
    assert_equal(answered.state.phish_score, 1)
    assert_equal(answered.state.phish_guess, "Phishing")
    assert_equal("Correct. This message is phishing." in str(answered.content), True)
    assert_equal("classes='panel verdict correct'" in str(answered.content), True)
    assert_equal("What gives it away" in str(answered.content), True)
    assert_equal("check_phish" in str(answered.content), False)
    assert_equal("Score so far: 1 of 1" in str(answered.content), True)
    check_phish(state, "Legitimate")
    assert_equal(state.phish_score, 1)
    assert_equal(state.phish_guess, "Phishing")
    next_phish(state)
    assert_equal(state.phish_position, 1)
    assert_equal(state.phish_guess, "")
    next_phish(state)
    assert_equal(state.phish_position, 1)
    check_phish(state, "Maybe")
    assert_equal(state.phish_guess, "")
    wrong = check_phish(state, "Phishing")
    assert_equal(wrong.state.phish_score, 1)
    assert_equal("Not quite. This message is legitimate." in str(wrong.content), True)
    assert_equal("classes='panel verdict incorrect'" in str(wrong.content), True)
    assert_equal("Why it can be trusted" in str(wrong.content), True)
    for message in MESSAGES[2:]:
        next_phish(state)
        if message.is_phish:
            check_phish(state, "Phishing")
        else:
            check_phish(state, "Legitimate")
    assert_equal("See my score" in str(phish_spotter(state).content), True)
    summary = next_phish(state)
    assert_equal(summary.state.phish_score, 29)
    assert_equal("29 of 30 spotted correctly" in str(summary.content), True)
    assert_equal("panel score-card score-high" in str(summary.content), True)
    assert_equal("Red flags to remember" in str(summary.content), True)
    assert_equal("Link('Phishing', 'phish_spotter', classes='active')" in str(summary.content), True)
    assert_equal("Red flags to remember" in str(check_phish(state, "Phishing").content), True)
    assert_equal(state.phish_score, 29)
    restarted = restart_phish(state)
    assert_equal([restarted.state.phish_position, restarted.state.phish_score, restarted.state.phish_guess],
                 [0, 0, ""])
    assert_equal("Message 1 of 30" in str(restarted.content), True)
    assert_equal(sorted(restarted.state.phish_order), list(range(30)))
    # A broken order is repaired before an answer is scored, instead of crashing
    restarted.state.phish_order = []
    assert_equal(check_phish(restarted.state, "Phishing").state.phish_position, 0)
    assert_equal(sorted(restarted.state.phish_order), list(range(30)))
    # The summary button really ticks off the phishing habit
    ticked = complete_phishing(initial_state())
    assert_equal([tip.completed for tip in ticked.state.tips], [False, False, True, False, False, False])
    assert_equal("1 of 6 habits completed" in str(ticked.content), True)
    # The action plan does not claim quiz results before a quiz is taken
    fresh = initial_state()
    assert_equal(action_plan(fresh).state.highlight, False)
    assert_equal("don't point to any" in str(action_plan(fresh).content), False)
    assert_equal("30 practice messages" in str(index(fresh).content), True)
    # Breach steps: first steps always, extra sections for each ticked kind of data
    breach = breach_steps(state)
    assert_equal("Link('Tools', 'password_tools', classes='active')" in str(breach.content), True)
    assert_equal("Start here" in str(breach.content), True)
    assert_equal(str(breach.content).count("CheckBox("), 4)
    assert_equal("If a password was exposed" in str(breach.content), False)
    plan = breach_plan(state, True, False, False, True)
    assert_equal(plan.state.exposures, ["password", "identity"])
    assert_equal("If a password was exposed" in str(plan.content), True)
    assert_equal("If an ID number was exposed" in str(plan.content), True)
    assert_equal("If card or bank details were exposed" in str(plan.content), False)
    assert_equal("Freeze your credit" in str(plan.content), True)
    assert_equal("CheckBox('password', True" in str(plan.content), True)
    assert_equal("CheckBox('email')" in str(plan.content), True)
    assert_equal("classes='panel alert'" in str(plan.content), False)
    empty = breach_plan(state, False, False, False, False)
    assert_equal(empty.state.exposures, [])
    assert_equal("Tick at least one" in str(empty.content), True)
    assert_equal("classes='panel alert'" in str(empty.content), True)
    assert_equal("If a password was exposed" in str(empty.content), False)
    # Device setup: a picker, then the steps and official guides for the chosen device
    devices = device_guide(state)
    assert_equal("Link('Devices', 'device_guide', classes='active')" in str(devices.content), True)
    assert_equal("SelectBox('platform', ['Choose a device'" in str(devices.content), True)
    assert_equal("Choose a device to see" in str(devices.content), True)
    for platform in PLATFORMS[1:]:
        assert_equal(len(DEVICE_GUIDES[platform]), 5)
        shown = device_steps(state, platform)
        assert_equal(shown.state.platform, platform)
        assert_equal("Your " + platform + " checklist" in str(shown.content), True)
        assert_equal(str(shown.content).count("classes='settings-path'"), 5)
        assert_equal(DEVICE_SOURCES[platform][0][1] in str(shown.content), True)
    assert_equal("Menus vary" in str(device_steps(state, "Android").content), True)
    assert_equal("Menus vary" in str(device_steps(state, "Mac").content), False)
    assert_equal("FileVault" in str(device_steps(state, "Mac").content), True)
    device_steps(state, "Linux")
    assert_equal(state.platform, "Mac")
    assert_equal(device_steps(state, "Choose a device").state.platform, "")
    reset = reset_progress(state).state
    expected = initial_state()
    expected.phish_order = reset.phish_order
    assert_equal(reset, expected)


# Run the tests on your computer and during deployment, but not in the
# visitor's browser ("emscripten"), where each assertion looks up main.py
# over the network and slows down the first page load.
if sys.platform != "emscripten":
    assert_equal(run_bakery_tests(), None)

set_website_title("Cyber Compass | CISC 106")
set_website_style("none")
# The site has its own light and dark themes, so ask the Dark Reader extension
# not to restyle it (it rewrites colours and breaks the dropdown arrow's position).
add_website_header('<meta name="darkreader-lock">')
set_website_framed(False)
hide_debug_information()
add_website_css_file("style.css")
add_website_js_file("theme.js")
add_website_js_file("private-tools.js")

start_server(initial_state(), port=8001, host="127.0.0.1", open_browser=True)


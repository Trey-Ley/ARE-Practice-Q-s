#!/usr/bin/env python3
"""
ARE 5.0 daily flashcard email — offline question bank, no API, no cost.

Every weekday at 7:45 AM Chicago time you get three exam-style questions, alternating:
  Set A: PcM, PjM, CE      Set B: PA, PDD, PPD

All 20 days (60 questions) live in are_questions.json. The script works through them in
order, one day per weekday, tracking its place in are_progress.json. The last few emails
of the set warn you that the bank is running low so you can regenerate it.

The email has all three questions first, then a screen of blank space, then the answer
key: why the right answer is right, why each wrong answer is wrong, and the citation.

Usage:
  python are_flashcards.py            # today's set
  python are_flashcards.py --test     # send now, ignoring the weekday check
  python are_flashcards.py --preview  # print to the screen, send nothing, don't advance
  python are_flashcards.py --day 7    # send a specific day (0-19) without advancing
  python are_flashcards.py --status   # print how many days remain
"""
import argparse
import json
import os
import re
import smtplib

from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo


TZ = ZoneInfo("America/Chicago")
QUESTIONS_FILE = os.getenv("QUESTIONS_FILE", "are_questions.json")
PROGRESS_FILE = os.getenv("PROGRESS_FILE", "are_progress.json")
LOW_WARNING_AT = 3          # start warning when this many days (or fewer) remain

NAMES = {
    "PcM": "Practice Management",
    "PjM": "Project Management",
    "PA": "Programming & Analysis",
    "PPD": "Project Planning & Design",
    "PDD": "Project Development & Documentation",
    "CE": "Construction & Evaluation",
}


def log(*a):
    print(datetime.now(TZ).strftime("[%H:%M:%S]"), *a, flush=True)


def load_bank():
    with open(QUESTIONS_FILE) as f:
        return json.load(f)["days"]


def load_progress():
    try:
        with open(PROGRESS_FILE) as f:
            return int(json.load(f).get("next_index", 0))
    except Exception:
        return 0


def save_progress(i):
    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump({"next_index": i,
                       "updated": datetime.now(TZ).date().isoformat()}, f, indent=1)
    except Exception as e:
        log("Couldn't save progress:", e)


def banner_for(remaining, cycle):
    """Message warning that the bank is running out (or has wrapped around)."""
    if cycle > 0:
        return ("You have now seen every question in this bank. These are repeats from "
                "round %d. Ask Claude to generate a fresh 20-day set when you want new ones." % (cycle + 1))
    if remaining == 0:
        return ("LAST DAY of this question bank. There are no new questions after this email. "
                "Ask Claude to generate a fresh 20-day set, then replace are_questions.json "
                "and delete are_progress.json to start the new bank at day 1.")
    if remaining <= LOW_WARNING_AT:
        return ("Running low: %d day%s of new questions left after today. Time to ask Claude "
                "for a fresh 20-day set." % (remaining, "" if remaining == 1 else "s"))
    return ""


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render(qs, d, letter, note=""):
    day = d.strftime("%A, %B %-d, %Y")
    divs = ", ".join(q["division"] for q in qs)
    css_q = "margin:0 0 6px;font:600 15px/1.5 Georgia,serif"
    html = [f"""<div style="max-width:660px;margin:0 auto;font:15px/1.6 Georgia,serif;color:#1a1a1a">
<h2 style="margin:0 0 2px">ARE 5.0 — Set {letter}: {esc(divs)}</h2>
<div style="color:#666;font-size:13px">{esc(day)}</div>"""]
    text = [f"ARE 5.0 — Set {letter}: {divs}", day, ""]
    if note:
        html.append(f'<p style="background:#fff6e0;border-left:4px solid #e0a800;'
                    f'padding:10px 12px;font-size:13px;margin:12px 0">⚠️ {esc(note)}</p>')
        text += ["** " + note + " **", ""]

    for i, q in enumerate(qs, 1):
        html.append(f"""<hr style="border:none;border-top:1px solid #ddd;margin:22px 0">
<div style="font:600 12px/1 Helvetica,sans-serif;letter-spacing:.08em;color:#8a6d3b">
QUESTION {i} — {esc(q['division'])} · {esc(NAMES[q['division']])}</div>
<p style="{css_q}">{esc(q['stem'])}</p><table cellpadding="3" style="font-size:15px">""")
        text += [f"--- QUESTION {i} — {q['division']} ({NAMES[q['division']]})", q["stem"], ""]
        for ltr in "ABCD":
            html.append(f'<tr><td valign="top"><b>{ltr}.</b></td><td>{esc(q["options"][ltr])}</td></tr>')
            text.append(f"   {ltr}. {q['options'][ltr]}")
        html.append("</table>")
        text.append("")

    spacer = "<br>" * 34
    html.append(f"""<div style="text-align:center;color:#999;font:13px Helvetica,sans-serif;
padding:14px 0;border-top:1px solid #ddd">↓ answers below — scroll when you're ready ↓</div>{spacer}
<h2 style="margin:0 0 10px;border-top:3px solid #1a1a1a;padding-top:10px">Answer key</h2>""")
    text += ["", "=" * 60, "ANSWERS (scroll past)", "=" * 60, ""]

    for i, q in enumerate(qs, 1):
        c = q["correct"]
        html.append(f"""<div style="margin:18px 0 6px;font:600 12px/1 Helvetica,sans-serif;
letter-spacing:.08em;color:#8a6d3b">QUESTION {i} — {esc(q['division'])}</div>
<p style="margin:0 0 8px"><b style="color:#1e7a34">Correct: {c}.</b> {esc(q['options'][c])}</p>
<p style="margin:0 0 10px">{esc(q['why_correct'])}</p>
<div style="font:600 13px Helvetica,sans-serif;margin-bottom:4px">Why the others fail</div><ul style="margin:0 0 8px;padding-left:20px">""")
        text += [f"QUESTION {i} — {q['division']}", f"Correct: {c}. {q['options'][c]}", q["why_correct"], "Why the others fail:"]
        for ltr in "ABCD":
            if ltr == c:
                continue
            html.append(f'<li style="margin-bottom:5px"><b>{ltr}.</b> {esc(q["why_wrong"].get(ltr, ""))}</li>')
            text.append(f"   {ltr}. {q['why_wrong'].get(ltr, '')}")
        ref = q.get("reference", "")
        html.append(f'</ul><div style="font-size:13px;color:#666">Reference: {esc(ref)}</div>')
        text += [f"Reference: {ref}", ""]

    html.append('<p style="color:#999;font-size:12px;margin-top:26px">Practice questions written for '
                'self-study; they are not NCARB items. Always verify against the current ARE 5.0 '
                'Guidelines and cited documents.</p></div>')
    text.append("Practice questions for self-study; not NCARB items.")
    flag = "⚠️ LAST SET — " if note.startswith("LAST DAY") else ""
    return "".join(html), "\n".join(text), f"{flag}ARE daily — {divs} ({day.split(',')[0]})"


def send_email(subject, html, text):
    sender = os.environ["GMAIL_ADDRESS"].strip()
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = sender, (os.getenv("EMAIL_TO") or sender), subject
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(sender, re.sub(r"\s", "", os.environ["GMAIL_APP_PASSWORD"]))
        smtp.send_message(msg)
    log("Email sent:", subject)


def correct_dst_slot(now):
    cron = os.getenv("TRIGGER_CRON", "").strip()
    if not cron:
        return True
    hour = cron.split()[1]
    offset = now.utcoffset().total_seconds() / 3600
    return (hour == "12" and offset == -5) or (hour == "13" and offset == -6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", type=int, help="send a specific day (0-based) without advancing")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    bank = load_bank()
    total = len(bank)
    cursor = load_progress()

    if args.status:
        done, cycle = cursor % total, cursor // total
        print(f"{total} days in the bank; {total - done} new day(s) left"
              f"{' (round ' + str(cycle + 1) + ')' if cycle else ''}.")
        return

    now = datetime.now(TZ)
    today = now.date()
    if not (args.test or args.preview or args.day is not None):
        if not correct_dst_slot(now):
            log("Other daylight-saving slot handles today. Exiting.")
            return
        if today.weekday() >= 5:
            log("Weekend. Exiting.")
            return

    index = args.day if args.day is not None else cursor
    day = bank[index % total]
    cycle = index // total
    remaining = total - (index % total) - 1
    log(f"Day {index % total + 1} of {total} — Set {day['set']}"
        f"{' (repeat round ' + str(cycle + 1) + ')' if cycle else ''}")

    html, text, subject = render(day["questions"], today, day["set"],
                                 banner_for(remaining, cycle))
    if args.preview:
        print(text)
        return
    send_email(subject, html, text)
    if args.day is None:
        save_progress(index + 1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        try:
            sender = os.environ["GMAIL_ADDRESS"].strip()
            m = EmailMessage()
            m["From"], m["To"] = sender, (os.getenv("EMAIL_TO") or sender)
            m["Subject"] = "⚠️ ARE flashcards didn't send today"
            m.set_content(f"{type(e).__name__}: {e}")
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
                s.login(sender, re.sub(r"\s", "", os.environ["GMAIL_APP_PASSWORD"]))
                s.send_message(m)
        except Exception:
            pass
        raise

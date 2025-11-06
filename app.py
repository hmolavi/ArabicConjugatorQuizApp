"""Simple Tkinter-based Arabic conjugation quiz app.

This app uses the local `arabic_conjugator_hmolavi` package (sibling
folder `../ArabicConjugator/src`) when available.

Run: python app.py

The UI asks multiple-choice questions (4 options). It supports a few
question styles to practice conjugations, tenses, moods, and pronouns.
"""

import os
import platform
import sys
import random
import tkinter as tk
from tkinter import messagebox
from arabic_reshaper import ArabicReshaper
from bidi.algorithm import get_display
import arabic_conjugator_hmolavi as ac


def should_reverse_gui_text():
    """
    Determines if Arabic text needs to be reshaped and reversed for GUI display.

    Returns:
        bool: True if the OS is likely a minimal environment (like Linux on Replit)
              that requires a fix. False otherwise.
    """
    # CLI/GUI override takes precedence when set
    if "FORCE_REVERSE_GUI" in globals() and globals().get("FORCE_REVERSE_GUI") is not None:
        return bool(globals().get("FORCE_REVERSE_GUI"))
    return platform.system() == "Linux"


def format_text_gui(text):
    """Return a GUI-ready string: reshape + bidi if GUI environment requires it and reshaper is available."""
    if not text:
        return text
    if not should_reverse_gui_text():
        return text
    try:
        cfg = {"delete_harakat": False, "shift_harakat_position": False}
        return get_display(ArabicReshaper(configuration=cfg).reshape(str(text)))
    except Exception:
        pass
    return text


# Small sample verb list (past-tense form with harakat). Keep variety in Babs.
SAMPLE_VERBS = [
    "كَتَبَ",  # kataba
    "فَتَحَ",  # fatha
    "نَصَرَ",  # nasara
    "ضَرَبَ",  # daraba
    "سَمِعَ",  # sami'a (kasra on second letter)
    "حَسِبَ",  # hasiba
    "كَرُمَ",  # karuma (damma on second)
    "دَرَسَ",  # darasa
    "شَرِبَ",
]

# Pronoun labels matching the 14-form ordering used by the conjugator
PRONOUNS = [
    ("3rd masc sing", "هو"),
    ("3rd masc dual", "هما"),
    ("3rd masc pl", "هم"),
    ("3rd fem sing", "هي"),
    ("3rd fem dual", "هما"),
    ("3rd fem pl", "هنّ"),
    ("2nd masc sing", "أنتَ"),
    ("2nd dual", "أنتما"),
    ("2nd masc pl", "أنتم"),
    ("2nd fem sing", "أنتِ"),
    ("2nd dual (alt)", "أنتما"),
    ("2nd fem pl", "أنتنّ"),
    ("1st sing", "أنا"),
    ("1st pl", "نحن"),
]


def safe_conjugate(verb, tense="past", bab_key=None, mood=None, reverse_input=False):
    """Wrapper that calls the package's conjugate_verb and returns (title, forms).

    If the package is not importable, return placeholder forms for testing.
    """
    if ac:
        try:
            return ac.conjugate_verb(verb, tense=tense, bab_key=bab_key, mood=mood, reverse_input=reverse_input)
        except Exception as e:
            # fall through to fallback
            print("Conjugation error:", e)

    # Fallback: manufacture fake conjugations by appending index (for offline testing)
    forms = [f"{verb}[{i}]" for i in range(14)]
    title = f"{tense} - {mood or 'default'}"
    return title, forms


class QuizApp:
    def __init__(self, master):
        self.master = master
        master.title("Arabic Conjugation Quiz")

        self.score = 0
        self.total = 0

        # UI layout
        self.header = tk.Label(master, text="Arabic Conjugation Quiz", font=(None, 16))
        self.header.pack(pady=6)

        self.question_frame = tk.Frame(master)
        self.question_frame.pack(pady=10)

        self.q_text = tk.Label(self.question_frame, text="", font=(None, 14), wraplength=500, justify="center")
        self.q_text.pack()

        self.meta_text = tk.Label(self.question_frame, text="", fg="gray")
        self.meta_text.pack()

        self.buttons_frame = tk.Frame(master)
        self.buttons_frame.pack(pady=8)

        self.option_vars = []
        self.option_buttons = []
        for i in range(4):
            btn = tk.Button(self.buttons_frame, text=f"Option {i+1}", width=36, command=lambda i=i: self.check_answer(i))
            btn.grid(row=i, column=0, pady=4)
            self.option_buttons.append(btn)

        self.status = tk.Label(master, text="Score: 0/0")
        self.status.pack(pady=6)

        self.controls = tk.Frame(master)
        self.controls.pack()

        tk.Button(self.controls, text="Next", command=self.next_question).grid(row=0, column=0, padx=6)
        tk.Button(self.controls, text="Quit", command=master.quit).grid(row=0, column=1, padx=6)

        # question generation state
        self.correct_index = None
        self.current_answer = None
        self.current_style = None

        self.next_question()

    def update_status(self):
        self.status.config(text=f"Score: {self.score}/{self.total}")

    def next_question(self):
        # pick a random style
        style = random.choice([1, 2, 3, 4])
        self.current_style = style
        if style == 1:
            q = self.make_style1()
        elif style == 2:
            q = self.make_style2()
        elif style == 3:
            q = self.make_style3()
        else:
            q = self.make_style_extra()

        self.display_question(q)

    def display_question(self, q):
        # q: dict with keys: text, meta, options (list), correct (string)
        # Format question and meta for GUI (handles Arabic reshaping/bidi when needed)
        qtext_raw = q.get("text", "")
        meta_raw = q.get("meta", "")
        self.q_text.config(text=format_text_gui(qtext_raw))
        self.meta_text.config(text=format_text_gui(meta_raw))

        opts = q.get("options", [])
        # Store formatted correct answer for comparison
        self.current_answer = format_text_gui(q.get("correct"))

        # shuffle options to randomize positions (format options for display)
        combined = [format_text_gui(o) for o in opts]
        random.shuffle(combined)
        # find the index of the formatted correct answer
        try:
            self.correct_index = combined.index(self.current_answer)
        except ValueError:
            # fallback: if not found (shouldn't happen), set to None
            self.correct_index = None

        for i, btn in enumerate(self.option_buttons):
            text = combined[i] if i < len(combined) else ""
            btn.config(text=text, state=tk.NORMAL, bg=None)
        # store for checking
        self.shown_options = combined

    def check_answer(self, chosen_idx):
        chosen_text = self.shown_options[chosen_idx]
        correct = self.current_answer
        self.total += 1
        if chosen_text == correct:
            self.score += 1
            self.option_buttons[chosen_idx].config(bg="#a6f3a6")
        else:
            self.option_buttons[chosen_idx].config(bg="#f3a6a6")
            # highlight correct
            for i, opt in enumerate(self.shown_options):
                if opt == correct:
                    self.option_buttons[i].config(bg="#a6f3f3")
        # disable buttons until Next
        for b in self.option_buttons:
            b.config(state=tk.DISABLED)

        self.update_status()

    # --- Question generation strategies ---
    def make_style1(self):
        """Show pronoun + base verb, ask for correct conjugation for that pronoun/tense/mood."""
        verb = random.choice(SAMPLE_VERBS)
        tense = random.choice(["past", "present"])
        bab_key = None
        mood = None
        if tense == "present":
            bab_key = random.choice(list(ac.BABS.keys())) if ac else None
            mood = random.choice([m[0] for m in (ac.MOODS if ac else [("Indicative (مرفوع)",), ("Subjunctive (منصوب)",), ("Jussive (مجزوم)",)])])

        title, forms = safe_conjugate(verb, tense=tense, bab_key=bab_key, mood=mood)
        pron_index = random.randrange(14)
        correct = forms[pron_index]

        # distractor 1: same verb different mood/tense
        d1_title, d1_forms = safe_conjugate(
            verb, tense=("present" if tense == "past" else "past"), bab_key=bab_key, mood=(None if mood else "Indicative (مرفوع)")
        )
        d1 = d1_forms[pron_index]

        # distractor 2: similar pronoun (choose neighbor index)
        neighbor = (pron_index + random.choice([-2, -1, 1, 2])) % 14
        d2 = forms[neighbor]

        # distractor 3: same pronoun/tensen but different verb
        other = random.choice([v for v in SAMPLE_VERBS if v != verb])
        ot_title, ot_forms = safe_conjugate(other, tense=tense, bab_key=bab_key, mood=mood)
        d3 = ot_forms[pron_index]

        options = [correct, d1, d2, d3]
        qtext = f"Select the correct conjugation for pronoun: {PRONOUNS[pron_index][0]} ({PRONOUNS[pron_index][1]})\nBase verb: {verb}"
        meta = f"Tense: {tense}  Mood: {mood or '—'}"
        return {"text": qtext, "meta": meta, "options": options, "correct": correct}

    def make_style2(self):
        """Show a conjugated form; ask which tense/mood it is (4 choices)."""
        verb = random.choice(SAMPLE_VERBS)
        # pick either past or present
        tense = random.choice(["past", "present"])
        bab_key = None
        mood = None
        if tense == "present":
            bab_key = random.choice(list(ac.BABS.keys())) if ac else None
            mood = random.choice([m[0] for m in (ac.MOODS if ac else [("Indicative (مرفوع)",), ("Subjunctive (منصوب)",), ("Jussive (مجزوم)",)])])

        title, forms = safe_conjugate(verb, tense=tense, bab_key=bab_key, mood=mood)
        pron = random.randrange(14)
        conj = forms[pron]

        # options: different tense/mood combos
        candidates = []
        candidates.append((tense, mood))
        # add three distractors
        distracts = []
        distract_tenses = [("past", None), ("present", "Indicative (مرفوع)"), ("present", "Subjunctive (منصوب)"), ("present", "Jussive (مجزوم)")]
        random.shuffle(distract_tenses)
        for t, m in distract_tenses:
            if (t, m) != (tense, mood) and len(distracts) < 3:
                distracts.append((t, m))

        options = []
        for t, m in [(tense, mood)] + distracts[:3]:
            label = t if m is None else f"{t} - {m}"
            options.append(label)

        qtext = f"Which tense/mood is this conjugated form?\n\n{conj}"
        meta = f"Pronoun: {PRONOUNS[pron][0]} ({PRONOUNS[pron][1]})  Base verb hidden"
        correct_label = tense if mood is None else f"{tense} - {mood}"
        return {"text": qtext, "meta": meta, "options": options, "correct": correct_label}

    def make_style3(self):
        """Given a conjugation A, ask: if base verb were conjugated for new (tense/mood/pronoun), which would it be?"""
        verb = random.choice(SAMPLE_VERBS)
        tense_a = random.choice(["past", "present"])
        mood_a = None
        bab_a = None
        if tense_a == "present":
            bab_a = random.choice(list(ac.BABS.keys())) if ac else None
            mood_a = random.choice([m[0] for m in (ac.MOODS if ac else [("Indicative (مرفوع)",), ("Subjunctive (منصوب)",), ("Jussive (مجزوم)",)])])

        t_a, forms_a = safe_conjugate(verb, tense=tense_a, bab_key=bab_a, mood=mood_a)
        pron_a = random.randrange(14)
        conj_a = forms_a[pron_a]

        # target settings
        tense_b = random.choice(["past", "present"])
        mood_b = None
        bab_b = None
        if tense_b == "present":
            bab_b = random.choice(list(ac.BABS.keys())) if ac else None
            mood_b = random.choice([m[0] for m in (ac.MOODS if ac else [("Indicative (مرفوع)",), ("Subjunctive (منصوب)",), ("Jussive (مجزوم)",)])])

        _, forms_b = safe_conjugate(verb, tense=tense_b, bab_key=bab_b, mood=mood_b)
        correct = forms_b[pron_a]

        # three distractors: (1) same verb different pronoun, (2) different verb same target, (3) same pronunciation but different mood
        d1 = forms_b[(pron_a + 1) % 14]
        other = random.choice([v for v in SAMPLE_VERBS if v != verb])
        _, other_forms = safe_conjugate(other, tense=tense_b, bab_key=bab_b, mood=mood_b)
        d2 = other_forms[pron_a]
        # different mood/tense
        alt_t = "past" if tense_b == "present" else "present"
        _, alt_forms = safe_conjugate(verb, tense=alt_t, bab_key=bab_b, mood=mood_b)
        d3 = alt_forms[pron_a]

        options = [correct, d1, d2, d3]
        qtext = f"Given this conjugated form (A): {conj_a}\nIf the same base verb were conjugated for: Tense={tense_b} Mood={mood_b or '—'} Pronoun={PRONOUNS[pron_a][0]}, which would it be?"
        meta = f"Base verb: {verb} (conjugation A shown)"
        return {"text": qtext, "meta": meta, "options": options, "correct": correct}

    def make_style_extra(self):
        """Extra challenge: match base verb given conjugated form among 4 verbs."""
        verbs = random.sample(SAMPLE_VERBS, 4)
        verb = verbs[0]
        tense = random.choice(["past", "present"])
        bab_key = None
        mood = None
        if tense == "present":
            bab_key = random.choice(list(ac.BABS.keys())) if ac else None
            mood = random.choice([m[0] for m in (ac.MOODS if ac else [("Indicative (مرفوع)",), ("Subjunctive (منصوب)",), ("Jussive (مجزوم)",)])])

        _, forms = safe_conjugate(verb, tense=tense, bab_key=bab_key, mood=mood)
        pron = random.randrange(14)
        conj = forms[pron]

        options = []
        for v in verbs:
            t, f = safe_conjugate(v, tense=tense, bab_key=bab_key, mood=mood)
            options.append(v)

        correct = verb
        qtext = f"Which base verb produced this conjugation?\n\n{conj}"
        meta = f"Pronoun: {PRONOUNS[pron][0]}  Tense: {tense}"
        return {"text": qtext, "meta": meta, "options": options, "correct": correct}


def main():
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

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
from tkinter import messagebox, ttk
from arabic_reshaper import ArabicReshaper
from bidi.algorithm import get_display
import arabic_conjugator_hmolavi as ac

def is_system_macos():
    """Check if the current operating system is macOS."""
    return platform.system() == "Darwin"

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


# Example verbs with their associated "bab" (remove random bab selection - each verb carries its bab)
SAMPLE_VERBS = [
    {"verb": "فَعَلَ", "bab": "Fatha/Fatha (فَتَحَ / يَفْتَحُ)"},
    {"verb": "ذَهَبَ", "bab": "Fatha/Fatha (فَتَحَ / يَفْتَحُ)"},
    {"verb": "كَتَبَ", "bab": "Fatha/Damma (نَصَرَ / يَنْصُرُ)"},
    {"verb": "جَلَسَ", "bab": "Fatha/Kasra (ضَرَبَ / يَضْرِبُ)"},
    {"verb": "شَرِبَ", "bab": "Kasra/Fatha (سَمِعَ / يَسْمَعُ)"},
    {"verb": "كَرُمَ", "bab": "Damma/Damma (كَرُمَ / يَكْرُمُ)"},
    {"verb": "حَسِبَ", "bab": "Kasra/Kasra (حَسِبَ / يَحْسِبُ)"},
    {"verb": "قَرَأَ", "bab": "Fatha/Fatha (فَتَحَ / يَفْتَحُ)"},
    {"verb": "دَخَلَ", "bab": "Fatha/Damma (نَصَرَ / يَنْصُرُ)"},
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
    ("2nd dual", "أنتما"),
    ("2nd fem pl", "أنتنّ"),
    ("1st sing", "أنا"),
    ("1st pl", "نحن"),
]

UNIQUE_PRONOUNS_IDX = [0, 1, 2, 3, 5, 6, 7, 8, 9, 11, 12, 13]  # excludes duplicates: 7=10, 1=4


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
        # Scoring toggle: disabled by default
        self.scoring_enabled = False

        # UI layout
        self.header = tk.Label(master, text="Arabic Conjugation Quiz", font=(None, 16))
        self.header.pack(pady=6)

        self.question_frame = tk.Frame(master)
        self.question_frame.pack(pady=10)

        self.q_text = tk.Label(self.question_frame, text="", font=(None, 14), wraplength=500, justify="center")
        self.q_text.pack()

        # Meta/hint: create the meta label but don't show it by default. A hint button will occupy
        # the same location; clicking it will reveal the meta and hide the button for that question.
        self.meta_text = tk.Label(self.question_frame, text="", fg="gray")
        # hint button placed where meta would appear
        self.hint_button = tk.Button(self.question_frame, text="Show hint", command=self.show_hint)
        self.hint_button.pack()

        self.buttons_frame = tk.Frame(master)
        self.buttons_frame.pack(pady=8)

        self.option_vars = []
        self.option_buttons = []
        for i in range(4):
            btn = tk.Button(self.buttons_frame, text=f"Option {i+1}", width=25, height=2, command=lambda i=i: self.check_answer(i))
            btn.grid(row=i // 2, column=i % 2, padx=6, pady=4)
            self.option_buttons.append(btn)

        # Start with scoring shown as disabled (greyed out)
        self.status = tk.Label(master, text="Score: 0 / 0", fg=self.master.cget("bg"))
        self.status.pack(pady=6)

        self.controls = tk.Frame(master)
        self.controls.pack(pady=(6, 12))

        tk.Button(self.controls, text="Next", command=self.next_question).grid(row=0, column=0, padx=6)
        tk.Button(self.controls, text="Quit", command=master.quit).grid(row=0, column=1, padx=6)
        # scoring toggle button (starts disabled)
        self.score_button = tk.Button(self.controls, text="Score", command=self.toggle_scoring, height=2)
        self.score_button.grid(row=0, column=2, padx=6)

        # Font size selector: dropdown (readonly combobox)
        # Use a StringVar for the combobox and store numeric sizes as strings
        self.font_size_var = tk.StringVar(value="20")
        tk.Label(self.controls, text="Font size:").grid(row=0, column=3, padx=(6, 2))
        self.font_size_combo = ttk.Combobox(
            self.controls,
            textvariable=self.font_size_var,
            values=[12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 48],
            width=4,
            state="readonly",
        )
        self.font_size_combo.grid(row=0, column=4, padx=(0, 6))
        # bind selection change
        self.font_size_combo.bind("<<ComboboxSelected>>", lambda e: self.on_font_size_change(self.font_size_var.get()))
        # apply initial font sizes
        self.apply_font_size()

        # question generation state
        self.correct_index = None
        self.current_answer = None
        self.current_style = None

        self.next_question()

    def update_status(self):
        # Update the status text and color depending on whether scoring is enabled.
        # When scoring is enabled show the score in white; when disabled set
        # the text color to the window background so it visually deactivates
        # (fallback to gray when background cannot be determined).
        self.status.config(text=f"Score: {self.score} / {self.total}")
        try:
            master_bg = self.master.cget("bg")
        except Exception:
            master_bg = None

        if self.scoring_enabled:
            fg = "white"
        else:
            fg = master_bg if master_bg is not None else "gray"

        try:
            self.status.config(fg=fg)
        except Exception:
            pass

    def next_question(self):
        self.reset_btn_colors()

        # pick a random style
        style = random.choice([1, 2, 3, 4, 5])
        self.current_style = style
        if style == 1:
            q = self.make_style1()
        elif style == 2:
            q = self.make_style2()
        elif style == 3:
            q = self.make_style3()
        elif style == 4:
            q = self.make_style4()
        else:
            q = self.make_style5()

        self.display_question(q)

    def display_question(self, q):
        # q: dict with keys: text, meta, options (list), correct (string)
        # Format question and meta for GUI (handles Arabic reshaping/bidi when needed)
        qtext_raw = q.get("text", "")
        meta_raw = q.get("meta", "")
        # set question text
        self.q_text.config(text=format_text_gui(qtext_raw))
        # prepare meta but keep it hidden until user requests hint
        self.meta_text.config(text=format_text_gui(meta_raw), pady=5)
        try:
            self.meta_text.pack_forget()
        except Exception:
            pass
        # show the hint button in the same location
        try:
            self.hint_button.pack_forget()
        except Exception:
            pass
        # Pack the hint button in the same location and force a redraw to avoid
        # a race where the button doesn't become visible until another UI event.
        self.hint_button.pack()
        try:
            # bring to top and force geometry update
            self.hint_button.lift()
            self.question_frame.update_idletasks()
        except Exception:
            pass

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
            # restore the clickable command and reset visual state (no emoji yet)
            btn.config(text=text, state=tk.NORMAL, bg=None, command=(lambda i=i: self.check_answer(i)))
        # store for checking
        self.shown_options = combined

    def reset_btn_colors(self):
        for i, btn in enumerate(self.option_buttons):
            try:
                btn.config(bg=self.master.cget("bg"), activebackground="#ececec")
            except Exception:
                pass

    def check_answer(self, chosen_idx):
        chosen_text = self.shown_options[chosen_idx]
        correct = self.current_answer
        # Only update score/total when scoring is enabled. Always show feedback.
        if self.scoring_enabled:
            self.total += 1
            if chosen_text == correct:
                self.score += 1

        for i, btn in enumerate(self.option_buttons):
            # base text for the option (already formatted for GUI)
            try:
                opt_text = self.shown_options[i]
            except Exception:
                opt_text = btn.cget("text")

            display = opt_text
            bg_color = None

            def append_symbol(text, correct_ans):
                """Helper to append a symbol to text if only in macOS."""

                if not is_system_macos():
                    return text

                if correct_ans:
                    return f"{text} ✅"
                else:
                    return f"{text} ❌"

            if i == chosen_idx:
                # the option the user picked
                if opt_text == correct:
                    display = append_symbol(opt_text, True)
                    bg_color = "#90EE90"  # light green
                else:
                    display = append_symbol(opt_text, False)
                    bg_color = "#FFB6C6"  # light red/pink
            elif opt_text == correct:
                # the correct answer (if not chosen)
                display = append_symbol(opt_text, True)
                bg_color = "#90EE90"  # light green
            else:
                bg_color = self.master.cget("bg")

            try:
                btn.config(text=display, bg=bg_color, activebackground=bg_color)
            except Exception:
                pass

            # lock further clicks by replacing the command with a no-op. This
            # preserves widget appearance across themes (vs disabling which
            # often greys-out the widget and hides styling).
            try:
                btn.config(command=lambda: None)
            except Exception:
                try:
                    btn.config(state=tk.DISABLED)
                except Exception:
                    pass

        self.update_status()

    def toggle_scoring(self):
        """Enable or disable scoring. When enabling/disabling, reset counters to 0/0.

        Default is disabled. Clicking toggles state and resets the score display.
        """
        if not self.scoring_enabled:
            # enable scoring
            self.scoring_enabled = True
            self.score = 0
            self.total = 0
        else:
            # disable scoring and reset
            self.scoring_enabled = False
            self.score = 0
            self.total = 0
        self.update_status()

    def show_hint(self):
        """Reveal the meta/hint text for the current question and hide the hint button."""
        try:
            self.hint_button.pack_forget()
        except Exception:
            pass
        try:
            self.meta_text.pack()
        except Exception:
            pass

    def on_font_size_change(self, val):
        """Callback from the Scale widget (val is a string). Apply font sizes."""
        try:
            size = int(float(val))
        except Exception:
            return
        self.apply_font_size(size)

    def apply_font_size(self, size=None):
        """Apply the selected font size to header, question text, meta, and option buttons.

        If size is None, use the current value of self.font_size_var.
        """
        if size is None:
            size = int(self.font_size_var.get())

        # Header slightly larger
        header_size = max(12, size + 2)
        try:
            self.header.config(font=(None, header_size))
        except Exception:
            pass

        try:
            self.q_text.config(font=(None, size))
        except Exception:
            pass

        # meta text a bit smaller
        try:
            self.meta_text.config(font=(None, max(9, size - 2)))
        except Exception:
            pass

        # update option button fonts
        for btn in getattr(self, "option_buttons", []):
            try:
                btn.config(font=(None, size))
            except Exception:
                pass

        # ensure status label is readable
        try:
            self.status.config(font=(None, max(9, size - 2)))
        except Exception:
            pass

    # --- Question generation strategies ---
    def make_style1(self):
        """Show pronoun + base verb, ask for correct conjugation for that pronoun/tense/mood."""
        verb_entry = random.choice(SAMPLE_VERBS)
        verb = verb_entry["verb"]
        tenses = ["present", "present", "past"]  # 4th option is always same as correct answer tense/mood
        moods = [m[0] for m in (ac.MOODS)]
        random.shuffle(tenses)
        random.shuffle(moods)
        tense = tenses[0]
        bab_key = None
        mood = None
        # Use the verb's associated bab when present tense is used
        if tense == "present":
            bab_key = verb_entry.get("bab")
            mood = moods[0]

        _, forms = safe_conjugate(verb, tense=tense, bab_key=bab_key, mood=mood)

        pron_index = 0
        if mood == "Imperative (أمر)":
            # choose an imperative pronoun index that actually appears in UNIQUE_PRONOUNS_IDX
            # UNIQUE_PRONOUNS_IDX excludes duplicate indices (10), so avoid picking 10 here
            possible_prons = [i for i in range(6, 12) if i != 10]
            pron_index = random.choice(possible_prons)
        else:
            # avoid duplicate indices 4 and 10 which are not present in UNIQUE_PRONOUNS_IDX
            possible_prons = [i for i in range(14) if i not in (4, 10)]
            pron_index = random.choice(possible_prons)

        correct = forms[pron_index]

        # All distractions are with the same verb but different mood/tense and different pronoun
        # 3 different random pronouns, which if mood is imperative, must be in imperative range!
        pronouns = UNIQUE_PRONOUNS_IDX.copy()
        pronouns.remove(pron_index)
        if mood == "Imperative (أمر)":
            pronouns = [i for i in pronouns if 6 <= i <= 11]
        random.shuffle(pronouns)

        # distractor 1: different mood/tense and different pronoun
        ot_tense = tenses[1]
        ot_mood = None
        ot_pronoun = pronouns[0]
        if ot_tense == "present":
            ot_mood = moods[1]
            if ot_mood == "Imperative (أمر)":
                # ensure pronoun is in imperative range
                imp_prons = [i for i in pronouns if 6 <= i <= 11]
                ot_pronoun = imp_prons[0]
        _, d1_forms = safe_conjugate(verb, tense=ot_tense, bab_key=bab_key, mood=ot_mood)
        d1 = d1_forms[ot_pronoun]
        pronouns.remove(ot_pronoun)

        # distractor 2: different mood/tense and different pronoun
        otot_tense = tenses[2]
        otot_mood = None
        otot_pronoun = pronouns[0]
        if otot_tense == "present":
            otot_mood = moods[2]
            if otot_mood == "Imperative (أمر)":
                # ensure pronoun is in imperative range
                imp_prons = [i for i in pronouns if 6 <= i <= 11]
                otot_pronoun = imp_prons[0]
        _, ot_forms = safe_conjugate(verb, tense=otot_tense, bab_key=bab_key, mood=otot_mood)
        d2 = ot_forms[otot_pronoun]
        pronouns.remove(otot_pronoun)

        # distractor 3: same tense/mood different pronoun
        d3 = forms[pronouns[0]]

        options = [correct, d1, d2, d3]
        qtext = f"Select the correct conjugation for {PRONOUNS[pron_index][0]} ({PRONOUNS[pron_index][1]})\nBase verb: {verb}\n"
        meta = f"{tense.capitalize()}{" "+mood if mood is not None else ''}"
        return {"text": qtext, "meta": meta, "options": options, "correct": correct}

    def make_style2(self):
        """Show a conjugated form; ask which tense/mood it is (4 choices)."""
        verb_entry = random.choice(SAMPLE_VERBS)
        verb = verb_entry["verb"]
        tense = random.choice(["past", "present"])
        bab_key = None
        mood = None
        if tense == "present":
            bab_key = verb_entry.get("bab")
            mood = random.choice([m[0] for m in (ac.MOODS)])

        _, forms = safe_conjugate(verb, tense=tense, bab_key=bab_key, mood=mood)
        pron = 0
        if mood == "Imperative (أمر)":
            pron = random.randrange(6) + 6
        else:
            pron = random.randrange(14)

        conj = forms[pron]

        # options: different tense/mood combos
        # add three distractors
        distracts = []
        distract_tenses = [("past", None)] + [("present", m[0]) for m in (ac.MOODS)]
        random.shuffle(distract_tenses)
        for t, m in distract_tenses:
            if (t, m) != (tense, mood) and len(distracts) < 3:
                distracts.append((t.capitalize(), m))

        # Add correct answer first, then distractors
        options = []
        for t, m in [(tense.capitalize(), mood)] + distracts[:3]:
            label = t if m is None else f"{t} - {m}"
            options.append(label)

        qtext = f"Which tense/mood is this conjugated form?\n{conj}\n"
        meta = f"Pronoun: {PRONOUNS[pron][0]} ({PRONOUNS[pron][1]}) Base verb: {verb}"
        correct_label = tense.capitalize() if mood is None else f"{tense.capitalize()} - {mood}"
        return {"text": qtext, "meta": meta, "options": options, "correct": correct_label}

    def make_style3(self):
        """Given a verb conjugation, ask: if base verb were conjugated for new (tense/mood) but same pronoun, which would it be?"""
        verb_entry = random.choice(SAMPLE_VERBS)
        verb = verb_entry["verb"]

        tenses = ["present", "past"]
        moods = [m[0] for m in (ac.MOODS)]
        random.shuffle(tenses)
        random.shuffle(moods)

        # Helper: canonicalize pron index to unique set mapping
        def canon_pron(idx):
            return {4: 1, 10: 7}.get(idx, idx)

        # 1) Pick TARGET first (so we can include "None" when Imperative)
        def pick_target_first():
            tb = random.choice(["past", "present"])
            mb = None
            bb = None
            if tb == "present":
                mb = random.choice(moods)
                bb = verb_entry.get("bab")
            return tb, mb, bb

        tense_b, mood_b, bab_b = pick_target_first()
        _, forms_b = safe_conjugate(verb, tense=tense_b, bab_key=bab_b, mood=mood_b)

        # 2) Build the GIVEN conjugation (source), independent of target
        tense_a = random.choice(["past", "present"])
        mood_a = None
        bab_a = None
        if tense_a == "present":
            bab_a = verb_entry.get("bab")
            mood_a = random.choice(moods)
        _, forms_a = safe_conjugate(verb, tense=tense_a, bab_key=bab_a, mood=mood_a)

        if mood_a == "Imperative (أمر)":
            pron_a = random.randrange(6, 12)  # 6..11 inclusive
        else:
            pron_a = random.randrange(14)
        conj_a = forms_a[pron_a]

        # 3) Determine correctness and generate options
        is_imp_target = mood_b == "Imperative (أمر)"
        valid_for_target = (not is_imp_target) or (6 <= pron_a <= 11)

        # Build pronoun pool based on target
        pron_pool = UNIQUE_PRONOUNS_IDX.copy()
        if is_imp_target:
            pron_pool = [i for i in pron_pool if 6 <= i <= 11]
        can = canon_pron(pron_a)
        if can in pron_pool:
            pron_pool.remove(can)
        random.shuffle(pron_pool)

        # Prepare alternative (tense, mood) combos distinct from target for variety
        all_combos = [("past", None)] + [("present", m) for m in moods]
        all_combos = [c for c in all_combos if c != (tense_b, mood_b)]
        random.shuffle(all_combos)

        def make_combo_form(tb, mb, fallback_forms_b=None, candidates=None):
            bb = None
            if tb == "present":
                bb = verb_entry.get("bab")
            _, fr = safe_conjugate(verb, tense=tb, bab_key=bb, mood=mb)
            # choose pronoun from candidates if provided and valid for imperative
            if candidates:
                cands = candidates
                if mb == "Imperative (أمر)":
                    cands = [p for p in cands if 6 <= p <= 11]
                if cands:
                    return fr[cands[0]]
            # otherwise fall back to using the same pron if valid, else 0
            try:
                if mb == "Imperative (أمر)" and not (6 <= pron_a <= 11):
                    # pick a default imperative pronoun
                    return fr[6]
                return fr[pron_a]
            except Exception:
                return (fallback_forms_b or fr)[0]

        options = []
        if valid_for_target:
            correct = forms_b[pron_a]
            # d1: same target combo, different pronoun
            if pron_pool:
                d1 = forms_b[pron_pool.pop(0)]
            else:
                # fallback: another combo with pron_a
                tb, mb = all_combos[0]
                d1 = make_combo_form(tb, mb, fallback_forms_b=forms_b, candidates=pron_pool)

            # d2: different combo
            tb2, mb2 = all_combos[0]
            d2 = make_combo_form(tb2, mb2, fallback_forms_b=forms_b, candidates=pron_pool)

            # d3: if target is imperative include "None" as distractor, else another combo
            if is_imp_target:
                d3 = "None"
            else:
                tb3, mb3 = all_combos[1] if len(all_combos) > 1 else all_combos[0]
                d3 = make_combo_form(tb3, mb3, fallback_forms_b=forms_b, candidates=pron_pool)
        else:
            # Target doesn't have a valid form for the same pronoun -> correct is "None"
            correct = "None"
            # d1: plausible target form (different pronoun)
            if pron_pool:
                d1 = forms_b[pron_pool.pop(0)]
            else:
                # If no pronoun available (edge), synthesize from a combo
                tb, mb = all_combos[0]
                d1 = make_combo_form(tb, mb, fallback_forms_b=forms_b, candidates=pron_pool)
            # d2 & d3: other combos
            tb2, mb2 = all_combos[0]
            d2 = make_combo_form(tb2, mb2, fallback_forms_b=forms_b, candidates=pron_pool)
            tb3, mb3 = all_combos[1] if len(all_combos) > 1 else all_combos[0]
            d3 = make_combo_form(tb3, mb3, fallback_forms_b=forms_b, candidates=pron_pool)

        options = [correct, d1, d2, d3]
        # Ensure uniqueness (rare case if underlying forms coincide); adjust by replacing duplicates with other combos
        seen = set()
        unique_opts = []
        for opt in options:
            if opt not in seen:
                seen.add(opt)
                unique_opts.append(opt)
        while len(unique_opts) < 4:
            # add more variety from remaining combos
            if all_combos:
                tb, mb = all_combos.pop()
                unique_opts.append(make_combo_form(tb, mb, fallback_forms_b=forms_b, candidates=pron_pool))
            else:
                # last resort, append a fabricated distinct label
                unique_opts.append(f"doodoo code 😭")

        qtext = (
            f"If the base verb of {conj_a} were conjugated in\n"
            f"{tense_b.capitalize()}{' ' + mood_b if mood_b is not None else ''} (same pronoun)\n"
            f"which one would it be?"
        )
        meta = f"{PRONOUNS[canon_pron(pron_a)][0]} ({PRONOUNS[canon_pron(pron_a)][1]}), base verb: {verb}"

        return {"text": qtext, "meta": meta, "options": unique_opts[:4], "correct": correct}

    def make_style4(self):
        """Given conjugated verb, ask for pronoun (meta being the tense/mood)"""

        # pick random verb, tense, mood
        verb_entry = random.choice(SAMPLE_VERBS)
        verb = verb_entry["verb"]
        tense = random.choice(["past", "present"])
        bab_key = None
        mood = None
        if tense == "present":
            bab_key = verb_entry.get("bab")
            mood = random.choice([m[0] for m in (ac.MOODS)])
        _, forms = safe_conjugate(verb, tense=tense, bab_key=bab_key, mood=mood)

        pron = 0
        if mood == "Imperative (أمر)":
            # choose an imperative pronoun index that actually appears in UNIQUE_PRONOUNS_IDX
            # UNIQUE_PRONOUNS_IDX excludes duplicate indices (10), so avoid picking 10 here
            possible_prons = [i for i in range(6, 12) if i != 10]
            pron = random.choice(possible_prons)
        else:
            # avoid duplicate indices 4 and 10 which are not present in UNIQUE_PRONOUNS_IDX
            possible_prons = [i for i in range(14) if i not in (4, 10)]
            pron = random.choice(possible_prons)

        conj = forms[pron]

        pronouns_idx = UNIQUE_PRONOUNS_IDX.copy()
        pronouns_idx.remove(pron)
        random.shuffle(pronouns_idx)

        # distractor pronouns -- idx
        d1 = pronouns_idx[0]
        d2 = pronouns_idx[1]
        d3 = pronouns_idx[2]

        options = [
            f"{PRONOUNS[pron][1]} - ({PRONOUNS[pron][0]})",
            f"{PRONOUNS[d1][1]} - ({PRONOUNS[d1][0]})",
            f"{PRONOUNS[d2][1]} - ({PRONOUNS[d2][0]})",
            f"{PRONOUNS[d3][1]} - ({PRONOUNS[d3][0]})",
        ]
        correct = f"{PRONOUNS[pron][1]} - ({PRONOUNS[pron][0]})"

        qtext = f"Which pronoun corresponds to this conjugation?\n{conj}\n"
        meta = f"Tense: {tense.capitalize()}{' ' + mood if mood is not None else ''}  Base verb: {verb}"
        return {"text": qtext, "meta": meta, "options": options, "correct": correct}

    def make_style5(self):
        """Extra challenge: match base verb given conjugated form among 4 verbs."""
        verbs = random.sample(SAMPLE_VERBS, 4)
        verb = verbs[0]["verb"]
        tense = random.choice(["past", "present"])
        bab_key = None
        mood = None
        if tense == "present":
            # use the chosen verb's bab for present
            bab_key = verbs[0].get("bab")
            mood = random.choice([m[0] for m in (ac.MOODS)])

        _, forms = safe_conjugate(verb, tense=tense, bab_key=bab_key, mood=mood)
        pron = random.randrange(14)
        conj = forms[pron]

        options = []
        for v in verbs:
            t, f = safe_conjugate(v["verb"], tense=tense, bab_key=v.get("bab"), mood=mood)
            options.append(v["verb"])

        correct = verb
        qtext = f"Which base verb produced this conjugation?\n{conj}\n"
        meta = f"Pronoun: {PRONOUNS[pron][0]}  Tense: {tense}"
        return {"text": qtext, "meta": meta, "options": options, "correct": correct}


def main():
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

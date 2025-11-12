# Arabic Conjugator Quiz

A small Tkinter-based multiple-choice quiz for practicing Arabic verb conjugations.

> Also available on [replit.com/@hmolavi/ArabicConjugatorQuizApp](https://replit.com/@hmolavi/ArabicConjugatorQuizApp).

## Demo

<div align="center">

_GIF to be inserted_
<!-- ![example](/assets/example.gif) -->

</div>

## Features

- Multiple-choice questions (4 options) for common triliteral verbs with harakat.
- Several question styles to practice tense, mood, and pronoun-specific conjugations.
- Timed Test mode: run a fixed-length test, track answers, and review results with per-question feedback.
- Scoring toggle: optionally enable or disable scoring; score resets when toggled.
- Adjustable display: change font size for readability.
- Hint/meta support: reveal additional info per question.
- Environment-aware Arabic formatting: reshapes and bidi-reorders Arabic text when necessary (uses `arabic_reshaper` + `python-bidi` when available).
- Graceful fallback when the conjugation package is unavailable (fake forms for offline testing).

## Getting Started

It is recommended to use a virtual environment.

1. Create and activate a virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the app (GUI):

    ```bash
    python app.py
    ```

The app will open a Tkinter window where you can start answering questions immediately.

## How to Use (GUI)

1. Launch the app (`python app.py`).
2. The main window shows a question and four options.
3. Click an option to answer. Visual feedback highlights correct and incorrect answers.
4. Use the `Next` button to move to the next question.
5. `Test` starts a timed session (fixed number of questions). At the end you'll enter Review mode where you can browse all questions and see which you got right.
6. Toggle scoring using the score button to enable persistent score tracking across questions. When toggled, the displayed score resets.
7. Change the font size with the Font size selector for comfortable reading.
8. Click `Show hint` to reveal meta information for the current question.

## Test Mode & Review

- Test mode runs a sequence of questions (default length in-app) with a stopwatch.
- Answers are recorded; after the test you can review each question, see which option was chosen, and navigate between questions using arrows.

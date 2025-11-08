# Arabic Conjugation Quiz App

## Overview
This is a desktop GUI application built with Python and Tkinter that helps users practice Arabic verb conjugations. The app presents multiple-choice questions to test knowledge of different conjugations, tenses, moods, and pronouns.

## Current State
The application is fully set up and running in the Replit environment with VNC display for the GUI.

## Recent Changes (November 08, 2025)
- Initial setup in Replit environment
- Installed Python dependencies: arabic-reshaper, python-bidi, arabic-conjugator
- Configured VNC workflow to display the Tkinter GUI application
- Verified application runs without errors

## Project Architecture

### Technology Stack
- **Language**: Python 3.12
- **GUI Framework**: Tkinter (Python's standard GUI library)
- **Dependencies**:
  - `arabic-reshaper`: Handles Arabic text reshaping for proper display
  - `python-bidi`: Bidirectional text algorithm for Arabic display
  - `arabic-conjugator`: Core library for Arabic verb conjugation

### File Structure
- `app.py`: Main application file containing the quiz UI and logic
- `requirements.txt`: Python package dependencies
- `.replit`: Replit configuration (Python 3.12 module)
- `.gitignore`: Git ignore patterns for Python projects

### Application Features
1. **Multiple Question Styles**: 5 different question types to practice conjugations
2. **Arabic Text Support**: Proper reshaping and bidirectional display for Arabic text
3. **Scoring System**: Optional scoring toggle (disabled by default)
4. **Hint System**: Show/hide hints for each question
5. **Font Size Control**: Adjustable font sizes (12-48pt) via dropdown
6. **Sample Verbs**: 9 pre-configured Arabic verbs with their associated "bab" patterns
7. **14 Pronoun Forms**: Comprehensive coverage of Arabic pronouns

### Running the Application
The app runs automatically via the VNC workflow. Click the "Run" button to launch the GUI application in a desktop environment.

## User Preferences
None specified yet.

## Notes
- This is a desktop GUI application, not a web application
- The application requires VNC display to show the Tkinter interface
- All dependencies are managed via Python pip in the `.pythonlibs` directory

''' Unit tests for NoteMakerForm from forms.noteMakerForm '''

import unittest
from app import app
from forms.noteMakerForm import NoteMakerForm


class TestNoteMakerForm(unittest.TestCase):
    '''TestNoteMakerForm is the class for unit tests on NoteMakerForm'''

    def test_valid_note_maker_form(self):
        ''' tests the form with a valid input containing the required date '''

        # Disable CSRF so WTForms validates without a live browser session
        app.config['WTF_CSRF_ENABLED'] = False

        # Push the app context so Flask-WTF can build the form in memory
        with app.app_context():
            form = NoteMakerForm(
                date_created="2026-07-14",
                song="Yellow Submarine",
                location="Seattle"
            )

            self.assertTrue(form.validate())

    def test_invalid_note_maker_form(self):
        ''' tests the form fails validation when missing the required date '''

        # Disable CSRF so WTForms validates without a live browser session
        app.config['WTF_CSRF_ENABLED'] = False

        # Push the app context so Flask-WTF can build the form in memory
        with app.app_context():
            form = NoteMakerForm(
                song="Yellow Submarine",
                location="Seattle"
            )

            self.assertFalse(form.validate())
            self.assertIn('date_created', form.errors)


if __name__ == "__main__":
    unittest.main()
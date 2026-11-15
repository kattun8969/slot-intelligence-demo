import unittest
from scripts.ev_counter_semantics import (
    CounterSemanticsError, validate_counter_value, parse_counter_value,
    inspect_transition,
)

class CounterSemanticsTests(unittest.TestCase):
    def test_negative_daily_difference_allowed(self):
        self.assertEqual(parse_counter_value("daily_difference_medals","-1500"),-1500)
    def test_negative_section_difference_allowed(self):
        self.assertEqual(parse_counter_value("section_difference_medals","-50"),-50)
    def test_positive_game_counter_allowed(self):
        self.assertEqual(parse_counter_value("at_games","350"),350)
    def test_negative_game_counter_rejected(self):
        with self.assertRaises(CounterSemanticsError):
            parse_counter_value("at_games","-1")
    def test_bool_not_integer(self):
        with self.assertRaises(CounterSemanticsError):
            validate_counter_value("daily_difference_medals",True)
    def test_float_rejected(self):
        with self.assertRaises(CounterSemanticsError):
            validate_counter_value("daily_difference_medals",2.5)
    def test_noncanonical_integer_rejected(self):
        for value in ("+1","01","-0"," 1","1,000","1.0",""):
            with self.subTest(value=value), self.assertRaises(CounterSemanticsError):
                parse_counter_value("daily_difference_medals",value)
    def test_signed_decrease_is_not_reset(self):
        t=inspect_transition("daily_difference_medals",500,-500,
                             previous_origin="daily_open",current_origin="daily_open")
        self.assertEqual(t.classification,"signed_difference_changed")
        self.assertFalse(t.needs_review)
    def test_game_decrease_without_boundary_quarantined(self):
        t=inspect_transition("at_games",350,20,
                             previous_origin="last_at_end",current_origin="last_at_end")
        self.assertEqual(t.classification,"unexplained_counter_decrease")
        self.assertTrue(t.needs_review)
    def test_game_decrease_with_evidence_still_reviewed(self):
        t=inspect_transition("at_games",350,20,
                             previous_origin="last_at_end",current_origin="last_at_end",
                             boundary_evidence="verified_at_end")
        self.assertEqual(t.classification,"decrease_with_boundary_evidence")
        self.assertTrue(t.needs_review)
    def test_origin_change_reviewed(self):
        t=inspect_transition("at_games",350,20,
                             previous_origin="last_at_end",current_origin="last_cz_end")
        self.assertEqual(t.classification,"origin_changed")
        self.assertTrue(t.needs_review)
    def test_unknown_counter_rejected(self):
        with self.assertRaises(CounterSemanticsError):
            parse_counter_value("unknown","100")

if __name__=="__main__":
    unittest.main()

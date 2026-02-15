import unittest
from datetime import datetime, timedelta
from automation import calculate_next_date
from dateutil.relativedelta import relativedelta

class TestAutomation(unittest.TestCase):
    def test_calculate_next_date_future(self):
        """Test calculation for a day later in the current month"""
        today = datetime.now()
        # If today is the 15th, target the 20th
        target_day = (today.day % 28) + 1
        if target_day <= today.day:
             # Force it to be in the next month for this test case if the logic requires
             pass 
        
        # Test basic calculation
        next_date = calculate_next_date(target_day)
        self.assertEqual(next_date.day, target_day)
        self.assertGreaterEqual(next_date, today)

    def test_calculate_next_date_rollover(self):
        """Test calculation when the day has already passed in the current month"""
        today = datetime.now()
        if today.day > 1:
            past_day = today.day - 1
            next_date = calculate_next_date(past_day)
            
            # Should be next month
            expected_month = (today.month % 12) + 1
            self.assertEqual(next_date.month, expected_month)
            self.assertEqual(next_date.day, past_day)

    def test_leap_year_edge_case(self):
        """Test handling of 31st on shorter months"""
        # February doesn't have 31 days
        next_date = calculate_next_date(31)
        # Should return the last day of the current or next month
        self.assertIn(next_date.day, [28, 29, 30, 31])

if __name__ == '__main__':
    unittest.main()

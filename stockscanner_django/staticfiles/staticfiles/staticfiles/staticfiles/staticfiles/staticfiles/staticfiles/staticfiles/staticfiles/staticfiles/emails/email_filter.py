import re

class EmailFilter:
    def __init__(self):
        self.categories = [
            "DVSA 50", "DVSA 100", "DVSA 150",
            "MC 10 IN", "MC 20 IN", "MC 30 IN",
            "MC 10 DE", "MC 20 DE", "MC 30 DE",
            "PE 10 IN", "PE 20 IN", "PE 30 IN",
            "PE 10 DE", "PE 20 DE", "PE 30 DE",
            "PRICE 10 DE", "PRICE 15 DE", "PRICE 20 DE"
        ]
        self.keywords = [
            ["dvsa", "volume", "50"],
            ["dvsa", "volume", "100"],
            ["dvsa", "volume", "150"],
            ["market cap", "increase", "10"],
            ["market cap", "increase", "20"],
            ["market cap", "increase", "30"],
            ["market cap", "decrease", "10"],
            ["market cap", "decrease", "20"],
            ["market cap", "decrease", "30"],
            ["pe", "increase", "10"],
            ["pe", "increase", "20"],
            ["pe", "increase", "30"],
            ["pe", "decrease", "10"],
            ["pe", "decrease", "20"],
            ["pe", "decrease", "30"],
            ["price", "drop", "10"],
            ["price", "drop", "15"],
            ["price", "drop", "20"],
        ]

    def filter_email(self, email_body):
        email_body = email_body.lower()
        for category, words in zip(self.categories, self.keywords):
            if all(word in email_body for word in words):
                return category
        return "Uncategorized"

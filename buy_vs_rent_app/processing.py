import collections


class OptionBuy:
    def __init__(
        self,
        home_price: float,
        downpayment: float,
        interest_rate: float,
        loan_length: float,
        tax: float,
        maintenance: float,
        monthly_hoa: float,
        home_growth: float,
        years_of_owning: int,
        sell_comission: float,
    ):

        self.home_price = home_price
        self.downpayment = downpayment
        self.loan_amount = self.home_price - self.downpayment
        self.interest_rate = interest_rate
        self.loan_length = loan_length
        self.tax = tax
        self.maintenance = maintenance
        self.monthly_hoa = monthly_hoa
        self.home_growth = home_growth
        self.years_of_owning = years_of_owning
        self.sell_comission = sell_comission
        self._update_mortgage()

    def _update_mortgage(self):
        self.monthly_interest_rate = self.interest_rate / 12
        monthly_interest_amount = self.monthly_interest_rate * self.loan_amount
        gamma = (1 + self.monthly_interest_rate) ** (-self.loan_length * 12)
        self.monthly_payment = monthly_interest_amount / (1 - gamma)

    def _calculate_home_extras(self):
        def add_expense(expense: float, expense_type: str, year: int):
            expenses_info["Expense"].append(expense)
            expenses_info["Type"].append(expense_type)
            expenses_info["Year"].append(year)

        expenses_info = collections.defaultdict(list)

        tax_yearly = self.home_price * self.tax
        maintenance_yearly = self.home_price * self.maintenance
        hoa_yearly = 12 * self.monthly_hoa

        self.total_tax = 0.0
        self.total_maintenance = 0.0
        self.total_hoa = 0.0

        for year in range(self.years_of_owning):
            self.total_tax += tax_yearly
            self.total_maintenance += maintenance_yearly
            self.total_hoa += hoa_yearly

            add_expense(tax_yearly, "Tax", year + 1)
            add_expense(maintenance_yearly, "Maintenance", year + 1)
            add_expense(hoa_yearly, "HOA", year + 1)

            tax_yearly *= 1.0 + self.home_growth
            maintenance_yearly *= 1.0 + self.home_growth
            hoa_yearly *= 1.0 + self.home_growth

        self.total_home_extra = self.total_tax + self.total_maintenance + self.total_hoa
        self.expenses_info = expenses_info

        return self.total_home_extra

    def _calculate_mortgage(self):
        def add_payment(payment: float, payment_type: str, year: int):
            mortgage_info["Payment"].append(payment)
            mortgage_info["Type"].append(payment_type)
            mortgage_info["Year"].append(year)

        mortgage_info = collections.defaultdict(list)

        loan = self.loan_amount
        self.total_interest = 0.0
        for year in range(self.years_of_owning):
            year_principal, year_interest = 0.0, 0.0
            for month in range(12):
                monthly_interest = self.monthly_interest_rate * loan
                monthly_principal = self.monthly_payment - monthly_interest
                loan -= monthly_principal
                self.total_interest += monthly_interest
                year_interest += monthly_interest
                year_principal += monthly_principal

            add_payment(year_principal, "Principal", year + 1)
            add_payment(year_interest, "Interest", year + 1)

        self.mortgage_info = mortgage_info

    def _calculate_home_sell(self):
        home_growth = (1.0 + self.home_growth) ** (self.years_of_owning)
        self.sell_home_price = self.home_price * home_growth
        self.home_delta = (
            self.sell_home_price * (1 - self.sell_comission) - self.home_price
        )

    def calculate(self) -> float:
        self._calculate_home_extras()
        self._calculate_mortgage()
        self._calculate_home_sell()

        profit = -self.total_home_extra - self.total_interest + self.home_delta
        return profit


class OptionRent:
    def __init__(
        self,
        monthly_rent: float,
        rent_growth: float,
        downpayment: float,
        roi_percent: float,
        years: int,
    ):

        self.monthly_rent = monthly_rent
        self.rent_growth = rent_growth
        self.downpayment = downpayment
        self.roi_percent = roi_percent
        self.years = years

    def calculate(self) -> [float, float]:
        total_roi = (
            self.downpayment * (1 + self.roi_percent) ** (self.years) - self.downpayment
        )

        total_rent = 0.0
        monthly_rent = self.monthly_rent

        rent_info = collections.defaultdict(list)

        for year in range(self.years):
            rent_yearly = monthly_rent * 12
            total_rent += rent_yearly
            rent_info["Year"].append(year + 1)
            rent_info["Rent"].append(rent_yearly)
            monthly_rent *= 1.0 + self.rent_growth

        return total_roi, total_rent, rent_info

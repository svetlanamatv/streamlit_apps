import streamlit as st
from processing import OptionBuy, OptionRent

st.title("Buy vs Rent")

st.markdown(
    f"This app allows you to compare two options: buying a home or renting and investing your downpayment. <br>"
    "You can adjust various parameters to fit your unique situation and account for changes in the housing and stock markets.<br>"
    "Tax amount, maintenance, and HOA fees are adjusted annually based on home value growth.",
    unsafe_allow_html=True,
)

MAX_INT_VALUE =  (1<<53) - 1

DEFAULT_HOME_PRICE = 850_000
DOWNPAYMENT_DEFAULT_PERCENTAGE = 20.0
DOWNPAYMENT_DEFAULT_VALUE = int(
    DEFAULT_HOME_PRICE * DOWNPAYMENT_DEFAULT_PERCENTAGE / 100
)


if "home_price" not in st.session_state:
    st.session_state.home_price = DEFAULT_HOME_PRICE
if "downpayment_in_dollars" not in st.session_state:
    st.session_state.downpayment_in_dollars = DOWNPAYMENT_DEFAULT_VALUE
if "downpayment_percentage" not in st.session_state:
    st.session_state.downpayment_percentage = DOWNPAYMENT_DEFAULT_PERCENTAGE
if "loan_amount" not in st.session_state:
    st.session_state.loan_amount = float(
        st.session_state.home_price - st.session_state.downpayment_in_dollars
    )


def update_downpayment_in_dollars():
    if st.session_state.full_downpayment:
        st.session_state.downpayment_percentage = 100.0

    st.session_state.downpayment_in_dollars = int(
        (st.session_state.downpayment_percentage / 100) * st.session_state.home_price
    )
    st.session_state.loan_amount = (
        st.session_state.home_price - st.session_state.downpayment_in_dollars
    )


def update_downpayment_percentage():
    if st.session_state.full_downpayment:
        st.session_state.downpayment_percentage = 100.0
        st.session_state.downpayment_in_dollars = st.session_state.home_price
    else:
        st.session_state.downpayment_percentage = (
            st.session_state.downpayment_in_dollars / st.session_state.home_price
        ) * 100
        st.session_state.loan_amount = (
            st.session_state.home_price - st.session_state.downpayment_in_dollars
        )


def updated_loan_amount():
    if st.session_state.full_downpayment:
        st.session_state.loan_amount = 0.0
    st.session_state.downpayment_in_dollars = int(
        st.session_state.home_price - st.session_state.loan_amount
    )
    st.session_state.downpayment_percentage = (
        st.session_state.downpayment_in_dollars / st.session_state.home_price
    ) * 100


def buy_for_cash():
    if st.session_state.full_downpayment:
        st.session_state.prev_downpayment_percentage = (
            st.session_state.downpayment_percentage
        )
    else:
        st.session_state.downpayment_percentage = (
            st.session_state.prev_downpayment_percentage
        )
    update_downpayment_in_dollars()


st.header("Scenario 1: buy a home", divider="gray")

col1, col2, col3 = st.columns(3)

with col1:

    st.number_input(
        label="Home Price",
        min_value=1,
        max_value=MAX_INT_VALUE,
        value=st.session_state.home_price,
        step=50000,
        on_change=update_downpayment_in_dollars,
        key="home_price",
    )
    st.number_input(
        label="Loan Amount ($)",
        min_value=0.0,
        max_value=float(st.session_state.home_price),
        value=float(st.session_state.loan_amount),
        step=50000.0,
        on_change=updated_loan_amount,
        key="loan_amount",
    )

with col2:
    st.number_input(
        label="Downpayment ($)",
        min_value=0,
        max_value=st.session_state.home_price,
        value=st.session_state.downpayment_in_dollars,
        step=50000,
        on_change=update_downpayment_percentage,
        key="downpayment_in_dollars",
    )
    interest_rate = st.number_input(
        label="Interest rate (%)",
        min_value=0.0,
        max_value=100.0,
        value=6.5,
        step=0.1,
        key="interest_rate",
    )
    interest_rate /= 100


with col3:
    st.number_input(
        label="Downpayment (%):",
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.downpayment_percentage,
        step=5.0,
        on_change=update_downpayment_in_dollars,
        key="downpayment_percentage",
    )
    loan_length = st.number_input(
        label="Loan Length (years)",
        min_value=0,
        max_value=30,
        value=30,
        step=5,
        key="loan_length",
    )


full_downpayment = st.toggle(
    "Buy for cash", key="full_downpayment", on_change=buy_for_cash
)

col4, col5, col6 = st.columns(3)

with col4:
    tax = st.number_input(
        label="Tax per year (%)",
        min_value=0.0,
        max_value=100.0,
        value=1.0,
        step=0.5,
        key="tax",
    ) / 100
    home_growth = st.number_input(
        label="Home growth per year (%)",
        min_value=0.0,
        max_value=100.0,
        value=3.0,
        step=1.0,
        key="home_growth",
    ) / 100
with col5:
    home_maintenance_percent = st.number_input(
        label="Home maintenance per year (%)",
        min_value=0.0,
        max_value=100.0,
        value=1.0,
        step=0.5,
        key="maintenance",
    ) / 100
    years = st.number_input(
        label="Years of owning",
        min_value=1,
        max_value=30,
        value=10,
        step=1,
        key="years_of_owning",
    )
with col6:
    hoa = st.number_input(
        label="HOA per month (if applicable)",
        min_value=0.0,
        max_value=100000.0,
        value=0.0,
        step=50.0,
        key="hoa",
    )
    sell_comission = st.number_input(
        label="Sell Comission (%)",
        min_value=0.0,
        max_value=100.0,
        value=10.0,
        step=1.0,
        key="sell_comission",
    ) / 100


# Calculations for scenario 1
s = OptionBuy(
    home_price=st.session_state.home_price,
    downpayment=st.session_state.downpayment_in_dollars,
    interest_rate=interest_rate,
    loan_length=loan_length,
    tax=tax,
    maintenance=home_maintenance_percent,
    monthly_hoa=hoa,
    home_growth=home_growth,
    years_of_owning=years,
    sell_comission=sell_comission,
)

with_home = s.calculate()

st.markdown(f"Your monthly mortgage payment: ${int(s.monthly_payment):,}")

total_home_expenses = s.total_interest + s.total_home_extra

st.markdown(
    f"**Home expenses over {years} years**<br>"
    f"{int(s.total_interest):,} (interest) + "
    f"{int(s.total_tax):,} (tax) + "
    f"{int(s.total_maintenance):,} (maintenance) + "
    f"{int(s.total_hoa):,} (HOA) = "
    f"**{int(total_home_expenses):,}**",
    unsafe_allow_html=True,
)

st.markdown(
    f"**Home sale revenue**<br>"
    f"Home price change over {years} years: {int(s.home_price):,} -> {int(s.sell_home_price):,}<br>"
    f"Home equity growth: {int(s.sell_home_price):,} - {int(s.home_price):,} = {int(s.sell_home_price - s.home_price):,}<br>"
    f"Sale revenue (including commission): **{int(s.home_delta):,}**",
    unsafe_allow_html=True,
)

st.markdown(
    f"**Total profit over {years} years: {int(s.home_delta):,} (home sale revenue) - {int(total_home_expenses):,} (home expenses) = {int(with_home):,}**"
)
st.divider()

st.markdown(f"**Home expenses broken down by year:**")
st.bar_chart(s.expenses_info, x="Year", y="Expense", color="Type", stack=True)
if not full_downpayment:
    st.markdown(f"**Mortgage payments broken down by year:**")
    st.bar_chart(s.mortgage_info, x="Year", y="Payment", color="Type", stack=True)

st.header("Scenario 2: rent and invest", divider="gray")

col7, col8, col9 = st.columns(3)

with col7:
    rent = st.number_input(
        label="Rent per month ($)",
        min_value=0.0,
        max_value=float(MAX_INT_VALUE),
        value=3500.0,
        step=500.0,
        key="monthly_rent",
    )

with col8:
    rent_growth = st.number_input(
        label="Rent growth per year (%)",
        min_value=0.0,
        max_value=100.0,
        value=3.0,
        step=0.5,
        key="rent_growth",
    ) / 100
with col9:
    roi = st.number_input(
        label="ROI per year on downpayment (%)",
        min_value=0.0,
        max_value=100.0,
        value=3.0,
        step=0.5,
        key="roi_percent",
    ) / 100

# Calculations for scenario 2
s_rent = OptionRent(
    monthly_rent=rent,
    rent_growth=rent_growth,
    downpayment=st.session_state.downpayment_in_dollars,
    roi_percent=roi,
    years=years,
)

total_roi, total_rent, rent_info = s_rent.calculate()
without_home = total_roi - total_rent

st.markdown(
    f"**Rent expenses over {years} years: {int(total_rent):,}**<br>"
    f"**ROI on downpayment ({int(st.session_state.downpayment_in_dollars):,}) over {years} years: {int(total_roi):,}**<br>"
    f"**Total profit: {int(total_roi):,} (ROI on downpayment) - {int(total_rent):,} (rent) = {int(without_home):,}**",
    unsafe_allow_html=True,
)

st.divider()

st.markdown(f"**Rent expenses broken down by year:**")
st.bar_chart(rent_info, x="Year", y="Rent", stack=False)

st.header("Conclusion", divider="gray")

delta = with_home - without_home


if with_home < 0:
    net_result_with_home = "Loss"
else:
    net_result_with_home = "Profit"

if without_home < 0:
    net_result_without_home = "Loss"
else:
    net_result_without_home = "Profit"

st.markdown(
    f"**{net_result_with_home} of owning home over {years} years: {int(abs(with_home)):,}**<br>"
    f"**{net_result_without_home} of renting but investing over {years} years: {int(abs(without_home)):,}**<br>",
    unsafe_allow_html=True,
)

if delta < 0:
    st.markdown(
        f"**=> It's better to rent!**<br>"
        f"**Losses on buying home over {years} years: {int(delta):,}**<br>"
        f"**Per month: {int(delta / years / 12):,}**<br>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"**=> It's better to buy!**<br>"
        f"**Profit on buying home over {years} years: {int(delta):,}**<br>"
        f"**Per month: {int(delta / years / 12):,}**<br>",
        unsafe_allow_html=True,
    )

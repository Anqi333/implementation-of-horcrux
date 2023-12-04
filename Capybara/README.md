This is the simulation of Capybara, Revive, and Shaduf in the Lightning Network. We respectively test the payment success ratio, depleted channels, and volume under the one-time running and long-term running.

## **Requirements:**

1. Python >= 3.7.3
2. curl
3. numpy 
4. networkx
5. random
6. scipy
7. json
8. functools
9. collections

## Usage:

1. Generate the Lightning network topology using network/generate_network.py
2. Get the Bitcoin payment value in 2020-03 using payment_value/get_payment_value.py
3. Get the LN and Shaduf's performance using shaduf.py
4. Get the Revive's performance using opt_revive.py
5. Get the Capybara's performance using capybara.py
6. Compare the results
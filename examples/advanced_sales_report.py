# advanced_sales_report.py
#
# This is a comprehensive example script designed to showcase the capabilities
# of the plexus-core compiler and decompiler.
#
# When you decompile this file, you will see a graph containing:
#  - Variable assignments (list, integers, strings)
#  - A 'for' loop
#  - A nested 'if/elif/else' block
#  - Math and comparison operations
#  - Multiple function calls ('print')

# 1. Initial Data Setup
# A list of dictionaries representing sales data.
sales_data = [
    {'customer_id': 101, 'amount': 150, 'status': 'gold'},
    {'customer_id': 102, 'amount': 80, 'status': 'silver'},
    {'customer_id': 103, 'amount': 210, 'status': 'bronze'},
    {'customer_id': 104, 'amount': 50, 'status': 'gold'},
]

print('--- Starting Sales Report Generation ---')

# 2. Main Processing Loop
# We iterate over each sale in the list.
for sale in sales_data:
    customer = sale['customer_id']
    original_amount = sale['amount']
    status = sale['status']
    
    discount_percentage = 0

    # 3. Conditional Logic
    # Determine the discount based on customer status.
    if status == 'gold':
        discount_percentage = 20
    elif status == 'silver':
        discount_percentage = 10
    else:
        # Bronze and other statuses get a default small discount.
        discount_percentage = 5

    # 4. Calculations
    # Calculate the final price after the discount.
    discount_amount = original_amount * discount_percentage / 100
    final_price = original_amount - discount_amount

    # 5. Print Formatted Output
    # Display the results for each customer.
    print('Processing Customer:')
    print(customer)
    print('Final Price:')
    print(final_price)

    # Add a separator for readability, except after the last entry.
    if customer != 104:
        print('--------------------')

print('--- Sales Report Generation Complete ---')


import json
import datetime
import random
import string
import copy
import argparse

def generate_random_string(length=8):
    """Generates a random string of lowercase letters and digits."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_large_dataset(target_rows, template_filename, output_filename, seed=42):
    """
    Generates a large, deterministic dataset by randomizing and duplicating 
    records from a template file based on a seed.
    """
    random.seed(seed) # Set the seed for deterministic randomness
    print("Loading template records...")
    try:
        with open(template_filename, 'r') as f:
            template_records = [json.loads(line) for line in f]
    except FileNotFoundError:
        print(f"Error: Template file '{template_filename}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error decoding JSON from '{template_filename}'. Ensure it's a valid JSONL file.")
        return

    print(f"Starting generation of {target_rows} rows. This may take a while...")
    current_timestamp = datetime.datetime(2023, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)

    with open(output_filename, 'w') as outfile:
        for i in range(target_rows):
            template_record = random.choice(template_records)
            new_record = copy.deepcopy(template_record)

            # Anonymize and randomize IDs to make the record unique
            order_id_map = {}
            payment_method_id_map = {}

            if 'customer' in new_record:
                new_record['customer']['customerEmail'] = f"{generate_random_string(10)}@example.com"
                new_record['customer']['customerPhone'] = f"{random.randint(100,999)}-555-{random.randint(1000,9999)}"
                new_record['customer']['customerDevice'] = generate_random_string(20)
                new_record['customer']['customerIPAddress'] = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"

            if 'paymentMethods' in new_record and isinstance(new_record['paymentMethods'], list):
                for method in new_record['paymentMethods']:
                    old_id = method.get('paymentMethodId')
                    if old_id:
                        new_id = generate_random_string(9)
                        method['paymentMethodId'] = new_id
                        payment_method_id_map[old_id] = new_id

            if 'orders' in new_record and isinstance(new_record['orders'], list):
                for order in new_record['orders']:
                    old_id = order.get('orderId')
                    if old_id:
                        new_id = generate_random_string(6)
                        order['orderId'] = new_id
                        order_id_map[old_id] = new_id
                    order['orderAmount'] = max(1, order.get('orderAmount', 0) + random.randint(-5, 5))

            if 'transactions' in new_record and isinstance(new_record['transactions'], list):
                 for trans in new_record['transactions']:
                    trans['transactionId'] = generate_random_string(8)
                    old_order_id = trans.get('orderId')
                    if old_order_id and old_order_id in order_id_map:
                        trans['orderId'] = order_id_map[old_order_id]
                    
                    old_pm_id = trans.get('paymentMethodId')
                    if old_pm_id and old_pm_id in payment_method_id_map:
                        trans['paymentMethodId'] = payment_method_id_map[old_pm_id]

                    if old_order_id and old_order_id in order_id_map:
                        order_amount = next((o.get('orderAmount') for o in new_record.get('orders', []) if o.get('orderId') == order_id_map[old_order_id]), None)
                        if order_amount:
                           trans['transactionAmount'] = order_amount

            # --- Timestamping Logic ---
            current_timestamp += datetime.timedelta(minutes=random.randint(1, 180))
            if 'customer' in new_record and isinstance(new_record['customer'], dict):
                new_record['customer']['loggedAt'] = current_timestamp.isoformat()

            if 'paymentMethods' in new_record and isinstance(new_record['paymentMethods'], list):
                for method in new_record['paymentMethods']:
                    current_timestamp += datetime.timedelta(minutes=random.randint(1, 10))
                    method['loggedAt'] = current_timestamp.isoformat()

            if 'orders' in new_record and isinstance(new_record['orders'], list):
                for order in new_record['orders']:
                    current_timestamp += datetime.timedelta(minutes=random.randint(5, 60))
                    order['loggedAt'] = current_timestamp.isoformat()

            order_timestamps = {order.get('orderId'): order.get('loggedAt') for order in new_record.get('orders', [])}
            if 'transactions' in new_record and isinstance(new_record['transactions'], list):
                for transaction in new_record['transactions']:
                    order_time_str = order_timestamps.get(transaction.get('orderId'))
                    if order_time_str:
                        transaction_time = datetime.datetime.fromisoformat(order_time_str)
                        transaction_time += datetime.timedelta(seconds=random.randint(5, 300))
                        transaction['loggedAt'] = transaction_time.isoformat()
                    else:
                        current_timestamp += datetime.timedelta(seconds=random.randint(30, 90))
                        transaction['loggedAt'] = current_timestamp.isoformat()
            # --- End of Timestamping Logic ---

            outfile.write(json.dumps(new_record) + '\n')

            # Progress indicator to show the script is working
            if (i + 1) % 100000 == 0:
                print(f"  ... {i + 1} / {target_rows} rows generated.")

    print(f"Generation complete. {target_rows} rows saved to '{output_filename}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a large, synthetic dataset based on a template file."
    )
    parser.add_argument(
        "num_rows",
        type=int,
        nargs='?',
        default=100_000,
        help="The number of rows to generate. Defaults to 100,000."
    )
    args = parser.parse_args()
    
    # --- Configuration ---
    # The seed ensures that the "random" data generated is the same every time the script is run.
    SEED = 42
    NUM_ROWS_TO_GENERATE = args.num_rows
    TEMPLATE_FILE = "customers.json"
    OUTPUT_FILE = f"customers_generated_{NUM_ROWS_TO_GENERATE}_seed{SEED}.jsonl"
    
    # --- Run the generator ---
    generate_large_dataset(
        target_rows=NUM_ROWS_TO_GENERATE,
        template_filename=TEMPLATE_FILE,
        output_filename=OUTPUT_FILE,
        seed=SEED
    )


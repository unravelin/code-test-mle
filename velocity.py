import argparse
from datetime import datetime, timedelta, timezone
import json

def batch_read_jsonl(filename, batch_size=1000):
    """Yield batches of records from a JSON Lines file with error handling."""
    batch = []
    try:
        with open(filename, 'r') as file:
            for line_number, line in enumerate(file, 1):
                try:
                    batch.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON on line {line_number}: {e}")
                    continue
                if len(batch) == batch_size:
                    yield batch
                    batch = []
            if batch:
                yield batch
    except FileNotFoundError:
        print(f"File not found: {filename}")
    except Exception as e:
        print(f"Unexpected error reading file {filename}: {e}")

if __name__ == "__main__":
    t0 = datetime.now()
    parser = argparse.ArgumentParser(
        description="Generate the velocity feature on the passed in dataset."
    )
    parser.add_argument(
        "batch_size",
        type=int,
        nargs='?',
        default="1000",
        help="The batch size to use when reading and writing the dataset. Defaults to 1000."
    )
    parser.add_argument(
        "dataset_file",
        type=str,
        nargs='?',
        default="customers_generated_10000_seed42.jsonl",
        help="The filename of the source the dataset. Defaults to customers_generated_1000_seed42.jsonl."
    )
    args = parser.parse_args()
    dataset_file = args.dataset_file
    batch_size = args.batch_size
    for index, batch in enumerate(batch_read_jsonl(dataset_file, batch_size)):
        # process rows in batches
        print("Processing Batch:", index)
        output_batch = []
        for record in batch:
            # save mapping of payment method ids and issuers
            payment_method_ids = {}
            payment_methods = record.get('paymentMethods', [])
            for method in payment_methods:
                payment_method_ids[method.get('paymentMethodId')] = method.get('paymentMethodIssuer')
            
            # parse transactions and increment velocities for each valid transaction
            issuer_velocities = {}
            transactions = record.get('transactions', [])
            for trans in transactions:
                # check if transaction timestamp is within the last 24 hours
                timestamp = datetime.fromisoformat(trans.get('loggedAt'))
                now = datetime.now(timezone.utc)
                if not (now - timedelta(hours=24) <= timestamp <= now):
                    continue
                
                # increment the velocity for the payment method issuer
                id = trans.get('paymentMethodId')
                issuer = payment_method_ids.get(id)
                if issuer not in issuer_velocities:
                    issuer_velocities[issuer] = 0
                issuer_velocities[issuer] += 1
            
            record['paymentMethodVelocities'] = issuer_velocities
            
            # save the updated records in batches for improved performance
            output_batch.append(record)
        # Write the output batch to a file
        output_filename = f"velocity_{dataset_file}"
        with open(output_filename, 'a') as outfile:
            for record in output_batch:
                outfile.write(json.dumps(record) + '\n')


    print("Processing complete. Time taken:", datetime.now() - t0)
    print("Output saved to:", output_filename)

# To run: python velocity.py [batch_size] [dataset_file]

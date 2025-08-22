# Writeup
See below my overview and analysis of my solution to the two tasks. 

## Task 1
This task required adding a new feature to each row that shows the velocity of the various paymentMethodIssuers present for each user.

### Basic Requirements
There are 4 basic requirements for this task:
- reading in the dataset
- tracking which transactions are associated with which paymentMethodIssuer
- counting only transactions performed in the last 24 hours
- writing the updated dataset

I have added brief commments throughout my code located in [velocity.py](velocity.py) indicating what each section does.

### Running
Use this command to run the script generating the velocities on the dataset:

`python velocity.py [batch_size] [dataset_file]`

### Code Analysis

There are a few extra steps I perform to optimize readability and performance:
- processing rows in batches, this is a key feature allowing for processing of very large datasets by loading only parts of the dataset into memory at once
    - the batch size can be specified via the command line eg: `python velocity.py {batch_size}`
    - as the dataset grows the batch size should grow to effectively utilize memory of the machine
    - the input data is read in via batches
    - the output data is written using batches of the same size
- `paymentMethodId` mapping to `paymentMethodIssuer`, improves readability and performance using a dictionary for lookups

### Dataset Analysis
I performed a short analysis of the dataset in [data_analysis.ipynb](data_analysis.ipynb)
- Check if there are multiple payment methods from the same paymentMethodIssuer
- Check what the range of dates looks like

### Scaling Analysis
The time complexity of the script is `O(n*p + n*t)` where `n` is the number of rows, `p` is the number of payment methods, and `t` is the number of transactions

As the number of records increases, the time taken to process the dataset will also increase linearly

Future improvements could include parallel processing with GPUs or distributed systems for very large datasets as the records do not have to be updated sequentially, they can be processed in parallel.

### Statistics
Using the 100,000 generated dataset, the velocity script takes about 2.7 seconds to run on my machine.

### Output

The output dataset is saved to a file with velocity prepended to the original dataset filename eg: `velocity_customers_generated_100000_seed42.jsonl`

Each row of the new dataset has the new feature `paymentMethodVelocities` which is an empty dict if there were no transactions in the past 24 hours and lists the velocities of the paymentMethodIssuers if there were transactions in the last 24 hours from when the script is run.

Eg:
`"paymentMethodVelocities": {"His Majesty Bank Corp.": 1, "Bulwark Trust Corp.": 1}}`

Meaning there was 1 transaction in the last 24 hours using a payment method from each of the paymentMethodIssuers respectively `His Majesty Bank Corp.` and `Bulwark Trust Corp.`

## Task 2

### Code Analysis

To serve the model I have used a simple FastAPI server hosting a POST at the `/predict` endpoint for inference. The server is located in [serve_model.py](serve_model.py). FastAPI is a rapidly growing framework and considered faster and more preferred to Flask or other serving options especially for serving models.

The context manager `with torch.no_grad():` is used to remove the memory needed to track the gradients which are only needed from training the model, not for inference. 

The endpoint returns `"fraud_probability": prob, "is_fraud": prediction` containing the probability of fraud and the final classification of fraud or not.

The request body is validated using a `TransactionRequest` class using pydantic for API request validation.

### Running

To start the server run: `fastapi dev serve_model.py`
To make a request to the endpoint: 
```
curl -X POST "http://127.0.0.1:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 150.75,
    "time": 14, 
    "mismatch": 1,
    "frequency": 3
  }'
```

This endpoint expects `"amount": 150.75,
    "time": 14,
    "mismatch": 1,
    "frequency": 3` in the request body.


### Statistics

The average response time for a single request running the server on my machine was: `0.00239` seconds.

I performed throughput testing and it was able to process `3200` requests in `1.069` seconds

This was the command I used to test the endpoint throughput:
`ab -n 3200 -c 50 -p payload.json -T application/json http://127.0.0.1:8000/predict`

### Further Optimizations
To improve throughput, batch processing could be used to more efficiently respond to requests coming in at the same time.

The server could also be deployed on multiple workers improving throughput.

There are many more features of FastAPI such as lifespan settings which are not implemented in this simple server.

## Environemnt
I have the environment requirements saved in the [Pipfile](Pipfile) and versions in the [pipfile.lock](pipfile.lock)

run `pipenv shell` to enter the virtual environment before any of the above referenced commands.
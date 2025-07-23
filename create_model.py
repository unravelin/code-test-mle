import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim


# 1. Define the Neural Network Model for Classification
class FraudNet(nn.Module):
    """
    A simple neural network for binary classification.
    It's designed for a fraud detection task.
    Input dimension: 4 (based on our synthetic features)
    Output dimension: 1 (a logit value for classification)
    """
    def __init__(self, input_features=4):
        super(FraudNet, self).__init__()
        # Define a sequence of layers
        self.layer_stack = nn.Sequential(
            nn.Linear(input_features, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1) # Output is a single logit
        )

    def forward(self, x):
        """
        Defines the forward pass of the neural network.
        """
        return self.layer_stack(x)

# 2. Generate Synthetic Fraud Prevention Test Data
def generate_fraud_data(num_samples=1000):
    """
    Generates a synthetic dataset for fraud detection.
    """
    # Feature generation
    amounts = np.random.lognormal(mean=3, sigma=1, size=num_samples) 
    times = np.random.randint(0, 24, size=num_samples)
    mismatches = np.random.randint(0, 2, size=num_samples)
    frequencies = np.random.randint(1, 10, size=num_samples)

    # Create features matrix
    features = np.vstack([amounts, times, mismatches, frequencies]).T

    # Label generation (simple rules for fraud)
    fraud_prob = 1 / (1 + np.exp(-(
        0.2 * (amounts / 100) + 0.1 * ((times < 6) | (times > 22)) + 
        2.0 * mismatches + 0.3 * (frequencies > 5) - 4.0
    )))
    labels = (np.random.rand(num_samples) < fraud_prob).astype(int)

    # Normalize features
    features = (features - features.mean(axis=0)) / features.std(axis=0)

    print(f"Generated {num_samples} samples. Number of fraud cases: {labels.sum()}")
    
    X_tensor = torch.tensor(features, dtype=torch.float32)
    y_tensor = torch.tensor(labels, dtype=torch.float32).view(-1, 1)
    
    return X_tensor, y_tensor

# Generate the data
X_train, y_train = generate_fraud_data()

# 3. Instantiate and Train the Model
model = FraudNet(input_features=X_train.shape[1])
loss_function = nn.BCEWithLogitsLoss()
optimizer = optim.Adam(model.parameters(), lr=0.005)

print("\nStarting model training...")
epochs = 200
for epoch in range(epochs):
    model.train()
    y_logits = model(X_train)
    loss = loss_function(y_logits, y_train)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    if (epoch + 1) % 20 == 0:
        print(f'Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}')
print("Training finished.")

# 4. Save the Model in TorchScript Format
# This is the key change for creating a generic, deployable model.
# We first set the model to evaluation mode.
model.eval()
# `torch.jit.script` analyzes the model's forward method to create a
# serialized, self-contained representation.
scripted_model = torch.jit.script(model)
model_path = 'fraud_prevention_model.pt'
scripted_model.save(model_path)

print(f"\nModel successfully trained and saved in TorchScript format to '{model_path}'")

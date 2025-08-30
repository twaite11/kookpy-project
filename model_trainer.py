import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import tensorflow as tf
import joblib
import os

def build_and_train_model(X_train, y_train):
    """
    Builds and trains a simple neural network model.

    Args:
        X_train (np.array): Training features.
        y_train (np.array): Training target.

    Returns:
        tf.keras.Model: The trained TensorFlow model.
    """
    # Define the neural network architecture
    model = Sequential([
        Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
        Dense(32, activation='relu'),
        Dense(1)  # Output layer for a single regression value
    ])

    # Compile the model
    model.compile(optimizer='adam', loss='mean_squared_error')

    # Train the model
    print("Starting model training...")
    model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=1)

    print("\nTraining complete.")
    return model

def save_model_and_scalers(model, scaler_X, scaler_y, model_filename, scaler_X_filename, scaler_y_filename):
    """
    Saves the trained model and data scalers to disk.

    Args:
        model (tf.keras.Model): The trained TensorFlow model.
        scaler_X (StandardScaler): The scaler for features.
        scaler_y (StandardScaler): The scaler for the target variable.
        model_filename (str): Filename for the model.
        scaler_X_filename (str): Filename for the feature scaler.
        scaler_y_filename (str): Filename for the target scaler.
    """
    # Save the model
    model.save(model_filename)
    # Save the scalers
    joblib.dump(scaler_X, scaler_X_filename)
    joblib.dump(scaler_y, scaler_y_filename)
    print(f"Model and scalers saved to {model_filename}, {scaler_X_filename}, and {scaler_y_filename}.")

if __name__ == '__main__':
    # Define the filename for the historical data
    data_file = "historical_surf_data.csv"

    # Check if the data file exists
    if not os.path.exists(data_file):
        print(f"Error: Historical data file '{data_file}' not found.")
        print("Please run 'data_collector.py' first to generate the data.")
    else:
        # Load the data
        try:
            df = pd.read_csv(data_file)
        except Exception as e:
            print(f"Error loading data from '{data_file}': {e}")
            df = pd.DataFrame()

        if not df.empty:
            # Drop any rows with missing values that might have slipped through
            df.dropna(inplace=True)

            # Define features and target variable
            features = ['swell_wave_height', 'swell_wave_period', 'wind_speed_10m']
            target = ['wave_quality_score']

            # Ensure the DataFrame is not empty after dropping NaNs
            if not df.empty and all(col in df.columns for col in features + target):
                # Prepare the data for the model
                X = df[features]
                y = df[target]

                print(f"Shape of X: {X.shape}")
                print(f"Shape of y: {y.shape}")

                # Split data into training and testing sets
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )

                # Scale the data using StandardScaler
                scaler_X = StandardScaler()
                X_train_scaled = scaler_X.fit_transform(X_train)

                scaler_y = StandardScaler()
                y_train_scaled = scaler_y.fit_transform(y_train)

                # Build and train the model
                model = build_and_train_model(X_train_scaled, y_train_scaled)

                # Save the trained model and scalers
                save_model_and_scalers(
                    model,
                    scaler_X,
                    scaler_y,
                    'wave_prediction_model.keras',
                    'scaler_X.pkl',
                    'scaler_y.pkl'
                )
            else:
                print("Error: DataFrame is empty or missing required columns after cleaning.")
        else:
            print("Error: DataFrame is empty after loading. Check the CSV file.")

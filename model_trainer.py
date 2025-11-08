import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow import keras
import joblib
import os


def build_and_train_model(X_train, y_train, epochs=100):
    """
    Bread and butter of creating the actual model
    Builds and trains a simple neural network model using TensorFlow.
    TODO***: 1. Is MAE the best measure for loss and accuracy??? try MSE and others
    TODO***: 2. Need high quality image data... find source
    TODO***: 3. define and test CNN fusion layer for images (ResNet was looking best last check, try others)
    Args:
        X_train (np.array): Training data for features.
        y_train (np.array): Training data for the target variable (wave quality score).
        epochs (int): The number of times to train the model on the entire dataset.

    Returns:
        keras.Model: The trained TensorFlow model.
    """
    model = keras.Sequential([
        keras.layers.Dense(64, activation='relu',
                           input_shape=(X_train.shape[1],)),
        keras.layers.Dense(32, activation='relu'),
        keras.layers.Dense(1)
    ])

    model.compile(optimizer='adam', loss='mean_squared_error')

    print("Starting model training...")
    model.fit(X_train, y_train, epochs=epochs, batch_size=32, verbose=1)
    print("Model training complete.")
    return model


def save_model_and_scalers(model, scaler_X, scaler_y, model_path='wave_prediction_model.keras', scaler_X_path='scaler_X.pkl', scaler_y_path='scaler_y.pkl'):
    """
    Save model

    Args:
        model (keras.Model): The trained TensorFlow model.
        scaler_X (StandardScaler): The scaler used for the input features.
        scaler_y (StandardScaler): The scaler used for the target variable.
        model_path (str): File path for saving the model.
        scaler_X_path (str): File path for saving the feature scaler.
        scaler_y_path (str): File path for saving the target scaler.
    """
    model.save(model_path)
    joblib.dump(scaler_X, scaler_X_path)
    joblib.dump(scaler_y, scaler_y_path)
    print("\nModel and scalers saved successfully.")


if __name__ == '__main__':

    file_path = 'historical_surf_data.csv'

    if not os.path.exists(file_path):
        print(f"Error: Data file not found at '{file_path}'.")
        print("Please run 'data_collector.py' first to generate the historical data.")
    else:
        # load and drop if missing
        df = pd.read_csv(file_path, parse_dates=['time'])
        df.dropna(inplace=True)

        if df.empty:
            print(
                "Error: empty")
        else:
            # Define your features and target
            features = ['swell_wave_height', 'swell_wave_period',
                        'wind_speed_10m', 'sea_level_height_msl']
            target = 'wave_quality_score'

            # Check if all required columns exist
            if not all(col in df.columns for col in features + [target]):
                print("error missing column")
                print(f"required columns: {features + [target]}")
            else:
                X = df[features]
                y = df[target]

                # split the data into training and testing sets
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42)

                # scale the features and target data
                scaler_X = StandardScaler()
                X_train_scaled = scaler_X.fit_transform(X_train)

                scaler_y = StandardScaler()
                y_train_scaled = scaler_y.fit_transform(
                    y_train.values.reshape(-1, 1))

                # build and train the model
                model = build_and_train_model(X_train_scaled, y_train_scaled)

                # save the model and scalers
                save_model_and_scalers(model, scaler_X, scaler_y)

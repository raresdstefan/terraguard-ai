import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
import joblib

# Load dataset
file_path = "datasets/large_training_dataset.csv"
df = pd.read_csv(file_path)

# Features
X = df[["humidity", "ph", "light", "temperature"]]

# Labels
encoder = LabelEncoder()
y = encoder.fit_transform(df["soil_quality"])

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# Train model
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42
)

model.fit(X_train, y_train)

# Evaluate
predictions = model.predict(X_test)

print(classification_report(y_test, predictions))

# Save model
joblib.dump(model, "models/soil_quality_model.pkl")
joblib.dump(encoder, "models/label_encoder.pkl")

print("Model trained successfully")

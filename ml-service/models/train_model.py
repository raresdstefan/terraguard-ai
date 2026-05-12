"""
TerraGuard AI — Model Training
================================
Input features (8 parameters):
  Luminosity sensor : luminosity
  7-in-1 soil sensor: N, P, K, ph, EC, humidity, temperature
"""

import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import joblib

FEATURES = ["luminosity", "N", "P", "K", "ph", "EC", "humidity", "temperature"]

# Load final (balanced, scientifically grounded) dataset
file_path = "datasets/large_training_dataset.csv"
df = pd.read_csv(file_path)

print(f"Dataset loaded: {len(df):,} rows")
print("Class distribution:\n", df["soil_quality"].value_counts().to_string())

X = df[FEATURES]

encoder = LabelEncoder()
y = encoder.fit_transform(df["soil_quality"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

model = RandomForestClassifier(
    n_estimators=150,
    max_depth=14,
    min_samples_leaf=3,
    random_state=42,
    n_jobs=-1,
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)
print("\n── Test Set Report ──")
print(classification_report(y_test, predictions, target_names=encoder.classes_))

cv_scores = cross_val_score(model, X, y, cv=StratifiedKFold(5), scoring="accuracy")
print(f"── Cross-Validation (5-fold) ──")
print(f"  Mean: {cv_scores.mean():.4f}  Std: {cv_scores.std():.4f}")

print("\n── Feature Importances ──")
for feat, imp in sorted(zip(FEATURES, model.feature_importances_),
                         key=lambda x: -x[1]):
    bar = "█" * int(imp * 50)
    print(f"  {feat:12s} {imp:.4f}  {bar}")

joblib.dump(model,   "models/soil_quality_model.pkl")
joblib.dump(encoder, "models/label_encoder.pkl")
print("\nModel saved → models/soil_quality_model.pkl")

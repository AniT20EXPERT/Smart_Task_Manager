import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier
import matplotlib.pyplot as plt
import seaborn as sns

# ==========================
# 1️⃣ Load your dataset
# ==========================
data = pd.read_csv("synthetic_scheduler_dataset_tq.csv")  # <-- change this

# Separate features and target
X = data.drop(columns=["best_tq"])   # replace 'target' with your actual label column name
y = data["best_tq"]

# ==========================
# 2️⃣ Optional: Feature scaling
# ==========================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ==========================
# 3️⃣ Optional: SMOTE for imbalance
# ==========================
use_smote = True
if use_smote:
    sm = SMOTE(random_state=42, sampling_strategy="auto")
    X_scaled, y = sm.fit_resample(X_scaled, y)
    print(f"✅ After SMOTE: {X_scaled.shape[0]} samples")

# ==========================
# 4️⃣ Train-test split
# ==========================
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

# ==========================
# 5️⃣ Define model
# ==========================
xgb = XGBClassifier(
    objective="multi:softmax",
    num_class=len(np.unique(y)),
    eval_metric="mlogloss",
    tree_method="hist",  # fast for larger data
    use_label_encoder=False,
    random_state=42
)

# ==========================
# 6️⃣ Parameter tuning (quick randomized search)
# ==========================
param_grid = {
    "n_estimators": [200, 400, 600],
    "learning_rate": [0.01, 0.05, 0.1],
    "max_depth": [3, 5, 7, 9],
    "subsample": [0.7, 0.8, 1.0],
    "colsample_bytree": [0.7, 0.8, 1.0],
    "gamma": [0, 0.1, 0.3, 0.5],
    "min_child_weight": [1, 3, 5]
}

search = RandomizedSearchCV(
    xgb,
    param_distributions=param_grid,
    n_iter=20,
    scoring="accuracy",
    cv=3,
    verbose=1,
    n_jobs=-1,
    random_state=42
)

search.fit(X_train, y_train)

best_xgb = search.best_estimator_
print("\n✅ Best Parameters:")
print(search.best_params_)

#save model
# After training your model (e.g. best_xgb)
best_xgb.save_model("xgb_model_tq.json")
print("✅ Model saved to xgb_model_tq.json")




# ==========================
# 7️⃣ Evaluate model
# ==========================
y_pred = best_xgb.predict(X_test)

acc = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average="weighted")
cm = confusion_matrix(y_test, y_pred)

print("\n✅ XGBoost Results:")
print(f"Accuracy: {acc:.4f}")
print(f"F1 Score: {f1:.4f}")
print("\nConfusion Matrix:\n", cm)
print("\nClassification Report:\n", classification_report(y_test, y_pred))

# ==========================
# 8️⃣ Plot confusion matrix
# ==========================
plt.figure(figsize=(7,5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()

# ==========================
# 9️⃣ Feature importance
# ==========================
plt.figure(figsize=(10,6))
sns.barplot(x=best_xgb.feature_importances_, y=X.columns)
plt.title("Feature Importance")
plt.tight_layout()
plt.show()

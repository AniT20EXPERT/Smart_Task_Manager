import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
df = pd.read_csv("synthetic_scheduler_dataset_algo.csv")
corr = df.corr(numeric_only=True)
plt.figure(figsize=(10,6))
sns.heatmap(corr[['best_algo']].sort_values(by='best_algo', ascending=False), annot=True, cmap='coolwarm')
plt.title("Feature correlation with best_algo")
plt.show()

from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
# Features and target
X = df.drop(columns=["best_algo"])
y = df["best_algo"]
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X)
plt.scatter(X_pca[:,0], X_pca[:,1], c=y, cmap='tab10', s=10)
plt.title("PCA projection of dataset")
plt.show()


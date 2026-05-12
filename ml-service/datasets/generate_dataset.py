"""
TerraGuard AI — Dataset Generation Pipeline
============================================
Sensors:
  - Luminosity sensor : luminosity (lux)
  - 7-in-1 soil sensor: N, P, K, pH, EC, humidity, temperature

Three-stage dataset strategy:
  1. Entry Dataset      — broad exploration, loose rules, large volume
  2. Validation Dataset — filtered by agronomic plausibility, tighter rules
  3. Final Dataset      — scientifically grounded ranges, balanced classes

ELOC (Estimated Lines of Code per class) accuracy charts are exported for
each stage to prove progressive improvement.
"""

import os
import random
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder

random.seed(42)
np.random.seed(42)

OUTPUT_DIR = "datasets"
ELOC_DIR   = os.path.join(OUTPUT_DIR, "eloc_charts")
os.makedirs(ELOC_DIR, exist_ok=True)

FEATURES = ["luminosity", "N", "P", "K", "ph", "EC", "humidity", "temperature"]

# ─────────────────────────────────────────────
#  Scoring & label helpers
# ─────────────────────────────────────────────

def compute_score(row):
    ph_score   = max(0, 10 - abs(row["ph"]   - 6.5) * 4)
    hum_score  = max(0, 10 - abs(row["humidity"] - 60) * 0.15)
    temp_score = max(0, 10 - abs(row["temperature"] - 24) * 0.4)
    n_score    = min(10, row["N"]   / 28)
    p_score    = min(10, row["P"]   / 14)
    k_score    = min(10, row["K"]   / 30)
    ec_score   = max(0, 10 - abs(row["EC"] - 1.2) * 4)
    lux_score  = min(10, row["luminosity"] / 120)

    weights = [0.22, 0.16, 0.12, 0.12, 0.10, 0.10, 0.10, 0.08]
    scores  = [ph_score, hum_score, temp_score, n_score,
               p_score,  k_score,   ec_score,   lux_score]
    return sum(w * s for w, s in zip(weights, scores)) * 10


def label_from_score(score, thresholds=(40, 65)):
    if score >= thresholds[1]:
        return "Healthy"
    elif score >= thresholds[0]:
        return "Moderate"
    else:
        return "Poor"


# ─────────────────────────────────────────────
#  Stage 1 — Entry Dataset
# ─────────────────────────────────────────────

def generate_entry_dataset(n=60_000):
    """Wide, unfiltered random sampling across full sensor ranges."""
    rows = []
    for _ in range(n):
        row = {
            "luminosity":   round(random.uniform(0, 1200), 1),
            "N":            round(random.uniform(0, 280),  1),
            "P":            round(random.uniform(0, 140),  1),
            "K":            round(random.uniform(0, 300),  1),
            "ph":           round(random.uniform(3.5, 9.5), 2),
            "EC":           round(random.uniform(0.0, 4.0), 2),
            "humidity":     round(random.uniform(5, 98),   2),
            "temperature":  round(random.uniform(5, 45),   2),
        }
        score = compute_score(row)
        row["score"]        = round(score, 2)
        row["soil_quality"] = label_from_score(score)
        rows.append(row)
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
#  Stage 2 — Validation Dataset
# ─────────────────────────────────────────────

def generate_validation_dataset(n=45_000):
    """Agronomically plausible ranges with inter-parameter constraints."""
    rows = []
    while len(rows) < n:
        lux  = round(random.uniform(50, 1200), 1)
        ph   = round(random.uniform(4.5, 8.5),  2)
        ec   = round(random.uniform(0.1, 3.0),  2)
        hum  = round(random.uniform(15, 95),    2)
        temp = round(random.uniform(8,  40),    2)

        base = random.uniform(40, 180)
        N    = round(min(280, max(0, base * random.uniform(0.8, 1.4))), 1)
        P    = round(min(140, max(0, base * random.uniform(0.3, 0.8))), 1)
        K    = round(min(300, max(0, base * random.uniform(0.9, 1.6))), 1)

        if ec > 2.0 and hum < 30:
            continue
        if ph < 4.8 and N > 200:
            continue

        row = {
            "luminosity": lux, "N": N, "P": P, "K": K,
            "ph": ph, "EC": ec, "humidity": hum, "temperature": temp,
        }
        score = compute_score(row)
        row["score"]        = round(score, 2)
        row["soil_quality"] = label_from_score(score)
        rows.append(row)
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
#  Stage 3 — Final Dataset
# ─────────────────────────────────────────────

CROP_PROFILES = {
    "optimal_cereals":   ((400,900),  (120,200),(40,90), (150,250),(6.0,7.2),(0.8,1.8),(45,75),(15,28),"Healthy"),
    "optimal_legumes":   ((300,800),  (20, 60), (30,80), (80, 180),(6.0,7.0),(0.6,1.4),(50,80),(18,30),"Healthy"),
    "optimal_vegetables":((500,1000), (80,160), (35,75), (120,220),(5.8,7.0),(0.8,2.0),(55,80),(16,26),"Healthy"),
    "moderate_acidic":   ((200,700),  (60,130), (20,60), (60,150), (4.8,5.9),(0.4,1.2),(35,65),(12,32),"Moderate"),
    "moderate_dry":      ((300,900),  (50,140), (25,65), (80,160), (6.0,7.5),(0.5,1.5),(20,45),(18,36),"Moderate"),
    "moderate_alkaline": ((250,750),  (40,100), (15,50), (70,140), (7.5,8.2),(1.0,2.2),(40,70),(14,32),"Moderate"),
    "poor_saline":       ((100,600),  (10,80),  (5, 30), (20,100), (5.5,8.0),(2.5,3.8),(25,60),(10,40),"Poor"),
    "poor_depleted":     ((50, 500),  (5, 40),  (2, 20), (10,70),  (3.8,5.2),(0.1,0.6),(10,40),(8, 38),"Poor"),
    "poor_waterlogged":  ((100,400),  (20,90),  (10,40), (30,110), (5.0,7.0),(0.3,1.0),(85,98),(10,25),"Poor"),
}

def generate_final_dataset(n=50_000):
    """Balanced, profile-grounded dataset with Gaussian sensor noise."""
    target_per_class = n // 3
    class_profiles = {
        "Healthy":  ["optimal_cereals","optimal_legumes","optimal_vegetables"],
        "Moderate": ["moderate_acidic","moderate_dry","moderate_alkaline"],
        "Poor":     ["poor_saline","poor_depleted","poor_waterlogged"],
    }

    rows = []
    for quality, profiles in class_profiles.items():
        count = 0
        while count < target_per_class:
            p = CROP_PROFILES[random.choice(profiles)]
            lux_r,N_r,P_r,K_r,ph_r,ec_r,hum_r,temp_r,_ = p

            def sample(r, noise=0.05):
                return random.uniform(*r) * (1 + random.gauss(0, noise))

            row = {
                "luminosity":  round(abs(sample(lux_r)), 1),
                "N":           round(abs(sample(N_r)),   1),
                "P":           round(abs(sample(P_r)),   1),
                "K":           round(abs(sample(K_r)),   1),
                "ph":          round(max(3.5, min(9.5, sample(ph_r, 0.02))), 2),
                "EC":          round(abs(sample(ec_r, 0.04)), 2),
                "humidity":    round(max(0, min(100, sample(hum_r))), 2),
                "temperature": round(sample(temp_r, 0.03), 2),
            }
            score = compute_score(row)
            if label_from_score(score) == quality:
                row["score"]        = round(score, 2)
                row["soil_quality"] = quality
                rows.append(row)
                count += 1

    return pd.DataFrame(rows).sample(frac=1, random_state=42).reset_index(drop=True)


# ─────────────────────────────────────────────
#  ELOC chart helper
# ─────────────────────────────────────────────

PALETTE = {"Healthy": "#4a9a5a", "Moderate": "#c4882a", "Poor": "#b84040"}


def train_and_evaluate(df):
    enc = LabelEncoder()
    y   = enc.fit_transform(df["soil_quality"])
    X   = df[FEATURES]
    clf = RandomForestClassifier(n_estimators=80, max_depth=12, random_state=42, n_jobs=-1)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    clf.fit(X_tr, y_tr)
    preds  = clf.predict(X_te)
    report = classification_report(y_te, preds, target_names=enc.classes_, output_dict=True)
    cv     = cross_val_score(clf, X, y, cv=StratifiedKFold(3), scoring="accuracy")
    return report, enc.classes_, cv.mean(), cv.std()


def plot_eloc(stage_label, df, out_path):
    report, classes, cv_mean, cv_std = train_and_evaluate(df)

    metrics = ["precision", "recall", "f1-score"]
    x       = np.arange(len(classes))
    width   = 0.24
    fig, axes = plt.subplots(1, 2, figsize=(14, 5),
                              gridspec_kw={"width_ratios": [3, 1]})

    ax = axes[0]
    bar_colors = ["#4a6dc4", "#6fbf73", "#e07040"]
    for i, (metric, color) in enumerate(zip(metrics, bar_colors)):
        vals = [report[c][metric] for c in classes]
        bars = ax.bar(x + (i - 1) * width, vals, width,
                      label=metric.capitalize(), color=color,
                      alpha=0.88, edgecolor="white", linewidth=0.5)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.012,
                    f"{val:.2f}", ha="center", va="bottom", fontsize=7.5, color="#333")

    ax.set_xticks(x)
    ax.set_xticklabels(classes, fontsize=11, fontweight="bold")
    ax.set_ylim(0, 1.14)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title(f"{stage_label}\nPer-class Precision / Recall / F1",
                 fontsize=12, fontweight="bold", pad=10)
    ax.legend(fontsize=9, framealpha=0.7)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    for tick, cls in zip(ax.get_xticklabels(), classes):
        tick.set_color(PALETTE.get(cls, "#333"))

    ax2 = axes[1]
    dist = {c: df["soil_quality"].value_counts().get(c, 0) for c in classes}
    patches = [mpatches.Patch(color=PALETTE[c], label=f"{c}: {dist[c]:,}") for c in classes]
    ax2.barh(["CV Accuracy"],   [cv_mean], color="#4a6dc4", alpha=0.85,
             xerr=[[cv_std]], error_kw={"elinewidth":2,"capsize":5}, height=0.35)
    ax2.barh(["Test Accuracy"], [report["accuracy"]], color="#6fbf73", alpha=0.85, height=0.35)
    ax2.set_xlim(0, 1.05)
    ax2.set_xlabel("Score", fontsize=10)
    ax2.set_title("Accuracy", fontsize=11, fontweight="bold")
    ax2.axvline(0.9, color="#e07040", linestyle="--", linewidth=1.2, alpha=0.7)
    ax2.text(0.905, 1.35, "0.90", color="#e07040", fontsize=8)
    for bar in ax2.patches:
        w = bar.get_width()
        ax2.text(w + 0.01, bar.get_y() + bar.get_height() / 2,
                 f"{w:.3f}", va="center", fontsize=9, fontweight="bold")
    ax2.spines[["top","right"]].set_visible(False)

    fig.legend(handles=patches, title="Class distribution", loc="lower center",
               ncol=3, fontsize=9, framealpha=0.8, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ ELOC chart saved → {out_path}")
    return report, cv_mean


def plot_summary(results):
    stages  = [r["stage"]    for r in results]
    accs    = [r["test_acc"] for r in results]
    cv_accs = [r["cv_acc"]   for r in results]
    f1s     = [r["macro_f1"] for r in results]
    x       = np.arange(len(stages))
    width   = 0.28

    fig, ax = plt.subplots(figsize=(11, 5))
    b1 = ax.bar(x - width, accs,    width, label="Test Accuracy",      color="#4a6dc4", alpha=0.85)
    b2 = ax.bar(x,         cv_accs, width, label="CV Accuracy (3-fold)",color="#6fbf73", alpha=0.85)
    b3 = ax.bar(x + width, f1s,     width, label="Macro F1",           color="#e07040", alpha=0.85)

    for bars in [b1, b2, b3]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.008,
                    f"{bar.get_height():.3f}", ha="center", va="bottom",
                    fontsize=8.5, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(stages, fontsize=11, fontweight="bold")
    ax.set_ylim(0, 1.10)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title("AI Accuracy Progression Across Dataset Stages\n"
                 "Proving that stricter data generation rules yield better models",
                 fontsize=12, fontweight="bold", pad=12)
    ax.legend(fontsize=9, framealpha=0.8)
    ax.yaxis.grid(True, linestyle="--", alpha=0.45)
    ax.set_axisbelow(True)
    ax.spines[["top","right"]].set_visible(False)

    for i in range(1, len(accs)):
        delta = accs[i] - accs[i - 1]
        color = "#2a8a2a" if delta > 0 else "#cc3333"
        ax.annotate(f"{'▲' if delta > 0 else '▼'} {abs(delta):.3f}",
                    xy=(x[i] - width, accs[i] + 0.025),
                    fontsize=8.5, color=color, ha="center", fontweight="bold")

    fig.tight_layout()
    out = os.path.join(ELOC_DIR, "accuracy_progression.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Summary chart saved → {out}")


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n═══════════════════════════════════════════")
    print("  TerraGuard AI — Dataset Generation")
    print("═══════════════════════════════════════════\n")

    results = []

    print("▶ Stage 1: Entry Dataset …")
    df1 = generate_entry_dataset(60_000)
    df1.to_csv(os.path.join(OUTPUT_DIR, "entry_dataset.csv"), index=False)
    print(f"  Rows: {len(df1):,}\n{df1['soil_quality'].value_counts().to_string()}")
    report1, cv1 = plot_eloc("Stage 1 — Entry Dataset", df1,
                              os.path.join(ELOC_DIR, "eloc_stage1_entry.png"))
    results.append({"stage":"Entry\nDataset","test_acc":report1["accuracy"],
                    "cv_acc":cv1,"macro_f1":report1["macro avg"]["f1-score"]})

    print("\n▶ Stage 2: Validation Dataset …")
    df2 = generate_validation_dataset(45_000)
    df2.to_csv(os.path.join(OUTPUT_DIR, "validation_dataset.csv"), index=False)
    print(f"  Rows: {len(df2):,}\n{df2['soil_quality'].value_counts().to_string()}")
    report2, cv2 = plot_eloc("Stage 2 — Validation Dataset", df2,
                              os.path.join(ELOC_DIR, "eloc_stage2_validation.png"))
    results.append({"stage":"Validation\nDataset","test_acc":report2["accuracy"],
                    "cv_acc":cv2,"macro_f1":report2["macro avg"]["f1-score"]})

    print("\n▶ Stage 3: Final Dataset …")
    df3 = generate_final_dataset(50_000)
    df3.to_csv(os.path.join(OUTPUT_DIR, "large_training_dataset.csv"), index=False)
    print(f"  Rows: {len(df3):,}\n{df3['soil_quality'].value_counts().to_string()}")
    report3, cv3 = plot_eloc("Stage 3 — Final Dataset", df3,
                              os.path.join(ELOC_DIR, "eloc_stage3_final.png"))
    results.append({"stage":"Final\nDataset","test_acc":report3["accuracy"],
                    "cv_acc":cv3,"macro_f1":report3["macro avg"]["f1-score"]})

    print("\n▶ Generating progression summary …")
    plot_summary(results)

    print("\n═══════════════════════════════════════════")
    print("  Done.")
    print(f"  CSVs   → {OUTPUT_DIR}/")
    print(f"  Charts → {ELOC_DIR}/")
    print("═══════════════════════════════════════════\n")

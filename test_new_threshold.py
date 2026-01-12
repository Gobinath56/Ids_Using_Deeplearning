"""
QUICK THRESHOLD TESTING
Test different thresholds instantly without re-running evaluation
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report
)

print("=" * 80)
print("           QUICK THRESHOLD TESTING")
print("=" * 80)

# Load saved results
print("\nLoading evaluation results...")
data = np.load('evaluation_results.npz', allow_pickle=True)
y_test = data['y_test']
y_scores = data['y_scores']
attack_types = data['attack_types']

print(f"✓ Loaded {len(y_test)} test samples")


# ===========================
# TEST NEW THRESHOLD
# ===========================

def test_threshold(threshold_value):
    """Test a specific threshold and show results"""

    print("\n" + "=" * 80)
    print(f"   TESTING THRESHOLD = {threshold_value}")
    print("=" * 80)

    # Recalculate predictions
    y_pred = (y_scores > threshold_value).astype(int)

    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

    # Display
    print(f"\n📊 PERFORMANCE WITH THRESHOLD = {threshold_value}:\n")
    print(f"   Accuracy:        {accuracy:.4f} ({accuracy * 100:.2f}%)")
    print(f"   Precision:       {precision:.4f}")
    print(f"   Recall (TPR):    {recall:.4f}")
    print(f"   Specificity:     {specificity:.4f}")
    print(f"   F1-Score:        {f1:.4f}")
    print(f"   FPR:             {fpr:.4f}")

    print(f"\n📈 CONFUSION MATRIX:")
    print(f"   True Negatives:  {tn}")
    print(f"   False Positives: {fp}")
    print(f"   False Negatives: {fn}")
    print(f"   True Positives:  {tp}")

    # Per-attack analysis
    print("\n🔍 PER-ATTACK TYPE DETECTION:")
    attack_names = ['Normal', 'DoS_Flooding', 'Spoofing', 'MITM',
                    'Jamming', 'Replay', 'Data_Injection', 'Resource_Exhaustion']

    for attack_name in attack_names:
        mask = attack_types == attack_name
        if np.sum(mask) > 0:
            detected = np.sum(y_pred[mask] == 1)
            total = np.sum(mask)
            rate = detected / total * 100
            symbol = "✓" if rate >= 90 else "⚠" if rate >= 70 else "✗"
            print(f"   {symbol} {attack_name:20s}: {detected}/{total} ({rate:.1f}%)")

    # Quick visualization
    fig = plt.figure(figsize=(14, 5))

    # Confusion Matrix
    ax1 = plt.subplot(1, 3, 1)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Normal', 'Attack'],
                yticklabels=['Normal', 'Attack'],
                annot_kws={'size': 16, 'weight': 'bold'},
                cbar=False)
    plt.title(f'Confusion Matrix\n(Threshold = {threshold_value})',
              fontsize=14, fontweight='bold')
    plt.ylabel('True', fontsize=12)
    plt.xlabel('Predicted', fontsize=12)

    # Metrics
    ax2 = plt.subplot(1, 3, 2)
    metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
    values = [accuracy, precision, recall, f1]
    colors = ['#2ecc71' if v >= 0.9 else '#f39c12' if v >= 0.8 else '#e74c3c'
              for v in values]

    bars = plt.bar(metrics, values, color=colors, edgecolor='black', linewidth=2)
    plt.ylim([0, 1.1])
    plt.ylabel('Score', fontsize=12, fontweight='bold')
    plt.title(f'Metrics (Threshold = {threshold_value})', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')

    for i, v in enumerate(values):
        plt.text(i, v + 0.03, f'{v:.3f}', ha='center', fontsize=11, fontweight='bold')

    plt.axhline(y=0.9, color='green', linestyle='--', alpha=0.3)
    plt.axhline(y=0.8, color='orange', linestyle='--', alpha=0.3)
    plt.grid(axis='y', alpha=0.3)

    # Summary
    ax3 = plt.subplot(1, 3, 3)
    ax3.axis('off')

    grade = 'A' if accuracy >= 0.92 else 'B+' if accuracy >= 0.88 else 'B' if accuracy >= 0.85 else 'C'

    summary = f"""
    THRESHOLD EVALUATION
    {'=' * 30}

    Threshold:  {threshold_value}

    Accuracy:   {accuracy:.3f}
    Precision:  {precision:.3f}
    Recall:     {recall:.3f}
    F1-Score:   {f1:.3f}

    TP: {tp}  |  TN: {tn}
    FP: {fp}  |  FN: {fn}

    Grade: {grade}

    {'=' * 30}
    """

    ax3.text(0.1, 0.5, summary, fontsize=11, family='monospace',
             verticalalignment='center')

    plt.tight_layout()
    plt.savefig(f'threshold_{threshold_value}_test.png', dpi=300, bbox_inches='tight')
    print(f"\n✓ Saved: threshold_{threshold_value}_test.png")
    plt.show()

    return {
        'threshold': threshold_value,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }


def compare_thresholds(threshold_list):
    """Compare multiple thresholds"""

    print("\n" + "=" * 80)
    print("           COMPARING MULTIPLE THRESHOLDS")
    print("=" * 80)

    results = []

    for thresh in threshold_list:
        y_pred = (y_scores > thresh).astype(int)
        results.append({
            'Threshold': thresh,
            'Accuracy': accuracy_score(y_test, y_pred),
            'Precision': precision_score(y_test, y_pred),
            'Recall': recall_score(y_test, y_pred),
            'F1-Score': f1_score(y_test, y_pred)
        })

    import pandas as pd
    df = pd.DataFrame(results)

    print("\n📊 COMPARISON TABLE:\n")
    print(df.to_string(index=False))

    print("\n🏆 BEST BY METRIC:")
    print(f"   Accuracy:  {df.loc[df['Accuracy'].idxmax(), 'Threshold']:.2f} ({df['Accuracy'].max():.4f})")
    print(f"   Precision: {df.loc[df['Precision'].idxmax(), 'Threshold']:.2f} ({df['Precision'].max():.4f})")
    print(f"   Recall:    {df.loc[df['Recall'].idxmax(), 'Threshold']:.2f} ({df['Recall'].max():.4f})")
    print(f"   F1-Score:  {df.loc[df['F1-Score'].idxmax(), 'Threshold']:.2f} ({df['F1-Score'].max():.4f})")

    # Plot comparison
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    ax1 = axes[0]
    ax1.plot(df['Threshold'], df['Accuracy'], 'o-', label='Accuracy', linewidth=2, markersize=6)
    ax1.plot(df['Threshold'], df['Precision'], 's-', label='Precision', linewidth=2, markersize=6)
    ax1.plot(df['Threshold'], df['Recall'], '^-', label='Recall', linewidth=2, markersize=6)
    ax1.plot(df['Threshold'], df['F1-Score'], 'd-', label='F1-Score', linewidth=2, markersize=6)
    ax1.set_xlabel('Threshold', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Score', fontsize=12, fontweight='bold')
    ax1.set_title('All Metrics vs Threshold', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    ax2 = axes[1]
    best_idx = df['F1-Score'].idxmax()
    colors = ['green' if i == best_idx else 'steelblue' for i in range(len(df))]
    ax2.bar(df['Threshold'].astype(str), df['F1-Score'], color=colors,
            edgecolor='black', linewidth=1.5)
    ax2.set_xlabel('Threshold', fontsize=12, fontweight='bold')
    ax2.set_ylabel('F1-Score', fontsize=12, fontweight='bold')
    ax2.set_title('F1-Score Comparison', fontsize=14, fontweight='bold')
    ax2.set_ylim([df['F1-Score'].min() - 0.05, 1.0])

    for i, v in enumerate(df['F1-Score']):
        ax2.text(i, v + 0.01, f'{v:.3f}', ha='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig('threshold_comparison.png', dpi=300, bbox_inches='tight')
    print("\n✓ Saved: threshold_comparison.png")
    plt.show()


# ===========================
# INTERACTIVE MENU
# ===========================

def main():
    print("\n" + "=" * 80)
    print("Choose an option:")
    print("=" * 80)
    print("\n  1. Test a single threshold")
    print("  2. Compare multiple thresholds")
    print("  3. Find optimal threshold")
    print("  4. Exit")

    while True:
        try:
            choice = input("\nEnter choice (1-4): ").strip()

            if choice == '1':
                thresh = float(input("Enter threshold value (e.g., 0.60): "))
                test_threshold(thresh)

            elif choice == '2':
                print("\nEnter thresholds separated by comma (e.g., 0.5,0.6,0.7,0.8)")
                thresh_input = input("Thresholds: ")
                thresholds = [float(x.strip()) for x in thresh_input.split(',')]
                compare_thresholds(thresholds)

            elif choice == '3':
                print("\nFinding optimal threshold...")
                thresholds = np.arange(0.1, 2.0, 0.05)
                compare_thresholds(thresholds)

            elif choice == '4':
                print("\n👋 Exiting...")
                break

            else:
                print("❌ Invalid choice")

        except KeyboardInterrupt:
            print("\n\n👋 Exiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
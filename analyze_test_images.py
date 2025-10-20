"""
Script to apply predict_image() to all test images and analyze probability distributions.

This script processes all images in test_data/{seed_number} directories and computes
the probability distribution across all output classes using the model's predictions.
It also calculates accuracy based on ground truth labels.
"""

import sys
import os
from pathlib import Path
from PIL import Image
import numpy as np
from collections import defaultdict
import csv

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import params
from backend.model import predict_image

# Default container dimensions (these don't affect probability calculations)
CONTAINER_WIDTH = 512
CONTAINER_HEIGHT = 512


def load_ground_truth_labels(csv_path="test_data/test_labels_445.csv"):
    """
    Load ground truth labels from CSV file.

    Args:
        csv_path: Path to the CSV file containing ground truth labels

    Returns:
        dict: Dictionary mapping image filename -> class index
    """
    ground_truth = {}
    csv_file = Path(csv_path)

    if not csv_file.exists():
        print(f"Warning: Ground truth file not found: {csv_path}")
        return ground_truth

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Extract just the filename from the path
            image_path = row['image_path']
            image_filename = Path(image_path).name
            label = int(row['label'])
            ground_truth[image_filename] = label

    print(f"Loaded {len(ground_truth)} ground truth labels from {csv_path}")
    return ground_truth


def get_all_test_images(test_data_dir="test_data"):
    """
    Find all image files in test_data/{seed_number} directories.

    Returns:
        dict: Dictionary mapping seed_number -> list of image paths
    """
    test_data_path = Path(test_data_dir)
    images_by_seed = {}

    if not test_data_path.exists():
        print(f"Error: {test_data_dir} directory not found")
        return images_by_seed

    # Find all seed directories (numeric subdirectories)
    for seed_dir in test_data_path.iterdir():
        if seed_dir.is_dir() and seed_dir.name.isdigit():
            seed_number = seed_dir.name
            images = []

            # Look for image subdirectories (HAM10000_images_part_1, HAM10000_images_part_2, etc.)
            for subdir in seed_dir.iterdir():
                if subdir.is_dir():
                    # Find all .jpg images
                    for img_file in subdir.glob("*.jpg"):
                        images.append(img_file)

            if images:
                images_by_seed[seed_number] = sorted(images)
                print(f"Found {len(images)} images in seed {seed_number}")

    return images_by_seed


def analyze_probability_distribution(results):
    """
    Analyze probability distribution across all predictions.

    Args:
        results: List of prediction results from predict_image()

    Returns:
        dict: Statistics about the probability distribution
    """
    # Collect probabilities for each class
    class_probabilities = defaultdict(list)

    for result in results:
        for hypothesis in result['hypotheses']:
            class_name = hypothesis['hypothesis_name']
            probability = hypothesis['probability']
            class_probabilities[class_name].append(probability)

    # Compute statistics
    stats = {}
    for class_name, probs in class_probabilities.items():
        stats[class_name] = {
            'mean': float(np.mean(probs)),
            'std': float(np.std(probs)),
            'min': float(np.min(probs)),
            'max': float(np.max(probs)),
            'median': float(np.median(probs)),
            'count': len(probs)
        }

    return stats


def calculate_accuracy(results, ground_truth):
    """
    Calculate accuracy by comparing predictions with ground truth labels.

    Args:
        results: List of prediction results from predict_image()
        ground_truth: Dictionary mapping image filename -> class index

    Returns:
        dict: Accuracy statistics
    """
    correct = 0
    total = 0
    predictions_by_class = defaultdict(lambda: {'correct': 0, 'total': 0})

    for result in results:
        image_name = result['image_name']

        if image_name not in ground_truth:
            print(f"Warning: No ground truth label for {image_name}")
            continue

        # Get predicted class name from recommendation field (best_class_name from model.py)
        predicted_class_name = result['recommendation']

        # Get ground truth class index
        true_class_index = ground_truth[image_name]
        true_class_name = params.LABEL_FULLNAMES[true_class_index]

        # Check if prediction matches ground truth
        is_correct = (predicted_class_name == true_class_name)

        if is_correct:
            correct += 1
            predictions_by_class[true_class_name]['correct'] += 1

        total += 1
        predictions_by_class[true_class_name]['total'] += 1

    overall_accuracy = (correct / total * 100) if total > 0 else 0

    # Calculate per-class accuracy
    per_class_accuracy = {}
    for class_name, stats in predictions_by_class.items():
        acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        per_class_accuracy[class_name] = {
            'accuracy': acc,
            'correct': stats['correct'],
            'total': stats['total']
        }

    return {
        'overall_accuracy': overall_accuracy,
        'correct': correct,
        'total': total,
        'per_class_accuracy': per_class_accuracy
    }


def process_images(images, seed_number, ground_truth=None):
    """
    Process all images and collect predictions.

    Args:
        images: List of image paths
        seed_number: Seed number for the test data
        ground_truth: Optional dictionary of ground truth labels

    Returns:
        tuple: (results, probability_distribution, accuracy_stats)
    """
    results = []
    print(f"\nProcessing {len(images)} images for seed {seed_number}...")

    for idx, img_path in enumerate(images):
        try:
            # Load image
            image = Image.open(img_path).convert('RGB')

            # Get prediction
            result = predict_image(image, CONTAINER_WIDTH, CONTAINER_HEIGHT)

            # Add metadata
            result['image_path'] = str(img_path)
            result['image_name'] = img_path.name
            results.append(result)

            if (idx + 1) % 10 == 0:
                print(f"  Processed {idx + 1}/{len(images)} images...")

        except Exception as e:
            print(f"Error processing {img_path}: {e}")
            continue

    print(f"Successfully processed {len(results)} images")

    # Analyze probability distribution
    prob_distribution = analyze_probability_distribution(results)

    # Calculate accuracy if ground truth is provided
    accuracy_stats = None
    if ground_truth:
        accuracy_stats = calculate_accuracy(results, ground_truth)

    return results, prob_distribution, accuracy_stats


def save_results(results, prob_distribution, seed_number, output_dir="test_data"):
    """
    Save results to a txt file in test_data/ directory.
    Each line contains: image_name followed by probability distribution of all hypotheses.

    Args:
        results: List of prediction results
        prob_distribution: Probability distribution statistics
        seed_number: Seed number
        output_dir: Output directory for results
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Save predictions to txt file
    results_file = output_path / f"predictions_seed_{seed_number}.txt"
    with open(results_file, 'w') as f:
        for result in results:
            image_name = result['image_name']
            # Create probability distribution string for all hypotheses
            prob_str = ' '.join([
                f"{hyp['hypothesis_name']}:{hyp['probability']:.6f}"
                for hyp in result['hypotheses']
            ])
            f.write(f"{image_name} {prob_str}\n")

    print(f"\nPredictions saved to: {results_file}")


def print_accuracy_summary(accuracy_stats):
    """Print accuracy summary."""
    if not accuracy_stats:
        return

    print("\n" + "="*80)
    print("ACCURACY SUMMARY")
    print("="*80)
    print(f"\nOverall Accuracy: {accuracy_stats['overall_accuracy']:.2f}%")
    print(f"Correct: {accuracy_stats['correct']}/{accuracy_stats['total']}")

    print("\nPer-Class Accuracy:")
    for class_name in sorted(accuracy_stats['per_class_accuracy'].keys()):
        stats = accuracy_stats['per_class_accuracy'][class_name]
        print(f"  {class_name}:")
        print(f"    Accuracy: {stats['accuracy']:.2f}%")
        print(f"    Correct:  {stats['correct']}/{stats['total']}")


def print_summary(prob_distribution):
    """Print a summary of the probability distribution."""
    print("\n" + "="*80)
    print("PROBABILITY DISTRIBUTION SUMMARY")
    print("="*80)

    for class_name in sorted(prob_distribution.keys()):
        stats = prob_distribution[class_name]
        print(f"\n{class_name}:")
        print(f"  Mean:   {stats['mean']:.4f}")
        print(f"  Std:    {stats['std']:.4f}")
        print(f"  Min:    {stats['min']:.4f}")
        print(f"  Max:    {stats['max']:.4f}")
        print(f"  Median: {stats['median']:.4f}")


def main():
    """Main function to process all test images."""
    print("Starting test image analysis...")
    print(f"Using model: {params.MODEL}")
    print(f"Algorithm: {params.ALGO}")
    print(f"Number of concepts: {params.NO_CONCEPTS}")

    # Load ground truth labels
    ground_truth = load_ground_truth_labels()

    # Get all test images organized by seed
    images_by_seed = get_all_test_images()

    if not images_by_seed:
        print("No test images found!")
        return

    # Process each seed directory
    for seed_number, images in images_by_seed.items():
        print(f"\n{'='*80}")
        print(f"Processing seed: {seed_number}")
        print(f"{'='*80}")

        # Process images
        results, prob_distribution, accuracy_stats = process_images(images, seed_number, ground_truth)

        # Save results
        save_results(results, prob_distribution, seed_number)

        # Print accuracy summary first (most important)
        print_accuracy_summary(accuracy_stats)

        # Print probability distribution summary
        print_summary(prob_distribution)

    print(f"\n{'='*80}")
    print("Analysis complete!")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()

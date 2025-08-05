import random

def simulate_jaccard_scenario(num_simulations=100000):
    """
    Simulates the scenario where 10 random elements are selected from
    two sets, each with 100 elements and 10 common elements,
    to estimate the expected intersection size.

    Args:
        num_simulations (int): The number of times to run the simulation.

    Returns:
        float: The average intersection size across all simulations.
    """

    total_intersection_size = 0

    # Define the universe of elements. We can just use integers.
    # Let's say elements 1 to 10 are the common ones.
    # Elements 11 to 100 are unique to set 1 (S1_unique).
    # Elements 101 to 190 are unique to set 2 (S2_unique).

    common_elements = set(range(1, 11)) # 10 common elements
    s1_unique = set(range(11, 101))    # 90 unique to S1
    s2_unique = set(range(101, 191))   # 90 unique to S2

    # Original sets
    original_set_1 = common_elements.union(s1_unique)
    original_set_2 = common_elements.union(s2_unique)

    # Sanity checks
    # print(f"Size of original_set_1: {len(original_set_1)}") # Should be 100
    # print(f"Size of original_set_2: {len(original_set_2)}") # Should be 100
    # print(f"Size of common_elements: {len(original_set_1.intersection(original_set_2))}") # Should be 10


    for _ in range(num_simulations):
        # Select 10 random elements from original_set_1
        # random.sample is used for sampling without replacement
        selected_from_s1 = set(random.sample(list(original_set_1), 10))

        # Select 10 random elements from original_set_2
        selected_from_s2 = set(random.sample(list(original_set_2), 10))

        # Calculate the intersection of the two selected sets
        current_intersection = selected_from_s1.intersection(selected_from_s2)

        # Add the size of this intersection to the total
        total_intersection_size += len(current_intersection)

    # Calculate the average intersection size
    average_intersection_size = total_intersection_size / num_simulations
    return average_intersection_size

if __name__ == "__main__":
    # Run the simulation with a large number of trials
    # A larger number of simulations will yield a more accurate result
    # but will take longer to run.
    num_trials = 10000 # Increased for better convergence

    print(f"Running simulation with {num_trials} trials...")
    average_intersection = simulate_jaccard_scenario(num_trials)
    print(f"Expected intersection size (calculated): 0.1")
    print(f"Simulated average intersection size: {average_intersection}")

    # You can also run a test for the previous scenario just to show it
    def simulate_previous_scenario(num_simulations=100000):
        total_intersection_size = 0
        common_elements = set(range(1, 11))
        s1_unique = set(range(11, 101))
        s2_unique = set(range(101, 191))
        original_set_2 = common_elements.union(s2_unique)

        for _ in range(num_simulations):
            selected_from_s2 = set(random.sample(list(original_set_2), 10))
            current_intersection = common_elements.intersection(selected_from_s2)
            total_intersection_size += len(current_intersection)
        return total_intersection_size / num_simulations

    print("\n--- Testing Previous Scenario (Expected: 1.0) ---")
    avg_prev = simulate_previous_scenario(num_trials)
    print(f"Simulated average for previous scenario: {avg_prev}")
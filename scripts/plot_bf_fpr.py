
import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42

import numpy as np
import matplotlib.pyplot as plt

# Generate a range of values for bits per element (m/n)
bits_per_element = np.arange(1, 26, 0.1)

# Calculate the false positive rate (FPR) for each value
# The formula for the minimum FPR is (0.5)^(bits_per_element * ln(2))
# This is derived by substituting the optimal number of hash functions, k = (m/n) * ln(2),
# into the approximate FPR formula, (1 - e^(-kn/m))^k
fpr = (0.5)**(bits_per_element * np.log(2))

#(1 - e^(-ln(2)))^k
# (1 - e^(-ln(2)))^ (m/n) * ln(2)
# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(bits_per_element, fpr)

# Set title and labels
plt.title('Bloom Filter False Positive Rate vs bits per element', fontsize=16)
plt.xlabel('Bits per element ($m_{ratio}$)', fontsize=12)
plt.ylabel('False Positive Rate', fontsize=12)

# Use a logarithmic scale for the y-axis to better visualize the exponential decrease
plt.yscale('log')

# Add grid lines for better readability
plt.grid(True, which="both", ls="--")

# Save the plot to a file
plt.savefig('bf_fpr_decay.pdf', dpi=600)
print("Graph saved as bf_fpr_decay.pdf")
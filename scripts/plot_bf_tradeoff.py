import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42

import numpy as np
import matplotlib.pyplot as plt

# Fixed parameters
n = 10**6  # Number of elements in set A
# Use a more readable set of sizes to avoid clutter
b_minus_a_sizes = np.logspace(np.log10(5*10**4), np.log10(10**6), num=5)
ELEMENT_SIZE_BITS = 64

# Range for total bits used (m)
m_ratio_values = np.arange(0, 25, 0.1)

plt.figure(figsize=(10, 6))

first_run = True
for b_minus_a_size in b_minus_a_sizes:    
    # Calculate the false positive rate (FPR)
    fpr = (0.5)**(m_ratio_values * np.log(2))
    
    # Calculate the number of false positives
    num_false_positives = b_minus_a_size * fpr
    
    # Calculate the total transmitted bits
    transmitted = m_ratio_values*n + num_false_positives * ELEMENT_SIZE_BITS
    
    # Plot the full line for total transmitted bits
    plt.plot(m_ratio_values, transmitted, label=f'Total Transmitted for |B minus A| = {b_minus_a_size:,.0f}')
    
    # Find the minimum point
    min_index = np.argmin(transmitted)
    min_m_value = m_ratio_values[min_index]
    min_transmitted = transmitted[min_index]

    plt.plot(min_m_value, min_transmitted, 'o', color='black', markersize=6)

# Set plot title and labels
plt.title('Total Transmitted Bits vs bits per element', fontsize=16)
plt.xlabel('Bits per element ($m_{ratio}$)', fontsize=12)
plt.ylabel('Total Transmitted Bits', fontsize=12)

# Add a legend and grid
plt.legend(title='Size of B minus A')
plt.grid(True, which="both", ls="--")

# Save the plot
plt.savefig('bf_transmission_costs.pdf', dpi=600)   
print("Graph saved as bf_transmission_costs.pdf")
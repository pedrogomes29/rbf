import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# To run this script, you must have the matplotlib library installed.
# You can install it using pip:
# pip install matplotlib
# You also need numpy:
# pip install numpy

class BloomFilter:
    """
    A simple, fixed-size Bloom filter implementation with predefined hashes for educational purposes.
    """
    def __init__(self, size, num_hashes, predefined_hashes):
        """
        Initializes the Bloom filter.

        Args:
            size (int): The number of bits in the filter.
            num_hashes (int): The number of hash functions to use.
            predefined_hashes (dict): A dictionary mapping elements to a list of hash positions.
        """
        self.size = size
        self.num_hashes = num_hashes
        self.bit_array = [0] * size
        self.predefined_hashes = predefined_hashes

    def _get_hash_positions(self, element):
        """
        Retrieves the hash positions for a given element from a predefined mapping.

        Args:
            element: The element to get positions for.

        Returns:
            list: A list of integer indices where the bits should be set.
        """
        return self.predefined_hashes.get(element, [])

    def add(self, element):
        """
        Adds an element to the Bloom filter.
        """
        positions = self._get_hash_positions(element)
        for pos in positions:
            self.bit_array[pos] = 1

    def check(self, element):
        """
        Checks if an element is likely in the Bloom filter.
        """
        positions = self._get_hash_positions(element)
        if not positions:
            return False # Element not in our predefined mappings
        
        for pos in positions:
            if self.bit_array[pos] == 0:
                return False
        return True

def draw_insert_image(bloom_filter, insert_elements, filename="bloom_filter_insert.pdf"):
    """
    Draws a visual representation of the Bloom filter during insertion.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_aspect('equal')
    ax.set_facecolor('white')
    ax.set_title("Inserting", y=-0.1, fontsize=20, fontweight='bold')
    
    # Hide the axes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.get_xaxis().set_ticks([])
    ax.get_yaxis().set_ticks([])

    cell_size = 1.0
    bit_array_y = 0.0

    # Draw the main bit array
    for i in range(bloom_filter.size):
        x = i * cell_size
        y = bit_array_y
        
        fill_color = 'lightgray' if bloom_filter.bit_array[i] == 0 else 'gray'
        
        rect = patches.Rectangle((x, y), cell_size, cell_size,
                                 linewidth=2, edgecolor='black', facecolor=fill_color)
        ax.add_patch(rect)
        
        ax.text(x + cell_size / 2, y + cell_size / 2, str(bloom_filter.bit_array[i]),
                ha='center', va='center', fontsize=18)

    # Draw hash function arrows and element labels
    arrow_color = 'black'
    
    label_y = bit_array_y + 2.5
    
    # Position the labels closer to the center
    total_elements_width = sum([len(e) * 0.5 for e in insert_elements])
    spacing = 4.0
    total_width = total_elements_width + (len(insert_elements) - 1) * spacing
    
    start_x_base = (bloom_filter.size - total_width) / 2
    
    # Draw elements and their arrows
    for i, element in enumerate(insert_elements):
        element_x = start_x_base + i * (len(element) * 0.5 + spacing)
        
        # Draw the element label
        ax.text(element_x, label_y, element, ha='center', va='center', fontsize=24)

        # Get hash positions and draw straight arrows
        positions = bloom_filter._get_hash_positions(element)
        
        for pos_index, pos in enumerate(positions):
            x_target = pos + cell_size / 2
            
            # Start and end points of the arrow
            start_point = (element_x, label_y - 0.5)
            end_point = (x_target, bit_array_y + cell_size)
            
            # Use a straight arrow with a bigger line width
            ax.annotate("", xy=end_point, xytext=start_point,
                        arrowprops=dict(arrowstyle="->", lw=4, color=arrow_color))

    # Set axes limits and save
    ax.set_xlim(-1, bloom_filter.size + 1)
    ax.set_ylim(bit_array_y - 1, label_y + 1)
    fig.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0)
    print(f"Image saved as '{filename}'")

    plt.close(fig)

def draw_lookup_image(bloom_filter, insert_elements, lookup_elements, filename="bloom_filter_lookup.pdf"):
    """
    Draws a visual representation of the Bloom filter during lookups.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_aspect('equal')
    ax.set_facecolor('white')
    ax.set_title("Lookup", y=-0.1, fontsize=20, fontweight='bold')
    
    # Hide the axes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.get_xaxis().set_ticks([])
    ax.get_yaxis().set_ticks([])

    cell_size = 1.0
    bit_array_y = 0.0

    # Draw the main bit array
    for i in range(bloom_filter.size):
        x = i * cell_size
        y = bit_array_y
        
        fill_color = 'lightgray' if bloom_filter.bit_array[i] == 0 else 'gray'
        
        rect = patches.Rectangle((x, y), cell_size, cell_size,
                                 linewidth=2, edgecolor='black', facecolor=fill_color)
        ax.add_patch(rect)
        
        ax.text(x + cell_size / 2, y + cell_size / 2, str(bloom_filter.bit_array[i]),
                ha='center', va='center', fontsize=18)

    # Draw elements and their arrows for lookup
    lookup_spacing = 3.0
    label_y = bit_array_y + 2.5
    
    # Position the labels closer to the center
    total_elements_width = sum([len(e) * 0.5 for e in lookup_elements])
    total_width = total_elements_width + (len(lookup_elements) - 1) * lookup_spacing
    start_x_base = (bloom_filter.size - total_width) / 2
    
    for i, element in enumerate(lookup_elements):
        element_x = start_x_base + i * (len(element) * 0.5 + lookup_spacing)
        
        # Check if the element is likely in the filter
        result = bloom_filter.check(element)
        
        # Determine the result type and color
        if element in insert_elements:
            result_text = "True Positive"
            result_color = 'green'
        elif result:
            result_text = "False Positive"
            result_color = 'red'
        else:
            result_text = "True Negative"
            result_color = 'black'

        # Draw the result text above the element label
        ax.text(element_x, label_y + 0.5, f"({result_text})", ha='center', va='center', fontsize=16, color=result_color)
        # Draw the element label
        ax.text(element_x, label_y, element, ha='center', va='center', fontsize=24)


        # Draw arrows for the lookup
        positions = bloom_filter._get_hash_positions(element)
        for pos_index, pos in enumerate(positions):
            x_target = pos + cell_size / 2
            
            # Start and end points of the arrow
            start_point = (element_x, label_y - 0.5)
            end_point = (x_target, bit_array_y + cell_size)
            
            # Use a straight arrow with a bigger line width
            ax.annotate("", xy=end_point, xytext=start_point,
                        arrowprops=dict(arrowstyle="->", lw=4, color='black'))

    # Set axes limits and save
    ax.set_xlim(-1, bloom_filter.size + 1)
    ax.set_ylim(bit_array_y - 1, label_y + 2)
    
    fig.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0)
    print(f"Image saved as '{filename}'")

    plt.close(fig)


# --- Main execution block ---
if __name__ == "__main__":
    # Define the custom hash mappings
    predefined_hashes = {
        "x1": [1, 4, 8],  # True positive
        "x2": [4, 6, 10], # True positive
        "y1": [2, 5, 7],  # True negative
        "y2": [4, 6, 8],  # False positive
    }

    # Create a Bloom filter with a size of 12 bits and 3 hash functions
    my_bloom_filter = BloomFilter(size=12, num_hashes=3, predefined_hashes=predefined_hashes)

    # Elements to insert
    insert_elements = ["x1", "x2"]

    # Elements to lookup
    lookup_elements = ["x1", "y1", "y2"]

    # Add the elements to the filter
    for element in insert_elements:
        my_bloom_filter.add(element)

    # Draw the final state of the Bloom filter as a PNG image
    draw_insert_image(my_bloom_filter, insert_elements)
    draw_lookup_image(my_bloom_filter, insert_elements, lookup_elements)

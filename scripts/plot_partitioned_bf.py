import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# To run this script, you must have the matplotlib library installed.
# You can install it using pip:
# pip install matplotlib
# You also need numpy:
# pip install numpy

class PartitionedBloomFilter:
    """
    A partitioned Bloom filter for educational purposes.
    """
    def __init__(self, num_partitions, partition_size, predefined_hashes):
        """
        Initializes the partitioned Bloom filter.

        Args:
            num_partitions (int): The number of partitions (rows).
            partition_size (int): The size of each partition (columns).
            predefined_hashes (dict): A dictionary mapping elements to a list of
                                      (partition_index, column_index) tuples.
        """
        self.num_partitions = num_partitions
        self.partition_size = partition_size
        self.bit_array = [[0] * partition_size for _ in range(num_partitions)]
        self.predefined_hashes = predefined_hashes

    def _get_hash_positions(self, element):
        """
        Retrieves the hash positions for a given element from a predefined mapping.

        Args:
            element: The element to get positions for.

        Returns:
            list: A list of (partition_index, column_index) tuples.
        """
        return self.predefined_hashes.get(element, [])

    def add(self, element):
        """
        Adds an element to the partitioned Bloom filter.
        """
        positions = self._get_hash_positions(element)
        for part_index, col_index in positions:
            if 0 <= part_index < self.num_partitions and 0 <= col_index < self.partition_size:
                self.bit_array[part_index][col_index] = 1

def draw_bloom_filter_as_image(bloom_filter, elements_to_draw, filename="partitioned_bloom_filter.pdf"):
    """
    Draws a visual representation of the Bloom filter and saves it as a PDF file.
    """
    # Create the figure and axes
    fig, ax = plt.subplots(figsize=(20, 8))
    ax.set_aspect('equal')
    ax.set_facecolor('white')

    # Hide the axes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.get_xaxis().set_ticks([])
    ax.get_yaxis().set_ticks([])

    cell_size = 1.0
    row_spacing = 1.0
    grid_y_start = 0.0

    # Draw the main partitioned bit array
    for r in range(bloom_filter.num_partitions):
        for c in range(bloom_filter.partition_size):
            x = c * cell_size
            y = grid_y_start - r * row_spacing
            
            fill_color = 'lightgray' if bloom_filter.bit_array[r][c] == 0 else 'gray'
            
            rect = patches.Rectangle((x, y), cell_size, cell_size,
                                     linewidth=2, edgecolor='black', facecolor=fill_color)
            ax.add_patch(rect)
            
            ax.text(x + cell_size / 2, y + cell_size / 2, str(bloom_filter.bit_array[r][c]),
                    ha='center', va='center', fontsize=18)
        
        # Add the index to the left of each row
        ax.text(-1.5, grid_y_start - r * row_spacing + cell_size / 2, str(r), ha='center', va='center', fontsize=32)
    
    # Add a "Partition" header on top of the indices
    ax.text(-1.5, grid_y_start + 0.35 + row_spacing, "Partition", ha='center', va='center', fontsize=32)

    # Draw element labels and hash function arrows
    arrow_color = 'black'
    
    label_y = grid_y_start + 2.5
    
    # Position the labels closer to the center
    total_elements_width = sum([len(e) * 0.5 for e in elements_to_draw])
    spacing = 4.0 # Spacing between elements
    total_width = total_elements_width + (len(elements_to_draw) - 1) * spacing
    
    start_x_base = (bloom_filter.partition_size - total_width) / 2
    
    # Draw elements and their arrows
    for i, element in enumerate(elements_to_draw):
        element_x = start_x_base + i * (len(element) * 0.5 + spacing)
        
        # Draw the element label
        ax.text(element_x, label_y, element, ha='center', va='center', fontsize=32)

        # Get hash positions and draw straight arrows
        positions = bloom_filter._get_hash_positions(element)
        
        for pos_index, (part_index, col_index) in enumerate(positions):
            x_target = col_index + cell_size / 2
            y_target = grid_y_start - part_index * row_spacing + cell_size
            
            # Start and end points of the arrow
            start_point = (element_x, label_y - 0.2)
            end_point = (x_target, y_target)
            
            # Use a straight arrow with a bigger line width
            ax.annotate("", xy=end_point, xytext=start_point,
                        arrowprops=dict(arrowstyle="->",
                                        lw=4,
                                        color=arrow_color))

    # Set axes limits and save
    ax.set_xlim(-2.5, bloom_filter.partition_size + 1)
    ax.set_ylim(grid_y_start - bloom_filter.num_partitions * row_spacing - 1, label_y + 1)
    fig.tight_layout()
    plt.savefig(filename, dpi=300)
    print(f"Image saved as '{filename}'")

    plt.close(fig)

# --- Main execution block ---
if __name__ == "__main__":
    # Define the custom hash mappings for a partitioned filter
    predefined_hashes = {
        # (partition_index, column_index)
        "x1": [(0, 0), (1, 2), (2, 2)],
        "x2": [(0, 1), (1, 2), (2, 3)]
    }

    # Create a Partitioned Bloom filter with 3 partitions and a size of 4 bits each
    my_bloom_filter = PartitionedBloomFilter(num_partitions=3, partition_size=4, predefined_hashes=predefined_hashes)

    # Elements to insert and visualize
    element_x1 = "x1"
    element_x2 = "x2"
    elements_to_draw = [element_x1, element_x2]

    # Add the elements to the filter
    my_bloom_filter.add(element_x1)
    my_bloom_filter.add(element_x2)

    # Draw the final state of the Bloom filter as a PNG image
    draw_bloom_filter_as_image(my_bloom_filter, elements_to_draw)

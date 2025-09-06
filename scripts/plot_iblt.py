import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# A simple, consistent way to turn a string into a number for XORing
def item_to_int(item):
    """Converts a string item to an integer for XORing."""
    return sum(ord(c) for c in item)

# A simple, different hash function for the hashSum
def item_to_hash_int(item):
    """A different hash function for the hashSum."""
    return sum(ord(c) * 2 for c in item)

class IBLT:
    """
    A simplified IBLT implementation for visualization.
    Correctly performs XOR sums for idSum and hashSum.
    """
    def __init__(self, num_cells, predefined_mappings):
        self.num_cells = num_cells
        self.cells = []
        for _ in range(num_cells):
            self.cells.append({
                'idSum': 0,      # XOR sum of item identifiers
                'hashSum': 0,    # XOR sum of item hashes
                'count': 0       # Number of items mapped to this cell
            })
        self.predefined_mappings = predefined_mappings
        
    def _get_cell_indices(self, item):
        return self.predefined_mappings.get(item, [])

    def add(self, item):
        """
        Adds an item to the IBLT, performing XOR sums correctly.
        """
        indices = self._get_cell_indices(item)
        for idx in indices:
            if 0 <= idx < self.num_cells:
                self.cells[idx]['idSum'] ^= item_to_int(item)
                self.cells[idx]['hashSum'] ^= item_to_hash_int(item)
                self.cells[idx]['count'] += 1

    def remove(self, item):
        """
        Removes an item from the IBLT.
        """
        indices = self._get_cell_indices(item)
        for idx in indices:
            if 0 <= idx < self.num_cells:
                self.cells[idx]['idSum'] ^= item_to_int(item)
                self.cells[idx]['hashSum'] ^= item_to_hash_int(item)
                self.cells[idx]['count'] -= 1

def draw_iblt_image(iblt_instance, items_added, filename="iblt_visualization.pdf"):
    """
    Draws a visual representation of the IBLT.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_aspect('equal')
    ax.set_facecolor('white')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.get_xaxis().set_ticks([])
    ax.get_yaxis().set_ticks([])

    cell_width = 2.0
    cell_height = 1.0
    row_labels = ["idSum", "hashSum", "count"]
    num_data_rows = len(row_labels)

    # Draw the IBLT cells
    for i in range(iblt_instance.num_cells):
        for r_idx, label in enumerate(row_labels):
            x = i * cell_width
            y = (num_data_rows - 1 - r_idx) * cell_height

            rect = patches.Rectangle((x, y), cell_width, cell_height,
                                     linewidth=1, edgecolor='black', facecolor='white')
            ax.add_patch(rect)
            
            cell_data = iblt_instance.cells[i][label]
            if label == "idSum":
                # Check for multiple items XORed into the cell and display the symbols
                items_in_cell = [item for item, indices in iblt_instance.predefined_mappings.items() if i in indices]
                text_content = ' $\\oplus$ '.join(items_in_cell)
                text_fontsize = 9.5
            elif label == "hashSum":
                text_content = ' $\\oplus$ '.join([f"h({item})" for item in items_in_cell])
                text_fontsize = 9.5
            else:
                text_content = str(cell_data)
                text_fontsize = 9

            ax.text(x + cell_width / 2, y + cell_height / 2, text_content,
                    ha='center', va='center', fontsize=text_fontsize)
            
            if r_idx == num_data_rows - 1:
                ax.text(x + cell_width / 2, y - cell_height * 0.7, f"{i}",
                        ha='center', va='center', fontsize=12)

    for r_idx, label in enumerate(row_labels):
        y = (num_data_rows - 1 - r_idx) * cell_height + cell_height / 2
        ax.text(-cell_width * 0.7, y, label, ha='center', va='center', fontsize=12, fontweight='bold')
    
    ax.text(-cell_width * 0.7, -cell_height * 0.7, "cell index", ha='center', va='center', fontsize=12, fontweight='bold')

    arrow_color = 'black'
    item_label_y_start = (num_data_rows) * cell_height + 1.5
    
    total_items_width = sum([len(item) * 0.5 for item in items_added])
    item_spacing = 1.0
    total_width_items_section = total_items_width + (len(items_added) - 1) * item_spacing
    start_x_base_items = (iblt_instance.num_cells * cell_width - total_width_items_section) / 2
    
    item_position_map = {}

    for i, item in enumerate(items_added):
        current_item_x = start_x_base_items + i * (len(item) * 0.5 + item_spacing)
        item_position_map[item] = current_item_x
        
        ax.text(current_item_x, item_label_y_start, item, ha='center', va='center', fontsize=16)

        indices = iblt_instance._get_cell_indices(item)
        
        for idx in indices:
            x_target = idx * cell_width + cell_width / 2
            y_target = (num_data_rows - 1) * cell_height + cell_height
            
            start_point = (current_item_x, item_label_y_start - 0.3)
            end_point = (x_target, y_target)
            
            ax.annotate("", xy=end_point, xytext=start_point,
                        arrowprops=dict(arrowstyle="->", lw=2, color=arrow_color))
            
    highlight_idx = 5
    if highlight_idx < iblt_instance.num_cells:
        for r_idx, label in enumerate(row_labels):
            x = highlight_idx * cell_width
            y = (num_data_rows - 1 - r_idx) * cell_height
            rect = patches.Rectangle((x, y), cell_width, cell_height,
                                     linewidth=3, edgecolor='red', facecolor='none')
            ax.add_patch(rect)

    ax.set_xlim(-cell_width * 1.5, iblt_instance.num_cells * cell_width + cell_width * 0.5)
    ax.set_ylim(-cell_height * 1.5, item_label_y_start + 1.0)
    
    fig.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0)
    print(f"IBLT image saved as '{filename}'")
    plt.close(fig)

if __name__ == "__main__":
    
    iblt_mappings = {
        "x0": [0, 1, 2],
        "x1": [0, 3, 4],
        "x2": [1, 2, 3],
        "x3": [2, 4, 5],
    }

    iblt_items_to_add = ["x0", "x1", "x2", "x3"]

    max_cell_idx = max([idx for sublist in iblt_mappings.values() for idx in sublist])
    iblt_num_cells = max_cell_idx + 1
    
    my_iblt = IBLT(num_cells=iblt_num_cells, predefined_mappings=iblt_mappings)

    for item in iblt_items_to_add:
        my_iblt.add(item)

    draw_iblt_image(my_iblt, iblt_items_to_add, filename="iblt.pdf")

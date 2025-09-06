import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import hashlib

# --- Hash Functions and IBLT Class ---

def hash_indices(item, num_cells, num_hashes=2):
    """
    Generates k hash indices for an item using a proper cryptographic hash function.
    Each hash is seeded to be independent.
    """
    indices = []
    item_str = str(item).encode('utf-8')
    for i in range(num_hashes):
        # Use a salt/seed to create independent hash functions
        salted_item = item_str + str(i).encode('utf-8')
        h = hashlib.sha1(salted_item).hexdigest()
        index = int(h, 16) % num_cells
        indices.append(index)
    return list(set(indices))

def item_to_hash_int(item):
    """A separate hash function for the hashSum using a different seed."""
    item_str = str(item).encode('utf-8')
    salted_item = item_str + b'hashsum_seed'
    h = hashlib.sha1(salted_item).hexdigest()
    return int(h, 16)

class IBLT:
    """A simplified IBLT implementation."""
    def __init__(self, num_cells):
        self.num_cells = num_cells
        self.cells = [{'idSum': 0, 'hashSum': 0, 'count': 0} for _ in range(num_cells)]
        
    def add(self, item):
        indices = hash_indices(item, self.num_cells)
        for idx in indices:
            if 0 <= idx < self.num_cells:
                self.cells[idx]['idSum'] ^= item
                self.cells[idx]['hashSum'] ^= item_to_hash_int(item)
                self.cells[idx]['count'] += 1

    def combine(self, other_iblt):
        combined_iblt = IBLT(self.num_cells)
        for i in range(self.num_cells):
            combined_iblt.cells[i]['idSum'] = self.cells[i]['idSum'] ^ other_iblt.cells[i]['idSum']
            combined_iblt.cells[i]['hashSum'] = self.cells[i]['hashSum'] ^ other_iblt.cells[i]['hashSum']
            combined_iblt.cells[i]['count'] = self.cells[i]['count'] - other_iblt.cells[i]['count']
        return combined_iblt

# --- Drawing Functions ---

def draw_single_iblt(ax, iblt_instance, title, x_offset, y_offset, num_data_rows, num_cells_to_draw, cell_width, cell_height, row_labels, items_to_show_mapping):
    """Helper function to draw a single IBLT with its title and arrows."""
    # Adjusted title position for more space
    ax.text(x_offset + (num_cells_to_draw * cell_width / 2), y_offset + num_data_rows * cell_height + 2.5, title, ha='center', va='center', fontsize=18, fontweight='bold')

    for i in range(num_cells_to_draw):
        for r_idx, label in enumerate(row_labels):
            x = x_offset + i * cell_width
            y = y_offset + (num_data_rows - 1 - r_idx) * cell_height
            rect = patches.Rectangle((x, y), cell_width, cell_height, linewidth=1, edgecolor='black', facecolor='white')
            ax.add_patch(rect)
            
            cell_data = iblt_instance.cells[i][label]
            if label == "idSum":
                text_content = str(cell_data) if cell_data != 0 else "0"
                text_fontsize = 10 if len(text_content) > 6 else 12
            elif label == "hashSum":
                text_content = str(cell_data)
                if len(text_content) > 7:
                    text_content = text_content[:7] + "..."
                text_fontsize = 10 if len(text_content) >= 10 else 12
            else:
                text_content = str(cell_data)
                text_fontsize = 12
            ax.text(x + cell_width / 2, y + cell_height / 2, text_content, ha='center', va='center', fontsize=text_fontsize)
            if r_idx == num_data_rows - 1:
                ax.text(x + cell_width / 2, y - cell_height * 0.7, f"{i}", ha='center', va='center', fontsize=12)

    for r_idx, label in enumerate(row_labels):
        y = y_offset + (num_data_rows - 1 - r_idx) * cell_height + cell_height / 2
        ax.text(x_offset - cell_width * 0.7, y, label, ha='center', va='center', fontsize=12, fontweight='bold')
    
    ax.text(x_offset - cell_width * 0.7, y_offset - cell_height * 0.7, "cell index", ha='center', va='center', fontsize=12, fontweight='bold')

    # Add arrow drawing logic here
    arrow_color = 'black'
    item_label_y_start = y_offset + (num_data_rows) * cell_height + 1.5
    
    total_items_width = sum([len(str(item)) * 0.5 for item in items_to_show_mapping])
    item_spacing = 1.0
    total_width_items_section = total_items_width + (len(items_to_show_mapping) - 1) * item_spacing
    start_x_base_items = (num_cells_to_draw * cell_width - total_width_items_section) / 2
    
    for i, item in enumerate(items_to_show_mapping):
        item_str = str(item)
        current_item_x = start_x_base_items + i * (2.5 + item_spacing)
        
        ax.text(x_offset + current_item_x, item_label_y_start, item_str, ha='center', va='center', fontsize=16)

        indices = hash_indices(item, iblt_instance.num_cells)
        
        for idx in indices:
            if idx < num_cells_to_draw:
                x_target = x_offset + idx * cell_width + cell_width / 2
                y_target = y_offset + (num_data_rows - 1) * cell_height + cell_height
                
                start_point = (x_offset + current_item_x, item_label_y_start - 0.3)
                end_point = (x_target, y_target)
                
                ax.annotate("", xy=end_point, xytext=start_point,
                            arrowprops=dict(arrowstyle="->", lw=2, color=arrow_color))

def draw_reconciliation_image(iblt_a, iblt_b, combined_iblt, set_a_exclusive, set_b_exclusive, filename="iblt_reconciliation.pdf"):
    """
    Draws a visual representation of the IBLT reconciliation process, with IBLTs in rows.
    """
    fig, ax = plt.subplots(figsize=(18, 15))
    ax.set_aspect('equal')
    ax.set_facecolor('white')
    ax.axis('off')

    cell_width = 2.0
    cell_height = 1.0
    row_labels = ["idSum", "hashSum", "count"]
    num_data_rows = len(row_labels)
    
    # Use the actual number of cells for drawing
    num_cells_to_draw = iblt_a.num_cells
    
    # Adjusted space between blocks for clarity
    iblt_block_height = (num_data_rows + 1) * cell_height + 3
    
    y_offset_c = 0
    y_offset_b = y_offset_c + iblt_block_height + 1
    y_offset_a = y_offset_b + iblt_block_height + 1

    # --- Draw IBLT for Set A (Top Row) ---
    draw_single_iblt(ax, iblt_a, "IBLT for Set A", 0, y_offset_a, num_data_rows, num_cells_to_draw, cell_width, cell_height, row_labels, set_a_exclusive)

    # --- Draw IBLT for Set B (Middle Row) ---
    draw_single_iblt(ax, iblt_b, "IBLT for Set B", 0, y_offset_b, num_data_rows, num_cells_to_draw, cell_width, cell_height, row_labels, set_b_exclusive)
    
    # --- Draw the Combined IBLT (Bottom Row) ---
    draw_single_iblt(ax, combined_iblt, "Combined IBLT (Symmetric Difference)", 0, y_offset_c, num_data_rows, num_cells_to_draw, cell_width, cell_height, row_labels, set_b_exclusive + set_a_exclusive)

    ax.set_xlim(-3, num_cells_to_draw * cell_width + 3)
    ax.set_ylim(-1.5, y_offset_a + iblt_block_height - 1)
    
    fig.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close(fig)

if __name__ == "__main__":
    
    # Define the large sets
    set_a = list(range(1, 100002))
    set_b = list(range(3, 100004))

    # The symmetric difference will be a small set: {0, 1, 100001, 100002}
    symmetric_difference = list(set(set_a) ^ set(set_b))
    
    # Correctly identify the exclusive elements for visualization
    set_a_exclusive = [1,2]
    set_b_exclusive = [100002, 100003]
    
    # The number of cells should be proportional to the symmetric difference
    num_cells = int(len(symmetric_difference) * 1.5)
    
    iblt_a = IBLT(num_cells)
    for item in set_a:
        iblt_a.add(item)
    
    iblt_b = IBLT(num_cells)
    for item in set_b:
        iblt_b.add(item)

    combined_iblt = iblt_b.combine(iblt_a)
    
    draw_reconciliation_image(iblt_a, iblt_b, combined_iblt, set_a_exclusive, set_b_exclusive)
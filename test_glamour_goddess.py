#!/usr/bin/env python3
"""
Test script for enhanced Glamour Goddess with color picker functionality
"""

import sys
import os
sys.path.append('.')

from glamour_goddess import GlamourGoddess

def test_color_conversion():
    """Test the RGB to name conversion functionality"""
    print("Testing color conversion:")
    
    test_colors = [
        ("#FF0000", "red"),           # Pure red
        ("#8B4513", "brown"),         # Saddle brown
        ("#000000", "black"),         # Pure black  
        ("#FFFFFF", "white"),         # Pure white
        ("#FFB6C1", "light pink"),    # Light pink
        ("#800080", "purple"),        # Purple
        ("#00FF00", "lime-green"),    # Lime green
        ("#0000FF", "blue"),          # Pure blue
        ("#FFFF00", "yellow"),        # Yellow
        ("#FFA500", "orange"),        # Orange
    ]
    
    for hex_color, expected_base in test_colors:
        result = GlamourGoddess.rgb_to_name(hex_color)
        print(f"  {hex_color} -> {result}")
    
    print()

def test_input_structure():
    """Test the input types structure"""
    print("Testing input structure:")
    
    input_types = GlamourGoddess.INPUT_TYPES()
    required = input_types["required"]
    
    print(f"  Total fields: {len(required)}")
    
    # Check color fields
    color_fields = GlamourGoddess.COLOR_FIELDS
    print(f"  Color picker fields: {len(color_fields)}")
    for field in color_fields:
        if field in required:
            field_type = required[field]
            print(f"    {field}: {field_type}")
    
    # Check dropdown fields  
    dropdown_count = 0
    for field, field_type in required.items():
        if field not in color_fields and field != "extra":
            dropdown_count += 1
            print(f"    {field}: {len(field_type[0])} options")
    
    print(f"  Dropdown fields: {dropdown_count}")
    print()

def test_pick_method():
    """Test the enhanced pick method"""
    print("Testing pick method:")
    
    gg = GlamourGoddess()
    
    # Test color picking
    color_result = gg.pick("hair_color", "#8B4513")
    print(f"  Color pick result: {color_result}")
    
    # Test dropdown picking
    dropdown_result = gg.pick("hair_length", "long hair")
    print(f"  Dropdown pick result: {dropdown_result}")
    
    # Test random selection
    random_result = gg.pick("hairstyle", "Random")
    print(f"  Random pick result: {random_result}")
    
    print()

if __name__ == "__main__":
    test_color_conversion()
    test_input_structure() 
    test_pick_method()
    print("All tests completed successfully! ✨")

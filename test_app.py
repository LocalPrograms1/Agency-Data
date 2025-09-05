#!/usr/bin/env python3
"""
Test script to verify the Dash app functionality
"""

import pandas as pd
import sys
import os

def test_data_loading():
    """Test if the CSV data loads correctly"""
    try:
        df = pd.read_csv('geocoded_results_google.csv')
        print(f"✓ Data loaded successfully: {len(df)} rows, {len(df.columns)} columns")
        
        # Check required columns
        required_cols = ['Latitude', 'Longitude', 'Parent Organization Info Name', 
                        'Program Type', 'Extension Program Authorized Full Time Sworn Personnel']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"✗ Missing required columns: {missing_cols}")
            return False
        else:
            print("✓ All required columns present")
        
        # Check data quality
        clean_df = df.dropna(subset=['Latitude', 'Longitude'])
        print(f"✓ {len(clean_df)} agencies have valid coordinates")
        
        program_types = df['Program Type'].value_counts()
        print("✓ Program type distribution:")
        for ptype, count in program_types.items():
            print(f"  - {ptype}: {count}")
            
        return True
        
    except FileNotFoundError:
        print("✗ geocoded_results_google.csv not found")
        return False
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return False

def test_imports():
    """Test if all required packages are available"""
    try:
        import dash
        print(f"✓ Dash version: {dash.__version__}")
        
        import plotly
        print(f"✓ Plotly version: {plotly.__version__}")
        
        import pandas
        print(f"✓ Pandas version: {pandas.__version__}")
        
        import numpy
        print(f"✓ Numpy version: {numpy.__version__}")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def main():
    print("CALEA Dashboard Test")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("❌ Import test failed")
        sys.exit(1)
    
    print()
    
    # Test data loading
    if not test_data_loading():
        print("❌ Data loading test failed")
        sys.exit(1)
    
    print()
    print("✅ All tests passed! The dashboard should work correctly.")
    print()
    print("To run the dashboard:")
    print("  python app.py")
    print()
    print("Then open your browser to: http://127.0.0.1:8050")

if __name__ == "__main__":
    main()
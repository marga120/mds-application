print("Testing imports...")

try:
    import numpy as np
    print(f"✅ NumPy {np.__version__} imported successfully")
except ImportError as e:
    print(f"❌ NumPy import failed: {e}")

try:
    import pandas as pd
    print(f"✅ Pandas {pd.__version__} imported successfully")
except ImportError as e:
    print(f"❌ Pandas import failed: {e}")

try:
    import flask
    print(f"✅ Flask {flask.__version__} imported successfully")
except ImportError as e:
    print(f"❌ Flask import failed: {e}")

print("All imports completed!")
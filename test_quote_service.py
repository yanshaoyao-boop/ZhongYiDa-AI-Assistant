import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.quote_service import get_quote_data_as_string

try:
    data = get_quote_data_as_string()
    print("Length of returned string:", len(data))
    print(data[:1000])
except Exception as e:
    import traceback
    traceback.print_exc()

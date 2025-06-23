#!/usr/bin/env python3
"""
Test the specific error that occurred with image upload
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.errors import ErrorHandler

def test_specific_error():
    """Test the specific AttributeError that occurred"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 TESTING SPECIFIC ERROR SCENARIO")
        print("=" * 50)
        
        # Simulate the exact error that happened
        print("\n🎯 Simulating the AttributeError that occurred...")
        
        try:
            # This simulates the error that happened: 'NoneType' object has no attribute 'strip'
            none_value = None
            none_value.strip()  # This will cause the AttributeError
            
        except AttributeError as e:
            print(f"✅ Caught the error: {e}")
            
            # Test our error handler
            print("📤 Testing error handler with this specific error...")
            
            try:
                ErrorHandler.log_error(
                    error=e,
                    error_type="server_error", 
                    user_id=None,
                    ip_address="127.0.0.1",
                    url="/admin/dashboard",
                    send_email=True
                )
                print("✅ Error was logged and email notification attempted!")
                print("📧 Check your email and the admin panel for the error report.")
                
            except Exception as handler_error:
                print(f"❌ Error handler failed: {handler_error}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 50)
        print("🏁 Test completed!")

if __name__ == '__main__':
    test_specific_error()

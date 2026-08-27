import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

# Create a cookie jar to handle session
cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login data
login_data = urllib.parse.urlencode({
    'email': 'shivanalla633@gmail.com',
    'password': 'Nshiva@123'
}).encode('utf-8')

# Login
login_url = 'http://127.0.0.1:5000/login'
try:
    login_response = opener.open(login_url, login_data)
    print(f"Login status: {login_response.status}")
    
    # Get dashboard
    dashboard_url = 'http://127.0.0.1:5000/candidate-dashboard'
    dashboard_response = opener.open(dashboard_url)
    html_content = dashboard_response.read().decode('utf-8')
    
    print(f"Dashboard status: {dashboard_response.status}")
    print(f"Final URL after redirect: {dashboard_response.url}")
    
    # Check what page we're actually on
    print(f"\n=== Page Identification ===")
    print(f"'Candidate Dashboard' text present: {'Candidate Dashboard' in html_content}")
    print(f"'Login' text present: {'Login' in html_content}")
    print(f"'HR Dashboard' text present: {'HR Dashboard' in html_content}")
    
    # Check if available slots table is present
    print(f"\n=== Available Slots Table ===")
    print(f"'Available Interview Slots' text present: {'Available Interview Slots' in html_content}")
    print(f"'Available slots at the moment' (empty message): {'No available interview slots at the moment' in html_content}")
    
    # Check for table structure
    print(f"'<table class=\"table table-hover\">' count: {html_content.count('<table class=\"table table-hover\">')}")
    
    # Check for modals
    print("\n=== Modal Analysis ===")
    print(f"Total 'bookingModal' occurrences: {html_content.count('bookingModal')}")
    print(f"bookingModal82 present: {'bookingModal82' in html_content}")
    print(f"bookingModal83 present: {'bookingModal83' in html_content}")
    print(f"bookingModal1 present: {'bookingModal1' in html_content}")
    print(f"bookingModal2 present: {'bookingModal2' in html_content}")
    
    # Check for data-bs-target
    print(f"\nTotal 'data-bs-target' occurrences: {html_content.count('data-bs-target')}")
    
    # Check for modal div structure
    print(f"\nModal div structure:")
    print(f"'<div class=\"modal fade\"' count: {html_content.count('<div class=\"modal fade\"')}")
    
    # Check if modals are inside content block
    print(f"\nStructure check:")
    print(f"'{{% endblock %}}' in HTML: {'{{% endblock %}}' in html_content or '{{%' in html_content}")
    
    # Extract all modal references
    import re
    modal_refs = re.findall(r'data-bs-target=\"(bookingModal\d+)\"', html_content)
    print(f"\nAll {len(modal_refs)} data-bs-target values: {modal_refs}")
    
    modal_divs = re.findall(r'<div class=\"modal fade\" id=\"(bookingModal\d+)\"', html_content)
    print(f"\nAll {len(modal_divs)} modal div IDs: {modal_divs}")
    
    # Extract slot IDs from the table
    slot_rows = re.findall(r'<tr>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>(.*?)</td>.*?<td>.*?data-bs-target=\"(bookingModal\d+)\"', html_content, re.DOTALL)
    print(f"\nSlot rows from table (License, Date, Start, End, ModalTarget):")
    for i, row in enumerate(slot_rows[:10]):  # Show first 10
        print(f"{i+1}. {row}")
    
    # Check for mismatches
    print(f"\n=== Mismatch Analysis ===")
    print(f"Number of data-bs-target attributes: {len(modal_refs)}")
    print(f"Number of modal div elements: {len(modal_divs)}")
    print(f"Match: {set(modal_refs) == set(modal_divs)}")
    
    # Check if all targets have corresponding modals
    missing_modals = set(modal_refs) - set(modal_divs)
    print(f"Modal targets without corresponding modal divs: {missing_modals}")
    
    extra_modals = set(modal_divs) - set(modal_refs)
    print(f"Modal divs without corresponding targets: {extra_modals}")
    
except Exception as e:
    print(f"Error: {e}")

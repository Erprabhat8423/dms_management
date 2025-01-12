from .models import College,CollegeTiming,DriverProfileMapping
from django.db import transaction

def save_driver_profile_mapping(driver_profile, college_name, start_shift, end_shift):
    """
    This function will handle:
      - Checking if the college exists or creating a new one.
      - Checking if the college timing exists or creating a new one.
      - Creating the mapping for the driver with the found/created college and timing.
    """
    try:
        with transaction.atomic():
            # Step 1: Check if the College exists or create it
            college, created = College.objects.get_or_create(college_name=college_name, is_active=True)

            # Step 2: Check if the CollegeTiming exists or create it
            timing, created = CollegeTiming.objects.get_or_create(start_shift=start_shift, end_shift=end_shift)

            # Step 3: Create DriverProfileMapping
            driver_mapping, created = DriverProfileMapping.objects.get_or_create(
                driver=driver_profile,
                college=college,
                timing=timing
            )

            if created:
                # Successfully created mapping
                return {"message": f"Driver profile mapped to {college_name} with shift {start_shift} - {end_shift}."}
            else:
                # Mapping already exists
                return {"message": "Driver profile mapping already exists."}

    except Exception as e:
        # If any error occurs, handle it here
        return {"error": f"An error occurred while saving the driver profile mapping: {str(e)}"}
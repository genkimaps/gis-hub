

# Custom helper function to detect if user is logged in or not.
@core_helper
def logged_in():
    if not g.user:
        return False
    return True

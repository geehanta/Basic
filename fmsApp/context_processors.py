def user_roles(request):
    roles = []
    if request.user.is_authenticated:
        if request.user.groups.filter(name="staff").exists():
            roles.append("staff")
        if request.user.groups.filter(name="reviewer").exists():
            roles.append("reviewer")
    return {"roles": roles}

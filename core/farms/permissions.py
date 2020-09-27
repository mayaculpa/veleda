from rest_framework import permissions


class ControllerAPIPermission(permissions.BasePermission):
    """
    Checks requests regarding controllers. Only the owner of the site to which
    the controller is registered is granted permission.
    """

    def has_object_permission(self, request, view, obj):
        if obj.site:
            return obj.site.owner == request.user
        return False

from django.urls import path

from user_management.forms import AccessRequestApprovalForm

from . import views

app_name = "user-management"
urlpatterns = [
    path(
        "request-access/intro",
        views.AccessRequestIntroView.as_view(),
        name="access-request-intro",
    ),
    path(
        "request-access",
        views.AccessRequestFormWizard.as_view(
            views.ACCESS_REQUEST_FORMS,
            condition_dict=views.ACCESS_REQUEST_FORMS_CONDITIONAL_DICT,
        ),
        name="access-request-form",
    ),
    path(
        "request-access/your-requests/<str:pk>",
        views.AccessRequestYourRequestView.as_view(),
        name="access-request-your-request",
    ),
    path(
        "confirmation",
        views.AccessRequestFormConfirmationPageView.as_view(),
        name="access-request-confirmation",
    ),
    path(
        "access-requests",
        views.AccessRequestsListView.as_view(),
        name="access-requests",
    ),
    path(
        "access-requests/<str:pk>",
        views.AccessRequestsDetailsPage.as_view(
            [("approval", AccessRequestApprovalForm)]
        ),
        name="access-request-details",
    ),
    path(
        "access-requests/<str:pk>/hide-request",
        views.AccessRequestHideRequest.as_view(),
        name="hide-access-request",
    ),
    path(
        "users",
        views.UserListView.as_view(),
        name="users",
    ),
    path(
        "users/<str:pk>",
        views.UserDetailsView.as_view(),
        name="user-details",
    ),
    path(
        "users/<str:user_pk>/remove-from-group/<str:group_pk>",
        views.UserRemoveGroupView.as_view(),
        name="user-remove-from-group",
    ),
    path(
        "groups",
        views.GroupListView.as_view(),
        name="groups",
    ),
    path(
        "groups/<str:pk>",
        views.GroupDetailsView.as_view(),
        name="group-details",
    ),
    path(
        "groups/<str:group_pk>/remove-user/<str:user_pk>",
        views.GroupRemoveUserView.as_view(),
        name="group-remove-user",
    ),
]

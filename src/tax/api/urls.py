from django.urls import path

from .views import TaxCaseStatusAPIView

urlpatterns = [
    path(
        "tax-cases/<uuid:tax_case_id>/status/",
        TaxCaseStatusAPIView.as_view(),
        name="tax-case-status",
    ),
]
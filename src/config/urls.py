from django.urls import include, path
from tax.api.documents import DocumentUploadAPIView
from tax.api.collection_status import (
    CollectionStatusAPIView,
)
from tax.api.document_review import (
    DocumentReviewAPIView,
)
from tax.api.document_review_resolution import (
    DocumentReviewResolutionAPIView,
)
from tax.api.tax_cases import TaxCaseListAPIView

"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include("tax.api.urls"),
    ),
    path(
    "api/tax-cases/<uuid:tax_case_id>/documents/",
    DocumentUploadAPIView.as_view(),
    name="document-upload",
    ),
    path(
        "api/tax-cases/<uuid:tax_case_id>/collection-status/",
        CollectionStatusAPIView.as_view(),
        name="collection-status",
    ),
    path(
        "api/tax-cases/<uuid:tax_case_id>/reviews/",
        DocumentReviewAPIView.as_view(),
        name="document-review",
    ),
    path(
        "api/documents/<uuid:document_id>/classification/",
        DocumentReviewResolutionAPIView.as_view(),
        name="document-review-resolution",
    ),
    path(
        "api/tax-cases/",
        TaxCaseListAPIView.as_view(),
        name="tax-case-list",
    ),
    
]

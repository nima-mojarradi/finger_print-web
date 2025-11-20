from django.contrib import admin
from .models import Address, CustomUser, Company, Fingerprint

admin.site.register(Address)
admin.site.register(CustomUser)
admin.site.register(Company)
# admin.site.register(Fingerprint)
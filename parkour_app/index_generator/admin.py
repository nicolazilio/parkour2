from django.conf import settings
from django.contrib import admin
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter

from .models import Pool, PoolSize


class BaseInline(admin.TabularInline):
    fields = (
        "name",
        "barcode",
        "status",
        "request",
    )
    readonly_fields = (
        "name",
        "barcode",
        "status",
        "request",
    )
    can_delete = False
    extra = 0

    @admin.display(description="Name")
    def name(self, instance):
        return getattr(instance, self.verbose_name.lower()).name

    @admin.display(description="Barcode")
    def barcode(self, instance):
        return getattr(instance, self.verbose_name.lower()).barcode

    @admin.display(description="Status")
    def status(self, instance):
        return getattr(instance, self.verbose_name.lower()).status

    @admin.display(description="Request")
    def request(self, instance):
        return getattr(instance, self.verbose_name.lower()).request.get().name

    def has_add_permission(self, request, obj=None):
        return False


class LibraryInline(BaseInline):
    model = Pool.libraries.through
    verbose_name = "Library"
    verbose_name_plural = "Libraries"


class SampleInline(BaseInline):
    model = Pool.samples.through
    verbose_name = "Sample"
    verbose_name_plural = "Sample"


@admin.register(Pool)
class PoolAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "size",
    )
    search_fields = (
        "name",
        "size__multiplier",
        "size__size",
    )
    list_filter = (("size", RelatedDropdownFilter),)
    inlines = [LibraryInline, SampleInline]
    exclude = (
        "libraries",
        "samples",
    )


@admin.register(PoolSize)
class PoolSizeAdmin(admin.ModelAdmin):
    list_display = ("name", "obsolete_name")
    actions = (
        "mark_as_obsolete",
        "mark_as_non_obsolete",
    )

    @admin.action(description="Mark pool size as obsolete")
    def mark_as_obsolete(self, request, queryset):
        queryset.update(obsolete=settings.OBSOLETE)

    @admin.action(description="Mark pool size as non-obsolete")
    def mark_as_non_obsolete(self, request, queryset):
        queryset.update(obsolete=settings.NON_OBSOLETE)

    @admin.display(description="STATUS")
    def obsolete_name(self, obj):
        return "Non-obsolete" if obj.obsolete == settings.NON_OBSOLETE else "Obsolete"

from django.conf import settings
from django.contrib import admin
from django.urls import resolve
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin

from .forms import IndexTypeForm
from .models import (
    ConcentrationMethod,
    IndexI5,
    IndexI7,
    IndexPair,
    IndexType,
    LibraryProtocol,
    LibraryType,
    Organism,
    ReadLength,
)


@admin.register(Organism)
class OrganismAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "scientific_name",
        "taxon_id",
    )


@admin.register(ConcentrationMethod)
class ConcentrationMethodAdmin(admin.ModelAdmin):
    pass


@admin.register(ReadLength)
class ReadLengthAdmin(admin.ModelAdmin):
    list_display = ("name", "obsolete_name")
    actions = ("mark_as_obsolete", "mark_as_non_obsolete")

    @admin.action(description="Mark read length as obsolete")
    def mark_as_obsolete(self, request, queryset):
        queryset.update(obsolete=settings.OBSOLETE)

    @admin.action(description="Mark read length as non-obsolete")
    def mark_as_non_obsolete(self, request, queryset):
        queryset.update(obsolete=settings.NON_OBSOLETE)

    @admin.display(description="STATUS")
    def obsolete_name(self, obj):
        return "Non-obsolete" if obj.obsolete == settings.NON_OBSOLETE else "Obsolete"


class IndexI7Inline(admin.TabularInline):
    model = IndexI7
    extra = 2


class IndexPairInline(admin.TabularInline):
    model = IndexPair
    extra = 2

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        args = resolve(request.path_info).args
        index_type_id = args[0] if args else None

        if db_field.name == "index1":
            kwargs["queryset"] = IndexI7.objects.filter(index_type__id=index_type_id)

        elif db_field.name == "index2":
            kwargs["queryset"] = IndexI5.objects.filter(index_type__id=index_type_id)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(IndexType)
class IndexTypeAdmin(admin.ModelAdmin):
    form = IndexTypeForm
    list_display = ("name", "index_length", "is_dual", "format", "obsolete_name")
    filter_horizontal = (
        "indices_i7",
        "indices_i5",
    )
    actions = (
        "mark_as_obsolete",
        "mark_as_non_obsolete",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "read_type",
                    "index_length",
                    "format",
                    "is_dual",
                    "indices_i7",
                    "indices_i5",
                ),
            },
        ),
    )

    @admin.action(description="Mark index type as obsolete")
    def mark_as_obsolete(self, request, queryset):
        queryset.update(obsolete=settings.OBSOLETE)

    @admin.action(description="Mark index type as non-obsolete")
    def mark_as_non_obsolete(self, request, queryset):
        queryset.update(obsolete=settings.NON_OBSOLETE)

    @admin.display(description="STATUS")
    def obsolete_name(self, obj):
        return "Non-obsolete" if obj.obsolete == settings.NON_OBSOLETE else "Obsolete"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        # Display inline when the object has been saved and
        # the format has been set to 'plate'
        self.inlines = []
        try:
            obj = self.model.objects.get(pk=object_id)
        except self.model.DoesNotExist:
            pass
        else:
            if obj.format == "plate":
                self.inlines = [IndexPairInline]
        return super().change_view(request, object_id, form_url, extra_context)


from import_export import fields, resources
# from import_export.admin import ImportMixin

from import_export.widgets import ForeignKeyWidget

class IndexPairImportResource(resources.ModelResource):

    index_type = fields.Field(
        column_name='index_type_name',
        attribute='name',
        widget=ForeignKeyWidget(IndexType, field='name'))

    index_i7_prefix = fields.Field(
        column_name='index_i7_prefix',
        attribute='prefix',
        widget=ForeignKeyWidget(IndexI7, field='prefix'))
    
    index_i7_number = fields.Field(
        column_name='index_i7_number',
        attribute='number',
        widget=ForeignKeyWidget(IndexI7, field='number'))

    index_i7_index = fields.Field(
        column_name='index_i7_index',
        attribute='index',
        widget=ForeignKeyWidget(IndexI7, field='index'))

    index_i5_prefix = fields.Field(
        column_name='index_i5_prefix',
        attribute='prefix',
        widget=ForeignKeyWidget(IndexI5, field='prefix'))

    index_i5_number = fields.Field(
        column_name='index_i5_number',
        attribute='number',
        widget=ForeignKeyWidget(IndexI5, field='number'))
    
    index_i5_index = fields.Field(
        column_name='index_i5_index',
        attribute='index',
        widget=ForeignKeyWidget(IndexI5, field='index'))

    class Meta:
        model = IndexPair
        fields = ('index_type', 'index_i7_prefix', 'index_i7_number',
                  'index_i7_index', 'index_i5_prefix', 'index_i5_number',
                  'index_i5_index', 'char_coord', 'num_coord')
        import_id_fields = ('index_type',)


    def before_import_row(self, row, **kwargs):
        logger.error(row)

import logging
logger = logging.Logger('django')
@admin.register(IndexPair)
class IndexPairAdmin(ImportExportModelAdmin):
    list_display = (
        "index_pair",
        "coordinate",
    )
    search_fields = ("index_type__name",)
    list_filter = ("index_type",)
    # resource_classes = [IndexPairImportResource]

    def index_pair(self, obj):
        return str(obj)

    def render_change_form(self, request, context, *args, **kwargs):
        context["adminform"].form.fields[
            "index_type"
        ].queryset = IndexType.objects.filter(format="plate")
        return super().render_change_form(request, context, args, kwargs)


class IndexI5Resource(resources.ModelResource):
    class Meta:
        model = IndexI5
        skip_unchanged = True
        fields = (
            "id",
            "prefix",
            "number",
            "index",
            "index_type__name",
        )


@admin.register(IndexI5)
class IndexI5Admin(ImportExportModelAdmin):
    list_display = (
        "idx_id",
        "index",
        "type",
    )
    search_fields = (
        "index",
        "index_type__name",
    )
    list_filter = (("index_type", RelatedDropdownFilter),)

    resource_class = IndexI5Resource

    @admin.display(description="Index ID")
    def idx_id(sef, obj):
        return obj.prefix + obj.number


class IndexI7Resource(resources.ModelResource):
    class Meta:
        model = IndexI7
        skip_unchanged = True
        fields = (
            "id",
            "prefix",
            "number",
            "index",
            "index_type__name",
        )


@admin.register(IndexI7)
class IndexI7Admin(ImportExportModelAdmin):
    list_display = (
        "idx_id",
        "index",
        "type",
    )
    search_fields = (
        "index",
        "index_type__name",
    )
    list_filter = (("index_type", RelatedDropdownFilter),)

    resource_class = IndexI7Resource

    @admin.display(description="Index ID")
    def idx_id(sef, obj):
        return obj.prefix + obj.number


@admin.register(LibraryProtocol)
class LibraryProtocolAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "type",
        "provider",
        "catalog",
        "typical_application",
        "obsolete_name",
    )
    search_fields = (
        "name",
        "provider",
        "catalog",
        "typical_application",
    )
    list_filter = ("type",)
    actions = (
        "mark_as_obsolete",
        "mark_as_non_obsolete",
    )

    @admin.action(description="Mark library protocol as obsolete")
    def mark_as_obsolete(self, request, queryset):
        queryset.update(obsolete=settings.OBSOLETE)

    @admin.action(description="Mark library protocol as non-obsolete")
    def mark_as_non_obsolete(self, request, queryset):
        queryset.update(obsolete=settings.NON_OBSOLETE)

    @admin.display(description="STATUS")
    def obsolete_name(self, obj):
        return "Non-obsolete" if obj.obsolete == settings.NON_OBSOLETE else "Obsolete"


@admin.register(LibraryType)
class LibraryTypeAdmin(admin.ModelAdmin):
    filter_horizontal = ("library_protocol",)

from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class ManifestStaticFilesStorageWithJsImports(ManifestStaticFilesStorage):
    """ManifestStaticFilesStorage that also rewrites ES module import/export
    paths in JS files to point at their fingerprinted equivalents.
    """

    support_js_module_import_aggregation = True

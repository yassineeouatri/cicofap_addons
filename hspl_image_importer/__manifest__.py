{
    "name": "Image Importer",
    "summary": """
        Import Image file in to the appropriate record""",
    "description": """
        Module helps to add image from the csv or xls file.
    """,
    "author": "Heliconia Solutions Pvt. Ltd.",
    "category": "Tools",
    "website": "https://heliconia.io",
    "version": "15.0.0.1.0",
    "license": "OPL-1",
    "depends": ["base"],
    "external_dependencies": {
        "python": ["xlrd"],
    },
    "data": [
        "security/ir.model.access.csv",
        "wizard/image_importer_wizard_views.xml",
    ],
}

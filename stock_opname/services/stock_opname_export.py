HEADER_HTML_WITH_CURRENT_STOCK = """
<html>
<body>
    <h1>Stock Opname</h1>
    <h2>Date: {date}</h2>
    <table style="width: 100%; border-collapse: collapse; border: 1px solid black; page-break-inside: avoid;">
        <tr>
            <th style="border: 1px solid black; padding: 8px; text-align: left;">SKU</th>
            <th style="border: 1px solid black; padding: 8px; text-align: left;">Product Name</th>
            <th style="border: 1px solid black; padding: 8px; text-align: left;">Current Stock</th>
            <th style="border: 1px solid black; padding: 8px; text-align: left;">Unit</th>
            <th style="border: 1px solid black; padding: 8px; text-align: left;">Real Stock</th>
        </tr>
"""

HEADER_HTML_NO_CURRENT_STOCK = """
<html>
    <body>
        <h1>Stock Opname</h1>
        <h2>Date: {date}</h2>
        <table style="width: 100%; border-collapse: collapse; border: 1px solid black; page-break-inside: avoid;">
            <tr>
                <th style="border: 1px solid black; padding: 8px; text-align: left;">SKU</th>
                <th style="border: 1px solid black; padding: 8px; text-align: left;">Product Name</th>
                <th style="border: 1px solid black; padding: 8px; text-align: left;">Unit</th>
                <th style="border: 1px solid black; padding: 8px; text-align: left;">Real Stock</th>
            </tr>
"""

FOOTER_HTML = """</table></body></html>"""



"""
Excel to PDF converter using win32com
"""
import win32com.client
import os

def excel_to_pdf(excel_path, pdf_path=None):
    """Convert Excel file to PDF"""
    excel_path = os.path.abspath(excel_path)

    if pdf_path is None:
        pdf_path = excel_path.replace('.xlsx', '.pdf')
    else:
        pdf_path = os.path.abspath(pdf_path)

    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    try:
        wb = excel.Workbooks.Open(excel_path)
        wb.ExportAsFixedFormat(0, pdf_path)  # 0 = PDF format
        wb.Close(False)
        print(f"PDF created: {pdf_path}")
        return pdf_path
    finally:
        excel.Quit()

if __name__ == "__main__":
    input_file = "c:/Users/koyom/agent-workspaces/workspaces/sasoli0502/misc-tasks/invoice_hyoryodo_20260128.xlsx"
    output_file = "c:/Users/koyom/agent-workspaces/workspaces/sasoli0502/misc-tasks/invoice_hyoryodo_20260128.pdf"
    excel_to_pdf(input_file, output_file)

import asyncio
import pandas as pd
import os

def creator_excel_doctor(data,filename="doctors_list.xlsx"):
  if not data:
    print("❌ [ERROR] NO DATA FOR EXCEL")
    return None
  try:
    if isinstance(data,dict):
      data = [data]

    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
      os.makedirs(directory)
      print(f"📁 Created directory: {directory}")

      
    df = pd.DataFrame(data)
    df.rename(columns={
      'name': 'Name',
      'ph_number': 'Phone number',
      'near_date': 'Nearest date', 
      'street' : 'Street',
      'link': 'URL'
    }, inplace=True)

    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
      sheet_name = 'Doctors'
      df.to_excel(writer, index=False, sheet_name=sheet_name)
      
      worksheet = writer.sheets[sheet_name]
      
      for i, col in enumerate(df.columns):
        max_len_data = df[col].astype(str).map(len).max()
        if pd.isna(max_len_data): max_len_data = 0
        
        max_len = max(max_len_data, len(str(col))) + 2 
        worksheet.set_column(i, i, max_len)
    
    print("✅  Excel file was created!")
    return os.path.abspath(filename)
  except Exception as e:
    print(f"❌ [ERROR] while creating Excel: {e}")
    return None
  

def creator_excel_product(data,filename = 'products_list.xlsx'):
  if not data:
    print("❌ [ERROR] NO DATA FOR EXCEL")
    return None
  
  try:
    if isinstance(data,dict):
      data = [data]

    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
      os.makedirs(directory)
      print(f"📁 Created directory: {directory}")

    df = pd.DataFrame(data)
    df.rename(columns={
      'name' : 'Name',
      'price' : 'Price',
      'review' : 'Review',
      'link' : 'URL'
    }, inplace=True)

    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
      sheet_name = 'Products'
      df.to_excel(writer, index=False, sheet_name=sheet_name)
      
      worksheet = writer.sheets[sheet_name]
      
      for i, col in enumerate(df.columns):
        max_len_data = df[col].astype(str).map(len).max()
        if pd.isna(max_len_data): max_len_data = 0
        
        max_len = max(max_len_data, len(str(col))) + 2 
        worksheet.set_column(i, i, max_len)
    
    print("✅  Excel file was created!")
    return os.path.abspath(filename)
  except Exception as e:
    print(f"❌ [ERROR] while creating Excel: {e}")
    return None
  

async def excel_file_doctor(data,filename="doctors_list.xlsx"):
  result = await asyncio.to_thread(creator_excel_doctor,data,filename)
  return result

async def excel_file_product(data, filename='products_list.xlsx'):
  result = await asyncio.to_thread(creator_excel_product,data,filename)
  return result